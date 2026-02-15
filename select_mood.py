#!/usr/bin/env python3
# 🧠 Intelligent mood selector with entropy target, spiral prevention, and weather/news influence

import json
import random
import sys
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from generate_mood_reason import generate_mood_reason, load_streaks

def load_mood_history(script_dir: Path) -> List[Dict[str, Any]]:
    """Load recent mood history"""
    try:
        with open(script_dir / "mood_history.json", "r") as f:
            data = json.load(f)
            return data.get("history", [])
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def load_moods(script_dir: Path) -> Dict[str, Any]:
    """Load mood definitions"""
    try:
        with open(script_dir / "moods.json", "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print("Error: moods.json not found or invalid", file=sys.stderr)
        sys.exit(1)

def get_recent_moods(mood_history: List[Dict[str, Any]], days: int = 7) -> List[str]:
    """Get moods from the last N days"""
    cutoff_date = date.today() - timedelta(days=days)
    recent_moods = []
    
    for entry in mood_history:
        try:
            entry_date = datetime.strptime(entry["date"], "%Y-%m-%d").date()
            if entry_date >= cutoff_date:
                recent_moods.append(entry["mood"])
        except (KeyError, ValueError):
            continue
    
    return recent_moods

def detect_spiral(mood_history: List[Dict[str, Any]]) -> Tuple[Optional[str], int]:
    """Detect if we're in a mood spiral (same mood multiple days)"""
    if len(mood_history) < 2:
        return None, 0
    
    # Check last few entries for consecutive same moods
    recent_entries = mood_history[-5:]  # Last 5 days max
    if not recent_entries:
        return None, 0
    
    current_mood = recent_entries[-1].get("mood")
    if not current_mood:
        return None, 0
    
    consecutive_count = 1
    for entry in reversed(recent_entries[:-1]):
        if entry.get("mood") == current_mood:
            consecutive_count += 1
        else:
            break
    
    if consecutive_count >= 2:
        return current_mood, consecutive_count
    
    return None, 0

def apply_entropy_target(mood_weights: Dict[str, float], recent_moods: List[str]) -> Dict[str, float]:
    """Apply entropy target - reduce weight of overused moods"""
    mood_counts = {}
    for mood in recent_moods:
        mood_counts[mood] = mood_counts.get(mood, 0) + 1
    
    # If a mood appeared 3+ times in last 7 days, reduce its weight by 50%
    for mood_id, count in mood_counts.items():
        if count >= 3 and mood_id in mood_weights:
            mood_weights[mood_id] *= 0.5
            print(f"  🎯 Entropy target: {mood_id} appeared {count} times recently, reducing weight 50%", file=sys.stderr)
    
    return mood_weights

def apply_weather_influence(mood_weights: Dict[str, float], moods_config: Dict[str, Any], weather: str) -> Dict[str, float]:
    """Apply weather influence to mood weights"""
    weather_influence = moods_config.get("weather_influence", {})
    weather_lower = weather.lower()
    
    # Try to match weather conditions
    weather_match = None
    for condition in weather_influence.keys():
        if condition.lower() in weather_lower:
            weather_match = condition
            break
    
    if weather_match:
        influence = weather_influence[weather_match]
        print(f"  🌤️  Weather influence: {weather_match}", file=sys.stderr)
        
        # Boost certain moods
        for mood_id in influence.get("boost", []):
            if mood_id in mood_weights:
                mood_weights[mood_id] *= 1.3
                print(f"    ↑ Boosting {mood_id} (weather)", file=sys.stderr)
        
        # Dampen certain moods
        for mood_id in influence.get("dampen", []):
            if mood_id in mood_weights:
                mood_weights[mood_id] *= 0.7
                print(f"    ↓ Dampening {mood_id} (weather)", file=sys.stderr)
    
    return mood_weights

def apply_day_of_week_influence(mood_weights: Dict[str, float], moods_config: Dict[str, Any], day_of_week: str) -> Dict[str, float]:
    """Apply day of week influence to mood weights"""
    dow_config = moods_config.get("day_of_week", {})
    multipliers = dow_config.get("multipliers", {}).get(day_of_week.lower(), {})
    
    if multipliers:
        print(f"  📅 Day of week influence: {day_of_week}", file=sys.stderr)
        for mood_id, multiplier in multipliers.items():
            if mood_id != "vibe" and mood_id in mood_weights:
                mood_weights[mood_id] *= multiplier
                arrow = "↑" if multiplier > 1 else "↓" if multiplier < 1 else "→"
                print(f"    {arrow} {mood_id}: {multiplier}x", file=sys.stderr)
    
    return mood_weights

def apply_news_influence(mood_weights: Dict[str, float], moods_config: Dict[str, Any], news_headlines: List[str]) -> Dict[str, float]:
    """Apply news influence to mood weights"""
    news_influence = moods_config.get("news_influence", {})
    
    # Simple keyword matching for news categories
    news_keywords = {
        "tech_breakthrough": ["AI", "breakthrough", "innovation", "discovered", "invented"],
        "political_drama": ["election", "political", "government", "policy", "vote"],
        "crisis_conflict": ["war", "conflict", "crisis", "attack", "emergency"],
        "crypto_market_move": ["bitcoin", "crypto", "blockchain", "ethereum", "trading"],
        "ai_news": ["AI", "artificial intelligence", "machine learning", "OpenAI", "ChatGPT"],
        "feel_good": ["rescued", "helped", "charity", "positive", "celebration", "achievement"],
        "boring_day": []  # Default if nothing else matches
    }
    
    matched_categories = []
    for headline in news_headlines:
        headline_lower = headline.lower()
        for category, keywords in news_keywords.items():
            if any(keyword.lower() in headline_lower for keyword in keywords):
                matched_categories.append(category)
                break
    
    # If no categories matched, consider it a boring day
    if not matched_categories:
        matched_categories = ["boring_day"]
    
    # Apply influence for matched categories
    for category in set(matched_categories):  # Remove duplicates
        if category in news_influence:
            influence = news_influence[category]
            print(f"  📰 News influence: {category}", file=sys.stderr)
            
            # Boost certain moods
            for mood_id in influence.get("boost", []):
                if mood_id in mood_weights:
                    mood_weights[mood_id] *= 1.2
                    print(f"    ↑ Boosting {mood_id} (news)", file=sys.stderr)
            
            # Dampen certain moods
            for mood_id in influence.get("dampen", []):
                if mood_id in mood_weights:
                    mood_weights[mood_id] *= 0.8
                    print(f"    ↓ Dampening {mood_id} (news)", file=sys.stderr)
    
    return mood_weights

def apply_night_summary_influence(mood_weights: Dict[str, float], script_dir: Path) -> List[str]:
    """Apply night summary influence to mood weights and return reason factors"""
    night_summary_file = script_dir / "night_summary.json"
    night_factors = []
    
    try:
        with open(night_summary_file, "r") as f:
            night_summary = json.load(f)
        
        sessions = night_summary.get("sessions", 0)
        productive = night_summary.get("productive", False)
        energy_avg = night_summary.get("energy_avg", "none")
        
        if sessions > 0:
            print(f"  🌙 Night summary influence: {sessions} sessions, {energy_avg} energy, productive={productive}", file=sys.stderr)
            
            if productive and sessions >= 3 and energy_avg in ["high", "medium"]:
                # Productive night: bias toward momentum moods
                if "determined" in mood_weights:
                    mood_weights["determined"] *= 1.3
                    print(f"    ↑ Boosting determined (productive night)", file=sys.stderr)
                if "hyperfocus" in mood_weights:
                    mood_weights["hyperfocus"] *= 1.2
                    print(f"    ↑ Boosting hyperfocus (productive night)", file=sys.stderr)
                night_factors.append("productive night momentum")
                
            elif energy_avg == "low" or (sessions < 3 and energy_avg != "high"):
                # Rough night: bias toward recovery moods
                if "cozy" in mood_weights:
                    mood_weights["cozy"] *= 1.3
                    print(f"    ↑ Boosting cozy (recovery from rough night)", file=sys.stderr)
                if "curious" in mood_weights:
                    mood_weights["curious"] *= 1.2
                    print(f"    ↑ Boosting curious (recovery from rough night)", file=sys.stderr)
                night_factors.append("recovering from rough night")
        
    except (FileNotFoundError, json.JSONDecodeError):
        # No night summary available, no influence
        pass
    
    return night_factors

def select_weighted_mood(mood_weights: Dict[str, float]) -> str:
    """Select a mood using weighted random selection"""
    moods = list(mood_weights.keys())
    weights = list(mood_weights.values())
    
    # Ensure all weights are positive
    min_weight = min(weights)
    if min_weight <= 0:
        weights = [w - min_weight + 0.1 for w in weights]
    
    return random.choices(moods, weights=weights)[0]

def create_spiral_warning(spiral_mood: str, consecutive_days: int) -> str:
    """Create a spiral warning message"""
    if consecutive_days == 2:
        return f"Careful, this is day 2 of {spiral_mood} — might be a spiral"
    elif consecutive_days >= 3:
        return f"Day {consecutive_days} of {spiral_mood} — definitely a spiral, but we're rolling with it"
    return ""

def select_mood(weather: str = "", news_headlines: List[str] = None, location: str = "unknown location") -> Dict[str, Any]:
    """Main mood selection logic"""
    if news_headlines is None:
        news_headlines = []
    
    script_dir = Path(__file__).parent
    moods_config = load_moods(script_dir)
    mood_history = load_mood_history(script_dir)
    streaks = load_streaks(script_dir)
    
    # Get base mood weights
    base_moods = moods_config.get("base_moods", [])
    mood_weights = {}
    for mood in base_moods:
        mood_weights[mood["id"]] = mood.get("weight", 1.0)
    
    print("🧠 Mood Selection Process", file=sys.stderr)
    print("=" * 40, file=sys.stderr)
    
    # Apply entropy target (prevent convergence)
    recent_moods = get_recent_moods(mood_history, days=7)
    print(f"  📊 Recent moods (7 days): {recent_moods}", file=sys.stderr)
    mood_weights = apply_entropy_target(mood_weights, recent_moods)
    
    # Detect mood spiral
    spiral_mood, consecutive_days = detect_spiral(mood_history)
    if spiral_mood and consecutive_days >= 3:
        # Force a different mood
        print(f"  🌀 Spiral detected: {consecutive_days} days of {spiral_mood}, forcing change", file=sys.stderr)
        mood_weights[spiral_mood] = 0.01  # Nearly eliminate the spiral mood
    
    # Apply influences
    day_of_week = datetime.now().strftime('%A')
    mood_weights = apply_day_of_week_influence(mood_weights, moods_config, day_of_week)
    mood_weights = apply_weather_influence(mood_weights, moods_config, weather)
    mood_weights = apply_news_influence(mood_weights, moods_config, news_headlines)
    night_factors = apply_night_summary_influence(mood_weights, script_dir)
    
    # Select mood
    selected_mood_id = select_weighted_mood(mood_weights)
    selected_mood = next(m for m in base_moods if m["id"] == selected_mood_id)
    
    print(f"  🎯 Selected mood: {selected_mood['emoji']} {selected_mood['name']}", file=sys.stderr)
    print("=" * 40, file=sys.stderr)
    
    # Generate mood reason
    mood_reason = generate_mood_reason(
        selected_mood=selected_mood_id,
        weather=weather,
        day_of_week=day_of_week.lower(),
        news_headlines=news_headlines,
        streaks=streaks,
        location=location,
        script_dir=script_dir
    )
    
    # Add night summary context if available
    if night_factors:
        mood_reason = f"{mood_reason} (boosted by {', '.join(night_factors)})"
    
    # Add spiral warning if needed
    if spiral_mood and consecutive_days >= 2 and spiral_mood == selected_mood_id:
        spiral_warning = create_spiral_warning(spiral_mood, consecutive_days)
        mood_reason = f"{mood_reason} {spiral_warning}"
    
    # Create the result
    today_str = date.today().isoformat()
    result = {
        "id": selected_mood["id"],
        "name": selected_mood["name"],
        "emoji": selected_mood["emoji"],
        "description": selected_mood["description"],
        "date": today_str,
        "weather": weather,
        "mood_reason": mood_reason,
        "news_vibes": news_headlines[:5],  # Keep top 5 headlines
        "boosted_traits": selected_mood.get("traits", []),
        "dampened_traits": [],  # Could be filled based on mood selection
        "activity_log": [],
        "energy_score": 0,
        "vibe_score": 0,
        "last_drift": datetime.now().isoformat()
    }
    
    # Add spiral info if applicable
    if spiral_mood and consecutive_days >= 2:
        result["spiral_info"] = {
            "mood": spiral_mood,
            "consecutive_days": consecutive_days,
            "warning": spiral_warning
        }
    
    return result

def main():
    """Command line interface"""
    if len(sys.argv) < 2:
        print("Usage: select_mood.py <weather> [location]")
        sys.exit(1)
    
    weather = sys.argv[1] if len(sys.argv) > 1 else ""
    location = sys.argv[2] if len(sys.argv) > 2 else "unknown location"
    
    # Read news headlines from stdin if available
    news_headlines = []
    try:
        import select
        if select.select([sys.stdin], [], [], 0.0)[0]:
            news_headlines = [line.strip() for line in sys.stdin.readlines() if line.strip()]
    except:
        pass
    
    result = select_mood(weather=weather, news_headlines=news_headlines, location=location)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()