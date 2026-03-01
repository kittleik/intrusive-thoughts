#!/usr/bin/env python3
"""Tests for priority override system."""

import json
import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from priority_override import (
    detect_priority,
    load_priority_config,
    activate_override,
    load_active_override,
    clear_override,
    restore_previous_mood,
    check_and_apply,
)


def setup_test_dir():
    """Create a temp directory with required files."""
    tmp = Path(tempfile.mkdtemp())
    
    # priorities.json
    priorities = {
        "critical": ["human-request"],
        "high": ["bug-report"],
        "patterns": {
            "system-down": {
                "level": "critical",
                "keywords": ["server down", "critical error"],
                "override_mood": "determined",
                "duration_minutes": 120,
            },
            "security-alert": {
                "level": "critical",
                "keywords": ["security breach"],
                "regex": "CVE-\\d{4}-\\d+",
                "override_mood": "determined",
                "duration_minutes": 180,
            },
            "build-failure": {
                "level": "high",
                "keywords": ["build failed"],
                "override_mood": "determined",
                "duration_minutes": 60,
            },
        },
        "override": {"default_mood": "determined", "default_duration_minutes": 60},
    }
    with open(tmp / "priorities.json", "w") as f:
        json.dump(priorities, f)

    # today_mood.json
    mood = {
        "id": "cozy",
        "name": "Cozy",
        "emoji": "🛋️",
        "description": "Chill vibes",
        "activity_log": [],
    }
    with open(tmp / "today_mood.json", "w") as f:
        json.dump(mood, f)

    # moods.json
    moods = {
        "version": 2,
        "base_moods": [
            {
                "id": "determined",
                "name": "Determined",
                "emoji": "⚡",
                "boosted_traits": ["ship features", "close issues"],
                "dampened_traits": ["shitposts on Moltbook"],
            },
            {
                "id": "cozy",
                "name": "Cozy",
                "emoji": "🛋️",
                "boosted_traits": ["cozy"],
                "dampened_traits": [],
            },
        ],
    }
    with open(tmp / "moods.json", "w") as f:
        json.dump(moods, f)

    # mood_history.json
    with open(tmp / "mood_history.json", "w") as f:
        json.dump({"history": []}, f)

    return tmp


def teardown_test_dir(tmp):
    shutil.rmtree(tmp)


def test_detect_priority_keyword():
    config = {
        "patterns": {
            "system-down": {
                "level": "critical",
                "keywords": ["server down", "critical error"],
                "override_mood": "determined",
                "duration_minutes": 120,
            }
        }
    }
    result = detect_priority("The server down again!", config)
    assert result is not None
    assert result["level"] == "critical"
    assert result["trigger"] == "server down"
    assert result["pattern"] == "system-down"


def test_detect_priority_regex():
    config = {
        "patterns": {
            "security": {
                "level": "critical",
                "keywords": [],
                "regex": "CVE-\\d{4}-\\d+",
                "override_mood": "determined",
                "duration_minutes": 180,
            }
        }
    }
    result = detect_priority("Found CVE-2026-1234 in dependency", config)
    assert result is not None
    assert result["level"] == "critical"


def test_detect_priority_no_match():
    config = {
        "patterns": {
            "system-down": {
                "level": "critical",
                "keywords": ["server down"],
                "override_mood": "determined",
                "duration_minutes": 120,
            }
        }
    }
    result = detect_priority("Everything is fine", config)
    assert result is None


def test_activate_and_load_override():
    tmp = setup_test_dir()
    try:
        trigger = {
            "level": "critical",
            "trigger": "server down",
            "pattern": "system-down",
            "override_mood": "determined",
            "duration_minutes": 120,
        }
        override = activate_override(tmp, trigger, source="test")
        assert override["active"] is True
        assert override["level"] == "critical"
        assert override["previous_mood_id"] == "cozy"

        # Verify today_mood was changed
        with open(tmp / "today_mood.json") as f:
            mood = json.load(f)
        assert mood["id"] == "determined"
        assert mood["priority_override"] is True

        # Verify can load
        loaded = load_active_override(tmp)
        assert loaded is not None
        assert loaded["trigger"] == "server down"
    finally:
        teardown_test_dir(tmp)


def test_clear_and_restore():
    tmp = setup_test_dir()
    try:
        trigger = {
            "level": "critical",
            "trigger": "server down",
            "pattern": "system-down",
            "override_mood": "determined",
            "duration_minutes": 120,
        }
        activate_override(tmp, trigger, source="test")

        # Restore
        restored = restore_previous_mood(tmp)
        assert restored == "cozy"

        # Verify mood restored
        with open(tmp / "today_mood.json") as f:
            mood = json.load(f)
        assert mood["id"] == "cozy"
        assert "priority_override" not in mood
    finally:
        teardown_test_dir(tmp)


def test_no_double_override():
    tmp = setup_test_dir()
    try:
        trigger = {
            "level": "high",
            "trigger": "build failed",
            "pattern": "build-failure",
            "override_mood": "determined",
            "duration_minutes": 60,
        }
        activate_override(tmp, trigger, source="test")

        # Same level shouldn't override again
        result = check_and_apply(tmp, "build failed again", source="test")
        assert result is None

        # But critical SHOULD escalate
        result = check_and_apply(tmp, "server down!", source="test")
        assert result is not None
        assert result["level"] == "critical"
    finally:
        teardown_test_dir(tmp)


def test_override_logged_in_history():
    tmp = setup_test_dir()
    try:
        trigger = {
            "level": "critical",
            "trigger": "server down",
            "pattern": "system-down",
            "override_mood": "determined",
            "duration_minutes": 120,
        }
        activate_override(tmp, trigger, source="test")

        with open(tmp / "mood_history.json") as f:
            history = json.load(f)
        
        overrides = history.get("overrides", [])
        assert len(overrides) == 1
        assert overrides[0]["type"] == "activated"
        assert overrides[0]["previous_mood"] == "cozy"
    finally:
        teardown_test_dir(tmp)


if __name__ == "__main__":
    tests = [
        test_detect_priority_keyword,
        test_detect_priority_regex,
        test_detect_priority_no_match,
        test_activate_and_load_override,
        test_clear_and_restore,
        test_no_double_override,
        test_override_logged_in_history,
    ]
    
    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            print(f"  ✅ {test.__name__}")
            passed += 1
        except Exception as e:
            print(f"  ❌ {test.__name__}: {e}")
            failed += 1
    
    print(f"\n{passed}/{passed + failed} tests passed")
    sys.exit(1 if failed else 0)
