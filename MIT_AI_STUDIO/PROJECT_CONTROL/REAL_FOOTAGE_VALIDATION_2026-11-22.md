# Real-footage validation — 22 Nov 2026

Source: the owner's published reel "Kermesse.mov" (Google Drive, 34.0 s, 720×1280, H.264/AAC,
~23 shots of an outdoor children's kermesse produced by MIT_eventss). Downloaded read-only to
the session scratchpad; the workspace is **not committed** (identifiable children, public repo).
It is the only Drive video under the Drive connector's 10 MB download limit; the raw event
folders (30–200 MB files) and the Mac library could not be reached from this session.

## 1. Footage analysis (engine v1.1 → v1.2)

| | Ground truth | Engine v1.1 | Engine v1.2 |
|---|---|---|---|
| Scene cuts | 23 (ffmpeg scdet on every frame, confirmed visually on a 2 fps sheet) | **1** | **22**, 0 false |
| Missed | — | 22 | 1 (a 0.67 s shot merged by design: min segment 0.8 s) |
| False blur / dark / overexposed flags | 0 expected | 0 | 0 |
| Time | — | 13.0 s | 1.7 s |

Why v1.1 failed: the file has a single keyframe, so analysis fell back to 1 fps sampling, and
real outdoor shots with similar palettes rarely crossed the colour-histogram threshold. The
synthetic test could not reveal this. Fix: ffmpeg `scdet` runs inside the same decode pass
(frame-accurate, no extra decode); stage-light protection for keyframe mode is unchanged and
the synthetic suite still passes (hue-drift clip is still one segment).

## 2. QC benchmark on a published MIT_eventss reel

| Check | Result |
|---|---|
| Dimensions | **720×1280** — below the 1080×1920 delivery standard (export setting to fix in CapCut) |
| Duration, fps, codec, loudness (−14.1 LUFS), true peak (−2.5 dB) | pass |
| Hook | 1 cut within 2 s (1.43 s), high motion — pass |
| Branding | MIT logo bug bottom-right on every shot (brand file now allows this for V03 only) |
| Consent | identifiable children throughout → written consent required before any reuse |

QC hook counting was also moved to `scdet` after the benchmark showed 0 cuts where there was 1.

## 3. Music bed timing audit (licence-free beds)

The `music` command generates original beds with a beat map. Measured by cross-correlating the
encoded file with an ideal kick track on the beat grid: **+2.9 ms** lag (2.5 ms is the
deliberate stereo offset) for the 124 and 104 BPM beds. A generator bug found on the way
(sidechain duck applied to the kick itself) was fixed. Claude cannot hear: the owner judges
whether the beds sound acceptable; for publication a licensed track may still be preferred.

## 4. What this still does not validate
Emotional/storytelling scoring by the Media Analyst on raw footage, 4K HEVC speed, and a
30–50 GB event. These need the Mac library (migration plan step 2).
