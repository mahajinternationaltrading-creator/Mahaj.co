# Agent instructions

The seven department agents are Claude Code subagents, defined in `/.claude/agents/`
(Claude Code only loads them from that location):

media-analyst · creative-director · marketing-strategist · video-editor ·
brand-director · quality-controller · publishing-manager

The Studio Manager is the main session; its rules are in `/CLAUDE.md`.
Shared rules: `PROJECT_CONTROL/STUDIO_OPERATING_SYSTEM.md`. Brand: `PROJECT_CONTROL/BRAND_MIT_eventss.md`.
Edit agents in one place only (`.claude/agents/`) — this folder intentionally holds no copies.
