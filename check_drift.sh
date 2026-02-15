#!/bin/bash
# 💓 Heartbeat-triggered mood drift checker
# Analyzes today's mood activity_log, triggers drift if threshold crossed, syncs to workspace

set -e  # Exit on any error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MOOD_FILE="$SCRIPT_DIR/today_mood.json"
LOG_FILE="$SCRIPT_DIR/log/drift_check.log"

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

log() {
    echo "[$(date '+%H:%M:%S')] $*" | tee -a "$LOG_FILE" >&2
}

# Check if mood file exists
if [ ! -f "$MOOD_FILE" ]; then
    log "❌ No today_mood.json found - skipping drift check"
    exit 0
fi

# Read current mood state
ACTIVITY_COUNT=$(python3 -c "
import json, sys
try:
    with open('$MOOD_FILE') as f:
        data = json.load(f)
    activity_log = data.get('activity_log', [])
    print(len(activity_log))
except:
    print(0)
" 2>/dev/null)

LAST_DRIFT=$(python3 -c "
import json, sys
from datetime import datetime, timedelta
try:
    with open('$MOOD_FILE') as f:
        data = json.load(f)
    last_drift = data.get('last_drift', '')
    if last_drift:
        dt = datetime.fromisoformat(last_drift.replace('Z', '+00:00'))
        now = datetime.now()
        if now.tzinfo is None:
            now = now.replace(tzinfo=dt.tzinfo) if dt.tzinfo else now
        hours_since = (now - dt).total_seconds() / 3600
        print(f'{hours_since:.1f}')
    else:
        print('999')  # Very old
except:
    print('999')
" 2>/dev/null)

log "🔍 Drift check: $ACTIVITY_COUNT activities, ${LAST_DRIFT}h since last drift"

# Drift thresholds
MIN_ACTIVITIES=3
MIN_HOURS_BETWEEN_DRIFT=2.0

# Check if we should trigger drift
SHOULD_DRIFT=false

if (( $(echo "$ACTIVITY_COUNT >= $MIN_ACTIVITIES" | bc -l) )); then
    if (( $(echo "$LAST_DRIFT >= $MIN_HOURS_BETWEEN_DRIFT" | bc -l) )); then
        SHOULD_DRIFT=true
        log "✅ Drift threshold met: $ACTIVITY_COUNT activities, ${LAST_DRIFT}h since last"
    else
        log "⏳ Too soon for drift: only ${LAST_DRIFT}h since last (need ${MIN_HOURS_BETWEEN_DRIFT}h+)"
    fi
else
    log "📊 Not enough activities: $ACTIVITY_COUNT (need $MIN_ACTIVITIES+)"
fi

# Trigger drift if needed
if [ "$SHOULD_DRIFT" = true ]; then
    log "🌊 Triggering mood drift..."
    
    # Run the drift calculation
    if python3 "$SCRIPT_DIR/drift.py" "$MOOD_FILE" > /dev/null 2>&1; then
        log "✅ Drift calculation successful"
        
        # Sync updated mood to workspace
        if "$SCRIPT_DIR/update_mood_workspace.sh" > /dev/null 2>&1; then
            log "✅ Mood workspace updated"
        else
            log "⚠️  Workspace sync failed but drift completed"
        fi
    else
        log "❌ Drift calculation failed"
        exit 1
    fi
else
    log "😴 No drift needed - mood stable for now"
fi

# Clean up old log entries (keep last 50 lines)
if [ -f "$LOG_FILE" ]; then
    tail -n 50 "$LOG_FILE" > "${LOG_FILE}.tmp" && mv "${LOG_FILE}.tmp" "$LOG_FILE"
fi

log "🏁 Drift check complete"