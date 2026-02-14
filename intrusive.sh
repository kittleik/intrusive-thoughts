#!/bin/bash
# 🧠 Intrusive Thoughts — Random prompt picker (mood-aware)
# Usage: intrusive.sh <mood>  (night|day)
# Reads today_mood.json to bias thought selection toward current mood

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
THOUGHTS_FILE="$SCRIPT_DIR/thoughts.json"
MOOD_FILE="$SCRIPT_DIR/today_mood.json"
LOG_DIR="$SCRIPT_DIR/log"
mkdir -p "$LOG_DIR"

MOOD="${1:-day}"

# Pick a weighted random thought, influenced by today's mood
PROMPT=$(python3 -c "
import json, random, sys

with open('$THOUGHTS_FILE') as f:
    data = json.load(f)

mood_data = data['moods'].get('$MOOD')
if not mood_data:
    print('Unknown mood: $MOOD', file=sys.stderr)
    sys.exit(1)

# Load today's mood for bias
today_mood = None
try:
    with open('$MOOD_FILE') as f:
        today_mood = json.load(f)
except:
    pass

# Build weighted pool
pool = []
for t in mood_data['thoughts']:
    weight = t.get('weight', 1)
    
    # Apply mood bias if we have a mood set
    if today_mood:
        boosted = today_mood.get('boosted_traits', [])
        dampened = today_mood.get('dampened_traits', [])
        thought_id = t['id']
        
        # Check if this thought aligns with boosted/dampened traits
        if thought_id in boosted:
            weight = int(weight * 1.8)
        elif thought_id in dampened:
            weight = max(1, weight // 2)
    
    pool.extend([t] * weight)

pick = random.choice(pool)
jitter = random.randint(0, mood_data.get('jitter_seconds', mood_data.get('jitter_seconds', 1200)))

# Include today's mood context in output
mood_context = ''
if today_mood:
    mood_context = f\"{today_mood.get('emoji','')} {today_mood.get('name','')}: {today_mood.get('description','')}\"

print(json.dumps({
    'id': pick['id'],
    'prompt': pick['prompt'],
    'jitter_seconds': jitter,
    'timeout_seconds': mood_data.get('timeout_seconds', 300),
    'mood': '$MOOD',
    'today_mood': mood_context or 'no mood set',
    'mood_id': today_mood.get('id', 'none') if today_mood else 'none'
}))
")

echo "$PROMPT"

# Log the pick
TIMESTAMP=$(date -Iseconds)
THOUGHT_ID=$(echo "$PROMPT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['id'])" 2>/dev/null)
MOOD_ID=$(echo "$PROMPT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('mood_id','none'))" 2>/dev/null)
echo "$TIMESTAMP | mood=$MOOD | thought=$THOUGHT_ID | today_mood=$MOOD_ID" >> "$LOG_DIR/picks.log"
