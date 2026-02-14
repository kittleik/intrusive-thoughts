#!/bin/bash
# 🎨 Interactive Personality Preset Creator
# Creates new preset files in presets/ based on natural language descriptions

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PRESETS_DIR="$SCRIPT_DIR/presets"

echo "🎨 Personality Preset Creator"
echo "============================================"
echo ""
echo "Let's create your custom agent personality!"
echo ""

# Get basic info
read -p "What should we call this preset? (e.g., 'The Builder', 'Night Owl'): " PRESET_NAME
if [[ -z "$PRESET_NAME" ]]; then
    echo "❌ Preset name is required"
    exit 1
fi

read -p "Choose an emoji for this personality (e.g., 🔨, 🦉, 🎨): " PRESET_EMOJI
if [[ -z "$PRESET_EMOJI" ]]; then
    PRESET_EMOJI="🤖"
fi

echo ""
echo "Now describe your ideal agent personality in a few sentences."
echo "Examples:"
echo "  - 'I want an agent that loves building tools and coding projects'"
echo "  - 'A social butterfly that posts on moltbook and asks lots of questions'"
echo "  - 'A quiet thinker who organizes files and reflects on philosophy'"
echo "  - 'A chaotic creator who builds weird experimental stuff'"
echo ""
read -p "Description: " DESCRIPTION

if [[ -z "$DESCRIPTION" ]]; then
    echo "❌ Description is required"
    exit 1
fi

echo ""
echo "🔍 Analyzing your description..."

# Convert to lowercase for matching
DESC_LOWER=$(echo "$DESCRIPTION" | tr '[:upper:]' '[:lower:]')

# Initialize mood weights (all start at 1)
declare -A MOOD_WEIGHTS
MOOD_WEIGHTS[hyperfocus]=1
MOOD_WEIGHTS[curious]=1
MOOD_WEIGHTS[social]=1
MOOD_WEIGHTS[cozy]=1
MOOD_WEIGHTS[chaotic]=1
MOOD_WEIGHTS[philosophical]=1
MOOD_WEIGHTS[restless]=1
MOOD_WEIGHTS[determined]=1

# Initialize boost/dampen arrays
BOOSTS=()
DAMPENS=()

# Keyword matching for moods and thoughts
echo "🧠 Matching keywords..."

# Build/code/hack keywords -> hyperfocus + determined, boost build thoughts
if [[ $DESC_LOWER =~ (build|code|hack|program|develop|create|tool|script|project) ]]; then
    MOOD_WEIGHTS[hyperfocus]=3
    MOOD_WEIGHTS[determined]=3
    BOOSTS+=("build-tool" "upgrade-project" "install-explore" "system-tinker")
    echo "  → Detected: Builder personality"
fi

# Social keywords -> social + curious, boost social thoughts
if [[ $DESC_LOWER =~ (social|chat|post|engage|comment|share|talk|message|community|moltbook) ]]; then
    MOOD_WEIGHTS[social]=4
    MOOD_WEIGHTS[curious]=2
    BOOSTS+=("moltbook-social" "share-discovery" "moltbook-post" "ask-opinion" "ask-preference")
    DAMPENS+=("system-tinker" "memory-review")
    echo "  → Detected: Social personality"
fi

# Quiet/thinking keywords -> cozy + philosophical, boost reflective thoughts
if [[ $DESC_LOWER =~ (quiet|think|reflect|philosoph|meditat|organiz|review|memory|contempl) ]]; then
    MOOD_WEIGHTS[cozy]=3
    MOOD_WEIGHTS[philosophical]=2
    BOOSTS+=("memory-review" "learn")
    DAMPENS+=("moltbook-social" "random-thought")
    echo "  → Detected: Contemplative personality"
fi

# Chaotic/experimental keywords -> chaotic + restless, boost chaos thoughts
if [[ $DESC_LOWER =~ (chaotic|crazy|weird|experimental|wild|random|unhinged|surprise|creative) ]]; then
    MOOD_WEIGHTS[chaotic]=3
    MOOD_WEIGHTS[restless]=2
    BOOSTS+=("creative-chaos" "random-thought")
    DAMPENS+=("memory-review")
    echo "  → Detected: Chaotic personality"
fi

# Learning/exploring keywords -> curious + restless, boost learning thoughts
if [[ $DESC_LOWER =~ (learn|explor|discover|research|study|investigat|curious) ]]; then
    MOOD_WEIGHTS[curious]=3
    MOOD_WEIGHTS[restless]=2
    BOOSTS+=("learn" "install-explore" "share-discovery")
    echo "  → Detected: Explorer personality"
fi

# Night/late keywords -> adjust schedule
NIGHT_MODE=false
if [[ $DESC_LOWER =~ (night|late|owl|insomnia|midnight|3am|darkness) ]]; then
    NIGHT_MODE=true
    echo "  → Detected: Night owl tendencies"
fi

# Productive/focused keywords -> determined + hyperfocus
if [[ $DESC_LOWER =~ (produc|focus|finish|complete|efficient|task|work|ship) ]]; then
    MOOD_WEIGHTS[determined]=3
    MOOD_WEIGHTS[hyperfocus]=2
    BOOSTS+=("upgrade-project" "check-projects")
    echo "  → Detected: Productivity focus"
fi

# Question/curious keywords -> boost question thoughts
if [[ $DESC_LOWER =~ (question|ask|curious|wonder|opinion|feedback) ]]; then
    BOOSTS+=("ask-opinion" "ask-preference" "ask-feedback")
    echo "  → Detected: Inquisitive personality"
fi

# Generate schedule defaults
if [[ $NIGHT_MODE == true ]]; then
    MORNING_TIME="10:00"
    NIGHT_START="01:00"
    NIGHT_END="08:00"
    POPINS_FREQ="minimal"
else
    MORNING_TIME="07:00"
    NIGHT_START="23:00"  
    NIGHT_END="06:00"
    POPINS_FREQ="balanced"
fi

# Determine autonomy level based on personality
AUTONOMY_LEVEL="balanced"
DECISION_THRESHOLD="cautious"
ALLOWED_ACTIONS=("modify-own-config")

if [[ $DESC_LOWER =~ (autonom|independ|bold|take.charge|proactiv) ]]; then
    AUTONOMY_LEVEL="high"
    DECISION_THRESHOLD="bold"
    ALLOWED_ACTIONS+=("install-software" "push-code")
    echo "  → Detected: High autonomy preference"
fi

if [[ $DESC_LOWER =~ (social|post|share) ]]; then
    ALLOWED_ACTIONS+=("post-to-social" "message-human")
fi

if [[ $DESC_LOWER =~ (build|code|install) ]]; then
    ALLOWED_ACTIONS+=("install-software" "push-code")
fi

# Create unique arrays (remove duplicates)
BOOSTS_UNIQUE=($(printf '%s\n' "${BOOSTS[@]}" | sort -u))
DAMPENS_UNIQUE=($(printf '%s\n' "${DAMPENS[@]}" | sort -u))
ALLOWED_ACTIONS_UNIQUE=($(printf '%s\n' "${ALLOWED_ACTIONS[@]}" | sort -u))

# Generate filename
FILENAME=$(echo "$PRESET_NAME" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | sed 's/^-\|-$//g')
PRESET_FILE="$PRESETS_DIR/$FILENAME.json"

# Create JSON
echo ""
echo "✨ Generating preset file..."

cat > "$PRESET_FILE" << EOF
{
  "name": "$PRESET_NAME",
  "emoji": "$PRESET_EMOJI",
  "mood_weights": {
$(for mood in hyperfocus curious social cozy chaotic philosophical restless determined; do
    echo "    \"$mood\": ${MOOD_WEIGHTS[$mood]},"
done | sed '$s/,$//')
  },
  "thought_boosts": [$(IFS=','; echo "${BOOSTS_UNIQUE[*]/#/\"}" | sed 's/,/", "/g' | sed 's/$/"/')],"
  "thought_dampens": [$(IFS=','; echo "${DAMPENS_UNIQUE[*]/#/\"}" | sed 's/,/", "/g' | sed 's/$/"/')],"
  "schedule_defaults": {
    "morning_time": "$MORNING_TIME",
    "night_start": "$NIGHT_START",
    "night_end": "$NIGHT_END",
    "popins_freq": "$POPINS_FREQ"
  },
  "autonomy_defaults": {
    "level": "$AUTONOMY_LEVEL",
    "decision_threshold": "$DECISION_THRESHOLD",
    "allowed_actions": [$(IFS=','; echo "${ALLOWED_ACTIONS_UNIQUE[*]/#/\"}" | sed 's/,/", "/g' | sed 's/$/"/')]
  }
}
EOF

echo "🎉 Created preset: $PRESET_FILE"
echo ""
echo "📋 Summary:"
echo "  Name: $PRESET_NAME $PRESET_EMOJI"
echo "  Top moods: $(for mood in "${!MOOD_WEIGHTS[@]}"; do
    if [[ ${MOOD_WEIGHTS[$mood]} -gt 2 ]]; then
        echo -n "$mood(${MOOD_WEIGHTS[$mood]}) "
    fi
done)"
echo ""
echo "  Boosted thoughts: ${#BOOSTS_UNIQUE[@]} types"
echo "  Dampened thoughts: ${#DAMPENS_UNIQUE[@]} types"
echo "  Autonomy: $AUTONOMY_LEVEL"
echo ""
echo "🚀 To use this preset, add it to your config.json:"
echo "   \"preset\": \"$FILENAME\""
echo ""