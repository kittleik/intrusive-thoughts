#!/bin/bash
# Show stats about intrusive thought activity
/home/hk/Projects/intrusive-thoughts="$(cd "$(dirname "$0")" && pwd)"

python3 << 'PYEOF'
import json
from datetime import datetime, timedelta
from collections import Counter

HISTORY_FILE = "/home/hk/Projects/intrusive-thoughts/history.json"
PICKS_LOG = "/home/hk/Projects/intrusive-thoughts/log/picks.log"

print("🧠 INTRUSIVE THOUGHTS — STATS")
print("=" * 50)

# Pick frequency from log
try:
    with open(PICKS_LOG) as f:
        lines = [l.strip() for l in f if l.strip()]
    
    thought_counts = Counter()
    mood_counts = Counter()
    for line in lines:
        parts = dict(p.split("=") for p in line.split(" | ")[1:] if "=" in p)
        thought_counts[parts.get("thought", "?")] += 1
        mood_counts[parts.get("mood", "?")] += 1
    
    print(f"\n📊 Total picks: {len(lines)}")
    print(f"\n🌙 Night sessions: {mood_counts.get('night', 0)}")
    print(f"☀️  Day sessions:   {mood_counts.get('day', 0)}")
    
    print(f"\n🎯 Most picked thoughts:")
    for thought, count in thought_counts.most_common(10):
        bar = "█" * count
        print(f"  {thought:20s} {count:3d} {bar}")
except FileNotFoundError:
    print("\nNo picks log yet.")

# History (what was actually done)
try:
    with open(HISTORY_FILE) as f:
        history = json.load(f)
    
    if history:
        print(f"\n📝 Completed activities: {len(history)}")
        print(f"\n🕐 Recent activity:")
        for entry in history[-5:]:
            ts = entry['timestamp'][:16].replace('T', ' ')
            print(f"  [{ts}] {entry['mood']}/{entry['thought_id']}")
            print(f"    → {entry['summary'][:80]}")
    else:
        print("\nNo completed activities yet.")
except FileNotFoundError:
    print("\nNo history file yet.")

print(f"\n{'=' * 50}")
PYEOF
