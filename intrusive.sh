#!/bin/bash
# 🧠 Intrusive Thoughts — Random prompt picker (mood-aware)
# Usage: intrusive.sh <mood>    (night|day)
#        intrusive.sh wizard     (run setup wizard)
# Reads today_mood.json to bias thought selection toward current mood

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Handle subcommands
case "${1:-}" in
    --version|-v|version)
        if [[ -f "$SCRIPT_DIR/VERSION" ]]; then
            echo "Intrusive Thoughts v$(cat "$SCRIPT_DIR/VERSION")"
        else
            echo "Intrusive Thoughts (version unknown)"
        fi
        exit 0
        ;;
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
    explain)
        if [[ -z "$2" ]]; then
            echo "Usage: intrusive.sh explain <system>"
            echo "Available systems: moods, memory, trust, evolution, health, thoughts, proactive"
            exit 1
        fi
        exec python3 "$SCRIPT_DIR/explain_system.py" "$2"
        ;;
    introspect)
        exec python3 "$SCRIPT_DIR/introspect.py"
        ;;
    why)
        exec python3 "$SCRIPT_DIR/decision_trace.py" "${2:-}"
        ;;
    export-state)
        python3 -c "
import json
import sys
from datetime import datetime
from pathlib import Path
from config import get_data_dir, get_file_path

def load_json_safe(filepath, default=None):
    \"\"\"Safely load JSON file, return default if fails.\"\"\"
    try:
        if filepath.exists():
            return json.loads(filepath.read_text())
    except:
        pass
    return default if default is not None else {}

data_dir = get_data_dir()

# Load current mood
mood = load_json_safe(get_file_path('today_mood.json'), {})

# Load streaks
streaks = load_json_safe(get_file_path('streaks.json'), {})

# Load recent history (last 5 entries)
history = load_json_safe(get_file_path('history.json'), [])
recent_history = history[-5:] if len(history) > 5 else history

# Calculate trust score (if trust system exists)
trust_score = 0
trust_store_dir = data_dir / 'trust_store'
if trust_store_dir.exists():
    trust_files = list(trust_store_dir.glob('*.json'))
    trust_score = len(trust_files)

# Calculate memory stats
memory_stats = {}
memory_store_dir = data_dir / 'memory_store'
if memory_store_dir.exists():
    memory_files = list(memory_store_dir.glob('*.json'))
    memory_stats['total_memories'] = len(memory_files)
    total_size = sum(f.stat().st_size for f in memory_files)
    memory_stats['total_size_bytes'] = total_size

# Load achievements
achievements = load_json_safe(get_file_path('achievements_earned.json'), {})
if isinstance(achievements, dict):
    earned_list = achievements.get('earned', [])
    earned_count = len(earned_list)
    total_points = sum(a.get('points', 0) for a in earned_list if isinstance(a, dict))
elif isinstance(achievements, list):
    earned_count = len(achievements)  
    total_points = sum(a.get('points', 0) for a in achievements if isinstance(a, dict))
else:
    earned_count = 0
    total_points = 0

# Load active schedule if exists
schedule = load_json_safe(get_file_path('today_schedule.json'))

# Read version
version = 'unknown'
version_file = Path('$SCRIPT_DIR/VERSION')
if version_file.exists():
    version = version_file.read_text().strip()

# Build export data
export_data = {
    'version': version,
    'exported_at': datetime.now().isoformat(),
    'mood': mood,
    'streaks': streaks,
    'recent_history': recent_history,
    'trust_score': trust_score,
    'memory_stats': memory_stats,
    'achievements': {
        'earned_count': earned_count,
        'total_points': total_points
    },
    'active_schedule': schedule
}

print(json.dumps(export_data, indent=2))
"
        exit 0
        ;;
    import-state)
        if [[ -z "$2" ]]; then
            echo "Usage: intrusive.sh import-state <file>"
            echo "Imports agent state from a previously exported JSON file"
            exit 1
        fi
        
        if [[ ! -f "$2" ]]; then
            echo "Error: File '$2' does not exist"
            exit 1
        fi
        
        python3 -c "
import json
import sys
from pathlib import Path
from config import get_file_path

def save_json_safe(filepath, data):
    \"\"\"Safely save JSON data to file.\"\"\"
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(json.dumps(data, indent=2))
        return True
    except Exception as e:
        print(f'Error saving {filepath}: {e}', file=sys.stderr)
        return False

# Load import data
import_file = Path('$2')
try:
    import_data = json.loads(import_file.read_text())
except Exception as e:
    print(f'Error reading import file: {e}', file=sys.stderr)
    sys.exit(1)

restored = []
failed = []

# Restore mood
if 'mood' in import_data and import_data['mood']:
    if save_json_safe(get_file_path('today_mood.json'), import_data['mood']):
        restored.append('mood')
    else:
        failed.append('mood')

# Restore streaks  
if 'streaks' in import_data and import_data['streaks']:
    if save_json_safe(get_file_path('streaks.json'), import_data['streaks']):
        restored.append('streaks')
    else:
        failed.append('streaks')

print('🔄 State Import Summary')
print('=' * 30)
print(f'Source: {import_file}')
print(f'Exported: {import_data.get(\"exported_at\", \"unknown\")}')
print(f'Version: {import_data.get(\"version\", \"unknown\")}')
print()

if restored:
    print('✅ Successfully restored:')
    for item in restored:
        print(f'  • {item}')

if failed:
    print('❌ Failed to restore:')
    for item in failed:
        print(f'  • {item}')

if not restored and not failed:
    print('ℹ️  No restorable data found in import file')

print()
print('📊 Import Statistics:')
if 'trust_score' in import_data:
    print(f'  Trust score: {import_data[\"trust_score\"]}')
if 'achievements' in import_data:
    ach = import_data['achievements']
    print(f'  Achievements: {ach.get(\"earned_count\", 0)} earned, {ach.get(\"total_points\", 0)} points')
if 'memory_stats' in import_data:
    mem = import_data['memory_stats']
    print(f'  Memory: {mem.get(\"total_memories\", 0)} memories, {mem.get(\"total_size_bytes\", 0)} bytes')
print(f'  Recent history: {len(import_data.get(\"recent_history\", []))} entries')
"
        exit 0
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
        echo "  intrusive.sh --version           Show version information"
        echo ""
        echo "Self-awareness commands:"
        echo "  intrusive.sh explain <system>    Explain how a subsystem works"
        echo "  intrusive.sh introspect          Full state dump as JSON"
        echo "  intrusive.sh why [action-id]     Trace decision path for recent action"
        echo ""
        echo "Context survival:"
        echo "  intrusive.sh export-state        Export agent state as JSON"
        echo "  intrusive.sh import-state <file> Import and restore agent state"
        echo ""
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

# Min-interval guard: skip if last pick was less than 30 seconds ago
DECISIONS_FILE="$LOG_DIR/decisions.json"
if [[ -f "$DECISIONS_FILE" ]]; then
    LAST_TIMESTAMP=$(jq -r '.[-1].timestamp // empty' "$DECISIONS_FILE" 2>/dev/null)
    if [[ -n "$LAST_TIMESTAMP" ]]; then
        LAST_EPOCH=$(date -d "$LAST_TIMESTAMP" +%s 2>/dev/null || echo "0")
        NOW_EPOCH=$(date +%s)
        TIME_DIFF=$((NOW_EPOCH - LAST_EPOCH))
        
        if [[ $TIME_DIFF -lt 30 ]]; then
            echo "Skipping pick - last decision was $TIME_DIFF seconds ago (minimum 30 seconds required)" >&2
            exit 0
        fi
    fi
fi

# Pick a weighted random thought, influenced by today's mood and streak weights  
# Use temporary file to capture all output reliably
TEMP_OUTPUT="/tmp/intrusive_output_$$.txt"
python3 -c "
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

# Load day-of-week multipliers
day_of_week_mult = {}
day_of_week_vibe = ''
try:
    with open('$SCRIPT_DIR/moods.json') as f:
        moods_config = json.load(f)
    dow = datetime.now().strftime('%A').lower()
    dow_data = moods_config.get('day_of_week', {}).get('multipliers', {}).get(dow, {})
    day_of_week_vibe = dow_data.get('vibe', '')
    day_of_week_mult = {k: v for k, v in dow_data.items() if k != 'vibe'}
    # Get day flavor text
    day_flavors = moods_config.get('day_of_week', {}).get('flavor_text', {}).get(dow, [])
except:
    day_flavors = []

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
    if day_of_week_vibe:
        mood_context += f' | {datetime.now().strftime(\"%A\")}: {day_of_week_vibe}'
    if day_flavors:
        mood_context += f' — \"{random.choice(day_flavors)}\"'

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

print('__REJECTIONS__:' + json.dumps(rejections_to_log))
print('__DECISION_TRACE__:' + json.dumps(decision_trace))
" > "$TEMP_OUTPUT"

# Read the output
FULL_OUTPUT=$(cat "$TEMP_OUTPUT")
rm -f "$TEMP_OUTPUT"

# Debug: Check what we captured  
echo "DEBUG: FULL_OUTPUT length: ${#FULL_OUTPUT}" >&2
echo "DEBUG: First line of FULL_OUTPUT: $(echo "$FULL_OUTPUT" | head -1)" >&2
echo "DEBUG: Lines containing '__': $(echo "$FULL_OUTPUT" | grep "__" | wc -l)" >&2

# Process the output - extract rejections, decision trace, and main prompt
REJECTIONS_LINE=$(echo "$FULL_OUTPUT" | grep "^__REJECTIONS__:" | head -1)
DECISION_TRACE_LINE=$(echo "$FULL_OUTPUT" | grep "^__DECISION_TRACE__:" | head -1)  
MAIN_PROMPT=$(echo "$FULL_OUTPUT" | grep "^{" | head -1)

echo "DEBUG: REJECTIONS_LINE length: ${#REJECTIONS_LINE}" >&2
echo "DEBUG: DECISION_TRACE_LINE length: ${#DECISION_TRACE_LINE}" >&2
echo "DEBUG: REJECTIONS_LINE: ${REJECTIONS_LINE:0:100}..." >&2

echo "$MAIN_PROMPT"

# Log rejections to rejections.log
echo "DEBUG: About to process rejections, REJECTIONS_LINE='$REJECTIONS_LINE'" >&2
if [[ -n "$REJECTIONS_LINE" ]]; then
    REJECTIONS_JSON="${REJECTIONS_LINE#__REJECTIONS__:}"
    echo "DEBUG: REJECTIONS_JSON='$REJECTIONS_JSON'" >&2
    if [[ "$REJECTIONS_JSON" != "[]" ]]; then
        echo "DEBUG: Found rejections to log" >&2
        echo "$REJECTIONS_JSON" | python3 -c "
import json, sys
rejections = json.load(sys.stdin)
for rej in rejections:
    print(f\"{rej['timestamp']} | {rej['thought_id']} | {rej['mood']} | {rej['reason']} | {rej['flavor_text']}\")
" >> "$LOG_DIR/rejections.log"
    else
        echo "DEBUG: No rejections to log (empty array)" >&2
    fi
else
    echo "DEBUG: REJECTIONS_LINE is empty" >&2
fi

# Log decision trace to decisions.json (append to array)
echo "DEBUG: About to process decision trace, DECISION_TRACE_LINE length: ${#DECISION_TRACE_LINE}" >&2
if [[ -n "$DECISION_TRACE_LINE" ]]; then
    DECISION_JSON="${DECISION_TRACE_LINE#__DECISION_TRACE__:}"
    echo "DEBUG: Extracted DECISION_JSON, length: ${#DECISION_JSON}" >&2
    
    # Create decisions.json if it doesn't exist
    if [[ ! -f "$LOG_DIR/decisions.json" ]]; then
        echo "DEBUG: Creating new decisions.json" >&2
        echo "[]" > "$LOG_DIR/decisions.json"
    else
        echo "DEBUG: Using existing decisions.json" >&2
    fi
    
    # Append to the JSON array - pass JSON via stdin to avoid shell escaping issues
    echo "DEBUG: About to append decision to JSON file" >&2
    echo "$DECISION_JSON" | python3 -c "
import json, sys
import os

try:
    decision = json.load(sys.stdin)
    decisions_file = '$LOG_DIR/decisions.json'

    try:
        with open(decisions_file, 'r') as f:
            decisions = json.load(f)
    except:
        decisions = []

    decisions.append(decision)

    # Keep only last 100 entries to prevent file from growing too large  
    decisions = decisions[-100:]

    with open(decisions_file, 'w') as f:
        json.dump(decisions, f, indent=2)
    
    print('SUCCESS: Decision logged', file=sys.stderr)
except Exception as e:
    print(f'ERROR logging decision: {e}', file=sys.stderr)
"
else
    echo "DEBUG: DECISION_TRACE_LINE is empty" >&2
fi

# Log the pick (existing functionality)
TIMESTAMP=$(date -Iseconds)
THOUGHT_ID=$(echo "$MAIN_PROMPT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['id'])" 2>/dev/null)
MOOD_ID=$(echo "$MAIN_PROMPT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('mood_id','none'))" 2>/dev/null)
echo "$TIMESTAMP | mood=$MOOD | thought=$THOUGHT_ID | today_mood=$MOOD_ID" >> "$LOG_DIR/picks.log"
