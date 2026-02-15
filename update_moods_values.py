#!/usr/bin/env python3
# Script to add value_text to moods.json

import json
from pathlib import Path

def update_moods_with_values():
    script_dir = Path(__file__).parent
    moods_file = script_dir / "moods.json"
    
    # Load current moods
    with open(moods_file, 'r') as f:
        moods_data = json.load(f)
    
    # Value texts explaining why each mood is useful
    value_texts = {
        "hyperfocus": "Hyperfocus builds the impossible — when you're locked in, breakthrough happens",
        "curious": "Curiosity finds the unexpected — today's rabbit hole is tomorrow's innovation",
        "social": "Social energy spreads ideas — the best discoveries mean nothing if unshared",
        "cozy": "Cozy productivity is sustainable productivity — gentle progress beats burnout",
        "chaotic": "Chaos breeds innovation — break something on purpose and see what emerges",
        "philosophical": "Philosophy provides direction — big questions lead to bigger solutions",
        "restless": "Restless energy finds bugs others miss — fidgety minds catch edge cases",
        "determined": "Determination ships code — when focus meets deadline, magic happens"
    }
    
    # Add value_text to each mood
    for mood in moods_data["base_moods"]:
        mood_id = mood["id"]
        if mood_id in value_texts:
            mood["value_text"] = value_texts[mood_id]
    
    # Write updated moods back
    with open(moods_file, 'w') as f:
        json.dump(moods_data, f, indent=2, ensure_ascii=False)
    
    print("Updated moods.json with value_text fields")

if __name__ == "__main__":
    update_moods_with_values()