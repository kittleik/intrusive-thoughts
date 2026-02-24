#!/bin/bash
# set_focus.sh — Point night workshop at a specific project or topic
# Usage: ./set_focus.sh "cauldron-tui sell bug"
#        ./set_focus.sh --clear
#
# When focus is set, upgrade-project and build-tool get 2x weight boost
# and the prompt includes the focus context.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/load_config.sh"
FOCUS_FILE="$DATA_DIR/focus.json"

if [[ "${1:-}" == "--clear" ]]; then
    rm -f "$FOCUS_FILE"
    echo "✅ Focus cleared — back to open selection"
    exit 0
fi

if [[ "${1:-}" == "--show" ]]; then
    if [[ -f "$FOCUS_FILE" ]]; then
        python3 -c "import json; d=json.load(open('$FOCUS_FILE')); print(f'🎯 Focus: {d[\"focus\"]}  (set {d[\"set_at\"][:10]})')"
    else
        echo "No focus set"
    fi
    exit 0
fi

FOCUS="${1:-}"
if [[ -z "$FOCUS" ]]; then
    echo "Usage: $0 \"your focus\" | --clear | --show"
    exit 1
fi

python3 -c "
import json
from datetime import datetime
d = {
    'focus': '$FOCUS',
    'set_at': datetime.now().isoformat(),
    'boost_thoughts': ['upgrade-project', 'build-tool'],
    'boost_factor': 2.0
}
with open('$FOCUS_FILE', 'w') as f:
    json.dump(d, f, indent=2)
print(f'🎯 Focus set: $FOCUS')
print('  upgrade-project and build-tool will get 2x weight boost')
print('  Run ./set_focus.sh --clear when done')
"
