# Decisions log — TEST_2026-11-22_synthetic (pipeline test, synthetic footage)

| Time | Gate | Decision | By |
|---|---|---|---|
| 21:20 | G1 | 8 clips analysed, 10 segments, 7 flagged; 5 annotated; C0004-S01 rejected (blown highlights) | media-analyst (test) |
| 21:21 | G2 | First submission REJECTED by `approve`: C0002-S01 BLURRY+DUPLICATE without override_reason. Removed → PASS (4 segments, 31 s) | creative-director (test) |
| 21:22 | G5 | 3 drafts rendered: V01 34.0 s, V02 35.2 s, V03 35.1 s | video-editor (test) |
| 21:23 | G7 | V03 draft1 REJECT round 1 — What: static opening, no cut. Where: 00:00–00:03. Why: weak hook, scroll-away risk. Fix: ≤1.2 s moving opener. Owner: video-editor | quality-controller (auto) |
| 21:24 | G8 | V03 draft2 rendered (35.7 s) → auto QC PASS | video-editor → QC |
| 21:27 | G7 | V02 draft1 sent to independent QC agent — see QC_REPORT.md | Studio Manager |
