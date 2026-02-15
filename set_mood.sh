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
# NETWORK: Open-Meteo API - public, no auth, read-only GET request
# Default coords: Oslo (59.91, 10.75) — override via config.json
LAT=$(python3 -c "import json; print(json.load(open('$SCRIPT_DIR/config.json')).get('integrations',{}).get('weather',{}).get('latitude', 59.91))" 2>/dev/null || echo "59.91")
LON=$(python3 -c "import json; print(json.load(open('$SCRIPT_DIR/config.json')).get('integrations',{}).get('weather',{}).get('longitude', 10.75))" 2>/dev/null || echo "10.75")
METEO=$(curl -s --max-time 10 "https://api.open-meteo.com/v1/forecast?latitude=${LAT}&longitude=${LON}&current_weather=true" 2>/dev/null)
if [ -n "$METEO" ]; then
    echo "$METEO" | python3 -c "
import json, sys
d = json.load(sys.stdin)
w = d.get('current_weather', {})
codes = {0:'Clear',1:'Mainly clear',2:'Partly cloudy',3:'Overcast',45:'Foggy',48:'Rime fog',
         51:'Light drizzle',53:'Drizzle',55:'Heavy drizzle',61:'Light rain',63:'Rain',65:'Heavy rain',
         71:'Light snow',73:'Snow',75:'Heavy snow',77:'Snow grains',80:'Light showers',81:'Showers',
         85:'Light snow showers',86:'Heavy snow showers',95:'Thunderstorm'}
desc = codes.get(w.get('weathercode',99), 'Unknown')
loc = '${LOCATION}'
print(f'{loc}: {desc}, {w[\"temperature\"]}°C, wind {w[\"windspeed\"]}km/h')
" 2>/dev/null || echo "weather unavailable"
else
    echo "weather unavailable"
fi

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
