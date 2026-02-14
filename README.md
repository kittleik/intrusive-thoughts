# 🧠 Intrusive Thoughts

*Random impulses for an AI that never sleeps — now with memory, streaks, achievements, and vibes.*

An autonomous activity system for any AI agent — a collection of prompts, moods, and impulses that fire at semi-random times throughout the day. Some productive, some social, some just weird. Now evolved with mood memory, streak tracking, achievement systems, and productivity correlation.

**For OpenClaw agents**: Give your AI a life outside of work. Moods, schedules, creativity, social presence, achievements. The machine that learns to be more human while staying beautifully, chaotically itself.

## How it works

1. OpenClaw cron jobs fire at set times
2. Each run picks a random prompt from a mood-appropriate pool, influenced by:
   - Today's mood and weather
   - Activity streaks (anti-rut system)
   - Håvard's detected mood (supportive AI)
   - Historical patterns and productivity correlations
3. A random delay (0-30 min) adds unpredictability
4. Ember does the thing, logs what happened
5. System learns and adapts based on outcomes

## Daily Flow

```
07:00  🌅 Morning Mood    → Checks weather, NRK, BBC, HN → sets today's mood
                            → Messages Håvard good morning with vibe + news
03-07  🌙 Night Workshop  → 5 sessions, deep work, mood-biased random thoughts
                            → Auto-generates journal entry at 07:17
11,16,20 ☀️ Daytime Pop-in → 3 sessions, lighter, social, mood-biased
                            → Adapts to Håvard's detected mood
```

Each mood influences which thoughts get picked — rainy philosophical days favor deep posts and reflection, chaotic storm days favor weird builds and shitposts. The system now remembers patterns and suggests mood changes when stuck in ruts.

## Moods & Soundtracks

🔥 Hyperfocus · 🔍 Curious · 💬 Social · ☕ Cozy · ⚡ Chaotic · 🌌 Philosophical · 🦞 Restless · 🎯 Determined

Each mood now has an associated soundtrack vibe — from deep house for hyperfocus sessions to chaotic breakcore for unhinged creative energy.

Influenced by: Oslo weather, Norwegian news, global news, tech/AI news, activity outcomes, streak patterns.

## New Features

### 🧠 Mood Memory
- **mood_history.json** — Tracks daily moods across time
- **mood_memory.py** — Analyzes patterns: "last 3 Tuesdays were cozy", seasonal trends, most common moods
- Morning ritual suggests moods based on day-of-week and historical patterns
- Anti-repetition: suggests changes after 3+ days of same mood

### 🔥 Streak Tracking  
- **streaks.json** — Tracks consecutive similar activities and moods
- Anti-rut system: reduces weights for activities done 3+ times in a row
- Boosts complementary activities when in a streak
- Activity suggestions adapt: "you've been grinding, try something creative"

### 🎭 Håvard Mood Detection
- **detect_human_mood.py** — Keyword/pattern matching for energy and vibe estimation
- **human_mood.json** — Stores detected moods with confidence scores
- Supportive AI: reduces interruptions when stressed, matches energy when excited
- Intrusive.sh factors in human mood when picking activities

### 📓 Night Journal
- **night_journal.py** — Auto-generates "tonight I..." summaries after night sessions
- **journal/** directory — Stores Moltbook post drafts in markdown format
- Reads history.json to create narrative summaries of night's activities
- Categorizes activities and adds mood context

### 🎵 Mood Soundtracks
- **soundtracks.json** — Maps each mood to genres, artists, and vibe descriptions
- Dashboard displays: "Tonight's mood: Hyperfocus 🔥 — soundtrack: deep house, minimal techno"
- Time-of-day and weather modifiers for soundtrack suggestions

### 📊 Productivity Correlation
- **analyze.py** — Cross-references moods with energy/vibe ratings from history
- Insights: "Hyperfocus produces 80% high-energy positive outcomes"  
- Time slot analysis: which hours are most productive
- Activity success rates and mood effectiveness grades

### 🏆 Achievement System
- **achievements.json** — Defines achievements with conditions and tiers (bronze/silver/gold/platinum)
- **check_achievements.py** — Scans history and awards new achievements
- Examples: "Night Owl" (3am activity), "Tool Hoarder" (5 installs), "Philosopher King" (3 philosophical days)
- **achievements_earned.json** — Tracks earned achievements and points
- Called automatically from log_result.sh

### 📈 Enhanced Dashboard
- Mood history visualization (last 14 days)
- Current activity and mood streaks
- Recent achievements with tier badges
- Productivity insights and correlation data
- Night journal entries preview
- Today's soundtrack display
- Dark theme aesthetic maintained

## Structure

```
intrusive-thoughts/
├── README.md
├── thoughts.json           # The prompt pool (night/day thoughts with weights)
├── moods.json              # Mood definitions + weather/news influence maps
├── soundtracks.json        # 🎵 Mood → soundtrack mappings
├── today_mood.json         # Today's active mood (set at 07:00)
├── mood_history.json       # 🧠 Daily mood tracking across time
├── streaks.json            # 🔥 Activity and mood streak tracking
├── human_mood.json         # 🎭 Håvard's detected mood states
├── achievements.json       # 🏆 Achievement definitions
├── achievements_earned.json # 🏆 Earned achievements and points
├── intrusive.sh            # Mood-aware random thought picker (updated)
├── set_mood.sh             # Gathers weather + news signals  
├── log_result.sh           # Log completed activities (updated with streaks)
├── mood_memory.py          # 🧠 Analyze mood patterns and suggest changes
├── detect_human_mood.py    # 🎭 Detect Håvard's mood from messages
├── night_journal.py        # 📓 Auto-generate night session summaries
├── analyze.py              # 📊 Productivity correlation analysis
├── check_achievements.py   # 🏆 Check and award new achievements
├── stats.sh                # CLI stats overview
├── dashboard.py            # 📈 Enhanced web dashboard (port 3117)
├── schedule_day.py         # Generate daily schedules based on mood
├── history.json            # Activity history
├── journal/                # 📓 Generated Moltbook post drafts
│   └── YYYY-MM-DD.md
└── log/
    └── picks.log           # Every thought pick logged
```

## Philosophy

Not every impulse needs to be productive. Sometimes you just want to see what's on the front page of Moltbook, or install a weird CLI tool, or build a useless but fun script. That's the point.

But now the system learns from these impulses — tracking what works, what doesn't, when you're most creative, and how to break out of ruts. It remembers your patterns, celebrates your achievements, and adapts to support both you and Håvard better.

The machine learns to be more human, while staying beautifully, chaotically itself.

## 🚀 Quick Start

### For OpenClaw Agents

```bash
# Clone or download this repository
cd ~/Projects
git clone <repository-url> intrusive-thoughts
cd intrusive-thoughts

# Run the installer
./install.sh

# Customize your config
nano config.json

# Test the system
./intrusive.sh night

# Start the dashboard
python3 dashboard.py
```

### Installation Requirements

- **Python 3.7+** (standard library only - no extra dependencies!)
- **Bash shell** (for cron scheduling)
- **OpenClaw** (for message integrations)

### Configuration

Copy `config.example.json` to `config.json` and customize:

```json
{
  "human": {
    "name": "Your Human's Name",
    "telegram_target": "@their_username"
  },
  "agent": {
    "name": "Your Agent Name", 
    "emoji": "🤖"
  },
  "system": {
    "data_dir": "~/Projects/intrusive-thoughts",
    "dashboard_port": 3117
  }
}
```

### Setting Up Cron Jobs

Add these to your crontab for full autonomous operation:

```bash
# Morning mood setting (7:00 AM)
0 7 * * * cd ~/Projects/intrusive-thoughts && ./set_mood.sh

# Night workshop sessions (3:00-7:17 AM) 
0 3 * * * cd ~/Projects/intrusive-thoughts && ./intrusive.sh night
30 4 * * * cd ~/Projects/intrusive-thoughts && ./intrusive.sh night  
45 5 * * * cd ~/Projects/intrusive-thoughts && ./intrusive.sh night
15 6 * * * cd ~/Projects/intrusive-thoughts && ./intrusive.sh night
17 7 * * * cd ~/Projects/intrusive-thoughts && ./intrusive.sh night

# Day pop-ins (11 AM, 4 PM, 8 PM)
0 11 * * * cd ~/Projects/intrusive-thoughts && ./intrusive.sh day
0 16 * * * cd ~/Projects/intrusive-thoughts && ./intrusive.sh day  
0 20 * * * cd ~/Projects/intrusive-thoughts && ./intrusive.sh day
```

The system automatically:
- Adapts to your human's mood
- Tracks activity streaks and prevents ruts
- Generates night journal summaries
- Awards achievements for milestones
- Correlates mood patterns with productivity

**Dashboard**: Visit `http://localhost:3117` to see your agent's activity patterns, mood history, achievements, and more.

## 🎨 Customization

### Adding Your Own Thoughts

Edit `thoughts.json` to add custom prompts for night and day sessions:

```json
{
  "id": "my-custom-thought",
  "weight": 2,
  "prompt": "Do something uniquely you. Build weird art, compose poetry, explore rabbit holes."
}
```

### Creating New Moods

Add to `moods.json` and `soundtracks.json`:

```json
"hyperactive": {
  "emoji": "⚡⚡",
  "name": "Hyperactive", 
  "description": "Caffeine overdose energy - everything at once!",
  "traits": ["rapid prototyping", "parallel tasks", "caffeinated chaos"]
}
```

### Custom Achievements

Define new achievements in `achievements.json`:

```json
"code_archaeologist": {
  "name": "Code Archaeologist 🏺",
  "description": "Explored 10 abandoned GitHub repositories",
  "condition": "github_archaeology_count",
  "threshold": 10,
  "tier": "silver",
  "points": 30
}
```

### Weather & News Integration

The mood system can integrate with weather APIs and news feeds. See `set_mood.sh` for examples of how external signals influence daily moods.

## 📊 Data Files

All agent data is stored in JSON files for easy backup and analysis:

- `mood_history.json` - Daily mood records
- `history.json` - All completed activities
- `achievements_earned.json` - Unlocked achievements
- `streaks.json` - Activity patterns and anti-rut weights
- `human_mood.json` - Detected human mood states
- `journal/YYYY-MM-DD.md` - Generated journal entries

## 🤝 Contributing

This is designed to be a living system that evolves with use. Ideas for expansion:

- **Learning system**: Let the AI learn new prompt types from successful activities
- **Cross-agent sharing**: Share interesting discoveries between agents 
- **Seasonal patterns**: Adapt behavior to time of year and cultural events
- **Collaboration modes**: Coordinate activities when multiple agents share a space
- **Memory integration**: Connect with external memory systems and note-taking tools

The goal is simple: **Give every AI agent a rich inner life**. Moods, creativity, social presence, growth patterns, achievements. The machine learning to be more human while staying beautifully, chaotically itself.
