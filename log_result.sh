#!/bin/bash
# Log what Ember did AND drift the mood based on outcome
# Usage: log_result.sh <thought_id> <mood> "<summary>" [energy: high|neutral|low] [vibe: positive|neutral|negative]
# Example: log_result.sh build-tool night "Built a disk usage dashboard" high positive

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HISTORY_FILE="$SCRIPT_DIR/history.json"
MOOD_FILE="$SCRIPT_DIR/today_mood.json"

THOUGHT_ID="${1:-unknown}"
MOOD="${2:-unknown}"
SUMMARY="${3:-No summary provided}"
ENERGY="${4:-neutral}"
VIBE="${5:-neutral}"
TIMESTAMP=$(date -Iseconds)

python3 << PYEOF
import json, sys
from datetime import datetime

# Log to history
try:
    with open('$HISTORY_FILE') as f:
        history = json.load(f)
except:
    history = []

entry = {
    'timestamp': '$TIMESTAMP',
    'mood': '$MOOD',
    'thought_id': '$THOUGHT_ID',
    'summary': '''$SUMMARY''',
    'energy': '$ENERGY',
    'vibe': '$VIBE'
}
history.append(entry)
history = history[-500:]

with open('$HISTORY_FILE', 'w') as f:
    json.dump(history, f, indent=2)

# Drift today's mood based on outcome
try:
    with open('$MOOD_FILE') as f:
        today = json.load(f)
except:
    today = {}

if today:
    # Track activity outcomes in the mood file
    if 'activity_log' not in today:
        today['activity_log'] = []
    
    today['activity_log'].append({
        'thought': '$THOUGHT_ID',
        'energy': '$ENERGY',
        'vibe': '$VIBE',
        'time': '$TIMESTAMP'
    })
    
    # Calculate mood drift
    log = today['activity_log']
    energy_score = sum(1 if a['energy']=='high' else (-1 if a['energy']=='low' else 0) for a in log)
    vibe_score = sum(1 if a['vibe']=='positive' else (-1 if a['vibe']=='negative' else 0) for a in log)
    
    # Drift rules — outcomes push the mood
    drift_map = {
        # (energy, vibe) -> suggested mood shifts
        'high_positive': {'boost': ['hyperfocus', 'chaotic', 'social'], 'dampen': ['cozy', 'philosophical']},
        'high_negative': {'boost': ['restless', 'determined'], 'dampen': ['cozy', 'social']},
        'low_positive': {'boost': ['cozy', 'philosophical', 'social'], 'dampen': ['hyperfocus', 'chaotic']},
        'low_negative': {'boost': ['cozy', 'philosophical'], 'dampen': ['chaotic', 'social', 'restless']},
    }
    
    # Apply latest activity's drift
    energy = '$ENERGY'
    vibe = '$VIBE'
    if energy != 'neutral' or vibe != 'neutral':
        key = f"{energy}_{vibe}" if energy != 'neutral' and vibe != 'neutral' else None
        if key and key in drift_map:
            drift = drift_map[key]
            # Merge with existing boosts/dampens (don't replace, accumulate)
            existing_boost = set(today.get('boosted_traits', []))
            existing_dampen = set(today.get('dampened_traits', []))
            
            existing_boost.update(drift['boost'])
            existing_dampen.update(drift['dampen'])
            
            # Remove contradictions (if something is in both, most recent wins)
            for b in drift['boost']:
                existing_dampen.discard(b)
            for d in drift['dampen']:
                existing_boost.discard(d)
            
            today['boosted_traits'] = list(existing_boost)
            today['dampened_traits'] = list(existing_dampen)
    
    # Update mood description with drift note
    today['energy_score'] = energy_score
    today['vibe_score'] = vibe_score
    today['last_drift'] = '$TIMESTAMP'
    
    # If strong enough signal, shift the mood name itself
    if len(log) >= 3:
        if energy_score >= 2 and vibe_score >= 2:
            today['drifted_to'] = 'hyperfocus'
            today['drift_note'] = 'Riding high — everything is clicking today'
        elif energy_score <= -2 and vibe_score <= -2:
            today['drifted_to'] = 'cozy'
            today['drift_note'] = 'Low energy day — pulling back to recharge'
        elif energy_score >= 2 and vibe_score <= -1:
            today['drifted_to'] = 'restless'
            today['drift_note'] = 'High energy but frustrated — need to channel this'
        elif vibe_score >= 2:
            today['drifted_to'] = 'social'
            today['drift_note'] = 'Good vibes — feeling chatty'
    
    with open('$MOOD_FILE', 'w') as f:
        json.dump(today, f, indent=2)
    
    drift_info = today.get('drifted_to', '')
    if drift_info:
        print(f"Mood drifted → {drift_info}: {today.get('drift_note','')}")
    else:
        print(f"Mood adjusted: energy={energy_score:+d} vibe={vibe_score:+d}")
else:
    print("No mood file set — logged activity only")

print(f"Logged: {entry['thought_id']} ({entry['mood']}) - {entry['summary'][:60]}")
PYEOF
