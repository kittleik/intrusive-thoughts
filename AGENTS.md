# AGENTS.md — Intrusive Thoughts Development Guidelines

## Git Workflow

### Feature Branches (MANDATORY)
**Never push directly to `main`** when doing parallel work.

1. **Create a feature branch** per issue: `git checkout -b feat/<issue-number>-<short-name>`
   - Example: `feat/30-thought-stream`, `feat/32-tuning-controls`
2. **Do all work on the branch**, commit with conventional messages
3. **Push the branch**: `git push -u origin feat/<issue-number>-<short-name>`
4. **Merge to main** after work is done and verified:
   ```bash
   git checkout main
   git pull origin main
   git merge feat/<issue-number>-<short-name>
   git push origin main
   ```
5. **Delete the branch** after merge: `git branch -d feat/<issue-number>-<short-name>`

### Parallel Sub-Agents
When spawning multiple sub-agents that edit code:
- **Each agent gets its own branch** — include branch name in the task description
- **Never have two agents edit the same file on main** — this causes overwrites
- After all agents finish, **merge branches sequentially** to main, resolving conflicts
- Alternative: if agents edit **different files**, they can share a branch or use main

### Commit Messages
Follow conventional commits:
- `feat: <description> (fixes #N)` — new feature, auto-closes issue
- `fix: <description>` — bug fix
- `chore: <description>` — maintenance, version bumps
- `docs: <description>` — documentation only
- `refactor: <description>` — code restructuring

### Versioning
- ClawHub semver: `MAJOR.MINOR.PATCH` (currently 0.1.x)
- VERSION file at repo root is source of truth
- Don't use version labels on GitHub issues — milestones handle version grouping
- Update CHANGELOG.md with each release

## Project Structure

```
intrusive-thoughts/
├── intrusive.sh          # Main CLI entry point
├── config.json           # User config (gitignored)
├── config.example.json   # Template config
├── config.py             # Config loader
├── moods.json            # Mood definitions + flavor text
├── thoughts.json         # Thought catalog + weights
├── dashboard.py          # Web dashboard (port 3117)
├── set_mood.sh           # Morning mood ritual
├── schedule_day.py       # Daily schedule generator
├── log_result.sh         # Activity result logger
├── memory_system.py      # Three-store memory with decay
├── trust_system.py       # Trust score tracking
├── self_evolution.py     # Weight adjustment system
├── proactive.py          # WAL-based proactive agent
├── health_monitor.py     # System health checks
├── explain_system.py     # Self-awareness explanations
├── introspect.py         # Full state introspection
├── decision_trace.py     # Decision path analysis
├── wizard.sh             # Interactive setup wizard
├── presets/              # Personality preset JSONs
├── docs/                 # Architecture docs
├── health/               # Health state (gitignored)
├── memory_store/         # Memory data (gitignored)
├── log/                  # Decision/rejection logs (gitignored)
└── wal/                  # Write-ahead log (gitignored)
```

## Testing
- `python3 -c "import ast; ast.parse(open('file.py').read())"` — syntax check Python files
- `bash -n script.sh` — syntax check bash scripts
- `python3 dashboard.py &` then `curl localhost:3117` — verify dashboard runs
- `./intrusive.sh day` — test thought selection
- `./intrusive.sh introspect` — test state dump

## Key Rules
- **Config stays portable**: no hardcoded paths or personal data in committed files
- **config.json is gitignored**: use config.example.json as template
- **Data files are gitignored**: health/, memory_store/, wal/, log/, today_mood.json, etc.
- **Credit contributors**: use CREDITS.md, mention inspirations in issue bodies
- **CLI-first**: all features accessible via `intrusive.sh` subcommands
