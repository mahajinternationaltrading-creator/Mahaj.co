# QC report — V02_viral_energy / draft2 — Verdict: ESCALATE

Automatic checks: QUALITY_CONTROL/V02_viral_energy_draft2/qc_auto.json (I ran this myself on 22 Nov with `--beats CREATIVE_BRIEFS/music/bed_energy_124bpm_beats.json`. Summary: technical_pass = true, 13/13. 1080x1920, 32.93 s, 30 fps, h264/yuv420p, AAC. No black gaps and no frozen picture. Hook: motion 17.0, 2 cuts in the first 2 s, luma 73. Rhythm: 31 cuts, average shot 1.03 s, CV 0.51, 39 % of shots the same length. Cuts on beat: 100 % within 70 ms.)
Music sync: owner to confirm by ear (measured: -13.9 LUFS integrated, true peak -1.5 dBTP. The 124 BPM bed fades in over 0.3 s and out from 31.40 s over 1.5 s, so the music ends on the end card. Cut density: 31 shot cuts plus the end card in 32.9 s, about 0.94 cuts/s. Every cut lands on the beat map, which I recomputed from the EDL. Shot lengths in beats are 1 ×10, 2 ×12, 3 ×8, and 4 ×1.)

**Test context.** This is a pipeline test. The footage is synthetic (particle field, fractal zoom, yellow/blue test split, colour bars) and the music bed is generated. `[TEST]` texts are deliberate placeholders and are not counted as defects. **These cannot be judged on this content:** whether a real scroller would stop, emotional storytelling and atmosphere, people, faces and crops that cut heads, sharpness, exposure and shake of real camera footage, sponsor or client identity, whether the text covers a real subject, and whether the cuts *feel* on the music (I cannot hear; the 100 % figure is arithmetic against the beat map, not perception). This review only judges what does not depend on content: cut structure, reuse of source material, text placement and contrast handling, and end-card build.

## Verification of the four draft1 issues (round 2)
| # | Draft1 issue | Status in draft2 | Evidence |
|---|---|---|---|
| 1 | Flat 1.5 s grid, no build or peak | **FIXED** (residual weakness below) | The cuts come from the 124 BPM beat map, all 31 on a beat. There is a 10 × 1-beat peak at 19.83–24.67 s (60–75 %), then a 2-2-3-4 beat breath into the card. CV 0.51 against draft1's flat grid. |
| 2 | Fixed four-source loop and repeated identical moments | **NOT FIXED.** The loop is broken, but the material is still reused. ESCALATE. | The A-B-C-D rotation is gone and no in-point is used twice. But the source ranges overlap: 42 shot pairs share source frames, and in **13 pairs one shot is wholly contained in another** (see Issues). The footage was not shortened and no extra segments were requested. |
| 3 | Centre text, weak legibility, hook on the 14 % line | **PARTLY FIXED.** Escalated as a tool decision. | Text now sits at y = h*0.72 (top 1382 px, bottom about 1466 px, so 72–76 %), outside both the top 14 % and the bottom 20 %. Size is 84 px. But the stroke is unchanged (3 px, black @ 0.6) with no box and no shadow, because the engine has no box option. White on the yellow bar at 12.1–13.5 s is readable only through the outline (full-resolution crop checked). |
| 4 | Weak end card | **FIXED** (residual weakness below) | Official logo (brand file, decided 22 Nov) plus `@mit_eventss`, with no invented slogan or contact. The card is 2.90 s (6 beats), about 2.5 s fully readable, and the music fades out on it. G6 BRAND_CHECK passed. |

## Strengths (≥2)
1. **Rhythm is now designed, not gridded.** All 31 cuts sit on the 124 BPM beat map (0 drift, snapped to whole frames). There is a clear peak run of ten 1-beat shots (0.47–0.50 s) at 19.8–24.7 s and a decelerating 2-2-3-4 beat landing into the card. This is the "powerful pacing" shape draft1 lacked.
2. **The end card now converts.** It has the official transparent logo at 45 % of the width on #111111, a red #B62125 / green #597832 accent bar, and the verified handle `@mit_eventss`. It lasts 2.9 s and the music fade finishes on it. No brand facts are invented (line1 is empty, there is no slogan).
3. **Text placement is safe-zone correct.** Both texts sit in the 72–76 % band, clear of the 14 % top and 20 % bottom zones and out of frame centre, where real faces would be. At 84 px they are readable at phone scale (first_2s.jpg, review sheet at 12–14 s).
4. **Export is clean.** All 13 automatic checks pass. Loudness is on target at -13.9 LUFS, there are no black gaps or frozen frames, and the duration of 32.9 s is inside the 30–40 s window.

## Weaknesses (≥2)
1. **Source material is still recycled.** Only four segments feed 31 shots: C0001-S02 ×11, C0001-S01 ×9, C0008-S01 ×6, C0006-S01 ×5. The review sheet shows the yellow/blue split at 11 of the 30 footage seconds and the fractal at 9. C0001-S01 is rated "portfolio filler only" in footage_database.csv, yet it is the second most used source.
2. **The first 60 % does not accelerate.** From 0 to 19.8 s, shots alternate between 2 and 3 beats (0.97–1.47 s). The "build" after the 2-beat hook actually slows to 3 beats at 3.9 s, so energy dips right after the hook and only rises at 19.8 s.
3. **The hook opens on the weakest shot.** Shot 1 is C0006-S01 (flagged DARK in the database) played at 0.8x slow motion, so the hook luma is 73 against draft1's 94. Whether this stops a scroller cannot be judged on synthetic content, but a dark, slowed first frame works against a viral hook.
4. **Bright-background text relies on a 3 px outline.** White on yellow has almost no fill contrast. It passes here only because the outline holds, and real footage with bright stage light would expose this.
5. **End-card details.** The handle is small (44 px, about 2.3 % of height, 85 % opacity). The logo and handle block sits in the upper half of the frame (18–57 %). The card fades in from black over 0.4 s (engine fixed), after a hard cut from the brightest frame (yellow/blue at 29.9 s), so the first 0.4 s of the card reads as a dim flash (checked at 30.1 s). None of these blocks the pass.
6. **Peak headroom is thin.** The true peak is -1.5 dBTP, inside the limit but with only 0.5 dB margin, against -8.7 dBTP in draft1. Platform transcoding could clip it, so the owner should listen to the peak run.

## Issues
ESCALATE V02_viral_energy/draft2
- What: Draft1 issue 2 (repeated moments) is not fixed in substance. Every in-point is unique, but the shots draw on the same source frames. Overlaps were computed from EDL in/dur/speed: 42 shot pairs overlap, and in 13 pairs one shot is wholly contained in another. Worst cases: shot 13 (C0001-S02 7.00–8.83) contains shot 5 (7.50–8.67), shot 31 (C0001-S01 1.40–3.82) contains shot 12 (2.10–3.53) and shot 4 (2.70–3.67), shot 15 (6.40–7.87) contains shot 8 (6.50–7.47), shot 17 (C0008-S01 5.50–6.93) contains shot 14 (5.60–6.57), and shot 30 (8.90–10.37) contains shots 18, 23 and 25.
- Where: 00:03.9 ↔ 00:13.5, 00:02.9 / 00:12.1 ↔ 00:28.1, 00:07.7 ↔ 00:16.0, 00:15.0 ↔ 00:18.4, and 00:19.8 / 00:22.3 / 00:23.2 ↔ 00:26.6, plus partial reuse across the whole timeline.
- Why: The draft1 rejection was about the viewer seeing the same moments again, not about identical numbers. A unique in-point 0.1–0.5 s apart shows the same frames. The method ("unique (segment, in-point)") will carry over to real footage and produce visible repeats there. The draft1 fix gave two outs, shorten the cut or get more segments, and neither was taken.
- Fix: This needs an owner decision, not a third editor pass. Either (a) the Creative Director approves more segments for V02 so that every shot has non-overlapping source ranges, or (b) the cut is shortened and repeats are allowed only as a deliberate, motivated callback. For a synthetic test, the owner may also explicitly accept the reuse as a test limitation. Whatever is chosen, the editor should add a check that no two shots of the same segment overlap in source time.
- Owner: Owner (decision); Creative Director (footage pool); Video Editor (re-cut after the decision)
- Round: 2, so escalated

ESCALATE V02_viral_energy/draft2
- What: Draft1 issue 3 is only partly fixed. Placement and size are fixed, but the requested legibility treatment (semi-transparent box, or a heavier stroke plus drop shadow) was not applied. The editor reports that the engine has no box option. The stroke is still 3 px, black @ 0.6, with no shadow.
- Where: 00:12.1–00:13.5 (text[1] over the yellow bar). It also applies to text[0] at 00:00–00:01.9 on any bright real footage.
- Why: White on yellow or on bright stage light has almost no fill contrast, so legibility rests on a thin outline. It holds here at full resolution but has no margin.
- Fix: This is a tooling decision for the Studio Manager or owner: either add box and shadow parameters to the engine's drawtext (e.g. `box=1:boxcolor=black@0.45:boxborderw=20` or `shadowx/shadowy`), or accept stroke-only text and raise borderw to about 5–6 within the current EDL options. This is not a defect the editor can fully close inside the current tool.
- Owner: Studio Manager / owner (engine capability); Video Editor (apply after the decision)
- Round: 2, so escalated

## Notes for the other gates (not defects of this draft)
- **Owner, by ear:** Confirm that the 10-beat peak (19.8–24.7 s) and the 4-beat landing feel on the music. Listen to the peak run for clipping (true peak -1.5 dBTP).
- **Creative Director:** C0001-S01 ("portfolio filler only") carries 9 of 31 shots in the energy cut. The approved pool for V02 is too thin for a 30+ s viral cut without reuse.
- **Re-review on real footage:** Whether the hook stops a scroller, the emotional arc, the framing and crop of people, text over real subjects, and source sharpness all still need review.
- Images reviewed: review_sheet_1fps.jpg, first_2s.jpg, final_frame.jpg, plus my own extracts from the draft2 render at 0.5 / 12.3 / 13.0 / 14.2 / 29.9 / 30.1 s (the originals were not opened).
