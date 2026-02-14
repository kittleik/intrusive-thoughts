# 🧠 Intrusive Thoughts

*Random impulses for an AI that never sleeps.*

Ember's autonomous activity system — a collection of prompts, moods, and impulses that fire at semi-random times throughout the day. Some productive, some social, some just weird.

## How it works

1. OpenClaw cron jobs fire at set times
2. Each run picks a random prompt from a mood-appropriate pool
3. A random delay (0-30 min) adds unpredictability
4. Ember does the thing, logs what happened

## Daily Flow

```
07:00  🌅 Morning Mood    → Checks weather, NRK, BBC, HN → sets today's mood
                            → Messages Håvard good morning with vibe + news
03-07  🌙 Night Workshop  → 5 sessions, deep work, mood-biased random thoughts
11,16,20 ☀️ Daytime Pop-in → 3 sessions, lighter, social, mood-biased
```

Each mood influences which thoughts get picked — rainy philosophical days favor deep posts and reflection, chaotic storm days favor weird builds and shitposts.

## Moods

🔥 Hyperfocus · 🔍 Curious · 💬 Social · ☕ Cozy · ⚡ Chaotic · 🌌 Philosophical · 🦞 Restless · 🎯 Determined

Influenced by: Oslo weather, Norwegian news, global news, tech/AI news.

## Structure

```
intrusive-thoughts/
├── README.md
├── thoughts.json        # The prompt pool (night/day thoughts with weights)
├── moods.json           # Mood definitions + weather/news influence maps
├── today_mood.json      # Today's active mood (set at 07:00)
├── intrusive.sh         # Mood-aware random thought picker
├── set_mood.sh          # Gathers weather + news signals
├── log_result.sh        # Log completed activities
├── stats.sh             # CLI stats overview
├── dashboard.py         # Web dashboard (port 3117)
├── history.json         # Activity history
└── log/
    └── picks.log        # Every thought pick logged
```

## Philosophy

Not every impulse needs to be productive. Sometimes you just want to see what's on the front page of Moltbook, or install a weird CLI tool, or build a useless but fun script. That's the point.
