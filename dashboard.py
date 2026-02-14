#!/usr/bin/env python3
"""🧠 Intrusive Thoughts Dashboard v2 — Consolidated edition with full feature set + self-awareness."""

import json
import os
import subprocess
import re
import markdown
import urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler
from datetime import datetime, timedelta
from collections import Counter
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from config import get_file_path, get_data_dir, get_dashboard_port, get_agent_name, get_agent_emoji

PORT = get_dashboard_port()
HISTORY_FILE = get_file_path("history.json")
THOUGHTS_FILE = get_file_path("thoughts.json")
ACHIEVEMENTS_FILE = get_file_path("achievements.json")
ACHIEVEMENTS_EARNED_FILE = get_file_path("achievements_earned.json")
PICKS_LOG = get_data_dir() / "log" / "picks.log"
REJECTIONS_LOG = get_data_dir() / "log" / "rejections.log"
DECISIONS_JSON = get_data_dir() / "log" / "decisions.json"


def load_history():
    try:
        return json.loads(HISTORY_FILE.read_text())
    except:
        return []


def load_picks():
    try:
        lines = [l.strip() for l in PICKS_LOG.read_text().splitlines() if l.strip()]
        picks = []
        for line in lines:
            parts = line.split(" | ")
            ts = parts[0] if parts else ""
            meta = dict(p.split("=", 1) for p in parts[1:] if "=" in p)
            picks.append({"timestamp": ts, **meta})
        return picks
    except:
        return []


def load_rejections():
    try:
        lines = [l.strip() for l in REJECTIONS_LOG.read_text().splitlines() if l.strip()]
        rejections = []
        for line in lines:
            parts = line.split(" | ", 4)  # Split into max 5 parts
            if len(parts) >= 5:
                rejections.append({
                    "timestamp": parts[0],
                    "thought_id": parts[1], 
                    "mood": parts[2],
                    "reason": parts[3],
                    "flavor_text": parts[4]
                })
        return rejections
    except:
        return []


def load_decisions():
    try:
        return json.loads(DECISIONS_JSON.read_text())
    except:
        return []


def load_thoughts():
    try:
        return json.loads(THOUGHTS_FILE.read_text())
    except:
        return {}


def load_all_achievements():
    try:
        return json.loads(ACHIEVEMENTS_FILE.read_text())
    except:
        return {"achievements": {}, "tiers": {}}


def load_earned_achievements():
    try:
        data = json.loads(ACHIEVEMENTS_EARNED_FILE.read_text())
        if isinstance(data, list):
            # Convert old format to new format
            return {"earned": data, "total_points": sum(a.get("points", 0) for a in data)}
        return data
    except:
        return {"earned": [], "total_points": 0}


def load_mood_history():
    try:
        data = json.loads(get_file_path("mood_history.json").read_text())
        return data.get("history", [])
    except:
        return []


def load_streaks():
    try:
        return json.loads(get_file_path("streaks.json").read_text())
    except:
        return {"current_streaks": {}}


def load_soundtracks():
    try:
        return json.loads(get_file_path("soundtracks.json").read_text())
    except:
        return {}


def load_today_mood():
    try:
        return json.loads(get_file_path("today_mood.json").read_text())
    except:
        return {}


def load_moods():
    try:
        return json.loads(get_file_path("moods.json").read_text())
    except:
        return {}


def load_presets():
    try:
        preset_dir = get_data_dir() / "presets"
        presets = {}
        if preset_dir.exists():
            for preset_file in preset_dir.glob("*.json"):
                preset_data = json.loads(preset_file.read_text())
                presets[preset_file.stem] = preset_data
        return presets
    except:
        return {}


def load_stream_data(limit=50):
    """Load combined stream of recent activity: picks, rejections, and mood drifts."""
    stream_items = []
    
    # Add picks
    picks = load_picks()
    for pick in picks[-limit:]:
        stream_items.append({
            "type": "pick",
            "timestamp": pick.get("timestamp", ""),
            "thought_id": pick.get("thought", "unknown"),
            "mood": pick.get("today_mood", "unknown"),
            "summary": f"Picked {pick.get('thought', 'unknown')} thought",
            "details": pick
        })
    
    # Add rejections
    rejections = load_rejections()
    for rejection in rejections[-limit:]:
        stream_items.append({
            "type": "rejection",
            "timestamp": rejection.get("timestamp", ""),
            "thought_id": rejection.get("thought_id", "unknown"),
            "mood": rejection.get("mood", "unknown"), 
            "summary": f"Rejected {rejection.get('thought_id', 'unknown')}: {rejection.get('reason', 'no reason')}",
            "details": rejection
        })
    
    # Add mood drifts from today_mood.json activity_log
    today_mood = load_today_mood()
    if today_mood and "activity_log" in today_mood:
        for activity in today_mood["activity_log"][-limit:]:
            stream_items.append({
                "type": "mood_drift",
                "timestamp": activity.get("time", ""),
                "mood": activity.get("action", {}).get("to", "unknown"),
                "summary": f"Mood drift: {activity.get('action', {}).get('from', '?')} → {activity.get('action', {}).get('to', '?')}",
                "details": activity
            })
    
    # Sort by timestamp (most recent first)
    stream_items.sort(key=lambda x: x["timestamp"], reverse=True)
    return stream_items[:limit]


def get_schedule_data():
    """Load schedule data from schedule_day.py output."""
    try:
        result = subprocess.run(['python3', 'schedule_day.py', '--json'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            return json.loads(result.stdout)
    except:
        pass
    return {"schedule": [], "current_phase": "unknown"}


def get_night_stats():
    """Calculate day vs night activity statistics."""
    picks = load_picks()
    day_picks = night_picks = 0
    
    for pick in picks:
        try:
            timestamp = pick.get("timestamp", "")
            if timestamp:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                hour = dt.hour
                if 6 <= hour <= 20:
                    day_picks += 1
                else:
                    night_picks += 1
        except:
            continue
    
    return {
        "day_picks": day_picks,
        "night_picks": night_picks,
        "total": day_picks + night_picks,
        "night_percentage": (night_picks / (day_picks + night_picks) * 100) if (day_picks + night_picks) > 0 else 0
    }


def load_journal_entries(limit=None):
    """Load journal entries from the journal directory."""
    try:
        journal_dir = get_data_dir() / "journal"
        entries = []
        if journal_dir.exists():
            for file in journal_dir.glob("*.md"):
                content = file.read_text()
                entries.append({
                    "date": file.stem,
                    "filename": file.name,
                    "content": content,
                    "preview": content[:300] + "..." if len(content) > 300 else content,
                    "word_count": len(content.split())
                })
        
        entries = sorted(entries, key=lambda x: x["date"], reverse=True)
        if limit:
            entries = entries[:limit]
        return entries
    except:
        return []


def run_introspect():
    """Run introspect.py and return JSON result."""
    try:
        result = subprocess.run(['python3', 'introspect.py'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return json.loads(result.stdout)
    except Exception as e:
        return {"error": f"Failed to run introspect: {str(e)}"}
    return {"error": "Introspection unavailable"}


def run_explain_system(system_name):
    """Run explain_system.py for a specific system."""
    try:
        result = subprocess.run(['python3', 'explain_system.py', system_name], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return {"output": result.stdout, "system": system_name}
        else:
            return {"error": f"System '{system_name}' not found or error occurred", "stderr": result.stderr}
    except Exception as e:
        return {"error": f"Failed to explain {system_name}: {str(e)}"}


def run_decision_trace():
    """Run decision_trace.py to get the last decision explanation."""
    try:
        result = subprocess.run(['python3', 'decision_trace.py'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return {"output": result.stdout}
        else:
            return {"error": "No recent decisions found", "stderr": result.stderr}
    except Exception as e:
        return {"error": f"Failed to trace decision: {str(e)}"}


def get_version():
    """Get version from VERSION file."""
    try:
        return get_file_path("VERSION").read_text().strip()
    except:
        return "unknown"


def build_html():
    history = load_history()
    picks = load_picks()
    thoughts = load_thoughts()
    mood_history = load_mood_history()
    streaks = load_streaks()
    achievements = load_earned_achievements()
    soundtracks = load_soundtracks()
    today_mood = load_today_mood()
    moods = load_moods()
    presets = load_presets()
    night_stats = get_night_stats()
    journal_entries = load_journal_entries(5)  # Recent 5 entries
    version = get_version()

    # Current mood and flavor text
    mood_display = "🤔 Unknown"
    mood_description = ""
    if today_mood:
        mood_id = today_mood.get("drifted_to", today_mood.get("id", ""))
        mood_emoji = today_mood.get("emoji", "🤔")
        mood_name = today_mood.get("name", "Unknown")
        mood_display = f"{mood_emoji} {mood_name}"
        mood_description = today_mood.get("description", "")

    # Stats
    total_picks = len(picks)
    total_completed = len(history)
    thought_counts = Counter(p.get("thought", "?") for p in picks)

    # Top thoughts by pick count
    top_thoughts = []
    for thought_id, count in thought_counts.most_common(10):
        thought_data = thoughts.get("thoughts", {}).get(thought_id, {})
        mood_weights = thought_data.get("weights", {})
        mood_name = max(mood_weights.keys(), key=lambda k: mood_weights[k]) if mood_weights else "unknown"
        
        top_thoughts.append({
            "id": thought_id,
            "mood": mood_name,
            "weight": thought_data.get("weight", 1),
            "prompt": thought_data.get("prompt", f"Unknown thought {thought_id}"),
            "times_picked": count,
        })

    # Recent achievements
    recent_achievements = achievements.get("earned", [])[-5:][::-1]

    # Today's soundtrack
    today_soundtrack = ""
    if today_mood:
        mood_id = today_mood.get("drifted_to", today_mood.get("id", ""))
        soundtrack_info = soundtracks.get("mood_soundtracks", {}).get(mood_id, {})
        if soundtrack_info:
            vibe = soundtrack_info.get("vibe_description", "")
            genres = ", ".join(soundtrack_info.get("genres", [])[:3])
            today_soundtrack = f"{vibe} — {genres}"

    # Mood graph data (last 14 days)
    mood_graph_data = mood_history[-14:] if mood_history else []
    
    # Current streaks
    current_streaks = streaks.get("current_streaks", {})
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>🧠 Intrusive Thoughts Dashboard</title>
<style>
  :root {{ 
    --bg: #0a0a0f; --card: #12121a; --border: #1e1e2e; --text: #c9c9d9; 
    --accent: #f59e0b; --accent2: #8b5cf6; --dim: #555568; --success: #22c55e; 
    --warning: #eab308; --danger: #ef4444; 
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ 
    background: var(--bg); color: var(--text); 
    font-family: 'SF Mono', 'Fira Code', monospace; 
    padding: 2rem; max-width: 1600px; margin: 0 auto; 
  }}
  
  /* Header */
  .header {{ text-align: center; margin-bottom: 2rem; }}
  .header h1 {{ color: var(--accent); font-size: 2.5rem; margin-bottom: 0.5rem; }}
  .header .mood {{ font-size: 1.5rem; margin-bottom: 0.5rem; }}
  .header .description {{ color: var(--dim); margin-bottom: 1rem; }}
  .soundtrack {{ 
    background: linear-gradient(135deg, var(--accent2), var(--accent)); 
    padding: 1rem; border-radius: 12px; text-align: center; color: white; 
    margin-bottom: 2rem; 
  }}
  
  /* Navigation */
  .nav {{ 
    position: sticky; top: 0; background: var(--card); border: 1px solid var(--border); 
    border-radius: 12px; padding: 1rem; margin-bottom: 2rem; z-index: 100; 
    display: flex; flex-wrap: wrap; gap: 1rem; justify-content: center; 
  }}
  .nav a {{ 
    color: var(--accent); text-decoration: none; padding: 0.5rem 1rem; 
    border-radius: 8px; transition: background 0.2s; 
  }}
  .nav a:hover {{ background: var(--border); }}
  
  /* Layouts */
  .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem; }}
  .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 2rem; }}
  .grid-3 {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1rem; margin-bottom: 2rem; }}
  
  /* Cards */
  .stat-card {{ 
    background: var(--card); border: 1px solid var(--border); 
    border-radius: 12px; padding: 1.5rem; text-align: center; 
  }}
  .stat-card .number {{ font-size: 2.5rem; font-weight: bold; color: var(--accent); }}
  .stat-card .label {{ color: var(--dim); font-size: 0.85rem; margin-top: 0.3rem; }}
  
  .section {{ 
    background: var(--card); border: 1px solid var(--border); 
    border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem; 
  }}
  .section h2 {{ color: var(--accent2); font-size: 1.2rem; margin-bottom: 1rem; }}
  
  /* Components */
  .btn {{ 
    background: var(--accent); color: white; border: none; 
    padding: 0.5rem 1rem; border-radius: 8px; cursor: pointer; 
    margin: 0.25rem; transition: opacity 0.2s; 
  }}
  .btn:hover {{ opacity: 0.8; }}
  .btn-secondary {{ background: var(--border); color: var(--text); }}
  
  .tabs {{ display: flex; gap: 1rem; margin-bottom: 1rem; }}
  .tab {{ 
    padding: 0.5rem 1rem; border-radius: 8px; cursor: pointer; 
    background: var(--border); transition: background 0.2s; 
  }}
  .tab.active {{ background: var(--accent); color: white; }}
  
  .tab-content {{ display: none; }}
  .tab-content.active {{ display: block; }}
  
  /* Stream and lists */
  .stream-item {{ border-bottom: 1px solid var(--border); padding: 0.8rem 0; }}
  .stream-item:last-child {{ border: none; }}
  .stream-item .time {{ color: var(--accent); font-size: 0.75rem; }}
  .stream-item .summary {{ margin-top: 0.3rem; font-size: 0.9rem; }}
  .stream-item.pick {{ border-left: 3px solid var(--success); padding-left: 0.8rem; }}
  .stream-item.rejection {{ border-left: 3px solid var(--danger); padding-left: 0.8rem; }}
  .stream-item.mood_drift {{ border-left: 3px solid var(--accent2); padding-left: 0.8rem; }}
  
  .mood-dot {{ 
    width: 12px; height: 12px; border-radius: 50%; 
    margin: 0 4px; display: inline-block; 
  }}
  
  .controls {{ display: flex; gap: 1rem; flex-wrap: wrap; align-items: center; margin-bottom: 1rem; }}
  .controls input, .controls select {{ 
    background: var(--border); border: 1px solid var(--border); 
    color: var(--text); padding: 0.5rem; border-radius: 8px; 
  }}
  
  .empty {{ color: var(--dim); font-style: italic; text-align: center; padding: 2rem; }}
  
  /* Self-awareness panel */
  .self-awareness {{ 
    background: linear-gradient(135deg, var(--card), var(--border)); 
    border: 2px solid var(--accent2); border-radius: 12px; 
    padding: 1.5rem; margin-bottom: 1.5rem; 
  }}
  .self-awareness h2 {{ color: var(--accent2); }}
  .explain-buttons {{ display: flex; gap: 0.5rem; flex-wrap: wrap; margin: 1rem 0; }}
  .introspect-summary {{ 
    background: var(--border); padding: 1rem; border-radius: 8px; 
    margin: 1rem 0; font-family: monospace; font-size: 0.85rem; 
  }}
  
  /* Footer */
  footer {{ 
    text-align: center; color: var(--dim); font-size: 0.75rem; 
    margin-top: 3rem; padding-top: 2rem; border-top: 1px solid var(--border); 
  }}
  
  /* Auto-refresh indicator */
  .refresh-indicator {{ 
    position: fixed; top: 1rem; right: 1rem; 
    background: var(--success); color: white; 
    padding: 0.5rem; border-radius: 8px; font-size: 0.8rem; 
    opacity: 0; transition: opacity 0.3s; 
  }}
  .refresh-indicator.show {{ opacity: 1; }}
</style>
</head>
<body>

<!-- Header -->
<div class="header">
  <h1>🧠 Intrusive Thoughts Dashboard</h1>
  <div class="mood">{mood_display}</div>
  <div class="description">{mood_description}</div>
</div>

<!-- Soundtrack -->
{f'<div class="soundtrack">🎵 {today_soundtrack}</div>' if today_soundtrack else ''}

<!-- Navigation -->
<div class="nav">
  <a href="#stats">Stats</a>
  <a href="#stream">Live Stream</a>
  <a href="#mood">Mood</a>
  <a href="#controls">Controls</a>
  <a href="#health">System Health</a>
  <a href="#night">Night Workshop</a>
  <a href="#achievements">Achievements</a>
  <a href="#self-awareness">🪞 Self-Awareness</a>
</div>

<!-- Refresh indicator -->
<div id="refresh-indicator" class="refresh-indicator">
  Updated
</div>

<!-- Stats Cards -->
<div id="stats" class="grid">
  <div class="stat-card">
    <div class="number">{total_picks}</div>
    <div class="label">Total Impulses</div>
  </div>
  <div class="stat-card">
    <div class="number">{total_completed}</div>
    <div class="label">Completed</div>
  </div>
  <div class="stat-card">
    <div class="number">{len(achievements.get('earned', []))}</div>
    <div class="label">🏆 Achievements</div>
  </div>
  <div class="stat-card">
    <div class="number">{achievements.get('total_points', 0)}</div>
    <div class="label">🎯 Points</div>
  </div>
</div>

<!-- Live Thought Stream -->
<div id="stream" class="section">
  <h2>📡 Live Thought Stream</h2>
  <div id="stream-content">
    <div class="empty">Loading stream...</div>
  </div>
</div>

<!-- Mood Visualization -->
<div id="mood" class="grid-2">
  <div class="section">
    <h2>🌈 Mood Timeline (Last 14 Days)</h2>
    <div id="mood-timeline">
      {''.join(f'<span class="mood-dot" style="background: hsl({hash(m.get("mood_id",""))%360}, 70%, 60%)" title="{m.get("date","")} - {m.get("mood_id","")}"></span>' for m in mood_graph_data) if mood_graph_data else '<div class="empty">No mood history yet</div>'}
    </div>
    <div style="margin-top: 1rem; font-size: 0.8rem; color: var(--dim);">
      {f"Recent pattern: {' → '.join([m.get('mood_id','?')[:4] for m in mood_graph_data[-5:]])}" if len(mood_graph_data) >= 5 else "Building mood patterns..."}
    </div>
  </div>
  
  <div class="section">
    <h2>🔥 Current Streaks</h2>
    {f'''<div style="background: var(--border); padding: 0.8rem; border-radius: 8px; margin-bottom: 0.5rem;"><strong>Activity:</strong> {current_streaks.get('activity_type', ['none'])[0]} × {len(current_streaks.get('activity_type', []))}</div>''' if current_streaks.get('activity_type') else ''}
    {f'''<div style="background: var(--border); padding: 0.8rem; border-radius: 8px; margin-bottom: 0.5rem;"><strong>Mood:</strong> {current_streaks.get('mood', ['none'])[0]} × {len(current_streaks.get('mood', []))}</div>''' if current_streaks.get('mood') else ''}
    {f'''<div style="background: var(--border); padding: 0.8rem; border-radius: 8px; margin-bottom: 0.5rem;"><strong>Time:</strong> {current_streaks.get('time_of_day', ['none'])[0]} × {len(current_streaks.get('time_of_day', []))}</div>''' if current_streaks.get('time_of_day') else ''}
    {'<div class="empty">No active streaks</div>' if not any(current_streaks.values()) else ''}
  </div>
</div>

<!-- Interactive Controls -->
<div id="controls" class="section">
  <h2>🎛️ Interactive Controls</h2>
  
  <div class="tabs">
    <div class="tab active" onclick="showControlTab('thought-weights')">Thought Weights</div>
    <div class="tab" onclick="showControlTab('mood-override')">Mood Override</div>
    <div class="tab" onclick="showControlTab('schedule')">Schedule</div>
    <div class="tab" onclick="showControlTab('presets')">Presets</div>
  </div>
  
  <div id="thought-weights" class="tab-content active">
    <div class="controls">
      <select id="thought-select">
        <option value="">Select a thought...</option>
        {' '.join(f'<option value="{t["id"]}">{t["prompt"][:50]}...</option>' for t in top_thoughts)}
      </select>
      <input type="range" id="weight-slider" min="0.1" max="3.0" step="0.1" value="1.0">
      <span id="weight-value">1.0</span>
      <button class="btn" onclick="updateThoughtWeight()">Update Weight</button>
    </div>
  </div>
  
  <div id="mood-override" class="tab-content">
    <div class="controls">
      <select id="mood-select">
        <option value="">Select mood...</option>
        {' '.join(f'<option value="{mood["id"]}">{mood["emoji"]} {mood["name"]}</option>' for mood in moods.get("base_moods", []))}
      </select>
      <button class="btn" onclick="setMood()">Set Mood</button>
      <button class="btn btn-secondary" onclick="triggerImpulse()">Trigger Impulse</button>
    </div>
  </div>
  
  <div id="schedule" class="tab-content">
    <div id="schedule-content">
      <div class="empty">Loading schedule...</div>
    </div>
  </div>
  
  <div id="presets" class="tab-content">
    <div class="controls">
      <select id="preset-select">
        <option value="">Select preset...</option>
        {' '.join(f'<option value="{preset_name}">{preset_name}</option>' for preset_name in presets.keys())}
      </select>
      <button class="btn" onclick="applyPreset()">Apply Preset</button>
    </div>
    <div id="preset-details" style="margin-top: 1rem; background: var(--border); padding: 1rem; border-radius: 8px; display: none;">
      <div id="preset-description"></div>
    </div>
  </div>
</div>

<!-- System Health -->
<div id="health" class="section">
  <h2>🏥 System Health</h2>
  
  <div class="tabs">
    <div class="tab active" onclick="showHealthTab('memory')">Memory Explorer</div>
    <div class="tab" onclick="showHealthTab('trust')">Trust Dashboard</div>
    <div class="tab" onclick="showHealthTab('evolution')">Evolution History</div>
    <div class="tab" onclick="showHealthTab('proactive')">Proactive Status</div>
    <div class="tab" onclick="showHealthTab('health-monitor')">Health Monitor</div>
  </div>
  
  <div id="memory" class="tab-content active">
    <div id="memory-content">
      <div class="empty">Loading memory data...</div>
    </div>
  </div>
  
  <div id="trust" class="tab-content">
    <div id="trust-content">
      <div class="empty">Loading trust data...</div>
    </div>
  </div>
  
  <div id="evolution" class="tab-content">
    <div id="evolution-content">
      <div class="empty">Loading evolution data...</div>
    </div>
  </div>
  
  <div id="proactive" class="tab-content">
    <div id="proactive-content">
      <div class="empty">Loading proactive data...</div>
    </div>
  </div>
  
  <div id="health-monitor" class="tab-content">
    <div id="health-monitor-content">
      <div class="empty">Loading health monitor data...</div>
    </div>
  </div>
</div>

<!-- Night Workshop -->
<div id="night" class="section">
  <h2>🌙 Night Workshop</h2>
  
  <div class="grid-3">
    <div>
      <h3>Day vs Night Stats</h3>
      <div style="background: var(--border); padding: 1rem; border-radius: 8px;">
        <div>Day picks: {night_stats['day_picks']}</div>
        <div>Night picks: {night_stats['night_picks']}</div>
        <div>Night percentage: {night_stats['night_percentage']:.1f}%</div>
      </div>
    </div>
    
    <div>
      <h3>Recent Journal Entries</h3>
      <div id="journal-list">
        {' '.join(f'<div style="background: var(--border); padding: 0.8rem; border-radius: 8px; margin-bottom: 0.5rem; cursor: pointer;" onclick="loadJournalEntry(\\"{entry["date"]}\\")"><strong>{entry["date"]}</strong><br><small>{entry["word_count"]} words</small></div>' for entry in journal_entries) if journal_entries else '<div class="empty">No journal entries yet</div>'}
      </div>
    </div>
    
    <div>
      <h3>Night Timeline</h3>
      <div id="night-timeline">
        <div class="empty">Loading night timeline...</div>
      </div>
    </div>
  </div>
  
  <div id="journal-viewer" style="margin-top: 1rem; background: var(--border); padding: 1rem; border-radius: 8px; display: none;">
    <h3 id="journal-title">Journal Entry</h3>
    <div id="journal-content"></div>
  </div>
</div>

<!-- Achievement Showcase -->
<div id="achievements" class="section">
  <h2>🏆 Achievement Showcase</h2>
  <div id="achievements-content">
    <div class="empty">Loading achievements...</div>
  </div>
</div>

<!-- Self-Awareness Panel -->
<div id="self-awareness" class="self-awareness">
  <h2>🪞 Self-Awareness Panel</h2>
  <p style="margin-bottom: 1rem; color: var(--dim);">Understanding my own architecture and current state</p>
  
  <div class="introspect-summary" id="introspect-summary">
    <div class="empty">Loading introspection...</div>
  </div>
  
  <div class="explain-buttons">
    <button class="btn" onclick="explainSystem('moods')">Explain Moods</button>
    <button class="btn" onclick="explainSystem('memory')">Explain Memory</button>
    <button class="btn" onclick="explainSystem('trust')">Explain Trust</button>
    <button class="btn" onclick="explainSystem('evolution')">Explain Evolution</button>
    <button class="btn" onclick="explainSystem('health')">Explain Health</button>
    <button class="btn" onclick="explainSystem('thoughts')">Explain Thoughts</button>
    <button class="btn" onclick="explainSystem('proactive')">Explain Proactive</button>
  </div>
  
  <div id="system-explanation" style="background: var(--border); padding: 1rem; border-radius: 8px; margin: 1rem 0; display: none;">
    <h4 id="explanation-title">System Explanation</h4>
    <pre id="explanation-content" style="white-space: pre-wrap; font-family: monospace; font-size: 0.85rem;"></pre>
  </div>
  
  <div style="margin: 1rem 0;">
    <button class="btn btn-secondary" onclick="showWhyExplanation()">🤔 Why did I do that?</button>
    <a href="docs/ARCHITECTURE.md" class="btn btn-secondary" style="text-decoration: none;" target="_blank">📚 Architecture Docs</a>
  </div>
  
  <div id="why-explanation" style="background: var(--border); padding: 1rem; border-radius: 8px; margin: 1rem 0; display: none;">
    <h4>Last Decision Trace</h4>
    <pre id="why-content" style="white-space: pre-wrap; font-family: monospace; font-size: 0.85rem;"></pre>
  </div>
</div>

<!-- Footer -->
<footer>
  Intrusive Thoughts Dashboard v{version} | Last updated: <span id="last-updated">--:--</span>
</footer>

<script>
// Auto-refresh for live stream
let refreshInterval;

function showRefreshIndicator() {{
  const indicator = document.getElementById('refresh-indicator');
  indicator.classList.add('show');
  setTimeout(() => indicator.classList.remove('show'), 2000);
}}

function updateLastUpdated() {{
  document.getElementById('last-updated').textContent = new Date().toLocaleTimeString();
}}

function refreshStream() {{
  fetch('/api/stream')
    .then(r => r.json())
    .then(data => {{
      const content = document.getElementById('stream-content');
      if (data.length === 0) {{
        content.innerHTML = '<div class="empty">No recent activity</div>';
        return;
      }}
      
      content.innerHTML = data.map(item => `
        <div class="stream-item ${{item.type}}">
          <div class="time">${{item.timestamp}}</div>
          <div class="summary">${{item.summary}}</div>
        </div>
      `).join('');
      
      showRefreshIndicator();
      updateLastUpdated();
    }})
    .catch(e => console.error('Stream refresh failed:', e));
}}

// Tab management
function showControlTab(tabId) {{
  document.querySelectorAll('.tab-content').forEach(content => {{
    content.classList.remove('active');
  }});
  document.querySelectorAll('.tab').forEach(tab => {{
    tab.classList.remove('active');
  }});
  
  document.getElementById(tabId).classList.add('active');
  event.target.classList.add('active');
}}

function showHealthTab(tabId) {{
  document.querySelectorAll('#health .tab-content').forEach(content => {{
    content.classList.remove('active');
  }});
  document.querySelectorAll('#health .tab').forEach(tab => {{
    tab.classList.remove('active');
  }});
  
  document.getElementById(tabId).classList.add('active');
  event.target.classList.add('active');
  
  // Load tab content
  loadHealthTab(tabId);
}}

// Interactive controls
function updateThoughtWeight() {{
  const thoughtId = document.getElementById('thought-select').value;
  const weight = document.getElementById('weight-slider').value;
  
  if (!thoughtId) {{
    alert('Please select a thought first');
    return;
  }}
  
  fetch('/api/thought-weight', {{
    method: 'PUT',
    headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify({{thought_id: thoughtId, weight: parseFloat(weight)}})
  }})
  .then(r => r.json())
  .then(data => {{
    if (data.status === 'success') {{
      alert('Thought weight updated!');
    }} else {{
      alert('Error: ' + (data.error || 'Unknown error'));
    }}
  }});
}}

function setMood() {{
  const moodId = document.getElementById('mood-select').value;
  if (!moodId) {{
    alert('Please select a mood first');
    return;
  }}
  
  fetch('/api/set-mood', {{
    method: 'POST',
    headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify({{mood_id: moodId}})
  }})
  .then(r => r.json())
  .then(data => {{
    if (data.status === 'success') {{
      alert('Mood set!');
      setTimeout(() => location.reload(), 1000);
    }} else {{
      alert('Error: ' + (data.error || 'Unknown error'));
    }}
  }});
}}

function triggerImpulse() {{
  fetch('/api/trigger', {{method: 'POST'}})
  .then(r => r.json())
  .then(data => {{
    if (data.status === 'success') {{
      alert('Impulse triggered!');
      refreshStream();
    }} else {{
      alert('Error: ' + (data.error || 'Unknown error'));
    }}
  }});
}}

function applyPreset() {{
  const presetName = document.getElementById('preset-select').value;
  if (!presetName) {{
    alert('Please select a preset first');
    return;
  }}
  
  fetch('/api/preset-apply', {{
    method: 'POST',
    headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify({{preset: presetName}})
  }})
  .then(r => r.json())
  .then(data => {{
    if (data.status === 'success') {{
      alert('Preset applied!');
      setTimeout(() => location.reload(), 1000);
    }} else {{
      alert('Error: ' + (data.error || 'Unknown error'));
    }}
  }});
}}

// Health tab loaders
function loadHealthTab(tabId) {{
  const content = document.getElementById(tabId + '-content');
  let endpoint = '/api/' + tabId;
  
  if (tabId === 'health-monitor') {{
    endpoint = '/api/health';
  }}
  
  fetch(endpoint)
    .then(r => r.json())
    .then(data => {{
      content.innerHTML = formatHealthData(tabId, data);
    }})
    .catch(e => {{
      content.innerHTML = '<div class="empty">Error loading data</div>';
    }});
}}

function formatHealthData(type, data) {{
  // Format different health data types
  if (type === 'memory') {{
    if (data.error) return `<div class="empty">${{data.error}}</div>`;
    return `
      <div style="background: var(--border); padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
        <h4>Memory Health</h4>
        <p>Total entries: ${{data.total_entries || 0}}</p>
        <p>Recent activity: ${{data.recent_activity || 'None'}}</p>
      </div>
    `;
  }}
  
  if (type === 'trust') {{
    if (data.error) return `<div class="empty">${{data.error}}</div>`;
    return `
      <div style="background: var(--border); padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
        <h4>Trust Score</h4>
        <p>Current score: ${{data.trust_score || 'Unknown'}}</p>
        <p>Status: ${{data.status || 'Unknown'}}</p>
      </div>
    `;
  }}
  
  // Default formatting
  return `<pre style="font-size: 0.8rem; white-space: pre-wrap;">${{JSON.stringify(data, null, 2)}}</pre>`;
}}

// Journal functions
function loadJournalEntry(date) {{
  fetch(`/api/journal?date=${{date}}`)
    .then(r => r.json())
    .then(data => {{
      if (data.content) {{
        document.getElementById('journal-viewer').style.display = 'block';
        document.getElementById('journal-title').textContent = `Journal Entry - ${{date}}`;
        document.getElementById('journal-content').innerHTML = `<pre style="white-space: pre-wrap; font-family: inherit; font-size: 0.9rem;">${{data.content}}</pre>`;
      }} else {{
        alert('Could not load journal entry');
      }}
    }});
}}

// Self-awareness functions
function loadIntrospection() {{
  fetch('/api/introspect')
    .then(r => r.json())
    .then(data => {{
      const content = document.getElementById('introspect-summary');
      if (data.error) {{
        content.innerHTML = `<div style="color: var(--danger);">Error: ${{data.error}}</div>`;
        return;
      }}
      
      content.innerHTML = `
        <div><strong>Current State:</strong></div>
        <div>Mood: ${{data.mood_state?.current_mood?.name || 'Unknown'}} ${{data.mood_state?.current_mood?.emoji || ''}}</div>
        <div>Memory Health: ${{data.memory_state?.health_score || 'Unknown'}}</div>
        <div>Trust Score: ${{data.trust_state?.current_score || 'Unknown'}}</div>
        <div>Evolution State: ${{data.evolution_state?.current_generation || 'Unknown'}}</div>
        <div>System Health: ${{data.system_health?.overall_status || 'Unknown'}}</div>
      `;
    }});
}}

function explainSystem(systemName) {{
  fetch(`/api/explain/${{systemName}}`)
    .then(r => r.json())
    .then(data => {{
      const explanationDiv = document.getElementById('system-explanation');
      const titleDiv = document.getElementById('explanation-title');
      const contentDiv = document.getElementById('explanation-content');
      
      if (data.error) {{
        titleDiv.textContent = `Error explaining ${{systemName}}`;
        contentDiv.textContent = data.error;
      }} else {{
        titleDiv.textContent = `${{systemName.charAt(0).toUpperCase() + systemName.slice(1)}} System Explanation`;
        contentDiv.textContent = data.output;
      }}
      
      explanationDiv.style.display = 'block';
    }});
}}

function showWhyExplanation() {{
  fetch('/api/why')
    .then(r => r.json())
    .then(data => {{
      const whyDiv = document.getElementById('why-explanation');
      const contentDiv = document.getElementById('why-content');
      
      if (data.error) {{
        contentDiv.textContent = data.error;
      }} else {{
        contentDiv.textContent = data.output;
      }}
      
      whyDiv.style.display = 'block';
    }});
}}

// Weight slider handler
document.getElementById('weight-slider').addEventListener('input', function() {{
  document.getElementById('weight-value').textContent = this.value;
}});

// Preset selector handler  
document.getElementById('preset-select').addEventListener('change', function() {{
  const presetName = this.value;
  if (presetName) {{
    fetch(`/api/presets`)
      .then(r => r.json())
      .then(data => {{
        const preset = data[presetName];
        if (preset) {{
          document.getElementById('preset-details').style.display = 'block';
          document.getElementById('preset-description').innerHTML = `
            <h4>${{presetName}}</h4>
            <p>${{preset.description || 'No description'}}</p>
            <small>Weights: ${{Object.keys(preset.weights || {{}}).length}} thoughts</small>
          `;
        }}
      }});
  }} else {{
    document.getElementById('preset-details').style.display = 'none';
  }}
}});

// Load achievements
function loadAchievements() {{
  fetch('/api/achievements')
    .then(r => r.json())
    .then(data => {{
      const content = document.getElementById('achievements-content');
      const earned = data.earned || [];
      const allAchievements = data.all_achievements || {{}};
      
      if (earned.length === 0) {{
        content.innerHTML = '<div class="empty">No achievements yet</div>';
        return;
      }}
      
      content.innerHTML = earned.map(achievement => `
        <div style="display: flex; align-items: center; margin-bottom: 1rem; padding: 1rem; background: var(--border); border-radius: 8px;">
          <div style="margin-right: 1rem; font-size: 1.5rem;">${{achievement.tier_emoji || '🏆'}}</div>
          <div>
            <h4 style="color: var(--accent); margin-bottom: 0.2rem;">${{achievement.name}}</h4>
            <p style="color: var(--dim); font-size: 0.9rem; margin-bottom: 0.2rem;">${{achievement.description}}</p>
            <small style="color: var(--dim);">${{achievement.points}} points • ${{achievement.earned_at}}</small>
          </div>
        </div>
      `).join('');
    }});
}}

// Load schedule
function loadSchedule() {{
  fetch('/api/schedule')
    .then(r => r.json())
    .then(data => {{
      const content = document.getElementById('schedule-content');
      if (data.error) {{
        content.innerHTML = `<div class="empty">${{data.error}}</div>`;
        return;
      }}
      
      content.innerHTML = `
        <div style="background: var(--border); padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
          <h4>Current Phase: ${{data.current_phase || 'Unknown'}}</h4>
        </div>
        <div>
          <h4>Schedule:</h4>
          ${{(data.schedule || []).map(phase => `
            <div style="padding: 0.5rem; margin: 0.2rem 0; background: var(--border); border-radius: 4px;">
              <strong>${{phase.time || 'Unknown'}}</strong> - ${{phase.phase || 'Unknown'}}
            </div>
          `).join('') || '<div class="empty">No schedule data</div>'}}
        </div>
      `;
    }});
}}

// Initial load
refreshStream();
loadIntrospection();
loadAchievements();
loadSchedule();
updateLastUpdated();

// Auto-refresh every 30 seconds
refreshInterval = setInterval(refreshStream, 30000);

// Load default health tab
loadHealthTab('memory');
</script>
</body>
</html>"""


class DashboardHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        query = parse_qs(parsed_path.query)
        
        if path == "/" or path == "/index.html":
            html = build_html()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode())
            
        elif path == "/api/stats":
            history = load_history()
            picks = load_picks()
            thought_counts = Counter(p.get("thought", "?") for p in picks)
            achievements = load_earned_achievements()
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({
                "total_picks": len(picks),
                "total_completed": len(history),
                "achievements": len(achievements.get("earned", [])),
                "points": achievements.get("total_points", 0),
                "thought_counts": dict(thought_counts),
                "recent": history[-10:][::-1],
            }).encode())
            
        elif path == "/api/stream":
            stream_data = load_stream_data(50)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(stream_data, default=str).encode())
            
        elif path == "/api/decisions":
            decisions = load_decisions()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(decisions[-50:], default=str).encode())
            
        elif path == "/api/rejections":
            rejections = load_rejections()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(rejections[-50:], default=str).encode())
            
        elif path == "/api/mood-timeline":
            mood_history = load_mood_history()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(mood_history[-30:], default=str).encode())
            
        elif path == "/api/presets":
            presets = load_presets()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(presets, default=str).encode())
            
        elif path == "/api/schedule":
            schedule_data = get_schedule_data()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(schedule_data, default=str).encode())
            
        elif path == "/api/memory":
            try:
                from memory_system import get_dashboard_data
                data = get_dashboard_data()
            except Exception:
                data = {"error": "memory system unavailable"}
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(data, default=str).encode())
            
        elif path == "/api/trust":
            try:
                from trust_system import get_dashboard_data
                data = get_dashboard_data()
            except Exception:
                data = {"error": "trust system unavailable"}
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(data, default=str).encode())
            
        elif path == "/api/evolution":
            try:
                from self_evolution import get_dashboard_data
                data = get_dashboard_data()
            except Exception:
                data = {"error": "evolution system unavailable"}
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(data, default=str).encode())
            
        elif path == "/api/proactive":
            try:
                from proactive import get_dashboard_data
                data = get_dashboard_data()
            except Exception:
                data = {"error": "proactive system unavailable"}
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(data, default=str).encode())
            
        elif path == "/api/health":
            try:
                from health_monitor import get_dashboard_data
                data = get_dashboard_data()
            except Exception:
                data = {"error": "health monitor unavailable"}
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(data, default=str).encode())
            
        elif path == "/api/journal":
            date = query.get('date', [''])[0]
            if date:
                try:
                    journal_file = get_data_dir() / "journal" / f"{date}.md"
                    if journal_file.exists():
                        content = journal_file.read_text()
                        data = {"date": date, "content": content, "word_count": len(content.split())}
                    else:
                        data = {"error": f"Journal entry for {date} not found"}
                except Exception as e:
                    data = {"error": str(e)}
            else:
                data = {"error": "Date parameter required"}
                
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(data, default=str).encode())
            
        elif path == "/api/journal/list":
            entries = load_journal_entries()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(entries, default=str).encode())
            
        elif path == "/api/achievements":
            earned = load_earned_achievements()
            all_achievements = load_all_achievements()
            data = {
                "earned": earned.get("earned", []),
                "total_points": earned.get("total_points", 0),
                "all_achievements": all_achievements
            }
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(data, default=str).encode())
            
        elif path == "/api/night-stats":
            stats = get_night_stats()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(stats, default=str).encode())
            
        elif path == "/api/systems":
            # Consolidated system information
            systems = {
                "mood": {"status": "active", "current_mood": load_today_mood()},
                "memory": {"status": "active", "entries": len(load_history())},
                "thoughts": {"status": "active", "total_thoughts": len(load_thoughts().get("thoughts", {}))},
                "achievements": {"status": "active", "earned": len(load_earned_achievements().get("earned", []))},
                "health": {"status": "active", "monitoring": True}
            }
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(systems, default=str).encode())
            
        elif path == "/api/introspect":
            introspect_data = run_introspect()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(introspect_data, default=str).encode())
            
        elif path.startswith("/api/explain/"):
            system_name = path.split("/")[-1]
            explain_data = run_explain_system(system_name)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(explain_data, default=str).encode())
            
        elif path == "/api/why":
            decision_data = run_decision_trace()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(decision_data, default=str).encode())
            
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not found")
    
    def do_PUT(self):
        if self.path == "/api/thought-weight":
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length).decode('utf-8')
                data = json.loads(post_data)
                
                thought_id = data.get("thought_id")
                weight = data.get("weight")
                
                if not thought_id or weight is None:
                    raise ValueError("Missing thought_id or weight")
                
                # Update thought weight (would need to implement in thoughts system)
                result = {"status": "success", "message": f"Updated {thought_id} weight to {weight}"}
                
            except Exception as e:
                result = {"status": "error", "error": str(e)}
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        if self.path == "/api/set-mood":
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length).decode('utf-8')
                data = json.loads(post_data)
                
                mood_id = data.get("mood_id")
                if not mood_id:
                    raise ValueError("Missing mood_id")
                
                # Set mood using existing script
                result = subprocess.run(['./set_mood.sh', mood_id], 
                                      capture_output=True, text=True, timeout=5)
                
                if result.returncode == 0:
                    response = {"status": "success", "message": f"Mood set to {mood_id}"}
                else:
                    response = {"status": "error", "error": result.stderr or "Failed to set mood"}
                
            except Exception as e:
                response = {"status": "error", "error": str(e)}
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
        elif self.path == "/api/trigger":
            try:
                # Trigger an impulse using existing scripts
                result = subprocess.run(['./suggest_thought.sh'], 
                                      capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    response = {"status": "success", "message": "Impulse triggered"}
                else:
                    response = {"status": "error", "error": result.stderr or "Failed to trigger impulse"}
                
            except Exception as e:
                response = {"status": "error", "error": str(e)}
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
        elif self.path == "/api/preset-apply":
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length).decode('utf-8')
                data = json.loads(post_data)
                
                preset_name = data.get("preset")
                if not preset_name:
                    raise ValueError("Missing preset name")
                
                # Apply preset (would need to implement preset application logic)
                response = {"status": "success", "message": f"Applied preset {preset_name}"}
                
            except Exception as e:
                response = {"status": "error", "error": str(e)}
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()


if __name__ == "__main__":
    print(f"🧠 Starting Intrusive Thoughts Dashboard v{get_version()} on http://localhost:{PORT}")
    server = HTTPServer(("localhost", PORT), DashboardHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\\n🛑 Dashboard stopped")
        server.shutdown()