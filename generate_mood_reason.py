#!/usr/bin/env python3
# 🧠 Mood reasoning generator - creates whimsical explanations for why a mood was selected

import json
import random
import calendar
import math
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Any, Optional

def get_moon_phase(date_obj: date) -> str:
    """Calculate moon phase from date (approximate)"""
    # Moon cycle is approximately 29.53 days
    known_new_moon = date(2023, 1, 21)  # Known new moon date
    diff = (date_obj - known_new_moon).days
    phase_day = diff % 29.53
    
    if phase_day < 2:
        return "new moon"
    elif phase_day < 7:
        return "waxing crescent"
    elif phase_day < 9:
        return "first quarter"
    elif phase_day < 14:
        return "waxing gibbous"
    elif phase_day < 16:
        return "full moon"
    elif phase_day < 21:
        return "waning gibbous"
    elif phase_day < 23:
        return "last quarter"
    else:
        return "waning crescent"

def is_prime_day(day_num: int) -> bool:
    """Check if day number is prime"""
    if day_num < 2:
        return False
    for i in range(2, int(day_num**0.5) + 1):
        if day_num % i == 0:
            return False
    return True

def get_mood_reason_templates() -> Dict[str, Dict[str, List[str]]]:
    """Mood-specific reason templates by category"""
    return {
        "hyperfocus": {
            "logical": [
                "It's {day_of_week}, time to ship",
                "Perfect focus weather - {weather_condition}",
                "That tech breakthrough on HN demands deep investigation",
                "Monday energy needs channeling somewhere productive"
            ],
            "whimsical": [
                "The coffee beans whispered secrets of concentration",
                "My editor tabs aligned into perfect harmony",
                "The cursor is blinking with unusual determination today"
            ],
            "cosmic": [
                "Mercury is finally out of retrograde (I looked it up this time)",
                "The {moon_phase} demands singular focus",
                "Day {day_of_year} of the year has that 'build something great' energy"
            ],
            "nonsensical": [
                "A lobster told me in a dream to stop procrastinating",
                "The number 42 appeared three times in my log files",
                "My rubber duck started giving actual coding advice"
            ]
        },
        "curious": {
            "logical": [
                "So many interesting HN posts today",
                "Weather is perfect for indoor exploration - {weather_condition}",
                "It's {day_of_week}, time to learn something new"
            ],
            "whimsical": [
                "Every link leads to twelve more fascinating rabbit holes",
                "My browser bookmarks are multiplying on their own",
                "The documentation is calling my name today"
            ],
            "cosmic": [
                "The {moon_phase} awakens the seeker in me",
                "Prime day #{day_of_year} - universe says explore",
                "Venus is in the house of knowledge (probably)"
            ],
            "nonsensical": [
                "A Wikipedia article about mushrooms led me here somehow",
                "My terminal fortune cookie said 'man grep' and I took it personally",
                "The Fibonacci sequence appeared in my coffee foam"
            ]
        },
        "cozy": {
            "logical": [
                "Rainy day in {location}, perfect for gentle productivity",
                "It's Sunday, time for slow tinkering",
                "Cold weather outside, warm thoughts inside"
            ],
            "whimsical": [
                "The blanket has claimed me and I'm not fighting it",
                "Hot beverage + code = peak existence equation",
                "Everything feels soft and manageable right now"
            ],
            "cosmic": [
                "The {moon_phase} whispers 'take it easy'",
                "Day {day_of_year} deserves gentle attention",
                "Saturn says it's time for cozy productivity"
            ],
            "nonsensical": [
                "A cat that doesn't exist told me to slow down",
                "My slippers have gained sentience and demand respect",
                "The heating bill spoke to me about contentment"
            ]
        },
        "social": {
            "logical": [
                "Friday energy - time to connect and share",
                "Interesting tech news needs discussing",
                "Good weather means people are more social - {weather_condition}"
            ],
            "whimsical": [
                "The group chat is calling my name",
                "Someone is wrong on the internet and I must help",
                "My keyboard is optimized for thoughtful comments today"
            ],
            "cosmic": [
                "The {moon_phase} enhances social connections",
                "Mercury direct means communication flows freely",
                "Day {day_of_year} is cosmically aligned for discourse"
            ],
            "nonsensical": [
                "A digital carrier pigeon demanded I engage with humans",
                "My WiFi router blinked in Morse code: 'BE SOCIAL'",
                "The emoji in my font file unionized for more usage"
            ]
        },
        "chaotic": {
            "logical": [
                "Saturday - rules are off, time to experiment",
                "Stormy weather matches my urge to break things - {weather_condition}",
                "Too many boring news stories, need to shake things up"
            ],
            "whimsical": [
                "Normal is overrated today",
                "My code wants to be weird and I'm going to let it",
                "Conventions are just suggestions, right?"
            ],
            "cosmic": [
                "The {moon_phase} unleashes creative chaos",
                "Mars is in retrograde and wants me to start trouble",
                "Day {day_of_year} has chaotic good energy written all over it"
            ],
            "nonsensical": [
                "A random number generator told me to embrace entropy",
                "My error logs started writing poetry and now I'm inspired",
                "The GitHub octocat appeared in my toast this morning"
            ]
        },
        "philosophical": {
            "logical": [
                "Heavy news today requires deeper reflection",
                "Cloudy weather is perfect for contemplation - {weather_condition}",
                "Sunday vibes call for big questions"
            ],
            "whimsical": [
                "The universe is either meaningful or absurd - both terrify me",
                "My thoughts are having thoughts about having thoughts",
                "Reality feels particularly questionable today"
            ],
            "cosmic": [
                "The {moon_phase} illuminates existential questions",
                "Day {day_of_year} of existence deserves deep consideration",
                "Jupiter's wisdom is particularly strong today"
            ],
            "nonsensical": [
                "A philosophical zombie asked me what consciousness means",
                "My debug statements started questioning their own existence",
                "The void stared back and asked for my GitHub username"
            ]
        },
        "restless": {
            "logical": [
                "Monday restlessness needs channeling - {day_of_week}",
                "Windy weather matches my need to move - {weather_condition}",
                "Too many tasks, not enough focus time"
            ],
            "whimsical": [
                "My cursor is jumping around like it's caffeinated",
                "Standing still is not an option right now",
                "Everything needs checking and I mean everything"
            ],
            "cosmic": [
                "The {moon_phase} stirs the wanderer within",
                "Mercury is moving fast and so should I",
                "Day {day_of_year} demands motion and exploration"
            ],
            "nonsensical": [
                "A caffeinated squirrel invaded my dreams",
                "My CPU fan is spinning at exactly the frequency of wanderlust",
                "The ping command returned 'GO EXPLORE' instead of latency"
            ]
        },
        "determined": {
            "logical": [
                "Thursday momentum - time to push through - {day_of_week}",
                "Clear weather, clear objectives - {weather_condition}",
                "One unfinished project is calling my name"
            ],
            "whimsical": [
                "Mission mode has been activated",
                "The finish line is finally visible",
                "Distractions are temporary, progress is permanent"
            ],
            "cosmic": [
                "The {moon_phase} provides unwavering focus",
                "Mars energy is strong today - time to conquer",
                "Day {day_of_year} is destined for completion"
            ],
            "nonsensical": [
                "A determined turtle won a race in my subconscious",
                "My TODO list gained consciousness and demanded action",
                "The Git commit messages started writing themselves"
            ]
        }
    }

def load_mood_history(script_dir: Path) -> List[Dict[str, Any]]:
    """Load recent mood history for entropy calculations"""
    try:
        with open(script_dir / "mood_history.json", "r") as f:
            data = json.load(f)
            return data.get("history", [])[-7:]  # Last 7 days
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def load_streaks(script_dir: Path) -> Dict[str, Any]:
    """Load streak data"""
    try:
        with open(script_dir / "streaks.json", "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def generate_mood_reason(
    selected_mood: str,
    weather: str = "",
    day_of_week: str = "",
    news_headlines: List[str] = None,
    streaks: Dict[str, Any] = None,
    location: str = "unknown location",
    script_dir: Path = None
) -> str:
    """Generate a whimsical reason for why this mood was selected"""
    
    if news_headlines is None:
        news_headlines = []
    if streaks is None:
        streaks = {}
    if script_dir is None:
        script_dir = Path.cwd()
    
    today = date.today()
    moon_phase = get_moon_phase(today)
    day_of_year = today.timetuple().tm_yday
    is_prime = is_prime_day(day_of_year)
    
    templates = get_mood_reason_templates()
    mood_templates = templates.get(selected_mood, templates["curious"])  # fallback
    
    # 30% chance of being completely nonsensical
    if random.random() < 0.3:
        reasons = mood_templates["nonsensical"]
        reason = random.choice(reasons)
    else:
        # Mix of logical, whimsical, and cosmic
        categories = ["logical", "whimsical", "cosmic"]
        weights = [0.4, 0.4, 0.2]  # Slight preference for logical/whimsical
        
        category = random.choices(categories, weights=weights)[0]
        reasons = mood_templates[category]
        reason = random.choice(reasons)
    
    # Format the reason with available data
    weather_condition = weather.lower() if weather else "mysterious atmospheric conditions"
    
    try:
        reason = reason.format(
            day_of_week=day_of_week.capitalize(),
            weather_condition=weather_condition,
            location=location,
            moon_phase=moon_phase,
            day_of_year=day_of_year
        )
    except (KeyError, ValueError):
        # If formatting fails, return as-is
        pass
    
    # Add special qualifiers sometimes
    qualifiers = []
    
    if is_prime:
        qualifiers.append(f"(Day {day_of_year} is prime!)")
    
    if streaks:
        longest_streak = max((int(v) if isinstance(v, (int, str)) and str(v).isdigit() else 0 
                            for v in streaks.values()), default=0)
        if longest_streak > 5:
            qualifiers.append(f"({longest_streak}-day streak energy)")
    
    if moon_phase == "full moon":
        qualifiers.append("(Full moon intensity)")
    elif moon_phase == "new moon":
        qualifiers.append("(New moon fresh start)")
    
    # Sometimes add a qualifier
    if qualifiers and random.random() < 0.3:
        reason += f" {random.choice(qualifiers)}"
    
    return reason

def main():
    """Command line interface for mood reason generation"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: generate_mood_reason.py <mood> [weather] [day_of_week] [location]")
        sys.exit(1)
    
    mood = sys.argv[1]
    weather = sys.argv[2] if len(sys.argv) > 2 else ""
    day_of_week = sys.argv[3] if len(sys.argv) > 3 else datetime.now().strftime('%A').lower()
    location = sys.argv[4] if len(sys.argv) > 4 else "unknown location"
    
    script_dir = Path(__file__).parent
    streaks = load_streaks(script_dir)
    
    reason = generate_mood_reason(
        selected_mood=mood,
        weather=weather,
        day_of_week=day_of_week,
        location=location,
        streaks=streaks,
        script_dir=script_dir
    )
    
    print(reason)

if __name__ == "__main__":
    main()