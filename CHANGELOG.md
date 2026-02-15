# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.3] - 2026-02-15

### Added
- **Dashboard v2**: Live thought stream, mood visualization, drift graph, tuning controls, health/memory explorer, journal viewer, achievements panel, self-awareness panel with sticky nav
- **TypeScript dashboard rewrite**: Express server with typed services, static HTML frontend (`dashboard/`)
- **Self-awareness**: `intrusive.sh explain/introspect/why` commands, `docs/ARCHITECTURE.md`
- **Context survival**: `intrusive.sh export-state` / `import-state` for compaction survival
- **Version management**: `intrusive.sh --version`, VERSION file as source of truth
- **Decision trace**: Reconstruction and analysis tools with `/api/why` endpoint
- **Community contributions**: `create-preset` and `suggest-thought` commands for non-coders, `.github/ISSUE_TEMPLATE/new-preset.md`
- **Flavor text**: Mood-specific flavor for all 8 moods, Easter egg thoughts (Friday 13th, full moon, birthdays, streak interventions), funnier achievements
- **Test suite**: 100 tests covering mood drift, thought selection, memory decay, trust score, decision trace
- **AGENTS.md**: Git workflow documentation for parallel sub-agent development

### Changed
- Dashboard footer dynamically reads version from VERSION file
- Improved decision logging with detailed trace information
- Enhanced error handling and graceful fallbacks

### Added (Feb 15)
- **Wild mood reasoning**: 4 categories (logical, whimsical, cosmic, nonsensical) with 30% chaos chance
- **Entropy target**: Same mood 3+ times in 7 days → weight reduced 50%
- **Cozy spiral prevention**: Warns on day 2, forces change on day 3+
- **Mood values**: Every mood has a `value_text` explaining why it's useful
- **Day-of-week personality**: Weekdays focused, weekends playful, Friday ship-it energy
- **Moltbook ban checking**: Skips social thoughts when account suspended, auto-unbans
- **Decision trace**: Full candidate/rejection logging with reasons
- **30-second cooldown**: Prevents rapid re-rolling of thought selector
- **MOOD.md workspace integration**: Mood context loaded into every OpenClaw session
- **Activity → OpenClaw memory**: `log_result.sh` writes to `memory/YYYY-MM-DD.md`
- **Moon phase and prime number day** calculations for cosmic mood factors

### Fixed
- Removed accidentally committed `node_modules/` from git tracking

## [0.1.2] - 2024-02-10

### Added
- Interactive setup wizard for easy configuration
- Enhanced security model with audit capabilities
- ClawHub publish integration for community sharing
- Community feedback integration and response handling

### Changed
- Improved configuration management system
- Enhanced user onboarding experience

### Fixed
- Security vulnerabilities addressed
- Configuration template improvements

## [0.1.1] - 2024-02-05

### Added
- ClawHub integration improvements
- Security scanning capabilities
- Configuration template system

### Fixed
- Unicode handling issues in ClawHub integration
- Various ClawHub-related bugs and edge cases
- Configuration file generation problems

## [0.1.0] - 2024-02-01

### Added
- Initial release of Intrusive Thoughts system
- Core mood system with dynamic thought selection
- Night workshop functionality for offline processing  
- Interactive dashboard for monitoring and control
- Thought weighting system based on current mood
- Anti-rut system to prevent repetitive behaviors
- Basic logging and history tracking
- JSON-based configuration system
- Mood-aware prompt selection
- Streak tracking and weight adjustments
- Human mood detection and supportive responses