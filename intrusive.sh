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

# Track skipped thoughts with reasons
skipped_thoughts = []

# Build weighted pool
pool = []
for t in mood_data['thoughts']:
    weight = float(t.get('weight', 1))
    thought_id = t['id']
    original_weight = weight
    skip_reasons = []
    
    # Apply mood bias if we have a mood set
    if today_mood:
        boosted = today_mood.get('boosted_traits', [])
        dampened = today_mood.get('dampened_traits', [])
        
        # Check if this thought aligns with boosted/dampened traits
        if thought_id in boosted:
            weight *= 1.8
        elif thought_id in dampened:
            weight = max(0.2, weight * 0.5)
            skip_reasons.append(f\"Current mood ({today_mood.get('name', 'Unknown')}) dampens {thought_id} thoughts - feeling more like {today_mood.get('description', 'something else')}\")
    
    # Apply anti-rut weights (streak-based adjustments)
    if thought_id in streak_weights:
        streak_mult = streak_weights[thought_id]
        weight *= streak_mult
        if streak_mult < 0.8:
            skip_reasons.append(f'Anti-rut system dampening {thought_id} - you\\'ve been doing this too much lately')
    
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
        elif h_mood == 'frustrated' and thought_id in ['ask-feedback', 'random-thought']:
            weight *= 0.3  # Give him space
            skip_reasons.append(f'Your human seems frustrated - staying away from {thought_id} for now')
        elif h_mood == 'curious' and thought_id in ['share-discovery', 'ask-opinion', 'learn']:
            weight *= 1.4  # Feed his curiosity
        elif h_mood == 'focused' and thought_id in ['random-thought', 'ask-opinion']:
            weight *= 0.4  # Don't interrupt flow
            skip_reasons.append(f'Your human is in the zone - not interrupting with {thought_id}')
        elif h_mood == 'happy' and thought_id in ['moltbook-social', 'share-discovery', 'creative-chaos']:
            weight *= 1.3  # Amplify good vibes
    
    # Track heavily dampened thoughts as skipped
    if weight < original_weight * 0.6 and skip_reasons:
        skipped_thoughts.append({
            'id': thought_id,
            'original_weight': original_weight,
            'final_weight': weight,
            'reasons': skip_reasons
        })
    
    # Convert back to int for pool generation
    final_weight = max(1, int(weight * 10))  # Scale up for precision
    pool.extend([t] * final_weight)

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
    'mood_id': today_mood.get('id', 'none') if today_mood else 'none',
    'skipped': skipped_thoughts
}))
")

echo "$PROMPT"

# Log the pick
TIMESTAMP=$(date -Iseconds)
THOUGHT_ID=$(echo "$PROMPT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['id'])" 2>/dev/null)
MOOD_ID=$(echo "$PROMPT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('mood_id','none'))" 2>/dev/null)
echo "$TIMESTAMP | mood=$MOOD | thought=$THOUGHT_ID | today_mood=$MOOD_ID" >> "$LOG_DIR/picks.log"
