# MIT_eventss AI Studio

Multi-agent production system that turns raw event footage (30–50 GB) into three 30–40 s
vertical videos — Cinematic Story, Viral Energy, Commercial Portfolio — plus posting packs,
with approval gates, independent QC and minimal processing.

- Studio Manager rules: [`CLAUDE.md`](CLAUDE.md)
- Operating system: [`MIT_AI_STUDIO/PROJECT_CONTROL/STUDIO_OPERATING_SYSTEM.md`](MIT_AI_STUDIO/PROJECT_CONTROL/STUDIO_OPERATING_SYSTEM.md)
- Audit & migration plan: [`MIT_AI_STUDIO/PROJECT_CONTROL/AUDIT_2026-11-22_cloud_session.md`](MIT_AI_STUDIO/PROJECT_CONTROL/AUDIT_2026-11-22_cloud_session.md)
- Agents: [`.claude/agents/`](.claude/agents/)

## Quick start (macOS)

```bash
brew install ffmpeg && python3 -m pip install numpy pillow
```

```bash
E="python3 MIT_AI_STUDIO/ENGINE/mit_studio.py -w MIT_AI_STUDIO/EVENT_DATABASE/MITEV_2025-05-30_gala"
$E scan --source "$HOME/Desktop/Claude Studio/1 MIT Events/1 Sources/Event 30-05-25"
$E detect --max-seconds 110   # repeat until "analysed 0"
$E database && $E preview && $E status
```

Original footage is never modified, copied or committed.
