#!/usr/bin/env python3
"""
Priority Override System — critical events bypass mood.

When critical events are detected (security alerts, system failures, urgent human
messages), the mood temporarily shifts to 'determined' regardless of current state.

Overrides are tracked in mood_history.json and auto-expire after a configurable duration.
"""

import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple


def load_priority_config(script_dir: Path) -> Dict[str, Any]:
    """Load priority configuration with keyword patterns and override rules."""
    try:
        with open(script_dir / "priorities.json", "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"critical": [], "high": [], "patterns": {}, "override": {}}


def load_active_override(script_dir: Path) -> Optional[Dict[str, Any]]:
    """Load the currently active override, if any."""
    override_file = script_dir / "active_override.json"
    try:
        with open(override_file, "r") as f:
            data = json.load(f)
            if not data:
                return None
            # Check if expired
            expires = data.get("expires")
            if expires:
                exp_dt = datetime.fromisoformat(expires)
                if datetime.now(timezone.utc) > exp_dt:
                    # Expired — clear it
                    clear_override(script_dir, reason="expired")
                    return None
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def save_active_override(script_dir: Path, override: Dict[str, Any]) -> None:
    """Save an active override."""
    with open(script_dir / "active_override.json", "w") as f:
        json.dump(override, f, indent=2)


def clear_override(script_dir: Path, reason: str = "manual") -> Optional[Dict]:
    """Clear the active override and log it."""
    override_file = script_dir / "active_override.json"
    try:
        with open(override_file, "r") as f:
            old = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        old = None

    # Write empty
    with open(override_file, "w") as f:
        json.dump(None, f)

    if old:
        log_override_end(script_dir, old, reason)

    return old


def detect_priority(text: str, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Detect if text contains a priority trigger.

    Returns:
        Dict with 'level' (critical/high), 'trigger', 'pattern' if matched, else None.
    """
    patterns = config.get("patterns", {})

    # Check critical patterns first
    for pattern_name, pattern_def in patterns.items():
        level = pattern_def.get("level", "high")
        keywords = pattern_def.get("keywords", [])
        regex = pattern_def.get("regex")

        # Keyword match
        text_lower = text.lower()
        for kw in keywords:
            if kw.lower() in text_lower:
                return {
                    "level": level,
                    "trigger": kw,
                    "pattern": pattern_name,
                    "override_mood": pattern_def.get("override_mood", "determined"),
                    "duration_minutes": pattern_def.get("duration_minutes", 60),
                }

        # Regex match
        if regex:
            if re.search(regex, text, re.IGNORECASE):
                return {
                    "level": level,
                    "trigger": f"regex:{regex}",
                    "pattern": pattern_name,
                    "override_mood": pattern_def.get("override_mood", "determined"),
                    "duration_minutes": pattern_def.get("duration_minutes", 60),
                }

    return None


def activate_override(
    script_dir: Path,
    trigger_info: Dict[str, Any],
    source: str = "auto",
) -> Dict[str, Any]:
    """
    Activate a priority override, shifting mood to the override target.

    Args:
        script_dir: Project root
        trigger_info: Output from detect_priority()
        source: What triggered this (e.g. 'heartbeat', 'human-message', 'system-alert')

    Returns:
        The active override record.
    """
    now = datetime.now(timezone.utc)
    duration = trigger_info.get("duration_minutes", 60)
    expires = now + timedelta(minutes=duration)

    # Load current mood to preserve for restoration
    try:
        with open(script_dir / "today_mood.json", "r") as f:
            current_mood = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        current_mood = {}

    override = {
        "active": True,
        "level": trigger_info["level"],
        "trigger": trigger_info["trigger"],
        "pattern": trigger_info["pattern"],
        "override_mood": trigger_info["override_mood"],
        "previous_mood_id": current_mood.get("id", "unknown"),
        "previous_mood_name": current_mood.get("name", "Unknown"),
        "source": source,
        "activated_at": now.isoformat(),
        "expires": expires.isoformat(),
        "duration_minutes": duration,
    }

    save_active_override(script_dir, override)

    # Apply mood override to today_mood.json
    apply_mood_override(script_dir, trigger_info["override_mood"], override)

    # Log in mood history
    log_override_start(script_dir, override)

    return override


def apply_mood_override(
    script_dir: Path, mood_id: str, override: Dict[str, Any]
) -> None:
    """Apply the override mood to today_mood.json, preserving activity_log."""
    try:
        with open(script_dir / "today_mood.json", "r") as f:
            mood_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        mood_data = {}

    # Load mood definitions to get the target mood's traits
    try:
        with open(script_dir / "moods.json", "r") as f:
            moods = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        moods = {}

    target_mood = moods.get(mood_id, {})

    # Override mood but keep activity log and other metadata
    mood_data["id"] = mood_id
    mood_data["name"] = target_mood.get("name", mood_id.title())
    mood_data["emoji"] = target_mood.get("emoji", "⚡")
    mood_data["description"] = (
        f"Priority override ({override['level']}): {override['trigger']}. "
        f"Previous mood: {override['previous_mood_name']}. "
        f"Auto-reverts in {override['duration_minutes']}min."
    )
    mood_data["priority_override"] = True
    mood_data["override_expires"] = override["expires"]

    # Override boosted/dampened traits for urgent work
    mood_data["boosted_traits"] = target_mood.get("boosted_traits", [
        "determined", "ship features", "close issues", "hyperfocus",
        "long focus sessions", "build complex things"
    ])
    mood_data["dampened_traits"] = target_mood.get("dampened_traits", [
        "shitposts on Moltbook", "philosophical", "cozy",
        "weird projects", "rapid task switching"
    ])

    with open(script_dir / "today_mood.json", "w") as f:
        json.dump(mood_data, f, indent=2)


def log_override_start(script_dir: Path, override: Dict[str, Any]) -> None:
    """Log override activation in mood_history.json."""
    try:
        with open(script_dir / "mood_history.json", "r") as f:
            history = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        history = {"history": []}

    history.setdefault("overrides", []).append({
        "type": "activated",
        "level": override["level"],
        "trigger": override["trigger"],
        "pattern": override["pattern"],
        "override_mood": override["override_mood"],
        "previous_mood": override["previous_mood_id"],
        "source": override["source"],
        "timestamp": override["activated_at"],
        "expires": override["expires"],
    })

    with open(script_dir / "mood_history.json", "w") as f:
        json.dump(history, f, indent=2)


def log_override_end(script_dir: Path, override: Dict[str, Any], reason: str) -> None:
    """Log override deactivation in mood_history.json."""
    try:
        with open(script_dir / "mood_history.json", "r") as f:
            history = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        history = {"history": []}

    history.setdefault("overrides", []).append({
        "type": "deactivated",
        "level": override.get("level"),
        "trigger": override.get("trigger"),
        "override_mood": override.get("override_mood"),
        "previous_mood": override.get("previous_mood_id"),
        "reason": reason,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    with open(script_dir / "mood_history.json", "w") as f:
        json.dump(history, f, indent=2)


def restore_previous_mood(script_dir: Path) -> Optional[str]:
    """
    Clear override and restore the previous mood.
    Returns the restored mood ID or None.
    """
    override = load_active_override(script_dir)
    if not override:
        return None

    previous_mood_id = override.get("previous_mood_id")
    cleared = clear_override(script_dir, reason="resolved")

    if previous_mood_id and previous_mood_id != "unknown":
        # Restore mood
        try:
            with open(script_dir / "today_mood.json", "r") as f:
                mood_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            mood_data = {}

        # Load the original mood definition
        try:
            with open(script_dir / "moods.json", "r") as f:
                moods = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            moods = {}

        original = moods.get(previous_mood_id, {})
        mood_data["id"] = previous_mood_id
        mood_data["name"] = original.get("name", previous_mood_id.title())
        mood_data["emoji"] = original.get("emoji", "🎭")
        mood_data["description"] = f"Restored after priority override resolved."
        mood_data.pop("priority_override", None)
        mood_data.pop("override_expires", None)

        with open(script_dir / "today_mood.json", "w") as f:
            json.dump(mood_data, f, indent=2)

    return previous_mood_id


def check_and_apply(
    script_dir: Path, text: str, source: str = "auto"
) -> Optional[Dict[str, Any]]:
    """
    Main entry point: check text for priority triggers and activate override if found.
    
    Returns the override record if activated, None otherwise.
    """
    # Don't override if already in override
    existing = load_active_override(script_dir)
    if existing:
        # Already overridden — escalate if new trigger is higher priority
        config = load_priority_config(script_dir)
        trigger = detect_priority(text, config)
        if trigger and trigger["level"] == "critical" and existing["level"] != "critical":
            # Escalate
            return activate_override(script_dir, trigger, source)
        return None

    config = load_priority_config(script_dir)
    trigger = detect_priority(text, config)
    if trigger:
        return activate_override(script_dir, trigger, source)

    return None


# CLI interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Priority override system")
    subparsers = parser.add_subparsers(dest="command")

    # Check command
    check_parser = subparsers.add_parser("check", help="Check text for priority triggers")
    check_parser.add_argument("text", help="Text to check")
    check_parser.add_argument("--source", default="cli", help="Source identifier")
    check_parser.add_argument("--dir", default=".", help="Project directory")

    # Status command
    status_parser = subparsers.add_parser("status", help="Show active override status")
    status_parser.add_argument("--dir", default=".", help="Project directory")

    # Clear command
    clear_parser = subparsers.add_parser("clear", help="Clear active override")
    clear_parser.add_argument("--reason", default="manual", help="Reason for clearing")
    clear_parser.add_argument("--dir", default=".", help="Project directory")

    # Restore command
    restore_parser = subparsers.add_parser("restore", help="Restore previous mood")
    restore_parser.add_argument("--dir", default=".", help="Project directory")

    args = parser.parse_args()
    script_dir = Path(args.dir).resolve()

    if args.command == "check":
        result = check_and_apply(script_dir, args.text, args.source)
        if result:
            print(json.dumps(result, indent=2))
            sys.exit(0)
        else:
            print("No priority trigger detected")
            sys.exit(1)

    elif args.command == "status":
        override = load_active_override(script_dir)
        if override:
            print(json.dumps(override, indent=2))
        else:
            print("No active override")

    elif args.command == "clear":
        cleared = clear_override(script_dir, args.reason)
        if cleared:
            print(f"Cleared override: {cleared.get('trigger')}")
        else:
            print("No active override to clear")

    elif args.command == "restore":
        restored = restore_previous_mood(script_dir)
        if restored:
            print(f"Restored mood: {restored}")
        else:
            print("No override to restore from")

    else:
        parser.print_help()
