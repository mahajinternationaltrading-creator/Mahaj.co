#!/usr/bin/env python3
"""mit_eventss AI Studio — footage pipeline and draft renderer.

One script, one event workspace, originals are NEVER written to.

Stages (run in order; every stage is cached and incremental):
  scan      A  ffprobe inventory of the source folder (read-only)
  detect    B  keyframe-first, adaptive sampling: scene cuts, blur, exposure,
               black frames, motion/camera move, near-duplicates
  preview   C  per-clip contact sheets + ranked candidate pages (for AI review)
  database  D  footage_database.csv (technical prior + AI annotations merged)
  annotate     merge Media Analyst annotations (JSON) into the database
  approve   E  validate APPROVED_FOOTAGE.json written by the Creative Director
  extract   F  stream-copy approved segments (no re-encode) for CapCut hand-off
  render    G  render a 9:16 draft from an edit decision list (reads originals)
  qc           automatic technical QC + review sheet for the Quality Controller
  verify       prove originals are unchanged (size + mtime vs scan snapshot)
  status       short machine summary for the Studio Manager

Requirements: ffmpeg/ffprobe on PATH, Python 3.9+, numpy, Pillow.
  macOS:  brew install ffmpeg && python3 -m pip install numpy pillow
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

PIPELINE_VERSION = "1.2"
VIDEO_EXT = {".mp4", ".mov", ".m4v", ".mkv", ".avi", ".mts", ".m2ts", ".3gp", ".webm"}
ANALYSIS_LONG_SIDE = 320          # analysis frame size (long side, px)
KEYFRAME_MAX_GAP = 1.5            # s; sparser keyframes -> fall back to 1 fps decode
REFINE_DIFF = 0.25                # histogram diff that triggers adaptive refinement
CUT_DIFF = 0.45                   # histogram diff that marks a scene cut ...
CUT_MAX_CORR = 0.55               # ... only if structure also changed (luma correlation below)
REFINE_CORR = 0.75                # ... or structural change below this
SCDET_THRESHOLD = 10              # ffmpeg scdet score (0-100) for a frame-accurate cut
REFINE_FPS = 4
MAX_REFINE_SECONDS = 60           # per clip
MIN_SEGMENT = 0.8                 # s
DUP_HAMMING = 6                   # dHash bits

BRAND = {  # mit_eventss — keep in sync with PROJECT_CONTROL/BRAND_mit_eventss.md
    "name": "mit_eventss",
    "red": "0xB62125",
    "green": "0x597832",
    "dark": "0x111111",
}

SUBDIRS = ["MEDIA_ANALYSIS/cache", "MEDIA_ANALYSIS/thumbs", "MEDIA_ANALYSIS/sheets",
           "APPROVED_FOOTAGE/extracts", "CREATIVE_BRIEFS", "VIDEO_PRODUCTION",
           "QUALITY_CONTROL", "SOCIAL_MEDIA_DELIVERY"]


# --------------------------------------------------------------------------- utils
def run(cmd, capture=True, check=True):
    p = subprocess.run(cmd, stdout=subprocess.PIPE if capture else None,
                       stderr=subprocess.PIPE, check=False)
    if check and p.returncode != 0:
        raise RuntimeError(f"command failed ({p.returncode}): {' '.join(map(str, cmd))}\n"
                           f"{p.stderr.decode(errors='replace')[-2000:]}")
    return p


def tc(sec: float) -> str:
    sec = max(0.0, float(sec))
    m, s = divmod(sec, 60)
    return f"{int(m):02d}:{s:04.1f}"


def load_json(path: Path, default=None):
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return default


def save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)


def font(size: int):
    for f in ["/System/Library/Fonts/Supplemental/Arial Bold.ttf",
              "/System/Library/Fonts/Helvetica.ttc",
              "/Library/Fonts/Arial.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]:
        if os.path.exists(f):
            try:
                return ImageFont.truetype(f, size)
            except OSError:
                pass
    return ImageFont.load_default()


def drawtext_font() -> str:
    for f in ["/System/Library/Fonts/Supplemental/Arial Bold.ttf",
              "/Library/Fonts/Arial Bold.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]:
        if os.path.exists(f):
            return f
    raise RuntimeError("no font found for drawtext; set a fontfile in the EDL")


class Workspace:
    def __init__(self, root: Path):
        self.root = root
        self.ma = root / "MEDIA_ANALYSIS"
        self.cache = self.ma / "cache"
        self.thumbs = self.ma / "thumbs"
        self.sheets = self.ma / "sheets"
        self.inventory = self.ma / "inventory.json"
        self.db_csv = self.ma / "footage_database.csv"
        self.annotations = self.ma / "annotations.json"
        self.approved = root / "APPROVED_FOOTAGE" / "APPROVED_FOOTAGE.json"
        self.extracts = root / "APPROVED_FOOTAGE" / "extracts"
        self.briefs = root / "CREATIVE_BRIEFS"
        self.prod = root / "VIDEO_PRODUCTION"
        self.qc = root / "QUALITY_CONTROL"
        self.log = root / "production_log.csv"
        self.event = root / "event.json"

    def init(self, source: Path | None):
        for d in SUBDIRS:
            (self.root / d).mkdir(parents=True, exist_ok=True)
        ev = load_json(self.event, {})
        if source:
            ev["source"] = str(source.resolve())
        ev.setdefault("event_code", self.root.name)
        ev.setdefault("created", dt.datetime.now().isoformat(timespec="seconds"))
        save_json(self.event, ev)

    def source(self) -> Path:
        ev = load_json(self.event, {})
        if not ev.get("source"):
            sys.exit("workspace has no source folder; run: scan --source <folder>")
        return Path(ev["source"])

    def logrow(self, stage, seconds, **kw):
        new = not self.log.exists()
        with self.log.open("a", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            if new:
                w.writerow(["timestamp", "stage", "seconds", "details"])
            w.writerow([dt.datetime.now().isoformat(timespec="seconds"), stage,
                        f"{seconds:.1f}", json.dumps(kw, ensure_ascii=False)])


# --------------------------------------------------------------------------- A scan
def probe(path: Path) -> dict:
    p = run(["ffprobe", "-v", "error", "-print_format", "json", "-show_format",
             "-show_streams", str(path)], check=False)
    if p.returncode != 0:
        return {"error": p.stderr.decode(errors="replace")[-300:]}
    j = json.loads(p.stdout or b"{}")
    v = next((s for s in j.get("streams", []) if s.get("codec_type") == "video"), None)
    a = next((s for s in j.get("streams", []) if s.get("codec_type") == "audio"), None)
    if not v:
        return {"error": "no video stream"}
    rot = 0
    for sd in v.get("side_data_list", []) or []:
        if "rotation" in sd:
            rot = int(round(float(sd["rotation"])))
    rot = int(v.get("tags", {}).get("rotate", rot))
    w, h = int(v["width"]), int(v["height"])
    dw, dh = (h, w) if abs(rot) % 180 == 90 else (w, h)
    num, den = (v.get("avg_frame_rate") or "0/1").split("/")
    fps = float(num) / float(den) if float(den) else 0.0
    dur = float(j.get("format", {}).get("duration") or v.get("duration") or 0)
    return {
        "codec": v.get("codec_name"), "width": dw, "height": dh, "coded_w": w, "coded_h": h,
        "rotation": rot, "fps": round(fps, 3), "duration": round(dur, 3),
        "orientation": "vertical" if dh > dw else ("square" if dh == dw else "horizontal"),
        "bitrate": int(j.get("format", {}).get("bit_rate") or 0),
        "pix_fmt": v.get("pix_fmt"), "color_transfer": v.get("color_transfer"),
        "audio": bool(a), "audio_codec": a.get("codec_name") if a else None,
        "creation_time": j.get("format", {}).get("tags", {}).get("creation_time"),
    }


def cmd_scan(ws: Workspace, args):
    t0 = time.time()
    if args.source:
        src = Path(args.source)
        if not src.is_dir():
            sys.exit(f"source folder not found: {src}")
        ws.init(src)
    else:
        ws.init(None)
    src = ws.source()
    inv = load_json(ws.inventory, {"clips": {}, "next_id": 1})
    by_rel = {c["relpath"]: cid for cid, c in inv["clips"].items()}
    found, probed, cached = 0, 0, 0
    seen = set()
    for p in sorted(src.rglob("*")):
        if not p.is_file() or p.suffix.lower() not in VIDEO_EXT or p.name.startswith("._"):
            continue
        found += 1
        rel = str(p.relative_to(src))
        st = p.stat()
        cid = by_rel.get(rel)
        if cid and inv["clips"][cid]["size"] == st.st_size and inv["clips"][cid]["mtime"] == st.st_mtime:
            cached += 1
            seen.add(cid)
            continue
        if not cid:
            cid = f"C{inv['next_id']:04d}"
            inv["next_id"] += 1
        meta = probe(p)
        probed += 1
        inv["clips"][cid] = {"clip_id": cid, "relpath": rel, "size": st.st_size,
                             "mtime": st.st_mtime, **meta}
        seen.add(cid)
    for cid, c in inv["clips"].items():
        c["missing"] = cid not in seen
    inv["scanned"] = dt.datetime.now().isoformat(timespec="seconds")
    save_json(ws.inventory, inv)
    clips = [c for c in inv["clips"].values() if not c.get("missing")]
    gb = sum(c["size"] for c in clips) / 1e9
    mins = sum(c.get("duration", 0) for c in clips) / 60
    ws.logrow("scan", time.time() - t0, found=found, probed=probed, cached=cached, gb=round(gb, 2))
    print(f"scan: {found} videos, {mins:.1f} min, {gb:.2f} GB | probed {probed}, cached {cached}")


# --------------------------------------------------------------------------- B detect
def analysis_size(meta):
    w, h = meta["width"], meta["height"]
    s = ANALYSIS_LONG_SIDE / max(w, h)
    return max(2, int(round(w * s / 2)) * 2), max(2, int(round(h * s / 2)) * 2)


def decode_frames(path: Path, size, mode: str, start=None, dur=None, fps=1.0, scd=False):
    """Return (times[], frames[N,H,W,3] uint8, scene_cut_times[]). mode: key | fps.
    scd=True runs ffmpeg scdet on every decoded frame (frame-accurate cuts, no extra decode)."""
    W, H = size
    cmd = ["ffmpeg", "-hide_banner", "-nostdin", "-loglevel", "info"]
    if mode == "key":
        cmd += ["-skip_frame", "nokey"]
    if start is not None:
        cmd += ["-ss", f"{start:.3f}"]
    if dur is not None:
        cmd += ["-t", f"{dur:.3f}"]
    vf = f"scale={W}:{H}:flags=area,"
    if scd and mode == "fps":
        vf += f"scdet=threshold={SCDET_THRESHOLD}:sc_pass=0,"
    if mode == "fps":
        vf += f"fps={fps},"
    vf += "format=rgb24,showinfo"
    cmd += ["-i", str(path), "-an", "-sn", "-vf", vf, "-fps_mode", "passthrough",
            "-f", "rawvideo", "-"]
    p = run(cmd, check=False)
    raw = p.stdout
    n = len(raw) // (W * H * 3)
    times = [float(x) for x in re.findall(rb"pts_time:\s*([-\d.]+)", p.stderr)]
    n = min(n, len(times))
    off = start or 0.0
    cuts = [float(x) + off for x in re.findall(rb"lavfi\.scd\.time:\s*([-\d.]+)", p.stderr)]
    if n == 0:
        return [], np.zeros((0, H, W, 3), np.uint8), cuts
    frames = np.frombuffer(raw[: n * W * H * 3], np.uint8).reshape(n, H, W, 3)
    return [t + off for t in times[:n]], frames, cuts


def frame_metrics(fr: np.ndarray):
    g = fr.astype(np.float32) @ np.array([0.299, 0.587, 0.114], np.float32)
    lap = (-4 * g[1:-1, 1:-1] + g[:-2, 1:-1] + g[2:, 1:-1] + g[1:-1, :-2] + g[1:-1, 2:])
    hist = np.concatenate([np.histogram(fr[..., c], bins=16, range=(0, 256))[0] for c in range(3)])
    hist = hist / max(1, hist.sum() / 3)
    small = np.asarray(Image.fromarray(g.astype(np.uint8)).resize((64, 36), Image.BILINEAR), np.float32)
    return {
        "luma": float(g.mean()),
        "dark": float((g < 20).mean()),
        "bright": float((g > 245).mean()),
        "sharp": float(lap.var()),
        "sat": float((fr.max(axis=2).astype(np.int16) - fr.min(axis=2)).mean()),
        "_hist": hist,
        "_small": small,
    }


def is_cut(prev: dict, cur: dict):
    """Scene cut = colour histogram jump AND structural change (not a lighting change)."""
    diff = 0.5 * float(np.abs(cur["_hist"] - prev["_hist"]).sum())
    a, b = cur["_small"] - cur["_small"].mean(), prev["_small"] - prev["_small"].mean()
    corr = float((a * b).sum() / (np.sqrt((a ** 2).sum() * (b ** 2).sum()) + 1e-6))
    return diff, corr, diff > CUT_DIFF and corr < CUT_MAX_CORR


def phase_shift(a: np.ndarray, b: np.ndarray):
    A, B = np.fft.fft2(a - a.mean()), np.fft.fft2(b - b.mean())
    R = A * np.conj(B)
    R /= np.abs(R) + 1e-6
    r = np.fft.ifft2(R).real
    y, x = np.unravel_index(np.argmax(r), r.shape)
    if y > r.shape[0] // 2:
        y -= r.shape[0]
    if x > r.shape[1] // 2:
        x -= r.shape[1]
    return float(x), float(y)


def dhash(fr: np.ndarray) -> int:
    g = Image.fromarray(fr).convert("L").resize((9, 8), Image.BILINEAR)
    a = np.asarray(g, np.int16)
    bits = (a[:, 1:] > a[:, :-1]).flatten()
    return int("".join("1" if b else "0" for b in bits), 2)


def analyse_clip(src: Path, meta: dict, thumbs: Path):
    path = src / meta["relpath"]
    size = analysis_size(meta)
    dur = meta.get("duration") or 0
    times, frames, _ = decode_frames(path, size, "key")
    mode = "keyframes"
    scd_cuts = []
    gaps = np.diff(times) if len(times) > 1 else np.array([dur])
    if len(times) < 3 or float(np.mean(gaps)) > KEYFRAME_MAX_GAP:
        fps = 1.0 if dur > 20 else 2.0
        times, frames, scd_cuts = decode_frames(path, size, "fps", fps=fps, scd=True)
        mode = f"{fps:g}fps+scdet"
    if len(times) == 0:
        return {"error": "no frames decoded", "segments": []}
    samples = [dict(t=t, **frame_metrics(f)) for t, f in zip(times, frames)]
    frames = list(frames)

    # adaptive refinement: decode more where the picture changes fast
    refine_budget = MAX_REFINE_SECONDS
    extra = []
    for i in range(1, len(samples)):
        d, corr, _ = is_cut(samples[i - 1], samples[i])
        gap = samples[i]["t"] - samples[i - 1]["t"]
        if mode == "keyframes" and (d > REFINE_DIFF or corr < REFINE_CORR) \
                and gap > 1.0 / REFINE_FPS * 1.5 and refine_budget > 0:
            span = min(gap, refine_budget)
            et, ef, wc = decode_frames(path, size, "fps", start=samples[i - 1]["t"], dur=span,
                                       fps=REFINE_FPS, scd=True)
            scd_cuts += wc
            refine_budget -= span
            for t, f in zip(et, ef):
                if samples[i - 1]["t"] + 0.05 < t < samples[i]["t"] - 0.05:
                    extra.append((t, f))
    for t, f in extra:
        samples.append(dict(t=t, **frame_metrics(f)))
        frames.append(f)
    order = np.argsort([s["t"] for s in samples])
    samples = [samples[i] for i in order]
    frames = [frames[i] for i in order]

    # motion + cuts
    cuts = []
    for i, s in enumerate(samples):
        if i == 0:
            s["diff"], s["motion"], s["dx"], s["dy"] = 0.0, 0.0, 0.0, 0.0
            continue
        p = samples[i - 1]
        gap = max(1e-3, s["t"] - p["t"])
        s["diff"], s["corr"], cut = is_cut(p, s)
        s["motion"] = float(np.abs(s["_small"] - p["_small"]).mean()) / min(1.0, gap) ** 0.5
        s["dx"], s["dy"] = phase_shift(s["_small"], p["_small"])
        if cut and mode == "keyframes":
            cuts.append(s["t"])

    # segments: frame-accurate scdet cuts + keyframe-level cuts, merged within 0.3 s
    allc = []
    for c in sorted(cuts + scd_cuts):
        if 0.2 < c < dur - 0.2 and (not allc or c - allc[-1] > 0.3):
            allc.append(c)
    cuts = allc
    bounds = [0.0] + [c for c in cuts] + [max(dur, samples[-1]["t"] + 0.1)]
    merged = [bounds[0]]
    for b in bounds[1:-1]:
        if b - merged[-1] >= MIN_SEGMENT:
            merged.append(b)
    merged.append(bounds[-1])
    if len(merged) > 2 and merged[-1] - merged[-2] < MIN_SEGMENT:
        merged.pop(-2)
    segs = []
    for k in range(len(merged) - 1):
        a, b = merged[k], merged[k + 1]
        idx = [i for i, s in enumerate(samples) if a - 1e-3 <= s["t"] < b - 1e-3] or \
              [min(range(len(samples)), key=lambda i: abs(samples[i]["t"] - (a + b) / 2))]
        ss = [samples[i] for i in idx]
        best = max(idx, key=lambda i: samples[i]["sharp"])
        mid = [s for s in ss if s is not ss[0]] or ss  # first sample may straddle the cut
        dxs = [abs(s["dx"]) for s in mid]
        dys = [abs(s["dy"]) for s in mid]
        mot = float(np.median([s["motion"] for s in mid]))
        if np.median(dxs + [0]) >= 2:
            cam = "pan"
        elif np.median(dys + [0]) >= 2:
            cam = "tilt"
        elif mot > 6:
            cam = "handheld/active"
        else:
            cam = "static"
        seg_id = f"{meta['clip_id']}-S{k + 1:02d}"
        Image.fromarray(frames[best]).save(thumbs / f"{seg_id}.jpg", quality=82)
        segs.append({
            "seg_id": seg_id, "clip_id": meta["clip_id"], "start": round(a, 2), "end": round(b, 2),
            "duration": round(b - a, 2), "samples": len(ss), "thumb_t": round(samples[best]["t"], 2),
            "luma": round(float(np.median([s["luma"] for s in ss])), 1),
            "dark": round(float(np.median([s["dark"] for s in ss])), 3),
            "bright": round(float(np.median([s["bright"] for s in ss])), 3),
            "sharp": round(float(np.median([s["sharp"] for s in ss])), 1),
            "sat": round(float(np.median([s["sat"] for s in ss])), 1),
            "motion": round(mot, 2), "camera": cam, "dhash": dhash(frames[best]),
            "sig": [dhash(frames[min(idx, key=lambda i: abs(samples[i]["t"] - (a + q * (b - a))))])
                    for q in (0.25, 0.5, 0.75)],
        })
    return {"mode": mode, "samples": len(samples), "refined": len(extra), "cuts": len(cuts),
            "segments": segs, "pipeline": PIPELINE_VERSION}


def cmd_detect(ws: Workspace, args):
    t0 = time.time()
    inv = load_json(ws.inventory)
    if not inv:
        sys.exit("run scan first")
    src = ws.source()
    done = cached = errors = 0
    budget = args.max_seconds
    for cid, meta in sorted(inv["clips"].items()):
        if meta.get("missing") or meta.get("error"):
            continue
        cf = ws.cache / f"{cid}.json"
        c = load_json(cf)
        if c and c.get("size") == meta["size"] and c.get("mtime") == meta["mtime"] \
                and c.get("pipeline") == PIPELINE_VERSION:
            cached += 1
            continue
        if budget and time.time() - t0 > budget:
            print(f"detect: time budget reached; re-run to continue")
            break
        t1 = time.time()
        try:
            r = analyse_clip(src, meta, ws.thumbs)
        except Exception as e:  # keep going; record the problem
            r = {"error": str(e)[:300], "segments": []}
            errors += 1
        r.update(size=meta["size"], mtime=meta["mtime"], seconds=round(time.time() - t1, 2))
        save_json(cf, r)
        done += 1
        print(f"  {cid} {meta['relpath'][:50]:50s} {r.get('mode','-'):9s} "
              f"{len(r['segments']):3d} seg  {r['seconds']:.1f}s")
    ws.logrow("detect", time.time() - t0, analysed=done, cached=cached, errors=errors)
    print(f"detect: analysed {done}, cached {cached}, errors {errors}, {time.time() - t0:.1f}s")


# --------------------------------------------------------------------------- D database
DB_COLUMNS = ["seg_id", "clip_id", "original_file", "start", "end", "duration",
              "resolution", "orientation", "fps", "technical_quality", "flags", "camera",
              "energy", "visual_description", "people", "emotional_value", "storytelling",
              "marketing", "recommended_use", "tags", "duplicate_of", "selection_score",
              "score_basis", "thumb"]


def build_segments(ws: Workspace):
    inv = load_json(ws.inventory)
    ann = load_json(ws.annotations, {})
    segs = []
    for cid, meta in sorted(inv["clips"].items()):
        c = load_json(ws.cache / f"{cid}.json")
        if not c or meta.get("missing"):
            continue
        for s in c["segments"]:
            s = dict(s)
            s["meta"] = meta
            segs.append(s)
    if not segs:
        return []
    sharp = np.array([s["sharp"] for s in segs])
    mot = np.array([s["motion"] for s in segs])
    med_sharp = float(np.median(sharp))
    rank = lambda arr, v: float((arr < v).mean()) * 100
    for s in segs:
        flags = []
        if s["luma"] < 8:
            flags.append("BLACK")
        elif s["luma"] < 40 or s["dark"] > 0.6:
            flags.append("DARK")
        if s["bright"] > 0.30 or s["luma"] > 200:
            flags.append("OVEREXPOSED")
        if s["sharp"] < max(15.0, 0.30 * med_sharp):
            flags.append("BLURRY")
        if s["duration"] < 1.0:
            flags.append("SHORT")
        expo = 100 - min(100, abs(s["luma"] - 120) * 0.8) - s["bright"] * 100 - max(0, s["dark"] - 0.3) * 100
        tq = 0.55 * rank(sharp, s["sharp"]) + 0.30 * max(0, expo) + 0.15 * min(100, s["duration"] / 3 * 100)
        if {"BLACK", "BLURRY", "OVEREXPOSED"} & set(flags):
            tq *= 0.4
        s["flags"] = flags
        s["tq"] = round(tq, 1)
        s["energy"] = round(rank(mot, s["motion"]), 1)
    # near-duplicates: keep the best of each group
    # keep the master: highest resolution first, then best technical quality
    order = sorted(segs, key=lambda s: (-(s["meta"]["width"] * s["meta"]["height"]), -s["tq"]))
    ham = lambda x, y: bin(x ^ y).count("1")

    def is_dup(s, o):
        if abs(s["luma"] - o["luma"]) >= 15:
            return False
        if ham(s["dhash"], o["dhash"]) <= DUP_HAMMING:           # same static view
            return True
        if s.get("sig") and o.get("sig") and \
                min(s["duration"], o["duration"]) / max(s["duration"], o["duration"]) > 0.85:
            return sorted(ham(x, y) for x, y in zip(s["sig"], o["sig"]))[1] <= DUP_HAMMING + 2
        return False                                                # copied / re-encoded file

    for i, s in enumerate(order):
        s.setdefault("duplicate_of", "")
        if s["duplicate_of"]:
            continue
        for j in range(i + 1, len(order)):
            o = order[j]
            if not o.get("duplicate_of") and is_dup(s, o):
                o["duplicate_of"] = s["seg_id"]
                o["flags"] = o.get("flags", []) + ["DUPLICATE"]
    for s in segs:
        a = ann.get(s["seg_id"], {})
        s["ann"] = a
        ai = [a.get(k) for k in ("emotional_value", "storytelling", "marketing") if isinstance(a.get(k), (int, float))]
        if ai:
            s["score"] = round(0.35 * s["tq"] + 0.15 * s["energy"] + 0.5 * (sum(ai) / len(ai) - 1) / 4 * 100, 1)
            s["basis"] = "technical+AI"
        else:
            s["score"] = round(0.7 * s["tq"] + 0.3 * s["energy"], 1)
            s["basis"] = "technical-prior"
        if s.get("duplicate_of") or {"BLACK", "BLURRY"} & set(s["flags"]):
            s["score"] = round(s["score"] * 0.3, 1)
        if a.get("reject"):
            s["score"] = 0.0
            s["flags"].append("REJECTED-BY-ANALYST")
    return segs


def cmd_database(ws: Workspace, args):
    t0 = time.time()
    segs = build_segments(ws)
    with ws.db_csv.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=DB_COLUMNS)
        w.writeheader()
        for s in sorted(segs, key=lambda s: -s["score"]):
            m, a = s["meta"], s["ann"]
            w.writerow({
                "seg_id": s["seg_id"], "clip_id": s["clip_id"], "original_file": m["relpath"],
                "start": s["start"], "end": s["end"], "duration": s["duration"],
                "resolution": f"{m['width']}x{m['height']}", "orientation": m["orientation"],
                "fps": m["fps"], "technical_quality": s["tq"], "flags": "|".join(s["flags"]),
                "camera": s["camera"], "energy": s["energy"],
                "visual_description": a.get("visual_description", ""), "people": a.get("people", ""),
                "emotional_value": a.get("emotional_value", ""), "storytelling": a.get("storytelling", ""),
                "marketing": a.get("marketing", ""), "recommended_use": a.get("recommended_use", ""),
                "tags": a.get("tags", ""), "duplicate_of": s.get("duplicate_of", ""),
                "selection_score": s["score"], "score_basis": s["basis"],
                "thumb": f"MEDIA_ANALYSIS/thumbs/{s['seg_id']}.jpg",
            })
    bad = sum(1 for s in segs if s["flags"])
    ws.logrow("database", time.time() - t0, segments=len(segs), flagged=bad)
    print(f"database: {len(segs)} segments ({bad} flagged) -> {ws.db_csv.relative_to(ws.root)}")


# --------------------------------------------------------------------------- C preview
def label_tile(img: Image.Image, lines, tw, th, f):
    tile = Image.new("RGB", (tw, th + 34), (17, 17, 17))
    im = img.copy()
    im.thumbnail((tw, th))
    tile.paste(im, ((tw - im.width) // 2, (th - im.height) // 2))
    d = ImageDraw.Draw(tile)
    d.text((4, th + 2), lines[0], fill=(255, 255, 255), font=f)
    d.text((4, th + 18), lines[1], fill=(255, 120, 120) if "!" in lines[1] else (170, 220, 140), font=f)
    return tile


def grid(tiles, cols, title, f):
    if not tiles:
        return None
    tw, th = tiles[0].size
    rows = math.ceil(len(tiles) / cols)
    sheet = Image.new("RGB", (cols * tw + (cols + 1) * 6, rows * th + (rows + 1) * 6 + 30), (40, 40, 40))
    ImageDraw.Draw(sheet).text((8, 6), title, fill=(255, 255, 255), font=f)
    for i, t in enumerate(tiles):
        r, c = divmod(i, cols)
        sheet.paste(t, (6 + c * (tw + 6), 36 + r * (th + 6)))
    return sheet


def cmd_preview(ws: Workspace, args):
    t0 = time.time()
    segs = build_segments(ws)
    f = font(12)
    tw, th = 230, 200
    made = skipped = 0

    def tile(s):
        fl = ("!" + ",".join(s["flags"])) if s["flags"] else s["camera"]
        return label_tile(Image.open(ws.thumbs / f"{s['seg_id']}.jpg"),
                          [f"{s['seg_id']} {tc(s['start'])}-{tc(s['end'])}",
                           f"Q{s['tq']:.0f} E{s['energy']:.0f} {fl}"], tw, th, f)

    by_clip = {}
    for s in segs:
        by_clip.setdefault(s["clip_id"], []).append(s)
    for cid, ss in by_clip.items():
        out = ws.sheets / f"clip_{cid}.jpg"
        cf = ws.cache / f"{cid}.json"
        if out.exists() and out.stat().st_mtime >= cf.stat().st_mtime and not args.force:
            skipped += 1
            continue
        g = grid([tile(s) for s in ss], 6, f"{cid}  {ss[0]['meta']['relpath']}", f)
        g.save(out, quality=80)
        made += 1
    # ranked candidate pages: round-robin across clips for variety
    pool = [s for s in segs if not s.get("duplicate_of") and not {"BLACK", "BLURRY"} & set(s["flags"])]
    per_clip = {}
    for s in sorted(pool, key=lambda s: -s["score"]):
        per_clip.setdefault(s["clip_id"], []).append(s)
    ranked = []
    while any(per_clip.values()):
        rnd = [v.pop(0) for v in per_clip.values() if v]
        ranked += sorted(rnd, key=lambda s: -s["score"])
    for old in ws.sheets.glob("candidates_*.jpg"):
        old.unlink()
    page = 24
    n_pages = min(args.pages, math.ceil(len(ranked) / page))
    for p in range(n_pages):
        chunk = ranked[p * page:(p + 1) * page]
        g = grid([tile(s) for s in chunk], 6, f"CANDIDATES page {p + 1}/{n_pages} (ranked, variety-enforced)", f)
        g.save(ws.sheets / f"candidates_{p + 1:02d}.jpg", quality=80)
    mb = sum(x.stat().st_size for x in ws.sheets.glob("*.jpg")) / 1e6
    ws.logrow("preview", time.time() - t0, clip_sheets=made, cached=skipped, candidate_pages=n_pages)
    print(f"preview: {made} clip sheets ({skipped} cached), {n_pages} candidate pages, {mb:.1f} MB")


# --------------------------------------------------------------------------- annotate / approve
ANN_FIELDS = {"visual_description", "people", "emotional_value", "storytelling", "marketing",
              "recommended_use", "tags", "reject", "note"}


def cmd_annotate(ws: Workspace, args):
    new = json.loads(Path(args.file).read_text(encoding="utf-8"))
    valid = {s["seg_id"] for s in build_segments(ws)}
    ann = load_json(ws.annotations, {})
    bad = [k for k in new if k not in valid]
    if bad:
        sys.exit(f"unknown seg_id(s): {bad[:10]}")
    for k, v in new.items():
        extra = set(v) - ANN_FIELDS
        if extra:
            sys.exit(f"{k}: unknown field(s) {extra}")
        for f in ("emotional_value", "storytelling", "marketing"):
            if f in v and not (isinstance(v[f], (int, float)) and 1 <= v[f] <= 5):
                sys.exit(f"{k}: {f} must be 1-5")
        ann.setdefault(k, {}).update(v)
    save_json(ws.annotations, ann)
    ws.logrow("annotate", 0, segments=len(new))
    print(f"annotate: merged {len(new)} segments (total annotated {len(ann)})")


def approved_segments(ws: Workspace):
    ap = load_json(ws.approved)
    if not ap:
        sys.exit(f"missing {ws.approved.relative_to(ws.root)} (Creative Director writes it)")
    segs = {s["seg_id"]: s for s in build_segments(ws)}
    out, problems = [], []
    for item in ap.get("segments", []):
        s = segs.get(item.get("seg_id"))
        if not s:
            problems.append(f"{item.get('seg_id')}: not in footage database")
            continue
        a = float(item.get("in", s["start"]))
        b = float(item.get("out", s["end"]))
        if not (s["start"] - 0.01 <= a < b <= s["end"] + 0.01):
            problems.append(f"{s['seg_id']}: in/out {a}-{b} outside segment {s['start']}-{s['end']}")
        if {"BLACK", "BLURRY", "DUPLICATE"} & set(s["flags"]) and not item.get("override_reason"):
            problems.append(f"{s['seg_id']}: flagged {s['flags']} - needs override_reason")
        out.append({**item, "in": a, "out": b, "seg": s})
    return ap, out, problems


def cmd_approve(ws: Workspace, args):
    ap, items, problems = approved_segments(ws)
    if not ap.get("approved_by"):
        problems.append("approved_by is empty (Creative Director must sign)")
    total = sum(i["out"] - i["in"] for i in items)
    print(f"approve: {len(items)} segments, {total:.1f}s of footage, approved_by={ap.get('approved_by')!r}")
    for p in problems:
        print("  PROBLEM:", p)
    ws.logrow("approve-check", 0, segments=len(items), problems=len(problems))
    sys.exit(1 if problems else 0)


# --------------------------------------------------------------------------- F extract
def cmd_extract(ws: Workspace, args):
    t0 = time.time()
    _, items, problems = approved_segments(ws)
    if problems:
        sys.exit("fix APPROVED_FOOTAGE.json first:\n  " + "\n  ".join(problems))
    src = ws.source()
    made = cached = 0
    for i in items:
        m = i["seg"]["meta"]
        ext = Path(m["relpath"]).suffix.lower()
        out = ws.extracts / f"{i['seg_id']}{ext}"
        if out.exists() and not args.force:
            cached += 1
            continue
        run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{i['in']:.3f}",
             "-i", str(src / m["relpath"]), "-t", f"{i['out'] - i['in']:.3f}", "-map", "0:v:0",
             "-map", "0:a:0?", "-c", "copy", "-avoid_negative_ts", "make_zero", str(out)])
        made += 1
    mb = sum(p.stat().st_size for p in ws.extracts.glob("*")) / 1e6
    ws.logrow("extract", time.time() - t0, stream_copied=made, cached=cached, mb=round(mb, 1))
    print(f"extract: {made} stream-copied, {cached} cached, {mb:.1f} MB (no re-encode; "
          f"cut points snap to the nearest preceding keyframe)")


# --------------------------------------------------------------------------- brand text check
NAME_RE = re.compile(r"@?\bmit[\s_\-.]*e?vent?s*\b", re.I)


def brand_text_problems(text: str):
    """Owner rule 22 Nov 2026: the only name form is `mit_eventss` (handle `@mit_eventss`)."""
    probs = [f"name variant '{m.group(0)}' -> use 'mit_eventss'" for m in NAME_RE.finditer(text)
             if m.group(0).lstrip("@") != "mit_eventss"]
    if re.search(r"@gmail\.", text, re.I):
        probs.append("gmail address in public/client text")
    if re.search(r"info@mahaj\.co\b(?!m)", text, re.I):
        probs.append("'info@mahaj.co' typo")
    return probs


def cmd_brandcheck(ws: Workspace, args):
    bad = 0
    for f in args.files:
        p = Path(f) if Path(f).exists() else ws.root / f
        for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            for pr in brand_text_problems(line):
                print(f"  {p.name}:{i}: {pr}")
                bad += 1
    print(f"brandcheck: {bad} problem(s)")
    sys.exit(1 if bad else 0)


# --------------------------------------------------------------------------- G render
def esc(t: str) -> str:
    return t.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\u2019").replace("%", "\\%")


def cmd_render(ws: Workspace, args):
    t0 = time.time()
    edl_path = Path(args.edl)
    if not edl_path.exists():
        edl_path = ws.root / args.edl   # allow workspace-relative paths
    edl = json.loads(edl_path.read_text(encoding="utf-8"))
    segs = {s["seg_id"]: s for s in build_segments(ws)}
    _, approved, _ = approved_segments(ws)
    approved_ids = {a["seg_id"] for a in approved}
    src = ws.source()
    W, H, FPS = edl.get("width", 1080), edl.get("height", 1920), edl.get("fps", 30)
    screen_text = [t["text"] for t in edl.get("text", [])] + \
        [edl.get("end_card", {}).get(k, "") for k in ("line1", "line2")] if edl.get("end_card") else \
        [t["text"] for t in edl.get("text", [])]
    probs = [p for t in screen_text for p in brand_text_problems(t)]
    if probs:
        sys.exit("render refused (brand rule): " + "; ".join(probs))
    fontfile = edl.get("fontfile") or drawtext_font()
    inputs, chains, durs, inputs_meta = [], [], [], []
    for n, shot in enumerate(edl["shots"]):
        sid = shot["seg"]
        if sid not in approved_ids:
            sys.exit(f"shot {n + 1}: {sid} is not in APPROVED_FOOTAGE.json")
        s = segs[sid]
        a = float(shot.get("in", s["start"]))
        speed = float(shot.get("speed", 1.0))
        # snap cumulative cut points to whole frames so beat-timed EDLs do not drift
        cum0 = sum(durs)
        out_d = round((cum0 + float(shot["dur"])) * FPS) / FPS - round(cum0 * FPS) / FPS
        src_d = out_d * speed
        if a + src_d > s["end"] + 0.05:
            sys.exit(f"shot {n + 1}: {sid} needs {src_d:.2f}s from {a} but segment ends at {s['end']}")
        inputs += ["-ss", f"{a:.3f}", "-t", f"{src_d + 0.1:.3f}", "-i", str(src / s["meta"]["relpath"])]
        inputs_meta.append(sid)
        cx = float(shot.get("crop_x", 0.5))
        g = shot.get("grade", {})
        eq = f"eq=brightness={g.get('brightness', 0)}:contrast={g.get('contrast', 1)}:" \
             f"saturation={g.get('saturation', 1)}:gamma={g.get('gamma', 1)}"
        chains.append(
            f"[{n}:v]setpts=(PTS-STARTPTS)/{speed},fps={FPS},"
            f"scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,"
            f"crop={W}:{H}:(iw-{W})*{cx}:(ih-{H})/2,{eq},setsar=1,format=yuv420p,"
            f"trim=duration={out_d},setpts=PTS-STARTPTS[v{n}]")
        durs.append(out_d)
    n_shots = len(durs)
    # reuse lint: the same source frames shown twice reads as padding (QC lesson, 22 Nov)
    rng_ = []
    for shot in edl["shots"]:
        a = float(shot.get("in", segs[shot["seg"]]["start"]))
        rng_.append((shot["seg"], a, a + float(shot["dur"]) * float(shot.get("speed", 1.0))))
    overlap = sum(max(0.0, min(b1, b2) - max(a1, a2))
                  for i, (s1, a1, b1) in enumerate(rng_) for (s2, a2, b2) in rng_[i + 1:] if s1 == s2)
    used = sum(b - a for _, a, b in rng_)
    reuse_pct = 100 * overlap / used if used else 0
    if reuse_pct > 10:
        print(f"render WARNING: {reuse_pct:.0f}% of source time is shown more than once - "
              f"ask the Creative Director for more approved footage (rule: >= 2x runtime)")
    ec = edl.get("end_card")
    if ec:
        d = float(ec.get("dur", 2.5))
        l1, l2 = esc(ec.get("line1", BRAND["name"])), esc(ec.get("line2", ""))
        chains.append(
            f"color=c={BRAND['dark']}:s={W}x{H}:r={FPS}:d={d},"
            f"drawbox=x=(iw-520)/2:y=ih/2+40:w=260:h=10:color={BRAND['red']}:t=fill,"
            f"drawbox=x=iw/2:y=ih/2+40:w=260:h=10:color={BRAND['green']}:t=fill,"
            + (f"drawtext=fontfile={fontfile}:text='{l1}':fontsize=96:fontcolor=white:x=(w-tw)/2:y=h/2-110,"
               if l1.strip() and not ec.get("logo") else "")   # logo replaces the name line
            +
            f"drawtext=fontfile={fontfile}:text='{l2}':fontsize=60:fontcolor=white:x=(w-tw)/2:y=h/2+90,"
            f"fade=t=in:st=0:d=0.15,setsar=1,format=yuv420p" + ("[ecb]" if ec.get("logo") else f"[v{n_shots}]"))
        if ec.get("logo"):  # official transparent PNG, centred above the text
            logo = Path(ec["logo"]).expanduser()
            if not logo.exists():
                logo = ws.root / ec["logo"]
            li = len(inputs_meta)
            inputs += ["-loop", "1", "-t", f"{d:.3f}", "-i", str(logo)]
            inputs_meta.append("logo")
            chains.append(f"[{li}:v]scale={int(W * 0.45)}:-1,format=rgba,fade=t=in:st=0:d=0.15:alpha=1[lg];"
                          f"[ecb][lg]overlay=(W-w)/2:H/2-h-40,format=yuv420p[v{n_shots}]")
        durs.append(d)
    trans = edl.get("transition", "cut")
    xd = float(edl.get("transition_dur", 0.3))
    labels = [f"[v{i}]" for i in range(len(durs))]
    if trans == "cut" or len(durs) == 1:
        chains.append("".join(labels) + f"concat=n={len(durs)}:v=1:a=0[vc]")
        total = sum(durs)
    else:
        cur, off = labels[0], durs[0]
        for i in range(1, len(durs)):
            outl = f"[x{i}]" if i < len(durs) - 1 else "[vc]"
            chains.append(f"{cur}{labels[i]}xfade=transition={trans}:duration={xd}:offset={off - xd:.3f}{outl}")
            cur, off = outl, off - xd + durs[i]
        total = off
    texts = []
    for t in edl.get("text", []):
        # Instagram safe band: survives the 4:5 feed and 3:4 grid crops and clears the app UI
        y = {"top": "h*0.17", "center": "(h-th)/2", "bottom": "h*0.70"}[t.get("pos", "bottom")]
        box = ":box=1:boxcolor=black@0.45:boxborderw=18" if t.get("box", True) else ""
        texts.append(
            f"drawtext=fontfile={fontfile}:text='{esc(t['text'])}':fontsize={t.get('size', 64)}:"
            f"fontcolor=white:borderw=3:bordercolor=black@0.6{box}:x=(w-tw)/2:y={y}:"
            f"enable='between(t,{t['t']},{t['t'] + t['dur']})'")
    fade = f"fade=t=in:st=0:d={edl.get('fade_in', 0)}" if edl.get("fade_in") else ""
    post = ",".join(x for x in texts + [fade] if x)
    chains.append(f"[vc]{post or 'null'}[vout]")
    mus = edl.get("music")
    ai = len(inputs_meta)
    if mus:
        inputs += ["-ss", str(mus.get("start", 0)), "-i", str(Path(mus["file"]).expanduser())]
        chains.append(f"[{ai}:a]atrim=duration={total:.3f},asetpts=PTS-STARTPTS,"
                      f"afade=t=in:d=0.3,afade=t=out:st={max(0, total - 1.5):.3f}:d=1.5,"
                      f"loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[aout]")
    else:
        chains.append(f"anullsrc=r=48000:cl=stereo,atrim=duration={total:.3f}[aout]")
    vid = edl["video_id"]
    out_dir = ws.prod / vid
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{vid}_{edl.get('version', 'draft1')}.mp4"
    enc = ["-c:v", "libx264", "-preset", args.preset, "-crf", "18", "-maxrate", "20M", "-bufsize", "40M",
           "-profile:v", "high", "-pix_fmt", "yuv420p"]
    if args.hw:
        enc = ["-c:v", "h264_videotoolbox", "-b:v", "16M", "-pix_fmt", "yuv420p"]
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *inputs,
           "-filter_complex", ";\n".join(chains), "-map", "[vout]", "-map", "[aout]",
           *enc, "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-r", str(FPS), "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
           "-t", f"{total:.3f}", str(out)]
    (out_dir / f"{out.stem}_ffmpeg.txt").write_text(
        " ".join(f"'{c}'" if (" " in c or ";" in c or "[" in c) else c for c in cmd), encoding="utf-8")
    run(cmd)
    ws.logrow("render", time.time() - t0, video=vid, shots=n_shots, seconds_out=round(total, 2),
              source_reuse_pct=round(reuse_pct, 1),
              re_encoded="final render only")
    print(f"render: {out.relative_to(ws.root)}  {total:.1f}s  {n_shots} shots  {time.time() - t0:.1f}s")


# --------------------------------------------------------------------------- QC
def cmd_qc(ws: Workspace, args):
    t0 = time.time()
    path = Path(args.video)
    if not path.exists():
        path = ws.root / args.video          # allow workspace-relative paths
    if not path.exists() or path.stat().st_size == 0:
        sys.exit(f"qc: video not found or empty: {path}")
    m = probe(path)
    if m.get("error"):
        sys.exit(f"qc: cannot read video: {m['error']}")
    p = run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-vf",
             f"scale=270:-2,scdet=threshold={SCDET_THRESHOLD}:sc_pass=0,"
             "blackdetect=d=0.3:pic_th=0.97,freezedetect=n=0.003:d=1.5", "-af", "ebur128=peak=true",
             "-f", "null", "-"], check=False)
    err = p.stderr.decode(errors="replace")
    cut_t = [float(x) for x in re.findall(r"lavfi\.scd\.time:\s*([\d.]+)", err)]
    shots = np.diff([0.0] + cut_t + [m["duration"]]) if m["duration"] else np.array([])
    shot_cv = float(shots.std() / shots.mean()) if len(shots) > 1 else 0.0
    body_sh = shots[:-1] if len(shots) > 2 else shots                # end card excluded
    same_len_share = float(max((np.abs(body_sh - x) <= 0.1).mean() for x in body_sh)) if len(body_sh) else 0.0
    beat_sync = None
    if args.beats:
        bp = Path(args.beats) if Path(args.beats).exists() else ws.root / args.beats
        if not bp.exists():
            sys.exit(f"qc: beats file not found: {args.beats}")
        beats = np.array(load_json(bp)["beats"])
        body = [c for c in cut_t if c < m["duration"] - 3.5]
        if body and len(beats):
            beat_sync = float(np.mean([np.min(np.abs(beats - c)) <= 0.07 for c in body]))
    blacks = [(float(a), float(b)) for a, b in re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", err)]
    freezes = [float(x) for x in re.findall(r"freeze_duration: ([\d.]+)", err)]
    li = re.findall(r"I:\s+(-?[\d.]+) LUFS", err)
    tp = re.findall(r"Peak:\s+(-?[\d.inf]+) dBFS", err)
    lufs = float(li[-1]) if li else None
    peak = float(tp[-1]) if tp and tp[-1] not in ("-inf", "inf") else None
    # first 2 seconds: activity
    size = analysis_size(m)
    t2, f2, hook_scd = decode_frames(path, size, "fps", start=0, dur=2.0, fps=8, scd=True)
    met = [frame_metrics(f) for f in f2]
    hook_motion = float(np.mean([np.abs(met[i]["_small"] - met[i - 1]["_small"]).mean()
                                 for i in range(1, len(met))])) if len(met) > 1 else 0.0
    hook_cuts = len([c for c in hook_scd if 0.05 < c < 2.0])
    hook_luma = float(np.mean([x["luma"] for x in met])) if met else 0
    exp_w, exp_h = args.width, args.height
    objective = args.objective or ("energy" if re.search(r"energy|viral|V02", path.stem, re.I) else "other")
    energy = objective == "energy"   # uniform rhythm is a defect for energy edits, a style elsewhere
    silent = lufs is None or lufs < -60
    checks = [
        ("dimensions", (m["width"], m["height"]) == (exp_w, exp_h), f"{m['width']}x{m['height']} (want {exp_w}x{exp_h})"),
        ("duration_30_40s", 30 <= m["duration"] <= 40, f"{m['duration']:.2f}s"),
        ("fps", 23.9 <= m["fps"] <= 60.1, f"{m['fps']}"),
        ("bitrate_5-25Mbps", 5e6 <= m["bitrate"] <= 25e6, f"{m['bitrate'] / 1e6:.1f} Mbps (Instagram ~15-20 Mbps)"),
        ("codec", m["codec"] == "h264" and m["pix_fmt"] == "yuv420p", f"{m['codec']}/{m['pix_fmt']}"),
        ("no_black_gaps", not [b for b in blacks if b[0] > 0.2 and b[1] < m["duration"] - 3.5],
         f"{blacks}"),
        ("no_frozen_picture", not freezes, f"{freezes}"),
        ("audio_present", not silent, "silent track" if silent else "ok"),
        ("loudness_-16_to_-12_LUFS", lufs is not None and -16 <= lufs <= -12, f"{lufs}"),
        ("true_peak_<=-1dB", peak is not None and peak <= -1.0, f"{peak}"),
        ("hook_first_2s_active", hook_motion > 3 or hook_cuts >= 1, f"motion {hook_motion:.1f}, cuts {hook_cuts}"),
        ("hook_first_2s_not_dark", hook_luma > 35, f"luma {hook_luma:.0f}"),
        ("rhythm_not_uniform" + ("" if energy else " (info only)"),
         (not energy) or len(cut_t) < 8 or same_len_share < 0.6,
         f"{len(cut_t)} cuts, avg shot {shots.mean() if len(shots) else 0:.2f}s, CV {shot_cv:.2f}, "
         f"{same_len_share * 100:.0f}% of shots the same length (±0.1 s)"),
    ]
    if beat_sync is not None:
        checks.append(("cuts_on_beat_>=70%", beat_sync >= 0.7, f"{beat_sync * 100:.0f}% of cuts within 70 ms of a beat"))
    vid = path.stem
    qdir = ws.qc / vid
    qdir.mkdir(parents=True, exist_ok=True)
    # review sheet: one frame per second + final frame, for the Quality Controller agent
    n = int(math.floor(m["duration"]))
    cols = 8
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(path), "-vf",
         f"fps=1,scale=180:-2,drawtext=fontfile={drawtext_font()}:text='%{{pts\\:hms}}':x=4:y=4:"
         f"fontsize=16:fontcolor=yellow:box=1:boxcolor=black@0.6,tile={cols}x{math.ceil((n + 1) / cols)}:padding=4",
         "-frames:v", "1", str(qdir / "review_sheet_1fps.jpg")])
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-sseof", "-0.1", "-i", str(path),
         "-frames:v", "1", "-vf", "scale=540:-2", str(qdir / "final_frame.jpg")])
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(path), "-vf",
         "fps=4,scale=180:-2,tile=8x1:padding=4", "-t", "2", "-frames:v", "1", str(qdir / "first_2s.jpg")])
    report = {"video": str(path.name), "probe": m, "checks": [
        {"check": c, "pass": bool(ok), "value": v} for c, ok, v in checks],
        "technical_pass": all(ok for _, ok, _ in checks),
        "note": "Automatic checks only. Storytelling, rhythm, brand and objective are judged by the "
                "quality-controller agent from the review sheets; music/sync must be confirmed by ear."}
    save_json(qdir / "qc_auto.json", report)
    ws.logrow("qc-auto", time.time() - t0, video=vid, technical_pass=report["technical_pass"])
    for c in report["checks"]:
        print(f"  {'PASS' if c['pass'] else 'FAIL'}  {c['check']:28s} {c['value']}")
    print(f"qc: technical_pass={report['technical_pass']} -> {qdir.relative_to(ws.root)}/")


# --------------------------------------------------------------------------- music bed
def cmd_music(ws: Workspace, args):
    """Original, procedurally generated bed (no third-party samples -> no licence needed).
    Placeholder quality: for drafts, timing and beat-sync; replace with a licensed track
    for publication if the owner prefers."""
    t0 = time.time()
    sr = 48000
    bpm = args.bpm or {"cinematic": 76, "energy": 124, "corporate": 104}[args.style]
    n = int(args.dur * sr)
    t = np.arange(n) / sr
    beat = 60.0 / bpm
    rng = np.random.default_rng(args.seed)
    # A minor progression Am - F - C - G (one chord per bar of 4 beats)
    roots = [220.0, 174.61, 261.63, 196.0]
    thirds = [261.63, 220.0, 329.63, 246.94]
    fifths = [329.63, 261.63, 392.0, 293.66]
    bar = (t // (4 * beat)).astype(int) % 4
    out = np.zeros(n)
    env_bar = np.minimum(1, (t % (4 * beat)) / 0.4)
    for f_tab, g in ((roots, .16), (thirds, .11), (fifths, .10)):
        f = np.array(f_tab)[bar]
        ph = 2 * np.pi * np.cumsum(f) / sr
        out += g * env_bar * (np.sin(ph) + 0.3 * np.sin(2 * ph) + 0.15 * np.sin(ph * 1.003))
    bass_f = np.array(roots)[bar] / 2
    out += (0.10 if args.style == "cinematic" else 0.22) * np.sin(2 * np.pi * np.cumsum(bass_f) / sr)

    def hits(every, length, shape):
        sig = np.zeros(n)
        k = 0.0
        while k < args.dur:
            i0 = int(k * sr)
            seg = shape(np.arange(min(int(length * sr), n - i0)) / sr)
            sig[i0:i0 + len(seg)] += seg
            k += every
        return sig

    kick = lambda x: np.sin(2 * np.pi * (55 + 90 * np.exp(-x * 30)) * x) * np.exp(-x * 9)
    hat = lambda x: rng.standard_normal(len(x)) * np.exp(-x * 60)
    if args.style == "cinematic":
        out += 0.35 * hits(beat * 2, 0.5, kick)                   # soft pulse on 1 and 3
    else:
        out *= 1 - 0.45 * np.exp(-((t % beat) / 0.12))            # sidechain: duck pads/bass only
        out += 0.75 * hits(beat, 0.35, kick)                      # four on the floor, never ducked
        out += 0.10 * hits(beat / 2, 0.05, hat)
    fade = np.minimum(1, np.minimum(t / 1.0, (args.dur - t) / 2.0))
    out = out * fade
    out = out / (np.max(np.abs(out)) + 1e-9) * 0.8
    st = np.stack([out, np.roll(out, 120)], axis=1)            # light stereo width
    mdir = ws.briefs / "music"
    mdir.mkdir(parents=True, exist_ok=True)
    name = f"bed_{args.style}_{int(bpm)}bpm"
    pcm = (st * 32767).astype("<i2").tobytes()
    p = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "s16le",
                        "-ar", str(sr), "-ac", "2", "-i", "-", "-c:a", "aac", "-b:a", "192k",
                        str(mdir / f"{name}.m4a")], input=pcm, stderr=subprocess.PIPE)
    if p.returncode:
        sys.exit(p.stderr.decode()[-500:])
    beats = [round(i * beat, 4) for i in range(int(args.dur / beat) + 1)]
    save_json(mdir / f"{name}_beats.json", {"bpm": bpm, "beat_s": round(beat, 4), "style": args.style,
                                           "beats": beats, "bars": beats[::4],
                                           "licence": "original, generated by mit_studio.py - no third-party material"})
    ws.logrow("music", time.time() - t0, file=f"{name}.m4a", bpm=bpm)
    print(f"music: CREATIVE_BRIEFS/music/{name}.m4a  {bpm:g} BPM, beat {beat:.3f}s, {len(beats)} beats")


# --------------------------------------------------------------------------- verify / status
def cmd_verify(ws: Workspace, args):
    inv = load_json(ws.inventory)
    src = ws.source()
    changed = []
    for cid, c in inv["clips"].items():
        p = src / c["relpath"]
        if c.get("missing"):
            continue
        if not p.exists():
            changed.append(f"{cid} missing")
            continue
        st = p.stat()
        if st.st_size != c["size"] or st.st_mtime != c["mtime"]:
            changed.append(f"{cid} {c['relpath']} changed")
    n = sum(1 for c in inv["clips"].values() if not c.get("missing"))
    print(f"verify: {n - len(changed)}/{n} originals identical (size+mtime)")
    for x in changed:
        print("  ", x)
    sys.exit(1 if changed else 0)


def cmd_status(ws: Workspace, args):
    inv = load_json(ws.inventory, {"clips": {}})
    clips = [c for c in inv["clips"].values() if not c.get("missing")]
    analysed = sum(1 for c in clips if (ws.cache / f"{c['clip_id']}.json").exists())
    segs = build_segments(ws) if analysed else []
    ann = load_json(ws.annotations, {})
    ap = load_json(ws.approved, {})
    renders = sorted(p.relative_to(ws.root).as_posix() for p in ws.prod.glob("*/*.mp4"))
    qcs = {p.parent.name: load_json(p)["technical_pass"] for p in ws.qc.glob("*/qc_auto.json")}
    print(json.dumps({
        "event": load_json(ws.event, {}).get("event_code"),
        "clips": len(clips), "gb": round(sum(c["size"] for c in clips) / 1e9, 2),
        "minutes": round(sum(c.get("duration", 0) for c in clips) / 60, 1),
        "analysed": analysed, "segments": len(segs),
        "flagged": sum(1 for s in segs if s["flags"]), "annotated": len(ann),
        "approved_segments": len(ap.get("segments", [])), "approved_by": ap.get("approved_by"),
        "renders": renders, "qc_auto": qcs,
    }, indent=1))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--workspace", "-w", required=True, help="event workspace folder")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("scan"); s.add_argument("--source")
    s = sub.add_parser("detect"); s.add_argument("--max-seconds", type=float, default=0,
                                                 help="stop after N s (re-run continues)")
    s = sub.add_parser("preview"); s.add_argument("--pages", type=int, default=5); s.add_argument("--force", action="store_true")
    sub.add_parser("database")
    s = sub.add_parser("annotate"); s.add_argument("file")
    sub.add_parser("approve")
    s = sub.add_parser("extract"); s.add_argument("--force", action="store_true")
    s = sub.add_parser("render"); s.add_argument("edl"); s.add_argument("--preset", default="medium")
    s.add_argument("--hw", action="store_true", help="use Apple VideoToolbox encoder")
    s = sub.add_parser("qc"); s.add_argument("video"); s.add_argument("--width", type=int, default=1080)
    s.add_argument("--height", type=int, default=1920)
    s.add_argument("--beats", help="beats JSON from the music command, to measure cut-to-beat sync")
    s.add_argument("--objective", choices=["energy", "cinematic", "portfolio", "other"],
                   help="default: inferred from the file name (energy/viral/V02 -> energy)")
    s = sub.add_parser("music", help="original licence-free music bed + beat map")
    s.add_argument("--style", choices=["cinematic", "energy", "corporate"], required=True)
    s.add_argument("--bpm", type=float); s.add_argument("--dur", type=float, default=40)
    s.add_argument("--seed", type=int, default=1)
    sub.add_parser("verify")
    s = sub.add_parser("brandcheck", help="check name form / contacts in captions, EDLs, docs")
    s.add_argument("files", nargs="+")
    sub.add_parser("status")
    a = ap.parse_args()
    for tool in ("ffmpeg", "ffprobe"):
        if not shutil.which(tool):
            sys.exit(f"{tool} not found. macOS: brew install ffmpeg")
    ws = Workspace(Path(a.workspace))
    if a.cmd != "scan" and not ws.event.exists():
        sys.exit("not an event workspace; run scan --source first")
    globals()[f"cmd_{a.cmd}"](ws, a)


if __name__ == "__main__":
    main()
