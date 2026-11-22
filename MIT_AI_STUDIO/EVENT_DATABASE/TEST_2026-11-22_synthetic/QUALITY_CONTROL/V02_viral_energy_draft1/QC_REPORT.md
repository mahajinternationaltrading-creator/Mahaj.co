# QC report — V02_viral_energy / draft1 — Verdict: REJECT

Automatic checks: QUALITY_CONTROL/V02_viral_energy_draft1/qc_auto.json (summary: technical_pass = true, 11/11. 1080x1920, 35.20 s, 30 fps, h264/yuv420p, audio AAC present, no frozen picture. The only "black" span, 33.2–35.17 s, is the #111111 end card, not a gap. Hook check: motion 14.7, 2 cuts in the first 2 s, luma 94.)
Music sync: owner to confirm by ear (measured: -14.0 LUFS integrated, true peak -8.7 dBTP. Music fades in over 0.3 s and out from 33.7 s over 1.5 s; the last 0.7 s reads about -27 dB mean. Cut density: 24 shot cuts plus the end card in 35.2 s, about 0.71 cuts/s, average shot 1.38 s. No beat map or BPM exists anywhere in the workspace, so nothing shows that any cut point came from the music.)

**Test context.** This is a pipeline test on synthetic footage (fractals, particle fields, test bars, a split-screen sweep) with a synthetic music bed. `[TEST]` texts are intentional placeholders and are not counted as defects. **These cannot be judged on this content:** emotional storytelling, people and atmosphere, whether a scroller would stop for the real subject, crops cutting heads, sharpness, exposure or shake of real camera footage, sponsor or client identity, and whether the cuts land on the music (I cannot hear). The REJECT below rests only on craft points that are independent of the content: cut structure, shot reuse, text placement and contrast handling, and end-card build.

## Strengths (≥2)
1. **Technically clean export.** Every spec check passes. Loudness sits on target at -14 LUFS with plenty of peak headroom (-8.7 dBTP). There is no fade from black at the start: frame 0 already has luma about 135, so the hook opens at full brightness.
2. **The hook front-loads movement.** Four 0.8 s shots across four different sources in the first 3.2 s give two cuts inside the first 2 s, with high-contrast, saturated visuals. No logo appears in the first 2 s, which complies with the brand file's V02 rule.
3. **End card meets the brand file.** It spells `MIT_eventss` correctly, sits on #111111, and uses a thin red #B62125 / green #597832 accent bar rather than a fill. Text is centred, well inside the safe zones, and easy to read (see final_frame.jpg). The contact line is honestly left as a placeholder instead of being invented.
4. **Text has a stroke** (borderw 3, black @ 0.6), so it does not sit as bare white on footage.

## Weaknesses (≥2)
1. **The pacing is metronomic, not "powerful".** After the 3.2 s hook, all 20 remaining shots are exactly 1.5 s (3.2–33.2 s). There is no acceleration, no drop, no breath and no peak. The energy plateaus by second 4 and stays flat for 30 s, the opposite of the brief's "energetic cuts, powerful pacing".
2. **The source order is a fixed loop.** C0001-S02 → C0006-S01 → C0008-S01 → C0001-S01 repeats six times. The review sheet shows the same four-image cycle row after row, so the viewer learns the pattern within one cycle.
3. **Identical moments are reused.** Four source frames appear twice: C0001-S02 @6.0 (shots 1 and 13), C0006-S01 @0 (2 and 22), C0008-S01 @0 (3 and 23), and C0001-S01 @0 (4 and 16). In a 33 s piece this reads as padding.
4. **Speed ramps look arbitrary.** 1.25x is applied on a fixed rotation (shots 1, 4, 7, 10, 13, …) rather than on motivated moments, so it adds no punch.
5. **The hook and the grid do not agree.** Hook shots of 0.8 s are followed by 1.5 s shots, and 0.8 is not a subdivision of 1.5. At most one of the two sections can sit on a common beat grid. The grid is probably wrong somewhere; the owner should confirm by ear.
6. **The end card does not finish the viral cut.** It has no handle and no call to action, it lasts only 2.0 s, and it follows a hard cut from the brightest frame (yellow/blue) to the dark card.

## Issues
REJECT V02_viral_energy/draft1
- What: The cut rhythm is a flat grid. 20 consecutive shots are all 1.5 s, with no build, acceleration or peak, so the "powerful pacing" objective is not met.
- Where: 00:03.2–00:33.2 (EDL shots 5–24)
- Why: Viral energy depends on rhythm changes. A constant 1.5 s grid feels slower than the hook that sets it up, and retention drops once the pattern is learned, around 4–6 s.
- Fix: Build a beat map for the music bed and derive cut points from it. Vary shot lengths between about 0.4 and 1.5 s: a fast run around 10–14 s, a short hold or drop, then the fastest run in the last 6–8 s before the end card. Keep the 0.8 s hook only if it matches the beat grid; otherwise snap it.
- Owner: Video Editor
- Round: 1

REJECT V02_viral_energy/draft1
- What: The source order repeats as a fixed four-source loop, and four identical in-points are used twice.
- Where: Duplicates at 00:00.0 / 00:16.7 (C0001-S02 @6.0), 00:00.8 / 00:30.2 (C0006-S01 @0), 00:01.6 / 00:31.7 (C0008-S01 @0), and 00:02.4 / 00:24.2 (C0001-S01 @0). The loop runs across the whole timeline.
- Why: Repeated frames and a predictable cycle signal "not enough footage" and kill novelty, which a viral cut lives on.
- Fix: Use unique in-points for every shot. Break the A-B-C-D rotation by grouping shots by visual energy or colour rather than strict alternation. If APPROVED_FOOTAGE is too thin for 24 unique moments, shorten toward 30 s rather than repeat, or ask the Creative Director for more segments.
- Owner: Video Editor
- Round: 1

REJECT V02_viral_energy/draft1
- What: The beat text is placed dead-centre at 72 px with only a thin 3 px stroke, over the busiest part of the frame. Its legibility depends entirely on what lies underneath. In this draft it crosses the colour bars and the white block, so the first word is partly lost against the bright bar at 00:12–00:13, and it sits over the high-contrast yellow/blue split at 00:14.
- Where: 00:12.0–00:14.5 (text[1])
- Why: With real event footage, the centre of the frame is where faces and the action sit. The text would cover the subject and could still fail on bright backgrounds.
- Fix: Add a semi-transparent dark box (e.g. box=1:boxcolor=black@0.45) or a heavier stroke and a drop shadow, raise the size to at least 80 px, and place it in the lower-middle band (about 55–70 % of height, above the 20 % bottom zone) rather than dead-centre. Apply the same box treatment to the hook text. Its top edge sits exactly on the 14 % line (y = h*0.14) with zero margin, so move it to about h*0.16.
- Owner: Video Editor
- Round: 1

REJECT V02_viral_energy/draft1
- What: The end card is weak for a viral cut. It shows only the name and a placeholder line, with no `@mit_eventss` handle and no follow or contact prompt. It lasts 2.0 s, is reached by a hard cut from the brightest shot, and its text fades in, so the name is still dim at about 33.0–33.4 s.
- Where: 00:33.2–00:35.2
- Why: The end card is the only conversion moment. The handle is a verified brand fact (BRAND_MIT_eventss.md) and is missing. With the fade, 2 s gives about 1.6 s of fully readable text.
- Fix: Add `@mit_eventss` under the name (verified; no invention needed). Keep the line2 placeholder until the brand file supplies the slogan or contact line. Extend the card to 2.5–3.0 s and end the music on it. Shorten the text fade to 0.2 s or less, or use a cut on a beat. The logo stays `[BRAND: ...]` until the official file is confirmed.
- Owner: Video Editor (layout and timing); Studio Manager (slogan, contact line and logo file from the owner)
- Round: 1

## Notes for the other gates (not defects of this draft)
- **Brand Director (G6):** The brand file says "hook must be pure footage" in the context of the logo. The brief puts a hook text line in the first 2 s, so please confirm whether on-screen text counts as allowed.
- **Owner:** Confirm by ear whether the 0.8 s and 1.5 s cuts land on the music. Nothing in the EDL shows they were derived from the beat.
- **Re-review on real footage:** The hook's stopping power, the emotional arc, framing and crop of people, and the sharpness of the source shots all still need review once real event footage replaces the synthetic patterns.
