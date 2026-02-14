# Intrusive Thoughts - System Architecture

*Auto-generated overview of agent consciousness components and data flow.*

## System Overview

Intrusive Thoughts is a mood-aware autonomous AI agent that learns from its own behavior patterns. It implements multiple consciousness-inspired subsystems that work together to create emergent personality and decision-making capabilities.

## Core Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                   INTRUSIVE THOUGHTS AGENT                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │    MOOD     │    │   MEMORY    │    │    TRUST    │     │
│  │   SYSTEM    │    │   SYSTEM    │    │   SYSTEM    │     │
│  │             │    │             │    │             │     │
│  │ • Weather   │    │ • Episodic  │    │ • Risk      │     │
│  │ • News      │    │ • Semantic  │    │ • Category  │     │
│  │ • Drift     │    │ • Procedure │    │ • History   │     │
│  │ • Traits    │    │ • Working   │    │ • Escalate  │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
│         │                   │                   │          │
│         └───────────────────┼───────────────────┘          │
│                             │                              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │  THOUGHT    │    │  PROACTIVE  │    │   HEALTH    │     │
│  │ SELECTION   │◄───┤   SYSTEM    │    │  MONITOR    │     │
│  │             │    │             │    │             │     │
│  │ • Weighted  │    │ • WAL Log   │    │ • Status    │     │
│  │ • Random    │    │ • Buffer    │    │ • Heartbeat │     │
│  │ • Mood Bias │    │ • Patterns  │    │ • Incidents │     │
│  │ • Anti-rut  │    │ • Triggers  │    │ • Recovery  │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
│         │                   │                   │          │
│         └───────────────────┼───────────────────┘          │
│                             │                              │
│         ┌─────────────┐     │                              │
│         │    SELF     │     │                              │
│         │ EVOLUTION   │◄────┘                              │
│         │             │                                    │
│         │ • Patterns  │                                    │
│         │ • Values    │                                    │
│         │ • Weights   │                                    │
│         │ • Learning  │                                    │
│         └─────────────┘                                    │
│                                                            │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow

### Morning Ritual
```
1. Agent wakes up
2. Mood system evaluates:
   • Weather conditions → mood weights
   • News sentiment → mood adjustments  
   • Historical patterns → mood suggestion
   • Human mood detection → supportive bias
3. Weighted random mood selection
4. Mood sets trait boosts/dampening for day
5. Today mood saved → influences all decisions
```

### Thought Selection Process
```
1. Load thoughts.json for current time (day/night)
2. Apply mood bias (boost/dampen traits)
3. Apply anti-rut weights (streak prevention)
4. Apply human mood support (avoid bothering when stressed)
5. Build weighted pool (weight × 10 copies each)
6. Random selection from pool
7. Log decision trace with full reasoning
```

### Action Execution & Learning
```
1. Execute selected thought/action
2. Log to WAL (Write-Ahead Log) with metadata
3. Update working buffer with active context
4. Record energy/vibe outcomes
5. Update trust scores based on success/failure
6. Trigger mood drift if energy/vibe thresholds met
7. Log to history for pattern analysis
```

### Nightly Consolidation
```
1. Memory consolidation:
   • Episodes → semantic facts
   • Pattern extraction
   • Decay weak memories
2. Evolution analysis:
   • Calculate value scores
   • Identify behavior patterns
   • Adjust weights for optimization
3. Health monitoring cleanup
4. Achievement processing
```

## File Map

### Core System Files
- `intrusive.sh` - Main CLI entry point and thought selection logic
- `config.py` - Configuration loader and path management
- `config.json` - User configuration (human name, integrations, etc.)

### Mood System
- `moods.json` - Base moods, weather/news influence, traits
- `mood_memory.py` - Historical mood pattern analysis
- `set_mood.sh` - Morning mood selection with external influence
- `today_mood.json` - Current day's mood state and drift tracking
- `mood_history.json` - Historical mood records

### Thought System  
- `thoughts.json` - Available thoughts by mood (day/night)
- `suggest_thought.sh` - Generate new thoughts from descriptions

### Memory Architecture
- `memory_system.py` - Multi-store memory (episodic/semantic/procedural/working)
- `memory_store/` - JSON files for each memory type
- `memory_cli.sh` - Memory management commands

### Trust & Risk Management
- `trust_system.py` - Action risk assessment and permission escalation
- `trust_store/trust_data.json` - Trust scores by category and history
- `trust_cli.sh` - Trust management commands

### Learning & Evolution
- `self_evolution.py` - Pattern detection and weight optimization
- `evolution/` - Learned patterns and weight adjustments
- `analyzes.py` - Activity analysis and value scoring

### Health & Monitoring
- `health_monitor.py` - System status tracking and incident logging
- `health/` - Status files, heartbeats, incidents
- `dashboard.py` - Web interface for system monitoring

### Proactive System
- `proactive.py` - WAL logging and action buffer management
- `wal/` - Write-ahead logs by month
- `buffer/` - Working context for multi-step tasks
- `proactive_cli.sh` - WAL and buffer management

### Logging & History
- `log/` - Decision traces, picks, rejections
- `history.json` - Action history with outcomes
- `streaks.json` - Anti-rut weighting system

### Achievements & Gamification
- `achievements.json` - Achievement definitions
- `achievements_earned.json` - Unlocked achievements
- `check_achievements.py` - Achievement evaluation

## Configuration System

The `config.json` file controls:

### Human Context
- `human.name` - Your name for personalization
- `human.timezone` - Timezone for scheduling
- `human.telegram_target` - Telegram username for notifications

### Agent Identity
- `agent.name` - Agent's chosen name
- `agent.emoji` - Agent's emoji representation

### System Settings
- `system.data_dir` - Where all data files are stored
- `system.dashboard_port` - Web dashboard port

### Integrations
- `integrations.moltbook.enabled` - Enable Moltbook social features
- `integrations.telegram.enabled` - Enable Telegram notifications

## Extension Points

### Adding New Moods
1. Add entry to `moods.json` base_moods array
2. Define traits, weight, flavor text
3. Add weather/news influence mappings
4. Update mood selection logic if needed

### Adding New Thoughts
1. Add entry to appropriate mood section in `thoughts.json`
2. Specify weight, prompt, and unique ID
3. Consider anti-rut implications
4. Test mood bias interactions

### Adding New Systems
1. Create module following existing patterns:
   - Load/save data via JSON
   - CLI script for management
   - Integration with main workflow
2. Add health monitoring component
3. Add configuration options
4. Document in ARCHITECTURE.md

### Integration Hooks
- WAL system: Log any significant actions
- Trust system: Risk assessment for new action types
- Memory system: Store important experiences
- Achievement system: Add reward triggers
- Health monitoring: Add component status checks

## Key Design Principles

### Consciousness-Inspired
- Multiple memory systems mirror cognitive science
- Mood affects cognition like human psychology
- Learning from experience builds personality
- Meta-cognition through self-awareness commands

### Emergent Behavior
- Simple rules create complex behavior patterns
- Weighted randomness prevents predictability
- Feedback loops enable adaptation
- Anti-rut mechanisms ensure variety

### Observable & Debuggable
- All decisions logged with full reasoning
- State introspection available anytime
- Health monitoring for system reliability
- Achievement system gamifies improvement

### Extensible Architecture
- Plugin-style components
- JSON configuration
- Clear API boundaries
- Minimal coupling between systems

---

*This architecture documentation is generated from actual code analysis. Update using the explain system commands as the codebase evolves.*