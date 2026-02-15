#!/bin/bash
# 🧠 Mood setter — called by the morning cron, outputs today's mood context
# Gathers weather + news signals and picks a weighted random mood

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Load config for location
LOCATION="London"
if [ -f "$SCRIPT_DIR/config.json" ]; then
    LOCATION=$(python3 -c "import json; print(json.load(open('$SCRIPT_DIR/config.json')).get('integrations',{}).get('weather',{}).get('location','London').split(',')[0])" 2>/dev/null || echo "London")
fi

echo "=== WEATHER ==="
# NETWORK: wttr.in weather API - public, no auth, read-only GET request
curl -s "wttr.in/${LOCATION}?format=%c+%t+%h+%w" 2>/dev/null || echo "weather unavailable"
echo ""
# NETWORK: wttr.in weather API - public, no auth, read-only GET request  
curl -s "wttr.in/${LOCATION}?format=3" 2>/dev/null || echo ""

echo ""
echo "=== WEATHER DETAIL ==="
# NETWORK: wttr.in weather API - public, no auth, read-only GET request
curl -s "wttr.in/${LOCATION}?0T" 2>/dev/null | head -15 || echo "unavailable"

echo ""
echo "=== GLOBAL NEWS ==="
# NETWORK: BBC RSS feed - public, no auth, read-only GET request
curl -s "https://feeds.bbci.co.uk/news/world/rss.xml" 2>/dev/null | grep -oP '(?<=<title>).*?(?=</title>)' | head -8 || echo "unavailable"

echo ""
echo "=== TECH/AI NEWS ==="
# NETWORK: Hacker News RSS feed - public, no auth, read-only GET request
curl -s "https://hnrss.org/frontpage" 2>/dev/null | grep -oP '(?<=<title>).*?(?=</title>)' | head -8 || echo "unavailable"

echo ""
echo "=== DAY OF WEEK ==="
python3 -c "
import json
from datetime import datetime

day = datetime.now().strftime('%A').lower()
print(f'Today is {day.capitalize()}')

try:
    with open('$SCRIPT_DIR/moods.json') as f:
        moods = json.load(f)
    dow = moods.get('day_of_week', {}).get('multipliers', {}).get(day, {})
    vibe = dow.get('vibe', '')
    if vibe:
        print(f'Day vibe: {vibe}')
    
    # Show mood weight adjustments for today
    adjustments = {k: v for k, v in dow.items() if k != 'vibe'}
    if adjustments:
        print('Mood weight adjustments:')
        for mood_id, mult in sorted(adjustments.items(), key=lambda x: x[1], reverse=True):
            arrow = '↑' if mult > 1 else '↓' if mult < 1 else '→'
            print(f'  {arrow} {mood_id}: {mult}x')
    
    # Show flavor text
    flavors = moods.get('day_of_week', {}).get('flavor_text', {}).get(day, [])
    if flavors:
        import random
        print(f'\\n\"{random.choice(flavors)}\"')
except Exception as e:
    print(f'(day-of-week data unavailable: {e})')
" 2>/dev/null

echo ""
echo "=== CURRENT MOOD FILE ==="
cat "$SCRIPT_DIR/today_mood.json" 2>/dev/null || echo "no mood set yet"

# Sync mood to OpenClaw workspace for cross-session influence
if [ -f "$SCRIPT_DIR/update_mood_workspace.sh" ]; then
    bash "$SCRIPT_DIR/update_mood_workspace.sh"
fi
