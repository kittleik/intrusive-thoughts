#!/bin/bash
# 🧠 Intrusive Thoughts — Random prompt picker
# Usage: intrusive.sh <mood>  (night|day)
# Returns a random prompt from the thought pool, weighted by preference.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
THOUGHTS_FILE="$SCRIPT_DIR/thoughts.json"
LOG_DIR="$SCRIPT_DIR/log"
mkdir -p "$LOG_DIR"

MOOD="${1:-day}"

# Pick a weighted random thought and output the prompt
PROMPT=$(python3 -c "
import json, random, sys

with open('$THOUGHTS_FILE') as f:
    data = json.load(f)

mood = data['moods'].get('$MOOD')
if not mood:
    print('Unknown mood: $MOOD', file=sys.stderr)
    sys.exit(1)

# Build weighted pool
pool = []
for t in mood['thoughts']:
    pool.extend([t] * t.get('weight', 1))

pick = random.choice(pool)
jitter = random.randint(0, mood.get('jitter_seconds', 0))

# Output as JSON for the cron job to parse
print(json.dumps({
    'id': pick['id'],
    'prompt': pick['prompt'],
    'jitter_seconds': jitter,
    'timeout_seconds': mood.get('timeout_seconds', 300),
    'mood': '$MOOD'
}))
")

echo "$PROMPT"

# Log the pick
TIMESTAMP=$(date -Iseconds)
THOUGHT_ID=$(echo "$PROMPT" | python3 -c "import json,sys; print(json.load(sys.stdin)['id'])" 2>/dev/null)
echo "$TIMESTAMP | mood=$MOOD | thought=$THOUGHT_ID" >> "$LOG_DIR/picks.log"
