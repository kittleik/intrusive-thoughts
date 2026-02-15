#!/usr/bin/env python3
"""
🌙 Night Summary Generator

Analyzes history.json for night entries (03:00-07:00 today) and creates a summary
for morning mood selection bias. Night productivity influences morning mood choices.
"""

import json
import sys
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

def parse_timestamp(timestamp_str: str) -> Optional[datetime]:
    """Parse various timestamp formats"""
    formats = [
        "%Y-%m-%dT%H:%M:%S%z",  # ISO with timezone
        "%Y-%m-%dT%H:%M:%S+01:00",  # Specific timezone format
        "%Y-%m-%dT%H:%M:%S",     # ISO without timezone
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(timestamp_str, fmt)
        except ValueError:
            continue
    
    print(f"Warning: Could not parse timestamp: {timestamp_str}", file=sys.stderr)
    return None

def is_night_time(dt: datetime) -> bool:
    """Check if datetime falls in night work hours (03:00-07:00)"""
    hour = dt.hour
    return 3 <= hour < 7

def load_history(script_dir: Path) -> List[Dict[str, Any]]:
    """Load history.json"""
    try:
        with open(script_dir / "history.json", "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading history.json: {e}", file=sys.stderr)
        return []

def analyze_night_sessions(history: List[Dict[str, Any]], target_date: date) -> Dict[str, Any]:
    """Analyze night sessions for the given date"""
    night_sessions = []
    
    for entry in history:
        timestamp_str = entry.get("timestamp", "")
        if not timestamp_str:
            continue
            
        dt = parse_timestamp(timestamp_str)
        if not dt:
            continue
            
        # Convert to date for comparison (night sessions are typically early morning)
        entry_date = dt.date()
        
        # Check if this is a night session on the target date
        if entry_date == target_date and is_night_time(dt):
            night_sessions.append({
                "time": dt.strftime("%H:%M"),
                "mood": entry.get("mood", "unknown"),
                "thought_id": entry.get("thought_id", ""),
                "summary": entry.get("summary", ""),
                "energy": entry.get("energy", "medium"),
                "vibe": entry.get("vibe", "neutral")
            })
    
    if not night_sessions:
        return {
            "date": target_date.isoformat(),
            "sessions": 0,
            "productive": False,
            "energy_avg": "none",
            "shipped": [],
            "summary": "No night sessions found"
        }
    
    # Analyze energy levels
    energy_counts = {"high": 0, "medium": 0, "low": 0}
    for session in night_sessions:
        energy = session.get("energy", "medium")
        if energy in energy_counts:
            energy_counts[energy] += 1
    
    # Determine average energy
    total_sessions = len(night_sessions)
    if energy_counts["high"] >= total_sessions * 0.6:
        energy_avg = "high"
    elif energy_counts["low"] >= total_sessions * 0.6:
        energy_avg = "low"
    else:
        energy_avg = "medium"
    
    # Check for productivity indicators
    shipped_items = []
    productivity_keywords = [
        "shipped", "built", "created", "fixed", "implemented", 
        "completed", "finished", "released", "merged", "deployed"
    ]
    
    productive_sessions = 0
    for session in night_sessions:
        summary_lower = session.get("summary", "").lower()
        thought_id = session.get("thought_id", "").lower()
        
        # Look for GitHub issue patterns (e.g., "#44", "#48-53")
        import re
        issue_matches = re.findall(r'#(\d+(?:-\d+)?)', session.get("summary", ""))
        shipped_items.extend([f"#{match}" for match in issue_matches])
        
        # Count productive sessions
        if any(keyword in summary_lower or keyword in thought_id for keyword in productivity_keywords):
            productive_sessions += 1
    
    # Consider it productive if 3+ sessions OR mostly high energy
    productive = (
        total_sessions >= 3 and (
            productive_sessions >= total_sessions * 0.5 or 
            energy_avg == "high"
        )
    )
    
    # Create overall summary
    if total_sessions >= 4 and energy_avg == "high":
        summary = f"Very active night: {total_sessions} sessions, high energy work"
    elif productive:
        summary = f"Productive night: {total_sessions} sessions, steady progress"
    elif total_sessions >= 3:
        summary = f"Busy night: {total_sessions} sessions, mixed outcomes"
    elif energy_avg == "low":
        summary = f"Quiet night: {total_sessions} session{'s' if total_sessions > 1 else ''}, low energy"
    else:
        summary = f"Light night work: {total_sessions} session{'s' if total_sessions > 1 else ''}"
    
    # Add specific work mentions if we found them
    if shipped_items:
        summary += f", shipped {', '.join(shipped_items[:3])}"  # Limit to first 3 items
    
    return {
        "date": target_date.isoformat(),
        "sessions": total_sessions,
        "productive": productive,
        "energy_avg": energy_avg,
        "shipped": list(set(shipped_items))[:5],  # Unique items, max 5
        "summary": summary,
        "raw_sessions": night_sessions  # Include raw data for debugging
    }

def main():
    """Generate night summary for today or specified date"""
    script_dir = Path(__file__).parent
    
    # Use today's date or parse from command line
    if len(sys.argv) > 1:
        try:
            target_date = datetime.strptime(sys.argv[1], "%Y-%m-%d").date()
        except ValueError:
            print(f"Invalid date format: {sys.argv[1]}. Use YYYY-MM-DD", file=sys.stderr)
            sys.exit(1)
    else:
        target_date = date.today()
    
    # Load and analyze history
    history = load_history(script_dir)
    night_summary = analyze_night_sessions(history, target_date)
    
    # Write summary to file
    output_file = script_dir / "night_summary.json"
    with open(output_file, "w") as f:
        json.dump(night_summary, f, indent=2)
    
    print(f"📊 Night Summary for {target_date.isoformat()}:", file=sys.stderr)
    print(f"   Sessions: {night_summary['sessions']}", file=sys.stderr)
    print(f"   Productive: {night_summary['productive']}", file=sys.stderr)
    print(f"   Energy: {night_summary['energy_avg']}", file=sys.stderr)
    print(f"   Summary: {night_summary['summary']}", file=sys.stderr)
    if night_summary['shipped']:
        print(f"   Shipped: {', '.join(night_summary['shipped'])}", file=sys.stderr)
    
    # Also output JSON for piping
    print(json.dumps(night_summary, indent=2))

if __name__ == "__main__":
    main()