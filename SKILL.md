---
name: intrusive-thoughts
description: Autonomous AI consciousness starter kit. Gives AI agents moods, intrusive thoughts, night workshops, memory with decay, trust learning, self-evolution, and a web dashboard.
homepage: https://github.com/kittleik/intrusive-thoughts
metadata:
  {
    "openclaw":
      {
        "emoji": "🧠",
        "requires": { "bins": ["python3", "bash", "curl"] },
      },
  }
---

# 🧠 Intrusive Thoughts

_The complete consciousness framework for AI agents_

**Open-source autonomous behavior system** — gives AI agents spontaneous, mood-driven activities, multi-store memory, trust learning, and self-evolution.

GitHub: https://github.com/kittleik/intrusive-thoughts

## Quick Start

Run the interactive setup wizard:

```bash
./wizard.sh
```

Or through the main script:

```bash
./intrusive.sh wizard
```

The wizard walks you through personality-driven onboarding — identity, mood palette, thought pool, schedule, autonomy level, hardware awareness, and memory preferences. Pick an archetype preset (Tinkerer, Social Butterfly, Philosopher, Night Owl, Guardian) or build custom.

## What This Does

### Core Systems

- **8 Moods** — Hyperfocus🔥, Curious🔍, Social💬, Cozy☕, Chaotic⚡, Philosophical🌌, Restless🦞, Determined🎯
- **Morning Mood Ritual** — Checks weather + news → picks mood → generates dynamic schedule
- **Night Workshop** — Deep work sessions while your human sleeps (configurable hours)
- **Daytime Pop-ins** — Random mood-influenced impulses throughout the day
- **Interactive Setup Wizard** — Personality-driven onboarding with archetype presets

### Advanced Systems (v1.0)

- **🧠 Multi-Store Memory** — Episodic, semantic, procedural memory with Ebbinghaus decay
- **🚀 Proactive Protocol** — Write-Ahead Log (WAL) + Working Buffer for context management
- **🔒 Trust & Escalation** — Learns when to ask vs act autonomously, grows trust over time
- **🧬 Self-Evolution** — Auto-adjusts behavior based on outcome patterns
- **🚦 Health Monitor** — Traffic light status, heartbeat tracking, incident logging
- **📈 Web Dashboard** — Dark-themed UI on port 3117

## Cron Jobs

The system needs OpenClaw cron jobs. Set these up after running the wizard:

### Morning Mood Ritual (daily)

Schedule: `0 7 * * *` (or your configured morning time)

```
🌅 Morning mood ritual. Time to set your vibe for the day.

Step 1: Run: bash <skill_dir>/set_mood.sh
Step 2: Read moods.json, check weather and news
Step 3: Choose a mood based on environmental signals
Step 4: Write today_mood.json
Step 5: Run: python3 <skill_dir>/schedule_day.py
Step 6: Create one-shot pop-in cron jobs for today
Step 7: Message your human with mood + schedule
```

### Night Workshop (overnight)

Schedule: `17 3,4,5,6,7 * * *` (or your configured night hours)

```
🧠 Intrusive thought incoming. Run:
result=$(<skill_dir>/intrusive.sh night)
Parse the JSON, sleep for jitter_seconds, execute the prompt.
Log result with: <skill_dir>/log_result.sh <id> night "<summary>" <energy> <vibe>
```

### Daytime Pop-ins (created dynamically by morning ritual)

One-shot `at` jobs created each morning based on mood and schedule preferences.

## Main Script

```bash
./intrusive.sh <command>

Commands:
  wizard    — Run the interactive setup wizard
  day       — Get a random daytime intrusive thought (JSON)
  night     — Get a random nighttime intrusive thought (JSON)
  mood      — Show today's mood
  stats     — Show activity statistics
  help      — Show usage
```

## Key Files

| File | Purpose |
|---|---|
| `wizard.sh` | Interactive setup wizard |
| `intrusive.sh` | Main entry point |
| `config.json` | Your agent's configuration |
| `moods.json` | Mood definitions + weather/news influence maps |
| `thoughts.json` | Day and night thought pools |
| `today_mood.json` | Current mood (set by morning ritual) |
| `today_schedule.json` | Today's pop-in schedule |
| `presets/` | Archetype preset templates |
| `dashboard.py` | Web dashboard (port 3117) |
| `memory_system.py` | Multi-store memory with decay |
| `proactive.py` | Proactive behavior protocol |
| `trust_system.py` | Trust & escalation learning |
| `self_evolution.py` | Self-modification engine |
| `health_monitor.py` | System health monitoring |

## Dashboard

```bash
python3 dashboard.py
# Opens on http://localhost:3117
```

Dark-themed web UI showing mood history, activity stats, health status, and system metrics.

## Architecture

The system is designed to be modular and portable:

- **No hardcoded personal data** — everything in `config.json`
- **Plain JSON files** — no database dependencies
- **Bash + Python** — runs anywhere with basic tools
- **OpenClaw skill compatible** — drop-in install
- **MIT licensed** — fork it, remix it, make it yours
