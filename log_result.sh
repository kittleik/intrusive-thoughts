#!/bin/bash
# Log what Ember actually did with an intrusive thought
# Usage: log_result.sh <thought_id> <mood> "<summary>"
# Example: log_result.sh build-tool night "Built a disk usage dashboard in Python"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HISTORY_FILE="$SCRIPT_DIR/history.json"

THOUGHT_ID="${1:-unknown}"
MOOD="${2:-unknown}"
SUMMARY="${3:-No summary provided}"
TIMESTAMP=$(date -Iseconds)

python3 -c "
import json, sys

with open('$HISTORY_FILE') as f:
    history = json.load(f)

history.append({
    'timestamp': '$TIMESTAMP',
    'mood': '$MOOD',
    'thought_id': '$THOUGHT_ID',
    'summary': '''$SUMMARY'''
})

# Keep last 500 entries
history = history[-500:]

with open('$HISTORY_FILE', 'w') as f:
    json.dump(history, f, indent=2)

print(f'Logged: {\"$THOUGHT_ID\"} ({\"$MOOD\"}) - {\"$SUMMARY\"[:60]}...')
"
