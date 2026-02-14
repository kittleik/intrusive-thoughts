#!/bin/bash
# 🧠 Intrusive Thoughts — Random prompt picker (mood-aware)
# Usage: intrusive.sh <mood>    (night|day)
#        intrusive.sh wizard     (run setup wizard)
# Reads today_mood.json to bias thought selection toward current mood

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Handle subcommands
case "${1:-}" in
    create-preset)
        exec "$SCRIPT_DIR/create_preset.sh"
        ;;
    suggest-thought)
        if [[ -z "$2" ]]; then
            echo "Usage: intrusive.sh suggest-thought \"description of the thought\""
            echo "Example: intrusive.sh suggest-thought \"Browse hackernews and share interesting tech articles\""
            exit 1
        fi
        shift
        exec "$SCRIPT_DIR/suggest_thought.sh" "$*"
        ;;
    wizard)
        exec "$SCRIPT_DIR/wizard.sh"
        ;;
    genuineness)
        shift
        exec python3 "$SCRIPT_DIR/genuineness.py" "${@:-report}"
        ;;
    audit|--audit)
        echo "🔍 Security Audit - Intrusive Thoughts"
        echo ""
        echo "📡 Network endpoints (all read-only GET requests):"
        echo "   Found in set_mood.sh:"
        grep -n "# NETWORK:" "$SCRIPT_DIR/set_mood.sh" | sed 's/^/   /'
        echo ""
        echo "🌐 Actual network calls:"
        grep -n "curl" "$SCRIPT_DIR/set_mood.sh" | sed 's/^/   /'
        echo ""
        echo "📁 File paths accessed (within skill directory only):"
        echo "   Config files:"
        find "$SCRIPT_DIR" -name "*.json" -not -path "*/.*" | sed 's/^/   /'
        echo ""
        echo "   Log directories:" 
        find "$SCRIPT_DIR" -type d -name "log" -o -name "memory_store" -o -name "trust_store" -o -name "health" | sed 's/^/   /'
        echo ""
        echo "🔧 Subprocess calls:"
        grep -n "subprocess.run\|os.system\|shell=True" "$SCRIPT_DIR"/*.py 2>/dev/null | head -10 | sed 's/^/   /' || echo "   None found"
        echo ""
        echo "✅ See SECURITY.md for complete audit report"
        exit 0
        ;;
    help|--help|-h)
        echo "🧠 Intrusive Thoughts"
        echo ""
        echo "Usage:"
        echo "  intrusive.sh [mood]              Pick a random thought (day|night)"
        echo "  intrusive.sh create-preset       Create a new personality preset interactively"
        echo "  intrusive.sh suggest-thought \"desc\" Generate a thought JSON from description"
        echo "  intrusive.sh wizard              Run the interactive setup wizard" 
        echo "  intrusive.sh audit               Show security audit information"
        echo "  intrusive.sh genuineness         Show genuineness report"
        echo "  intrusive.sh genuineness --json  Genuineness report as JSON"
        echo "  intrusive.sh help                Show this help"
        echo ""
        exit 0
        ;;
esac

source "$SCRIPT_DIR/load_config.sh"

THOUGHTS_FILE="$DATA_DIR/thoughts.json"
MOOD_FILE="$DATA_DIR/today_mood.json"
LOG_DIR="$DATA_DIR/log"
mkdir -p "$LOG_DIR"

MOOD="${1:-day}"

# Pick a weighted random thought, influenced by today's mood and streak weights
PROMPT=$(python3 -c "
import json, random, sys, time
from datetime import datetime

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

# Load streak weights (anti-rut system)
streak_weights = {}
try:
    with open('$DATA_DIR/streaks.json') as f:
        streaks = json.load(f)
        streak_weights = streaks.get('anti_rut_weights', {})
except:
    pass

# Load human mood for supportive adjustments
human_mood = None
try:
    with open('$DATA_DIR/human_mood.json') as f:
        human_data = json.load(f)
        human_mood = human_data.get('current')
except:
    pass

# Track all candidates and skipped thoughts with detailed reasoning
all_candidates = []
skipped_thoughts = []
rejections_to_log = []

# Build weighted pool and track all candidates
pool = []
for t in mood_data['thoughts']:
    weight = float(t.get('weight', 1))
    thought_id = t['id']
    original_weight = weight
    skip_reasons = []
    boost_reasons = []
    
    # Apply mood bias if we have a mood set
    if today_mood:
        boosted = today_mood.get('boosted_traits', [])
        dampened = today_mood.get('dampened_traits', [])
        
        # Check if this thought aligns with boosted/dampened traits
        if thought_id in boosted:
            weight *= 1.8
            boost_reasons.append(f\"Boosted by current mood ({today_mood.get('name', 'Unknown')}): {today_mood.get('description', '')}\")
        elif thought_id in dampened:
            weight = max(0.2, weight * 0.5)
            skip_reasons.append(f\"Current mood ({today_mood.get('name', 'Unknown')}) dampens {thought_id} thoughts - feeling more like {today_mood.get('description', 'something else')}\")
    
    # Apply anti-rut weights (streak-based adjustments)
    if thought_id in streak_weights:
        streak_mult = streak_weights[thought_id]
        weight *= streak_mult
        if streak_mult < 0.8:
            skip_reasons.append(f'Anti-rut system dampening {thought_id} - you\\'ve been doing this too much lately')
        elif streak_mult > 1.2:
            boost_reasons.append(f'Anti-rut system boosting {thought_id} - haven\\'t done this in a while')
    
    # Apply human mood influence
    if human_mood and human_mood.get('confidence', 0) > 0.4:
        h_mood = human_mood.get('mood', 'neutral')
        h_energy = human_mood.get('energy', 'neutral')
        h_vibe = human_mood.get('vibe', 'neutral')
        
        # Supportive adjustments based on your human's detected mood
        if h_mood == 'stressed' and thought_id in ['random-thought', 'ask-opinion', 'ask-preference']:
            weight *= 0.5  # Don't bother him when stressed
            skip_reasons.append(f'Your human seems stressed - avoiding {thought_id} to give them space')
        elif h_mood == 'excited' and thought_id in ['share-discovery', 'pitch-idea', 'moltbook-post']:
            weight *= 1.5  # Match his energy
            boost_reasons.append(f'Boosted to match human\\'s excited energy')
        elif h_mood == 'frustrated' and thought_id in ['ask-feedback', 'random-thought']:
            weight *= 0.3  # Give him space
            skip_reasons.append(f'Your human seems frustrated - staying away from {thought_id} for now')
        elif h_mood == 'curious' and thought_id in ['share-discovery', 'ask-opinion', 'learn']:
            weight *= 1.4  # Feed his curiosity
            boost_reasons.append(f'Boosted to feed human\\'s curiosity')
        elif h_mood == 'focused' and thought_id in ['random-thought', 'ask-opinion']:
            weight *= 0.4  # Don't interrupt flow
            skip_reasons.append(f'Your human is in the zone - not interrupting with {thought_id}')
        elif h_mood == 'happy' and thought_id in ['moltbook-social', 'share-discovery', 'creative-chaos']:
            weight *= 1.3  # Amplify good vibes
            boost_reasons.append(f'Boosted to amplify good vibes')
    
    # Track candidate with full details
    candidate = {
        'id': thought_id,
        'original_weight': original_weight,
        'final_weight': weight,
        'boost_reasons': boost_reasons,
        'skip_reasons': skip_reasons,
        'prompt': t['prompt']
    }
    all_candidates.append(candidate)
    
    # Track heavily dampened thoughts as rejections for logging
    if weight < original_weight * 0.6 and skip_reasons:
        timestamp = datetime.now().isoformat()
        mood_id = today_mood.get('id', 'none') if today_mood else 'none'
        reason = ', '.join(skip_reasons)
        flavor_text = f'Weight dropped from {original_weight:.1f} to {weight:.1f}'
        
        rejections_to_log.append({
            'timestamp': timestamp,
            'thought_id': thought_id,
            'mood': mood_id,
            'reason': reason,
            'flavor_text': flavor_text
        })
        
        skipped_thoughts.append({
            'id': thought_id,
            'original_weight': original_weight,
            'final_weight': weight,
            'reasons': skip_reasons
        })
    
    # Convert back to int for pool generation
    final_weight = max(1, int(weight * 10))  # Scale up for precision
    pool.extend([t] * final_weight)

# Make the random choice
random_seed = random.random()
pick = random.choice(pool)
jitter = random.randint(0, mood_data.get('jitter_seconds', mood_data.get('jitter_seconds', 1200)))

# Include today's mood context in output
mood_context = ''
if today_mood:
    mood_context = f\"{today_mood.get('emoji','')} {today_mood.get('name','')}: {today_mood.get('description','')}\"

# Create decision trace for logging
decision_trace = {
    'timestamp': datetime.now().isoformat(),
    'mood': '$MOOD',
    'mood_id': today_mood.get('id', 'none') if today_mood else 'none',
    'all_candidates': all_candidates,
    'winner': {
        'id': pick['id'],
        'prompt': pick['prompt'],
        'final_weight': next(c['final_weight'] for c in all_candidates if c['id'] == pick['id']),
        'boost_reasons': next(c['boost_reasons'] for c in all_candidates if c['id'] == pick['id'])
    },
    'skipped_thoughts': skipped_thoughts,
    'random_roll': random_seed,
    'total_candidates': len(all_candidates),
    'pool_size': len(pool)
}

# Export rejections for logging (will be handled by shell script)
print('__REJECTIONS__:' + json.dumps(rejections_to_log))
print('__DECISION_TRACE__:' + json.dumps(decision_trace))

print(json.dumps({
    'id': pick['id'],
    'prompt': pick['prompt'],
    'jitter_seconds': jitter,
    'timeout_seconds': mood_data.get('timeout_seconds', 300),
    'mood': '$MOOD',
    'today_mood': mood_context or 'no mood set',
    'mood_id': today_mood.get('id', 'none') if today_mood else 'none',
    'skipped': skipped_thoughts
}))
")

# Process the output - extract rejections, decision trace, and main prompt
REJECTIONS_LINE=$(echo "$PROMPT" | grep "^__REJECTIONS__:" | head -1)
DECISION_TRACE_LINE=$(echo "$PROMPT" | grep "^__DECISION_TRACE__:" | head -1)
MAIN_PROMPT=$(echo "$PROMPT" | grep -v "^__" | head -1)

echo "$MAIN_PROMPT"

# Log rejections to rejections.log
if [[ -n "$REJECTIONS_LINE" ]]; then
    REJECTIONS_JSON="${REJECTIONS_LINE#__REJECTIONS__:}"
    if [[ "$REJECTIONS_JSON" != "[]" ]]; then
        echo "$REJECTIONS_JSON" | python3 -c "
import json, sys
rejections = json.load(sys.stdin)
for rej in rejections:
    print(f\"{rej['timestamp']} | {rej['thought_id']} | {rej['mood']} | {rej['reason']} | {rej['flavor_text']}\")
" >> "$LOG_DIR/rejections.log"
    fi
fi

# Log decision trace to decisions.json (append to array)
if [[ -n "$DECISION_TRACE_LINE" ]]; then
    DECISION_JSON="${DECISION_TRACE_LINE#__DECISION_TRACE__:}"
    
    # Create decisions.json if it doesn't exist
    if [[ ! -f "$LOG_DIR/decisions.json" ]]; then
        echo "[]" > "$LOG_DIR/decisions.json"
    fi
    
    # Append to the JSON array
    python3 -c "
import json, sys
import os

decision = json.loads('$DECISION_JSON')
decisions_file = '$LOG_DIR/decisions.json'

try:
    with open(decisions_file, 'r') as f:
        decisions = json.load(f)
except:
    decisions = []

decisions.append(decision)

# Keep only last 1000 entries to prevent file from growing too large
decisions = decisions[-1000:]

with open(decisions_file, 'w') as f:
    json.dump(decisions, f, indent=2)
"
fi

# Log the pick (existing functionality)
TIMESTAMP=$(date -Iseconds)
THOUGHT_ID=$(echo "$MAIN_PROMPT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['id'])" 2>/dev/null)
MOOD_ID=$(echo "$MAIN_PROMPT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('mood_id','none'))" 2>/dev/null)
echo "$TIMESTAMP | mood=$MOOD | thought=$THOUGHT_ID | today_mood=$MOOD_ID" >> "$LOG_DIR/picks.log"
