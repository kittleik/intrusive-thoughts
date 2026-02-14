#!/bin/bash
# 💭 Thought Suggestion Generator
# Takes a natural language description and outputs a properly formatted thought entry JSON

DESCRIPTION="$1"

if [[ -z "$DESCRIPTION" ]]; then
    echo "Usage: suggest_thought.sh \"description of the thought\""
    echo "Example: suggest_thought.sh \"Browse hackernews and share interesting tech articles\""
    exit 1
fi

echo "💭 Generating thought from: $DESCRIPTION"
echo ""

# Convert to lowercase for matching
DESC_LOWER=$(echo "$DESCRIPTION" | tr '[:upper:]' '[:lower:]')

# Generate unique ID from description
THOUGHT_ID=$(echo "$DESCRIPTION" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9 ]//g' | sed 's/ \+/-/g' | cut -c1-25)

# Default weight
WEIGHT=2

# Adjust weight based on keywords
if [[ $DESC_LOWER =~ (build|create|develop|code|tool|project) ]]; then
    WEIGHT=3
    echo "🔨 Detected: High-effort building activity (weight: 3)"
elif [[ $DESC_LOWER =~ (browse|check|quick|simple|look) ]]; then
    WEIGHT=1
    echo "👀 Detected: Low-effort browsing activity (weight: 1)"
elif [[ $DESC_LOWER =~ (post|share|message|ask|comment) ]]; then
    WEIGHT=2
    echo "💬 Detected: Social interaction activity (weight: 2)"
elif [[ $DESC_LOWER =~ (learn|explore|research|study) ]]; then
    WEIGHT=2
    echo "🧠 Detected: Learning activity (weight: 2)"
else
    echo "⚖️  Using default weight: 2"
fi

# Enhance the prompt with contextual details
ENHANCED_PROMPT="$DESCRIPTION"

# Add helpful context based on keywords
if [[ $DESC_LOWER =~ (hackernews|hn) ]]; then
    ENHANCED_PROMPT="$DESCRIPTION If you find something interesting, message your human about it."
elif [[ $DESC_LOWER =~ (moltbook) ]]; then
    ENHANCED_PROMPT="$DESCRIPTION Pick the right submolt and engage thoughtfully with the community."
elif [[ $DESC_LOWER =~ (build|create) ]]; then
    ENHANCED_PROMPT="$DESCRIPTION Save it somewhere sensible and log what you made."
elif [[ $DESC_LOWER =~ (install) ]]; then
    ENHANCED_PROMPT="$DESCRIPTION Try it out and if it's useful, add it to TOOLS.md."
elif [[ $DESC_LOWER =~ (learn|study) ]]; then
    ENHANCED_PROMPT="$DESCRIPTION Take notes and update your knowledge."
fi

# Generate the JSON
cat << EOF
{
  "id": "$THOUGHT_ID",
  "weight": $WEIGHT,
  "prompt": "$ENHANCED_PROMPT"
}
EOF

echo ""
echo "✨ Copy the JSON above and add it to the appropriate mood section in thoughts.json"
echo ""
echo "💡 Suggested placement:"
if [[ $DESC_LOWER =~ (browse|check|social|post|message) ]]; then
    echo "   → Add to 'day' thoughts (lighter activities)"
elif [[ $DESC_LOWER =~ (build|code|develop|create|deep|focus) ]]; then
    echo "   → Add to 'night' thoughts (deep work activities)"
else
    echo "   → Add to either 'day' or 'night' based on when this activity fits best"
fi
echo ""