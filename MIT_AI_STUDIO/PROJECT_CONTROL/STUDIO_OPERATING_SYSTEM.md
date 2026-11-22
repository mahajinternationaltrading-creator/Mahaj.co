# mit_eventss AI Studio — Operating System v1.0 (2026-11-22)

One studio, seven departments, one Studio Manager. mit_eventss is the events trade name of
**Mahaj International Trading**. Blocking safety rules: `PUBLISHING_SAFETY_RULES.md`. The goal is better videos with less
processing, not more AI activity.

## 1. Event workspace (one per event)

```
MIT_AI_STUDIO/EVENT_DATABASE/<BRANDCODE>_<YYYY-MM-DD>_<short-name>/
  event.json                    source folder path, event facts, objectives (Studio Manager)
  production_log.csv            every stage: time, files, cache hits (written by the engine)
  decisions.md                  signed gates, rejections, corrections (Studio Manager)
  MEDIA_ANALYSIS/               inventory.json, cache/, thumbs/, sheets/,
                                footage_database.csv, annotations.json        (Media Analyst)
  APPROVED_FOOTAGE/             APPROVED_FOOTAGE.json, extracts/ (CapCut only) (Creative Director)
  CREATIVE_BRIEFS/              briefs.md, marketing_challenge.md, V0x_*_edl.json
  VIDEO_PRODUCTION/V0x_*/       drafts + the exact ffmpeg command used        (Video Editor)
  QUALITY_CONTROL/V0x_*/        qc_auto.json, review sheets, QC_REPORT.md, BRAND_CHECK.md
  SOCIAL_MEDIA_DELIVERY/        posting packs                                 (Publishing Manager)
```
Footage is **referenced**, never copied. On a Mac the workspace may live next to the
footage (e.g. `~/Desktop/Claude Studio/_STUDIO/EVENTS/`); pass it with `-w`.
Shared knowledge (this file, brand files, agents, engine) is kept separate from events.

Brand codes in use: `MITEV` (mit_eventss), `MIT`, `PO` (Palais Ouazzani), `ABU`
(Abulcasis / BDE UIASS), `FRK` (Frankie). New client → new code, same structure.

## 2. Engine (`MIT_AI_STUDIO/ENGINE/mit_studio.py`)

| Stage | Command | Who | Cost |
|---|---|---|---|
| A Scan | `scan --source <folder>` | Media Analyst | ffprobe only, cached by size+mtime |
| B Detect | `detect [--max-seconds 110]` | Media Analyst | keyframe decode at 320 px, adaptive refinement |
| C Preview | `preview` | Media Analyst | per-clip + ranked candidate sheets (JPEG, ~25 KB/clip) |
| D Database | `database`, `annotate <json>` | Media Analyst | merges AI annotations; no re-analysis |
| E Approve | `approve` | Creative Director | validates seg IDs, in/out, flags |
| F Extract | `extract` | Video Editor | stream copy, only for CapCut hand-off |
| Music | `music --style cinematic\|energy\|corporate [--bpm N --dur S]` | Video Editor | original licence-free bed + beat map JSON |
| G Render | `render <edl.json> [--hw]` | Video Editor | single encode, reads originals directly; end card can carry the official logo |
| QC | `qc <video> [--beats <beats.json>]` | Quality Controller | technical checks incl. rhythm uniformity and cut-to-beat sync + 1 fps review sheet |
| Verify | `verify` | Studio Manager | originals unchanged (size+mtime) |
| Status | `status` | Studio Manager | ~20-line JSON summary |

All commands: `python3 MIT_AI_STUDIO/ENGINE/mit_studio.py -w <workspace> <command>`.
Long events: `detect --max-seconds 110` and repeat; the cache makes every run resume.

**Detection logic (v1.2):** frame-accurate cuts from ffmpeg `scdet` in the same decode pass
when frames are sampled; in keyframe mode, cut = colour-histogram jump **and** structural
change (so stage-light colour changes are not cuts), refined with `scdet` around changes.
Validated on a real mit_eventss reel: 22/23 cuts, 0 false (REAL_FOOTAGE_VALIDATION). Blur = Laplacian variance below 30 % of the
event median. Dark / overexposed / black by luma and clipped-pixel share. Duplicates =
perceptual hash on the representative frame or at 25/50/75 % of the segment; the
highest-resolution file is kept as master. Camera move from phase correlation.

## 3. Approval chain (gates)

| Gate | Owner | Input | Output | Passes when |
|---|---|---|---|---|
| G1 | Media Analyst | source folder | database + sheets + annotations + shortlist | every shortlisted seg has description + 3 scores |
| G2 | Creative Director | G1 | `APPROVED_FOOTAGE.json`, 3 concepts in `briefs.md` | `approve` exits 0; concepts genuinely differ |
| G3 | Marketing Strategist | G2 concepts | `marketing_challenge.md` | each concept: KEEP / CHANGE / REPLACE with reason |
| G4 | **Studio Manager** | G2 + G3 | final briefs, 3 EDLs requested | conflicts resolved, recorded in `decisions.md` |
| G5 | Video Editor | G4 | 3 drafts + EDLs | 30–40 s, 1080×1920, renders reproducible |
| G6 | Brand Director | G5 | `BRAND_CHECK.md` per video | PASS, or REJECT with timestamps |
| G7 | Quality Controller | G5 (+G6) | `qc_auto.json` + `QC_REPORT.md` | PASS; otherwise REJECT with fixes |
| G8 | responsible agent | rejection | corrected version (draftN+1) | re-reviewed by the rejecting gate only |
| G9 | Publishing Manager | G7 PASS | posting pack per video | complete, brand-checked text |
| G10 | **Studio Manager** → owner | all | delivery summary | owner approves; nothing is published by the studio |

**Rejection format (mandatory):**
```
REJECT <video/version>
- What:  <the defect>
- Where: <timestamp or seg ID / file>
- Why:   <effect on the viewer or objective>
- Fix:   <the specific correction>
- Owner: <agent responsible>
- Round: <1 | 2>  (after round 2 → escalate to owner, do not loop)
```
Small issues are fixed by editing the EDL and re-rendering that one video; never restart the
workflow. Only the gate that rejected re-reviews the correction.

## 4. Deliverables per event
1. V01 Cinematic Story, 30–40 s · 2. V02 Viral Energy, 30–40 s · 3. V03 Commercial Portfolio,
30–40 s (all 1080×1920, H.264, AAC, −14 LUFS, true peak ≤ −1 dB) · 4. captions ·
5. hashtags · 6. cover frame recommendations · 7. video specs · 8. QC report ·
9. selected footage inventory (`APPROVED_FOOTAGE.json` + database rows) · 10. production summary.

Other job types: commercial ad → 1 hero ad + optional cut-down; corporate film → 1 main film.

## 5. Token, time and resource rules
1. One footage analysis per event. Reopen originals only if: a file was added; the analysis
   is incomplete; the Creative Director requests more footage; QC identifies a missing moment.
   Each reopen is logged in `decisions.md` with the reason.
2. AI looks at contact sheets (≈0.2 MB per 24 shots), never at full video files.
3. Agents exchange files (CSV / JSON / short MD), not conversation history. Each subagent
   receives only the paths it needs.
4. Scripts do repetitive work; models do judgement. Model tiers are set in each agent file.
5. Previews are cached; `preview` regenerates a clip sheet only when its analysis changed.
6. Re-encode exactly once: the final render. Extracts are stream copies and only for CapCut.
7. Agent reports ≤ 15 lines, 5-field format.
8. The Studio Manager reads `production_log.csv` at G10 and lists any wasted processing.

## 6. Privacy — this repository is PUBLIC
Real event workspaces, footage images, client names and people's descriptions are git-ignored
(`.gitignore`). Only synthetic `TEST_*` workspaces are committed. The logo copy in
`PROJECT_CONTROL/brand_assets/` is local only. Change this rule only after the owner makes
the repository private.

## 7. Honest limits (v1.0)
- Subagents are separate Claude instances with their own context and tools, but they are
  invoked by the Studio Manager; they do not run on their own.
- Claude cannot hear. Music sync and audio are checked by measurement (loudness, peaks, cut
  timing); the owner judges the sound.
- People / face recognition is manual from sheets; no automatic face clustering.
- The draft renderer covers cuts, fades, speed, crop, grade, text, music and end card. Final
  polish (beat-exact sync, effects, licensed music) is done in CapCut or the existing
  `studio_render.py` v1.6 on the Mac (see AUDIT §5 — reconcile before production).
- RAW photos (.ARW) are outside the video pipeline.
