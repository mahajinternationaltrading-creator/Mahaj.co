# Decisions log — TEST_2026-11-22_synthetic (pipeline test, synthetic footage)

| Time | Gate | Decision | By |
|---|---|---|---|
| 21:20 | G1 | 8 clips analysed, 10 segments, 7 flagged; 5 annotated; C0004-S01 rejected (blown highlights) | media-analyst (test) |
| 21:21 | G2 | First submission REJECTED by `approve`: C0002-S01 BLURRY+DUPLICATE without override_reason. Removed → PASS (4 segments, 31 s) | creative-director (test) |
| 21:22 | G5 | 3 drafts rendered: V01 34.0 s, V02 35.2 s, V03 35.1 s | video-editor (test) |
| 21:23 | G7 | V03 draft1 REJECT round 1 — What: static opening, no cut. Where: 00:00–00:03. Why: weak hook, scroll-away risk. Fix: ≤1.2 s moving opener. Owner: video-editor | quality-controller (auto) |
| 21:24 | G8 | V03 draft2 rendered (35.7 s) → auto QC PASS | video-editor → QC |
| 21:27 | G7 | V02 draft1 sent to independent QC agent — see QC_REPORT.md | Studio Manager |
| 21:35 | G7 | V02 draft1 **REJECT round 1** by independent QC agent despite 11/11 automatic PASS: uniform 1.5 s shots (no build), strict 4-source loop with repeated in-points, beat text readability 0:12–0:13, end card lacks handle/CTA. Owner: video-editor. Not corrected: test goal (correction loop) already proven on V03; fix belongs to real production | quality-controller (agent) |
| 21:35 | — | Lesson: auto QC measures specs, not craft. Candidate engine addition: shot-length variance + repeated in-point check | Studio Manager |
| 21:50 | — | Owner delegated open decisions ("do it on your own"). Decided: on-screen name MIT_eventss / @mit_eventss; logo = Drive transparent PNG; licence-free generated beds for drafts. Not decidable by the studio: consent, Mac access | Studio Manager |
| 21:55 | — | Engine v1.2 after real-footage test (22/23 cuts); QC: scdet hook + rhythm uniformity + beat sync; `music` command; end-card logo | Studio Manager |
| 22:00 | G8 | V02 correction round 2 sent to video-editor agent (beat-locked cuts, varied rhythm, logo end card) | Studio Manager |
