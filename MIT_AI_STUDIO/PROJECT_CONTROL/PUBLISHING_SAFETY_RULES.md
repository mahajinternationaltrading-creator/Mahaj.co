# Publishing safety rules — avoid mistakes, blocks and reach penalties (v1.0, 22 Nov 2026)

Applies to every video, caption and file the studio produces for Instagram, TikTok,
YouTube Shorts, the web and this repository. **A failed rule blocks delivery** (G9/G10);
it is not a note passed along with the file. Platform behaviour changes: re-verify the
items marked *(verify quarterly)* each quarter and record the date here.

## 1. Identity and ownership
- **mit_eventss is a trade name of Mahaj International Trading.** It is the name used
  for events; the legal entity is always **Mahaj International Trading**.
- On screen and in captions: `mit_eventss` / `@mit_eventss`. Legal mentions (contracts,
  invoices, quotes, website legal page, paid-partnership disclosures) name
  **Mahaj International Trading**, with company facts (address, registration numbers, email,
  phone) taken **only** from the current MAHAJ Company Brain — never typed from memory.
- Contact rules (same as `mahaj-controle-document`): no `gmail` address and never
  `info@mahaj.co` (typo) in any public or client-facing text; no superseded address.
- Never invent a slogan, a client, a sponsor, a price, an award or a statistic.

## 2. Instagram / TikTok — avoid blocked, muted or down-ranked posts *(verify quarterly)*
| Risk | Rule | Enforced by |
|---|---|---|
| Music muted / video blocked (copyright) | Only original studio beds (`music` command), properly licensed tracks with written proof, or audio added **inside the app** from its own library. Never upload a file containing commercial songs (including music playing at the venue that dominates the sound). Business accounts have a reduced in-app music library — check before planning a trend. | Editor, QC, Publishing Manager |
| Reduced recommendation (unoriginal content) | No other-platform watermarks (TikTok/CapCut logos), no re-uploads of someone else's footage, no near-identical reposts. Export a clean master and post natively to each platform. | Editor, QC (manual look) |
| Blurry / cropped video | 1080×1920, 9:16 exactly, H.264, AAC, 30 fps, ~8–20 Mbps, Rec.709 (engine defaults). The published Kermesse reel was 720×1280 — export at 1080×1920. | engine `render` + `qc` |
| Text or face cut by the feed/grid crop or hidden by the app UI | Keep hook text, faces, logo and CTA inside y **285–1570 px** (of 1920) and ~65 px from the sides. Engine text positions are inside this band. | engine, Brand Director, QC |
| Minors | Identifiable children only with written consent from the organiser/parents; no names, schools or locations that identify a child; no children in ads without consent of both organiser and parents. Without consent → do not publish, or blur faces. | Publishing Manager blocks |
| Undisclosed sponsorship | When a post promotes a client, sponsor or partner for payment or exchange, use the platform's **Paid partnership** label; sponsor logos only if the client agreement allows. | Publishing Manager |
| Engagement bait / spam signals | No "like/tag 3 friends/comment YES" bait; 3–8 relevant hashtags (never banned or unrelated tags, never the same block on every post); no identical caption across many posts. | Publishing Manager |
| Action blocks on the account | Publish manually or through Meta Business Suite / an approved scheduler; never automation that likes/follows/comments; no mass DMs; no password sharing with unofficial apps. The studio never publishes. | Studio Manager |
| Cover | Choose the cover before publishing (cannot be edited after on Instagram); key text bold ≥ 60 px inside the 3:4 grid centre. | Publishing Manager |
| Misleading claims | No guarantees of results, no fake reviews/testimonials, no "official" claims about the authorities. | Brand Director |

## 3. Web and this repository — avoid public mistakes
- **This GitHub repository is public.** Never commit: real footage, frames, contact sheets or
  QC images of real events; people's names or descriptions; client names, prices, quotes,
  contracts; phone numbers or emails; the earlier private audit. `.gitignore` enforces the
  main cases — check `git status` before every push.
- Prefer making the repository **private** (owner action: GitHub → Settings → General →
  Danger Zone → Change visibility).
- Website / public pages: same identity rules as §1; every company fact from the Company
  Brain; links checked; no client logo without permission; images compressed and with alt
  text; no personal data of guests.
- Never paste secrets (tokens, passwords) into any file, caption, prompt or commit.

## 4. Pre-publish checklist (Publishing Manager, per video)
1. QC `technical_pass` true and QC_REPORT verdict PASS (or owner accepted escalation).
2. `brandcheck` on the caption file passes; brand check PASS: `mit_eventss` spelling, official logo, ownership correct where legal text appears.
3. Music source recorded (original bed file / licence proof / in-app audio).
4. Consent recorded for identifiable people, especially children; sponsors cleared.
5. No other-platform watermark; 1080×1920; text in the safe band.
6. Caption: facts only from event.json + brand file; no gmail / `info@mahaj.co`; 3–8 hashtags;
   paid-partnership label if applicable; no engagement bait.
7. Cover chosen and safe for the 3:4 grid.
8. Owner's explicit approval recorded in `decisions.md`. The studio never posts.
