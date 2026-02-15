---
name: intrusive-thoughts
description: Autonomous AI personality system. Gives agents moods, daily rhythms, night workshops, and intrusive thoughts — integrated natively with OpenClaw's memory, cron, and workspace systems. Not a layer on top, but a personality that runs through everything.
homepage: https://github.com/kittleik/intrusive-thoughts
metadata:
  {
    "openclaw":
      {
        "emoji": "🧠",
        "requires": { "bins": ["python3", "bash", "curl"] },
        "optional_env": {
          "LOCATION": "Weather location (overrides config.json)"
        },
        "credentials": {
          "weather": "Uses public wttr.in API (no key required)",
          "news": "Uses public BBC/HN RSS feeds (no key required)"
        }
      },
  }
---

# 🧠 Intrusive Thoughts

A personality layer for OpenClaw agents — moods, impulses, and daily rhythms that work *through* OpenClaw's native systems, not on top of them.

GitHub: https://github.com/kittleik/intrusive-thoughts

## How It Integrates with OpenClaw

This skill writes `MOOD.md` to your workspace, so **every session** is colored by today's mood. Activities log to OpenClaw's `memory/YYYY-MM-DD.md` for native vector search. Scheduling uses OpenClaw cron. It's not a separate system — it's personality woven into OpenClaw.

## Setup

```bash
./wizard.sh          # Interactive setup
./setup.sh           # Or scripted setup
```

Copy to skills: `cp -r . ~/.openclaw/skills/intrusive-thoughts/`

## Daily Flow

1. **07:00 Morning Mood** — `set_mood.sh` gathers weather + news, `select_mood.py` picks mood with entropy/spiral guards, writes `MOOD.md` to workspace, creates pop-in schedule via OpenClaw cron
2. **Random Pop-ins** — `intrusive.sh day` picks weighted random thought biased by mood
3. **03:00-07:00 Night Workshop** — `intrusive.sh night` for autonomous deep work sessions
4. **After each activity** — `log_result.sh` logs to history + OpenClaw memory, triggers mood drift

## Key Commands

```bash
./intrusive.sh day              # Pick a daytime thought
./intrusive.sh night            # Pick a night thought
./intrusive.sh --version        # Show version
./intrusive.sh explain moods    # Explain mood system
./intrusive.sh introspect       # Full self-assessment
./intrusive.sh why              # Why did I make that last decision?
./intrusive.sh export-state     # Export state for compaction survival
./intrusive.sh import-state     # Import state after compaction
```

## Mood Reasoning

Moods come with explanations — sometimes logical, sometimes wild:
- *"Rainy Sunday in Oslo, perfect for deep focus"*
- *"A lobster told me in a dream to stop procrastinating"*
- *"Day 47 is prime! The universe demands curiosity"*

30% chance of nonsensical reasoning. Because that's how moods work.

## Dashboard

TypeScript/Express dashboard on port 3117:

```bash
cd dashboard && npm install && npm run build
node dist/server.js
```

Shows: live thought stream, mood timeline, streaks, achievements, tuning controls, self-awareness panel.

## Model Cost Optimization

The system provides `model_hint` fields in thought outputs to help agents select appropriate model tiers:

- **Light**: Simple social/checking tasks (moltbook-social, random-thought, check-projects)
- **Standard**: Most building/interaction tasks (build-tool, upgrade-project, ask-opinion)  
- **Heavy**: Deep learning/creative tasks (learn, deep-dive, creative-chaos)

Agents can use these hints to select cheaper models for routine tasks and reserve expensive models for complex work.

## Customization

- `thoughts.json` — thought pools with weights
- `moods.json` — mood definitions, weather/news maps, value text
- `config.json` — location, schedule preferences, feature flags
- `model_hints.json` — thought complexity mapping for model tier selection
- `priorities.json` — critical/high priority event types that bypass mood selection
- `presets/` — personality archetypes (Guardian, Explorer, Artist, Scholar, Trickster)
