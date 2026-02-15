# Intrusive Thoughts — Architecture

## Design Principle

Intrusive Thoughts is **not a separate system** — it's a personality layer that works *through* OpenClaw's native capabilities. Mood doesn't live in a JSON file you read; it lives in `MOOD.md` which is loaded into every session. Activities don't go to a custom log; they go to OpenClaw's `memory/YYYY-MM-DD.md` where they're vector-searchable. Scheduling uses OpenClaw cron, not crontab.

## Integration Points

```
┌─────────────────────────────────────────────────┐
│                   OPENCLAW                       │
│                                                  │
│  ┌──────────┐  ┌──────────┐  ┌───────────────┐  │
│  │ Workspace │  │   Cron   │  │    Memory     │  │
│  │          │  │          │  │               │  │
│  │ MOOD.md  │  │ Morning  │  │ memory/*.md   │  │
│  │ SOUL.md  │  │ Night    │  │ MEMORY.md     │  │
│  │ USER.md  │  │ Pop-ins  │  │ memory_search │  │
│  └────┬─────┘  └────┬─────┘  └──────┬────────┘  │
│       │              │               │           │
│       └──────────────┼───────────────┘           │
│                      │                           │
├──────────────────────┼───────────────────────────┤
│        INTRUSIVE THOUGHTS (personality layer)     │
│                      │                           │
│  ┌──────────┐  ┌─────┴────┐  ┌───────────────┐  │
│  │   Mood   │  │ Thought  │  │   Feedback    │  │
│  │  System  │  │ Selector │  │    Loops      │  │
│  │          │  │          │  │               │  │
│  │ Weather  │  │ Weighted │  │ Mood drift    │  │
│  │ News     │  │ Random   │  │ Streaks       │  │
│  │ Day/week │  │ Decision │  │ Achievements  │  │
│  │ Moon     │  │ Trace    │  │ Trust         │  │
│  │ Entropy  │  │ Ban-aware│  │ Evolution     │  │
│  │ Spirals  │  │          │  │               │  │
│  └──────────┘  └──────────┘  └───────────────┘  │
│                                                  │
│  ┌──────────────────────────────────────────┐    │
│  │           Dashboard (TypeScript)          │    │
│  │  Live stream · Mood viz · Tuning · Health │    │
│  │  Achievements · Self-awareness · Journal  │    │
│  └──────────────────────────────────────────┘    │
└──────────────────────────────────────────────────┘
```

## Data Flow

### Morning Ritual (07:00)
```
set_mood.sh
  → curl wttr.in (weather)
  → curl BBC/HN RSS (news)
  → select_mood.py (entropy + spirals + day-of-week + moon)
  → generate_mood_reason.py (30% nonsensical)
  → writes today_mood.json
  → update_mood_workspace.sh → MOOD.md (OpenClaw workspace)
  → schedule_day.py → creates OpenClaw cron one-shots
```

### Thought Selection (pop-in or night session)
```
intrusive.sh [day|night]
  → reads today_mood.json for bias
  → reads streaks.json for anti-rut
  → checks moltbook_status.json for bans
  → weighted random selection with full decision trace
  → outputs JSON: {id, prompt, mood_id, jitter_seconds}
  → agent executes the prompt
  → log_result.sh → history.json + OpenClaw memory + drift
```

### Mood Drift
```
Activity completes with energy/vibe rating
  → drift.py calculates cumulative drift
  → If threshold crossed: mood shifts
  → update_mood_workspace.sh refreshes MOOD.md
  → Next session sees the new mood automatically
```

## Key Files

| File | Purpose |
|------|---------|
| `MOOD.md` (workspace) | Loaded into every OpenClaw session |
| `today_mood.json` | Current mood state + reason |
| `moods.json` | Mood definitions, weights, influences, value text |
| `thoughts.json` | Thought pools (day/night) with weights |
| `mood_history.json` | Historical mood selections for entropy |
| `streaks.json` | Consecutive mood/activity tracking |
| `log/decisions.json` | Full decision traces with candidates |
| `moltbook_status.json` | Social platform ban tracking |

## Guards Against Staleness

1. **Entropy target** — mood used 3+ times in 7 days gets weight halved
2. **Spiral prevention** — same mood 3 days running forces a change
3. **Day-of-week weights** — weekdays ≠ weekends
4. **Weather/news influence** — real-world data shifts weights
5. **Mood drift** — activities change the mood mid-day
6. **Random jitter** — timing is never exact
7. **Wild reasoning** — 30% chance of absurd mood justification
