# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.3] - Unreleased

### Added
- Dashboard v2 with improved UI and performance
- Self-awareness capabilities and introspection features
- TypeScript rewrite for better maintainability
- Comprehensive test suite with pytest
- Version management system with `--version` flag
- Context survival system with export/import state functionality
- Decision trace reconstruction and analysis tools
- `intrusive.sh export-state` command for state backup
- `intrusive.sh import-state` command for state restoration

### Changed
- Dashboard footer now dynamically reads version from VERSION file
- Improved decision logging with detailed trace information
- Enhanced error handling and graceful fallbacks

### Fixed
- Various stability improvements and bug fixes

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