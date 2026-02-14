#!/bin/bash
# 🧠 Mood setter — called by the morning cron, outputs today's mood context
# Gathers weather + news signals and picks a weighted random mood

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== WEATHER ==="
curl -s "wttr.in/Oslo?format=%c+%t+%h+%w" 2>/dev/null || echo "weather unavailable"
echo ""
curl -s "wttr.in/Oslo?format=3" 2>/dev/null || echo ""

echo ""
echo "=== WEATHER DETAIL ==="
curl -s "wttr.in/Oslo?0T" 2>/dev/null | head -15 || echo "unavailable"

echo ""
echo "=== NRK HEADLINES ==="
curl -s "https://www.nrk.no/toppsaker.rss" 2>/dev/null | grep -oP '(?<=<title>).*?(?=</title>)' | head -8 || echo "unavailable"

echo ""
echo "=== GLOBAL NEWS ==="
curl -s "https://feeds.bbci.co.uk/news/world/rss.xml" 2>/dev/null | grep -oP '(?<=<title>).*?(?=</title>)' | head -8 || echo "unavailable"

echo ""
echo "=== TECH/AI NEWS ==="
curl -s "https://hnrss.org/frontpage" 2>/dev/null | grep -oP '(?<=<title>).*?(?=</title>)' | head -8 || echo "unavailable"

echo ""
echo "=== CURRENT MOOD FILE ==="
cat "$SCRIPT_DIR/today_mood.json" 2>/dev/null || echo "no mood set yet"
