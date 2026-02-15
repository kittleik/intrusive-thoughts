#!/usr/bin/env python3
"""Generate today's pop-in schedule based on mood. Called by morning ritual."""

import json
import random
from pathlib import Path
from datetime import datetime, timedelta

BASE = Path(__file__).parent
MOOD_FILE = BASE / "today_mood.json"
SCHEDULE_FILE = BASE / "today_schedule.json"

# Mood -> how many pop-ins and time distribution
# DEV MODE: high frequency for data collection (dial down later)
MOOD_PATTERNS = {
    "hyperfocus":    {"count": (6, 10), "cluster": "spread",    "earliest": 9,  "latest": 23, "prefer_long_gaps": False},
    "curious":       {"count": (8, 12), "cluster": "spread",    "earliest": 9,  "latest": 23, "prefer_long_gaps": False},
    "social":        {"count": (8, 12), "cluster": "afternoon", "earliest": 9,  "latest": 23, "prefer_long_gaps": False},
    "cozy":          {"count": (6, 10), "cluster": "evening",   "earliest": 10, "latest": 22, "prefer_long_gaps": False},
    "chaotic":       {"count": (8, 14), "cluster": "random",    "earliest": 8,  "latest": 23, "prefer_long_gaps": False},
    "philosophical": {"count": (6, 10), "cluster": "evening",   "earliest": 10, "latest": 23, "prefer_long_gaps": False},
    "restless":      {"count": (8, 12), "cluster": "spread",    "earliest": 8,  "latest": 23, "prefer_long_gaps": False},
    "determined":    {"count": (6, 10), "cluster": "spread",    "earliest": 9,  "latest": 22, "prefer_long_gaps": False},
}

DEFAULT_PATTERN = {"count": (8, 12), "cluster": "spread", "earliest": 9, "latest": 23, "prefer_long_gaps": False}


def generate_times(pattern):
    """Generate random pop-in times based on mood pattern."""
    count = random.randint(*pattern["count"])
    earliest = pattern["earliest"]
    latest = pattern["latest"]
    cluster = pattern["cluster"]
    
    times = []
    
    if cluster == "morning":
        # Bias toward morning hours
        for _ in range(count):
            hour = random.triangular(earliest, latest, earliest + 2)
            times.append(int(hour))
    elif cluster == "afternoon":
        # Bias toward 13-17
        for _ in range(count):
            hour = random.triangular(earliest, latest, 15)
            times.append(int(hour))
    elif cluster == "evening":
        # Bias toward evening
        for _ in range(count):
            hour = random.triangular(earliest, latest, latest - 2)
            times.append(int(hour))
    elif cluster == "random":
        # Truly random, can cluster anywhere
        for _ in range(count):
            hour = random.randint(earliest, latest)
            times.append(hour)
    else:  # spread
        # Even distribution
        if count > 0:
            span = latest - earliest
            step = span / count
            for i in range(count):
                base = earliest + step * i
                jitter = random.uniform(-step * 0.3, step * 0.3)
                times.append(int(max(earliest, min(latest, base + jitter))))
    
    # Add random minutes
    slots = []
    for hour in sorted(set(times)):  # deduplicate hours
        minute = random.randint(0, 59)
        slots.append({"hour": hour, "minute": minute, "time": f"{hour:02d}:{minute:02d}"})
    
    # Ensure minimum gap between pop-ins (reduced for dev data collection)
    if pattern.get("prefer_long_gaps"):
        min_gap = 60
    else:
        min_gap = 30
    
    filtered = [slots[0]] if slots else []
    for s in slots[1:]:
        prev = filtered[-1]
        gap = (s["hour"] * 60 + s["minute"]) - (prev["hour"] * 60 + prev["minute"])
        if gap >= min_gap:
            filtered.append(s)
    
    return filtered


def main():
    # Load mood
    try:
        mood = json.loads(MOOD_FILE.read_text())
        mood_id = mood.get("drifted_to", mood.get("id", "curious"))
    except:
        mood_id = "curious"
    
    pattern = MOOD_PATTERNS.get(mood_id, DEFAULT_PATTERN)
    slots = generate_times(pattern)
    
    schedule = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "mood_id": mood_id,
        "pattern": pattern["cluster"],
        "slots": slots,
        "cron_expr": ",".join(f"{s['minute']} {s['hour']}" for s in slots),
        "generated_at": datetime.now().isoformat()
    }
    
    SCHEDULE_FILE.write_text(json.dumps(schedule, indent=2))
    
    print(json.dumps(schedule, indent=2))


if __name__ == "__main__":
    main()
