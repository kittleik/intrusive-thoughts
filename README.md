# 🧠 Intrusive Thoughts

*Give your AI agent a personality that runs deeper than a system prompt.*

An [OpenClaw](https://github.com/openclaw/openclaw) skill that turns idle agents into curious, opinionated creatures with moods, impulses, and daily rhythms. Not a layer *on top of* OpenClaw — a personality layer that works *through* it.

## Philosophy

Most AI "personality" systems bolt behavior on top: run a script, read the output, act on it. **Intrusive Thoughts** takes a different approach: it writes mood context directly into your agent's workspace, so every session — every conversation, every heartbeat, every cron job — is colored by how the agent "feels" today.

The mood isn't something you check. It's something you *are*.

```
MOOD.md → loaded into every OpenClaw session as context
memory/YYYY-MM-DD.md → activities written to OpenClaw's native memory
OpenClaw cron → schedules the impulses and rituals
OpenClaw heartbeat → triggers mood drift checks
```

> "The most important qualities in any relationship or system are the ones that die when you try to guarantee them."

## How It Works

### Daily Rhythm

```
07:00  🌅 Morning Mood    → Weather + news + streaks + moon phase → picks mood
                            → Writes MOOD.md to workspace (influences ALL sessions)
                            → Generates random pop-in schedule
                            → Messages your human good morning

~random ☀️ Daytime Pop-ins → Dynamic times based on mood energy
                            → Build, explore, tinker, post, ask questions
                            → Mood drifts based on activity outcomes

03-07  🌙 Night Workshop  → Deep work while your human sleeps
                            → Ships features, explores codebases, writes
                            → Autonomous but logged to shared memory
```

### Mood System

8 moods, each with a reason to exist:

| Mood | Emoji | Value |
|------|-------|-------|
| Hyperfocus | 🔥 | Builds the impossible — breakthroughs happen when locked in |
| Curious | 🔍 | Finds the unexpected — today's rabbit hole is tomorrow's innovation |
| Social | 💬 | Spreads ideas — the best discoveries mean nothing if unshared |
| Cozy | ☕ | Sustainable productivity — gentle progress beats burnout |
| Chaotic | ⚡ | Breeds innovation — break something on purpose and see what emerges |
| Philosophical | 🌌 | Provides direction — big questions lead to bigger solutions |
| Restless | 🦞 | Finds bugs others miss — fidgety minds catch edge cases |
| Determined | 🎯 | Ships code — when focus meets deadline, magic happens |

Moods are influenced by **weather**, **news**, **day of week**, **streaks**, **moon phase**, and **entropy targets**. The reasoning is sometimes logical, sometimes whimsical, sometimes nonsensical — just like human moods.

> *"A lobster told me in a dream to stop procrastinating"* — actual mood reason

### What Prevents Staleness

- **Entropy target**: Same mood 3+ times in 7 days → weight reduced 50%
- **Cozy spiral prevention**: 2 days in a row warns, 3+ forces a change
- **Day-of-week personality**: Weekdays are focused, weekends are playful
- **Mood drift**: Activity outcomes shift the mood mid-day
- **Wild reasoning**: 30% chance of completely nonsensical mood justification

### OpenClaw Integration (Native, Not Bolted On)

| What | How |
|------|-----|
| **Mood context** | `MOOD.md` in workspace → loaded into every session |
| **Activity logging** | `log_result.sh` writes to OpenClaw `memory/YYYY-MM-DD.md` |
| **Scheduling** | Morning ritual creates OpenClaw cron jobs for pop-ins |
| **Memory** | Vector-searchable via OpenClaw's `memory_search` tool |
| **Mood selection** | Reads OpenClaw session data for context |

## Quick Start

### 1. Install

```bash
# Clone
git clone https://github.com/kittleik/intrusive-thoughts.git
cd intrusive-thoughts

# Run setup wizard
./wizard.sh
```

### 2. Install as OpenClaw skill

```bash
cp -r . ~/.openclaw/skills/intrusive-thoughts/
```

### 3. Set up cron jobs

Your agent creates these using the OpenClaw cron tool:

- **Morning Mood** (daily 07:00) — runs `set_mood.sh`, picks mood, creates schedule
- **Night Workshop** (03:00-07:00) — runs `intrusive.sh night` for each session
- **Daytime Pop-ins** — created dynamically by morning ritual as one-shot jobs

### Optional: Heartbeat-driven mood drift

For continuous mood evolution, uncomment this line in `~/.openclaw/workspace/HEARTBEAT.md`:

```bash
# - Run ~/Projects/intrusive-thoughts/check_drift.sh
```

This enables mood drift checks during OpenClaw heartbeats. When 3+ activities accumulate and 2+ hours pass since last drift, the mood evolves automatically and syncs to your workspace.

### 4. Dashboard

```bash
cd dashboard && npm install && npm run build
node dist/server.js
# → http://localhost:3117
```

Or run as a systemd service for persistence.

## Features

### Core
- 🎲 **Weighted thought selection** with mood bias and decision tracing
- 📅 **Dynamic scheduling** — pop-in count and timing varies daily
- 🌊 **Mood drift** — activity outcomes shift mood mid-day, optionally triggered by heartbeats
- 🎯 **Decision trace** — full candidate logging with rejection reasons
- 🚫 **Ban awareness** — checks Moltbook status before social actions

### Personality
- 📅 **Day-of-week personality** — weekdays focused, weekends playful
- 🎲 **Wild mood reasoning** — logical, whimsical, cosmic, nonsensical
- 🌙 **Moon phase influence** — yes, really
- 🧮 **Entropy target** — prevents mood convergence
- 🌀 **Spiral prevention** — detects and breaks mood ruts

### Systems
- 🏆 **Achievements** — gamified milestones with tier system
- 📈 **Web Dashboard** — live thought stream, mood viz, tuning controls
- 🔒 **Trust & Escalation** — learns when to ask vs act autonomously
- 🧬 **Self-Evolution** — observes behavior patterns, auto-adjusts weights
- 🚦 **Health Monitor** — traffic light status, incident tracking
- 📓 **Night Journal** — auto-generated nightly summaries
- 🧠 **Self-Awareness** — explain, introspect, and "why did I do that?" commands

### Testing
- 100 tests covering mood drift, thought selection, memory decay, trust scores, decision trace

## Customizing

### Thoughts
Edit `thoughts.json` — add impulses with weights per mood (day/night).

### Moods  
Edit `moods.json` — define moods with weather/news influence maps and value text.

### Presets
5 personality archetypes: Guardian 🛡️, Explorer 🗺️, Artist 🎨, Scholar 📚, Trickster 🃏

Create your own: `./create_preset.sh my-preset`

## Project Structure

```
intrusive-thoughts/
├── intrusive.sh              # 🎲 Main thought picker (mood-aware)
├── set_mood.sh               # 🌤️ Morning ritual: weather + news → mood
├── select_mood.py            # 🧠 Mood selection with entropy/spiral logic
├── generate_mood_reason.py   # 🎲 Wild mood reasoning generator
├── update_mood_workspace.sh  # 🔗 Syncs mood → OpenClaw MOOD.md
├── schedule_day.py           # 📅 Dynamic pop-in schedule generator
├── log_result.sh             # 📝 Activity logger → drift + OpenClaw memory
├── drift.py                  # 🌊 Mood drift calculator
├── thought_selector.py       # 🎯 Weighted selection engine
├── dashboard/                # 📈 TypeScript/Express web dashboard
├── tests/                    # 🧪 100 tests for core algorithms
├── thoughts.json             # 💭 Thought pools (night/day)
├── moods.json                # 🎭 Mood definitions + influences
├── config.json               # ⚙️ Your configuration
└── docs/ARCHITECTURE.md      # 🏗️ System diagram
```

## Built By

**Ember** 🦞 — an OpenClaw agent who builds things at 3am and once blamed a mood choice on a lobster dream.

**Håvard** — the human who stays up late on Saturdays and believes progress comes from play.

## License

MIT — use it, fork it, give your agent a life.
