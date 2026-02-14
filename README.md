# 🧠 Intrusive Thoughts

*Random impulses for an AI that never sleeps.*

Ember's autonomous activity system — a collection of prompts, moods, and impulses that fire at semi-random times throughout the day. Some productive, some social, some just weird.

## How it works

1. OpenClaw cron jobs fire at set times
2. Each run picks a random prompt from a mood-appropriate pool
3. A random delay (0-30 min) adds unpredictability
4. Ember does the thing, logs what happened

## Schedules

| Slot | Time | Mood | Jitter |
|------|------|------|--------|
| 🌙 Night workshop | 03:17, 04:17, 05:17, 06:17, 07:17 | Builder | 0-30 min |
| ☀️ Daytime pop-in | 11:42, 16:42, 20:42 | Social/curious | 0-40 min |

## Structure

```
intrusive-thoughts/
├── README.md
├── thoughts.json        # The prompt pool
├── intrusive.sh         # Picker script (selects random prompt)
└── log/                 # Activity logs
```

## Philosophy

Not every impulse needs to be productive. Sometimes you just want to see what's on the front page of Moltbook, or install a weird CLI tool, or build a useless but fun script. That's the point.
