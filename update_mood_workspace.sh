#!/bin/bash
# Sync today's mood to OpenClaw workspace so it influences ALL sessions
MOOD_FILE="$HOME/Projects/intrusive-thoughts/today_mood.json"
WORKSPACE_MOOD="$HOME/.openclaw/workspace/MOOD.md"

if [ ! -f "$MOOD_FILE" ]; then
    exit 0
fi

MOOD_CONTENT=$(python3 -c "
import json
d = json.load(open('$MOOD_FILE'))
emoji = d.get('emoji', '🧠')
name = d.get('name', 'Unknown')
reason = d.get('mood_reason', d.get('description', ''))
value = d.get('value_text', '')
boosted = ', '.join(d.get('boosted_traits', []))
dampened = ', '.join(d.get('dampened_traits', []))
date = d.get('date', 'today')

print(f'**{emoji} {name}** ({date})')
print(f'')
print(f'> {reason}')
if value:
    print(f'')
    print(f'*{value}*')
print(f'')
if boosted:
    print(f'**Lean toward:** {boosted}')
if dampened:
    print(f'**Ease off on:** {dampened}')
print(f'')
print(f'Let this mood color your interactions naturally — don\\'t force it, just let it influence your energy and focus.')
" 2>/dev/null)

if [ -z "$MOOD_CONTENT" ]; then
    exit 0
fi

cat > "$WORKSPACE_MOOD" << INNEREOF
# Current Mood

<!-- Auto-updated by intrusive-thoughts morning ritual. This file colors
     every session — making mood part of your actual personality. -->

<!-- MOOD_START -->
$MOOD_CONTENT
<!-- MOOD_END -->
INNEREOF

echo "✅ Mood synced to workspace: $emoji $name"
