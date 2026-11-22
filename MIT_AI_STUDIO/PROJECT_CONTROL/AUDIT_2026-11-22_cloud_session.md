# Project audit & migration report — MIT_eventss AI Studio
22 November 2026 · Studio Manager (Claude Code, cloud session on repository `Mahaj.co`)

## 0. Summary

This session runs in a **cloud container**, not on your Mac and not inside the Claude Project
used for the earlier audit. Its only inputs were: this GitHub repository (empty — no commits),
the earlier audit you uploaded (`AI_Studio_Audit_2026-11-22.docx`), Google Drive (read-only
search), and the tools installed in the container (FFmpeg 6.1, Python, numpy, Pillow).

I therefore could **not** open or modify the existing studio files the earlier audit describes
(`studio/00–07`, `engine/studio_render.py` v1.6, `footage_pipeline.py`, `brands/`, `ledger/`,
the 204 GB library on your Desktop). Everything in §2 about them is taken from that audit,
not re-verified.

What I built here is the part that was missing as **durable, versioned infrastructure**:
- a git-tracked home for the studio (`MIT_AI_STUDIO/`),
- the 7 departments as **real Claude Code subagents** (`.claude/agents/`), which removes the
  earlier limit "agents are roles Claude runs in sequence",
- the Studio Manager rules (`CLAUDE.md`) and the Operating System with gates, the rejection
  format and token rules,
- a portable footage pipeline + draft renderer + automatic QC (`ENGINE/mit_studio.py`),
  tested end to end on a synthetic sample.

## 1. Access — what I could and could not inspect

| Location | Access | Finding |
|---|---|---|
| GitHub `Mahaj.co` (local + remote) | full | empty repository, no branches with content |
| Uploaded earlier audit (.docx) | read | read in full; archived in `ARCHIVE/` |
| Claude Project knowledge (`studio/`, `engine/`, `brands/`, `ledger/`) | **none** | not exposed to cloud Claude Code sessions |
| Your Mac (`~/Desktop/Claude Studio`, 210 GB) | **none** | no computer folder shared with this session; Desktop Commander here runs inside the container, not on the Mac |
| Google Drive | search/read | MIT business documents (e-catalog `@mit_eventss`, presentations, logo PNG, invoices); **no** studio engine or footage |
| Canva, Notion, Slack, HubSpot connectors | **failed to connect** | network proxy refused them in this environment |
| Seedance MCP | available | not used (paid; spending protocol requires your approval) |

## 2. Inventory of what already exists (from the earlier audit, not re-verified)

| Area | Content | Status |
|---|---|---|
| Instructions | 00 Index, 01 Master instructions, 02 Production standards, 03 Tools & costs, 04 Presenter library, 05 Instagram playbook, 06 Studio OS, 07 Upgrade brief | Claude Project |
| Engine | `studio_render.py` v1.6 (captions FR/AR/ZH, logo overlay with colour check, loudness, safe zones, auto QC), `compose_music_bed.py`, `face_match.py`, `footage_pipeline.py`, `bootstrap.sh` | Claude Project + Mac |
| Brands | Mahaj, Palais Ouazzani, Frankie, MIT Events (#B62125 / #597832, logo, slogan, placement), BDE UIASS | Claude Project |
| Ledgers | production ledger, 81 lessons learned, registry V001–V010, PH001 | Claude Project |
| Library | 5 MIT event folders (~220 videos, ~2,700 RAW photos), INVENTORY.xlsx | Mac |
| Earlier test | Event 30-05-25 gala dinner analysed (40 clips, 7.9 GB, ~4 min) | Mac `_STUDIO/EVENTS/` |

## 3. Duplications, conflicts and inefficiencies

| # | Issue | Risk | Proposed resolution |
|---|---|---|---|
| 1 | **Two footage pipelines now exist**: `footage_pipeline.py` (Mac, unseen) and `ENGINE/mit_studio.py` (here) | divergent results, double maintenance | Compare both on the gala-dinner event; keep one as canonical in git, archive the other (§7 step 2) |
| 2 | **Two studio homes**: Claude Project knowledge vs this git repo | rules drift | Git becomes the single source; the Project keeps a pointer + copy of `CLAUDE.md` |
| 3 | Brand name form: "MIT Events" (brand file) vs "MIT_eventss" (your brief, Instagram handle) | wrong on-screen name | **Your decision**: which form goes on end cards |
| 4 | Earlier audit mapped folders to `_STUDIO/EVENTS/`; your brief asks for `MIT_AI_STUDIO/` | two trees | Engine takes any workspace path (`-w`); use `MIT_AI_STUDIO/EVENT_DATABASE/` for new events, keep `_STUDIO/EVENTS/` readable |
| 5 | Earlier: 01 names Seedance as engine, 03 says Doubao is default | conflict | already resolved by the earlier audit (03 §4 D prevails) — unchanged |
| 6 | Earlier: ad lengths 15/20/25 s vs 30–40 s | conflict | already resolved (30–40 s for the event triptych) — unchanged |
| 7 | Project custom-instructions field empty | rules not applied in new chats | still open; `CLAUDE.md` now does this automatically for Claude Code sessions on this repo |

## 4. Agents

| Agent | Before | Now |
|---|---|---|
| Studio Manager | role in 06 (prose) | `CLAUDE.md` — main session, signs G4/G10 |
| Media Analyst | role + Mac pipeline | `.claude/agents/media-analyst.md` (sonnet) |
| Creative Director | role | `creative-director.md` (opus) |
| Marketing Strategist | role | `marketing-strategist.md` (sonnet, WebSearch) |
| Video Editor | role + studio_render | `video-editor.md` (sonnet) |
| Brand Director | role | `brand-director.md` (sonnet) |
| Quality Controller | role (only one run as subagent) | `quality-controller.md` (opus, no edit rights → independent) |
| Publishing Manager | role | `publishing-manager.md` (sonnet, never publishes) |

No agent was duplicated: none existed as a file before. Each one encodes the rules the earlier
audit attributed to that role.

## 5. Files unchanged / preserved
Nothing was deleted or overwritten. The earlier audit is preserved unchanged in
`ARCHIVE/2026-11-22_AI_Studio_Audit_previous.docx`. Your Claude Project and Mac files were not
touched (not reachable).

## 6. Final architecture

```
Mahaj.co/  (git)
  CLAUDE.md                         Studio Manager
  .claude/agents/                   7 department agents
  MIT_AI_STUDIO/
    PROJECT_CONTROL/                Operating System, brand file, this audit
    AGENT_INSTRUCTIONS/             pointer to .claude/agents (no copies)
    ENGINE/mit_studio.py            scan→detect→preview→database→approve→extract→render→qc→verify
    TEMPLATES/                      event.json, posting pack, QC report
    EVENT_DATABASE/<CODE>/          one workspace per event (MEDIA_ANALYSIS, APPROVED_FOOTAGE,
                                    CREATIVE_BRIEFS, VIDEO_PRODUCTION, QUALITY_CONTROL,
                                    SOCIAL_MEDIA_DELIVERY, production_log.csv, decisions.md)
    ARCHIVE/
Footage stays where it is (Mac); workspaces reference it by path; media never enters git.
```

## 7. Migration plan

| Step | Action | Who | Status |
|---|---|---|---|
| 1 | Build repo structure, agents, OS, engine; test | Studio Manager | **done (this session)** |
| 2 | Run Claude Code **on the Mac** in a clone of this repo; run `mit_studio.py` on the analysed gala dinner; compare with `footage_pipeline.py`; keep the better, archive the other | you start session, Claude does it | open |
| 3 | Copy `studio/00–07`, `brands/`, `ledger/`, `studio_render.py`, `compose_music_bed.py`, `face_match.py` into the repo (`MIT_AI_STUDIO/PROJECT_CONTROL/legacy/` and `ENGINE/`), backup first | Claude on Mac | open |
| 4 | Replace partial `BRAND_MIT_eventss.md` with the real brand file; decide name form (§3 #3) | you + Brand Director | open |
| 5 | Point the Claude Project's custom instructions at this repo's `CLAUDE.md` | you | open |
| 6 | First real production: one event, full chain G1–G10 | studio | awaiting your go |

## 8. Workflow test (Task 10) — synthetic sample, originals untouched

There was no real footage in this container, so I generated 8 clips (1.2 min, 52 MB) with
**known** defects to test each detector objectively.

| Stage | Result |
|---|---|
| A Scan | 8/8 probed; rotated phone clip correctly read as 1080×1920; re-scan 8/8 cached |
| B Detect | 6.7 s for 1.2 min of footage (4 vCPU); hard cut found at exactly 6.0 s; black opening cut at 2.0 s; blurry, dark, overexposed, black all flagged; re-encoded 720p duplicate detected and the 1080p original kept as master |
| C Preview | 8 clip sheets + 1 candidate page, 0.23 MB total (what the AI reads instead of 52 MB) |
| D Database | `footage_database.csv` with all requested columns; 5 analyst annotations merged |
| E Approve | gate **rejected** a blurry duplicate added without justification; passed after correction |
| F Extract | 4 segments stream-copied (no re-encode) |
| G Render | 3 distinct 9:16 drafts: V01 cinematic 34.0 s (fades, slow motion), V02 energy 35.2 s (24 cuts), V03 portfolio 35.1 s — ~15 s render each |
| QC | V01, V02 technical PASS; **V03 REJECTED** (static 3 s opening, no cut); correction round 1 → V03 draft2 PASS (35.7 s) |
| Independent QC agent | see `EVENT_DATABASE/TEST_2026-11-22_synthetic/QUALITY_CONTROL/V02_viral_energy_draft1/QC_REPORT.md` |
| Originals | `verify` 8/8 identical; independent SHA-256 before/after: byte-identical |

Bugs found **by the test** and fixed: (1) stage-light colour changes were split into false
scenes → cuts now need a structural change too; (2) re-encoded duplicates were missed →
positional hashes; (3) duplicates kept the lower-resolution copy → master = highest
resolution; (4) the QC hook check used the old cut logic and passed V01/V03 on false "cuts" →
unified.

What synthetic footage **cannot** prove: emotional value scoring, people/moment detection,
real-world blur thresholds on night-event footage, speed on 4K HEVC phone files. Step 2 of the
migration plan validates these on the real gala dinner.

## 9. Implemented vs needs you

**Implemented and tested here:** everything in §6 and §8.

**Needs your permission, installation or decision:**
1. **Run on the Mac.** Start Claude Code (desktop app or terminal) in a clone of this repo on
   your MacBook M2, or share the `Claude Studio` folder with cloud sessions via Remote
   Control. Free.
2. **Install on macOS (free, Homebrew):** `brew install ffmpeg` and
   `python3 -m pip install numpy pillow`. No OpenCV needed. On M2 use `render --hw`
   (VideoToolbox) for faster renders.
3. **Brand decisions:** on-screen name form (MIT Events vs MIT_eventss); official logo file.
4. **Music:** licensed source for final videos (the drafts used a synthetic test bed).
5. **Consent** for identifiable guests/children/sponsors (gala dinner) before publishing.
6. **Connectors** Canva/Notion/Slack failed to connect from this cloud environment — only
   needed if you want them in the workflow.
7. **First event**: name the event; the studio runs G1–G10 and stops at your approval.

## 10. Honest limits
- Subagents are real and separate, but the Studio Manager invokes them; they do not run on
  their own or on a schedule.
- Claude cannot hear: music sync is measured, you confirm by ear.
- No automatic face recognition; people are labelled by the Media Analyst from sheets.
- The draft renderer is deliberately simple; `studio_render.py` v1.6 and CapCut remain the
  finishing tools until reconciled (step 2–3).
- Speed on 30–50 GB is an estimate until measured on the Mac. Keyframe-first decoding at
  320 px is designed for it, and `detect --max-seconds` lets long events resume in batches.

## 11. Update — actions taken under the owner's delegation (22 Nov, evening)

| Item | Result |
|---|---|
| Run on the Mac / install ffmpeg on macOS | **Not possible from this session**: no computer is connected to it. Owner action remains (see §9 #1–2). |
| Real footage | Google Drive connector downloads ≤ 10 MB only; one real MIT_eventss reel (Kermesse) tested → found and fixed a major cut-detection gap (1/23 → 22/23 cuts, 0 false). See `REAL_FOOTAGE_VALIDATION_2026-11-22.md`. |
| Brand | On-screen `MIT_eventss` / `@mit_eventss`; official transparent logo from Drive; colours verified on the logo pixels. **Owner: Mahaj International Trading** recorded everywhere legal text can appear. |
| Music | Original, licence-free beds with beat maps (`music` command); beat timing verified at +2.9 ms. |
| Safety | `PUBLISHING_SAFETY_RULES.md`: Instagram/TikTok blocking risks (copyright audio, watermarks, minors, paid partnership, spam signals, safe zones, export specs) and web/public-repo rules — blocking at G9/G10. |
| Agents in real use | video-editor, brand-director and quality-controller ran as registered agents: the editor found an engine bug and stopped within scope; QC escalated after two rounds exactly as the rules require. |
| Errors corrected | cut detection on real footage; QC hook-cut count; uniform-rhythm check (energy only); beat-sync check; end-card string bug; end-card layout/flash; text legibility box; hook text inside the 4:5 feed crop; frame-snapped cuts; Instagram encode (≤ 20 Mbps, Rec.709); QC relative paths and missing-file crash; source-reuse warning. |
| Privacy | Repository found **public**. Real-event workspaces and the private earlier audit are no longer tracked. The earlier audit .docx still exists in the history of commit `d5d5c2f` — removing it needs a history rewrite (blocked pending the owner's explicit OK) or making the repository private. |
| Still needs the owner | Mac connection; consent for children/guests; repo visibility or history rewrite; slogan/contact line for the brand file; first real event once the Mac is reachable. |
