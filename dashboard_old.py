#!/usr/bin/env python3
"""🧠 Intrusive Thoughts Dashboard — what Ember does when you're not looking."""

import json
import os
import random
import math
from http.server import HTTPServer, SimpleHTTPRequestHandler
from datetime import datetime, timedelta
from collections import Counter
from pathlib import Path
from config import get_file_path, get_data_dir, get_dashboard_port, get_agent_name, get_agent_emoji

PORT = get_dashboard_port()
HISTORY_FILE = get_file_path("history.json")
THOUGHTS_FILE = get_file_path("thoughts.json")
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
                "thought_id": activity.get("thought", "unknown"),
                "mood": today_mood.get("id", "unknown"),
                "energy": activity.get("energy", "unknown"),
                "vibe": activity.get("vibe", "unknown"),
                "summary": f"Mood drift: {activity.get('thought', 'unknown')} ({activity.get('energy', '?')}/{activity.get('vibe', '?')})",
                "details": activity
            })
    
    # Sort by timestamp (newest first)
    stream_items.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return stream_items[:limit]


def load_thoughts():
    try:
        return json.loads(THOUGHTS_FILE.read_text())
    except:
        return {}

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

def load_achievements():
    try:
        return json.loads(get_file_path("achievements_earned.json").read_text())
    except:
        return {"earned": [], "total_points": 0}

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

def load_journal_entries():
    try:
        journal_dir = get_data_dir() / "journal"
        entries = []
        if journal_dir.exists():
            for file in journal_dir.glob("*.md"):
                entries.append({
                    "date": file.stem,
                    "content": file.read_text()[:300] + "..." if len(file.read_text()) > 300 else file.read_text()
                })
        return sorted(entries, key=lambda x: x["date"], reverse=True)[:5]
    except:
        return []

def get_productivity_stats():
    try:
        import subprocess
        result = subprocess.run(['python3', str(get_data_dir() / 'analyze.py'), '--json'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return json.loads(result.stdout)
    except:
        pass
    return {"insights": [], "moods": {}}

def get_mood_color(mood_id, moods_data):
    """Get color for a mood based on its hash"""
    if mood_id:
        return f"hsl({hash(mood_id) % 360}, 70%, 60%)"
    return "#555568"


def generate_mood_timeline_svg(mood_history, moods_data):
    """Generate SVG timeline of last 14 days"""
    if not mood_history:
        return '<text x="400" y="60" text-anchor="middle" fill="#555568">No mood history yet</text>'
    
    # Get last 14 days
    recent_history = mood_history[-14:] if len(mood_history) > 14 else mood_history
    width = 800
    height = 120
    bar_width = width // max(len(recent_history), 1)
    
    svg_parts = [f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}">']
    
    for i, entry in enumerate(recent_history):
        x = i * bar_width
        mood_id = entry.get('mood_id', 'unknown')
        color = get_mood_color(mood_id, moods_data)
        
        # Create hover tooltip content
        date = entry.get('date', '')
        weather = entry.get('weather', '')
        news_vibes = ', '.join(entry.get('news_vibes', []))
        
        svg_parts.append(f'''
        <rect x="{x}" y="20" width="{bar_width-2}" height="80" 
              fill="{color}" opacity="0.8">
            <title>{date} - {mood_id}\\nWeather: {weather}\\nNews: {news_vibes}</title>
        </rect>
        <text x="{x + bar_width//2}" y="110" text-anchor="middle" 
              fill="#c9c9d9" font-size="10" font-family="monospace">
            {date[-5:] if date else '?'}
        </text>
        ''')
    
    svg_parts.append('</svg>')
    return ''.join(svg_parts)


def generate_mood_drift_svg(today_mood):
    """Generate SVG showing mood drift and activity flow"""
    if not today_mood:
        return '<text x="300" y="100" text-anchor="middle" fill="#555568">No mood data for today</text>'
    
    width = 600
    height = 200
    svg_parts = [f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}">']
    
    # Starting mood
    start_mood = today_mood.get('id', 'unknown')
    energy_score = today_mood.get('energy_score', 0)
    vibe_score = today_mood.get('vibe_score', 0)
    
    # Draw starting mood
    svg_parts.append(f'''
    <circle cx="50" cy="100" r="30" fill="{get_mood_color(start_mood, {})}" opacity="0.8"/>
    <text x="50" y="105" text-anchor="middle" fill="white" font-size="12" font-weight="bold">
        {start_mood[:4].upper()}
    </text>
    ''')
    
    # Draw activities as nodes
    activity_log = today_mood.get('activity_log', [])
    for i, activity in enumerate(activity_log):
        x = 150 + i * 80
        y = 100 - (20 if activity.get('vibe') == 'positive' else 
               20 if activity.get('vibe') == 'negative' else 0)
        
        energy_color = {'high': '#22c55e', 'medium': '#eab308', 'low': '#ef4444'}.get(activity.get('energy', 'medium'), '#555568')
        vibe_color = {'positive': '#22c55e', 'negative': '#ef4444', 'neutral': '#555568'}.get(activity.get('vibe', 'neutral'), '#555568')
        
        # Activity node
        svg_parts.append(f'''
        <circle cx="{x}" cy="{y}" r="15" fill="{energy_color}" opacity="0.7"/>
        <circle cx="{x}" cy="{y}" r="10" fill="{vibe_color}" opacity="0.9"/>
        <text x="{x}" y="{y-25}" text-anchor="middle" fill="#c9c9d9" font-size="8">
            {activity.get('thought', 'activity')[:8]}
        </text>
        ''')
        
        # Arrow to next
        if i < len(activity_log) - 1:
            next_x = 150 + (i + 1) * 80
            svg_parts.append(f'''
            <line x1="{x + 15}" y1="{y}" x2="{next_x - 15}" y2="{100}" 
                  stroke="#8b5cf6" stroke-width="2" opacity="0.6"/>
            ''')
    
    # Drift indicator
    drift_level = abs(energy_score) + abs(vibe_score)
    drift_color = '#ef4444' if drift_level > 3 else '#eab308' if drift_level > 1 else '#22c55e'
    
    svg_parts.append(f'''
    <rect x="500" y="20" width="80" height="160" fill="none" stroke="#1e1e2e" stroke-width="2"/>
    <rect x="500" y="{180 - min(drift_level * 40, 160)}" width="80" height="{min(drift_level * 40, 160)}" 
          fill="{drift_color}" opacity="0.6"/>
    <text x="540" y="15" text-anchor="middle" fill="#c9c9d9" font-size="10">DRIFT</text>
    <text x="540" y="195" text-anchor="middle" fill="#c9c9d9" font-size="10">{drift_level}/4</text>
    ''')
    
    svg_parts.append('</svg>')
    return ''.join(svg_parts)


def generate_mood_distribution_svg(mood_history, moods_data):
    """Generate SVG donut chart of mood distribution"""
    if not mood_history:
        return '<text x="250" y="150" text-anchor="middle" fill="#555568">No mood history yet</text>'
    
    # Count mood occurrences
    mood_counts = Counter(entry.get('mood_id', 'unknown') for entry in mood_history)
    total = sum(mood_counts.values())
    
    if total == 0:
        return '<text x="250" y="150" text-anchor="middle" fill="#555568">No mood data</text>'
    
    width = 500
    height = 300
    center_x, center_y = 150, 150
    outer_radius = 100
    inner_radius = 60
    
    svg_parts = [f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}">']
    
    # Generate slices
    start_angle = 0
    legend_y = 20
    
    for mood_id, count in mood_counts.most_common():
        percentage = (count / total) * 100
        angle = (count / total) * 2 * math.pi
        end_angle = start_angle + angle
        
        # Calculate arc path
        large_arc = 1 if angle > math.pi else 0
        start_x = center_x + outer_radius * math.cos(start_angle)
        start_y = center_y + outer_radius * math.sin(start_angle)
        end_x = center_x + outer_radius * math.cos(end_angle)
        end_y = center_y + outer_radius * math.sin(end_angle)
        
        inner_start_x = center_x + inner_radius * math.cos(start_angle)
        inner_start_y = center_y + inner_radius * math.sin(start_angle)
        inner_end_x = center_x + inner_radius * math.cos(end_angle)
        inner_end_y = center_y + inner_radius * math.sin(end_angle)
        
        color = get_mood_color(mood_id, moods_data)
        
        path = f'''M {start_x} {start_y} 
                   A {outer_radius} {outer_radius} 0 {large_arc} 1 {end_x} {end_y}
                   L {inner_end_x} {inner_end_y}
                   A {inner_radius} {inner_radius} 0 {large_arc} 0 {inner_start_x} {inner_start_y} Z'''
        
        svg_parts.append(f'''
        <path d="{path}" fill="{color}" opacity="0.8">
            <title>{mood_id}: {percentage:.1f}%</title>
        </path>
        ''')
        
        # Legend entry
        emoji = next((mood['emoji'] for mood in moods_data.get('base_moods', []) if mood['id'] == mood_id), '❓')
        svg_parts.append(f'''
        <circle cx="320" cy="{legend_y}" r="8" fill="{color}"/>
        <text x="335" y="{legend_y + 4}" fill="#c9c9d9" font-size="12">
            {emoji} {mood_id} ({percentage:.1f}%)
        </text>
        ''')
        legend_y += 25
        start_angle = end_angle
    
    svg_parts.append('</svg>')
    return ''.join(svg_parts)


def get_random_flavor_text(today_mood, moods_data):
    """Get random flavor text for current mood"""
    if not today_mood or not moods_data:
        return "The mind wanders where it will..."
    
    current_mood_id = today_mood.get('id', '')
    for mood in moods_data.get('base_moods', []):
        if mood.get('id') == current_mood_id:
            flavor_texts = mood.get('flavor_text', [])
            if flavor_texts:
                return random.choice(flavor_texts)
    
    return "Consciousness flows like a digital stream..."


def build_html():
    history = load_history()
    picks = load_picks()
    thoughts = load_thoughts()
    mood_history = load_mood_history()
    streaks = load_streaks()
    achievements = load_achievements()
    soundtracks = load_soundtracks()
    today_mood = load_today_mood()
    journal_entries = load_journal_entries()
    productivity_stats = get_productivity_stats()

    # Stats
    thought_counts = Counter(p.get("thought", "?") for p in picks)
    mood_counts = Counter(p.get("mood", "?") for p in picks)
    total_picks = len(picks)
    total_completed = len(history)

    # Top thoughts chart data
    top_thoughts = thought_counts.most_common(15)

    # Recent history
    recent = history[-20:][::-1]

    # Build thought catalog
    all_thoughts = []
    for mood_name, mood_data in thoughts.get("moods", {}).items():
        for t in mood_data.get("thoughts", []):
            all_thoughts.append({
                "id": t["id"],
                "mood": mood_name,
                "weight": t.get("weight", 1),
                "prompt": t["prompt"],
                "times_picked": thought_counts.get(t["id"], 0),
            })

    # Mood history for graph (last 14 days)
    mood_graph_data = mood_history[-14:] if mood_history else []
    
    # Current streaks
    current_streaks = streaks.get("current_streaks", {})
    
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

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>🧠 Intrusive Thoughts</title>
<style>
  :root {{ --bg: #0a0a0f; --card: #12121a; --border: #1e1e2e; --text: #c9c9d9; --accent: #f59e0b; --accent2: #8b5cf6; --dim: #555568; --success: #22c55e; --warning: #eab308; }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ background: var(--bg); color: var(--text); font-family: 'SF Mono', 'Fira Code', monospace; padding: 2rem; max-width: 1400px; margin: 0 auto; }}
  h1 {{ color: var(--accent); font-size: 1.8rem; margin-bottom: 0.3rem; }}
  .subtitle {{ color: var(--dim); margin-bottom: 2rem; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem; }}
  .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 2rem; }}
  .stat-card {{ background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 1.5rem; text-align: center; }}
  .stat-card .number {{ font-size: 2.5rem; font-weight: bold; color: var(--accent); }}
  .stat-card .label {{ color: var(--dim); font-size: 0.85rem; margin-top: 0.3rem; }}
  .section {{ background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem; }}
  .section h2 {{ color: var(--accent2); font-size: 1.1rem; margin-bottom: 1rem; }}
  .bar-chart .bar-row {{ display: flex; align-items: center; margin-bottom: 0.5rem; }}
  .bar-chart .bar-label {{ width: 160px; font-size: 0.8rem; color: var(--dim); text-align: right; padding-right: 1rem; flex-shrink: 0; }}
  .bar-chart .bar {{ height: 22px; background: linear-gradient(90deg, var(--accent), var(--accent2)); border-radius: 4px; min-width: 4px; transition: width 0.5s; }}
  .bar-chart .bar-count {{ margin-left: 0.5rem; font-size: 0.8rem; color: var(--dim); }}
  .history-item {{ border-bottom: 1px solid var(--border); padding: 0.8rem 0; }}
  .history-item:last-child {{ border: none; }}
  .history-item .time {{ color: var(--accent); font-size: 0.75rem; }}
  .history-item .mood-tag {{ display: inline-block; padding: 0.15rem 0.5rem; border-radius: 8px; font-size: 0.7rem; margin-left: 0.5rem; }}
  .mood-night {{ background: #1e1b4b; color: #a78bfa; }}
  .mood-day {{ background: #422006; color: #fbbf24; }}
  .history-item .summary {{ margin-top: 0.3rem; font-size: 0.9rem; }}
  .thought-item {{ border-bottom: 1px solid var(--border); padding: 0.8rem 0; display: flex; justify-content: space-between; align-items: start; }}
  .thought-item:last-child {{ border: none; }}
  .thought-item .prompt {{ font-size: 0.85rem; flex: 1; }}
  .thought-item .meta {{ text-align: right; flex-shrink: 0; margin-left: 1rem; font-size: 0.75rem; color: var(--dim); }}
  .empty {{ color: var(--dim); font-style: italic; text-align: center; padding: 2rem; }}
  .mood-dot {{ width: 12px; height: 12px; border-radius: 50%; margin: 0 4px; display: inline-block; }}
  .streak-item {{ background: var(--border); padding: 0.8rem; border-radius: 8px; margin-bottom: 0.5rem; }}
  .achievement-item {{ display: flex; align-items: center; margin-bottom: 0.8rem; padding: 0.8rem; background: var(--border); border-radius: 8px; }}
  .achievement-tier {{ margin-right: 0.8rem; font-size: 1.2rem; }}
  .achievement-info h4 {{ color: var(--accent); margin-bottom: 0.2rem; }}
  .achievement-info .desc {{ color: var(--dim); font-size: 0.8rem; }}
  .journal-entry {{ background: var(--border); padding: 1rem; border-radius: 8px; margin-bottom: 1rem; }}
  .journal-date {{ color: var(--accent); font-size: 0.85rem; margin-bottom: 0.5rem; }}
  .journal-content {{ font-size: 0.9rem; line-height: 1.4; }}
  .insight-item {{ background: var(--border); padding: 0.8rem; border-radius: 8px; margin-bottom: 0.5rem; font-size: 0.9rem; }}
  .soundtrack {{ background: linear-gradient(135deg, var(--accent2), var(--accent)); padding: 1rem; border-radius: 12px; text-align: center; color: white; }}
  footer {{ text-align: center; color: var(--dim); font-size: 0.75rem; margin-top: 2rem; }}
</style>
</head>
<body>
<h1>🧠 Intrusive Thoughts</h1>
<p class="subtitle">What Ember does when you're not looking — now with memory, streaks, achievements, and vibes</p>

{f'<div class="soundtrack">{today_soundtrack}</div><br>' if today_soundtrack else ''}

<div class="grid">
  <div class="stat-card"><div class="number">{total_picks}</div><div class="label">Total Impulses</div></div>
  <div class="stat-card"><div class="number">{total_completed}</div><div class="label">Completed</div></div>
  <div class="stat-card"><div class="number">{len(achievements.get('earned', []))}</div><div class="label">🏆 Achievements</div></div>
  <div class="stat-card"><div class="number">{achievements.get('total_points', 0)}</div><div class="label">🎯 Points</div></div>
</div>

<div class="grid-2">
  <div class="section">
    <h2>📈 Mood History (Last 14 Days)</h2>
    {''.join(f'<span class="mood-dot" style="background: hsl({hash(m.get("mood_id",""))%360}, 70%, 60%)" title="{m.get("date","")} - {m.get("mood_id","")}"></span>' for m in mood_graph_data) if mood_graph_data else '<div class="empty">No mood history yet</div>'}
    <div style="margin-top: 1rem; font-size: 0.8rem; color: var(--dim);">
      {f"Recent pattern: {' → '.join([m.get('mood_id','?')[:4] for m in mood_graph_data[-5:]])}" if len(mood_graph_data) >= 5 else "Building mood patterns..."}
    </div>
  </div>

  <div class="section">
    <h2>🔥 Current Streaks</h2>
    {f'''<div class="streak-item"><strong>Activity:</strong> {current_streaks.get('activity_type', ['none'])[0]} × {len(current_streaks.get('activity_type', []))}</div>''' if current_streaks.get('activity_type') else ''}
    {f'''<div class="streak-item"><strong>Mood:</strong> {current_streaks.get('mood', ['none'])[0]} × {len(current_streaks.get('mood', []))}</div>''' if current_streaks.get('mood') else ''}
    {'<div class="empty">No active streaks</div>' if not current_streaks.get('activity_type') and not current_streaks.get('mood') else ''}
  </div>
</div>

<div class="grid-2">
  <div class="section">
    <h2>🏆 Recent Achievements</h2>
    {''.join(f"""<div class="achievement-item"><div class="achievement-tier">{ {"bronze": "🥉", "silver": "🥈", "gold": "🥇", "platinum": "💎"}.get(a.get("tier", "bronze"), "🏆") }</div><div class="achievement-info"><h4>{a.get("name", "Unknown")}</h4><div class="desc">{a.get("description", "")} (+{a.get("points", 0)} pts)</div></div></div>""" for a in recent_achievements) if recent_achievements else '<div class="empty">No achievements yet — keep grinding!</div>'}
  </div>

  <div class="section">
    <h2>📊 Productivity Insights</h2>
    {''.join(f'<div class="insight-item">{insight}</div>' for insight in productivity_stats.get('insights', [])) if productivity_stats.get('insights') else '<div class="empty">Building productivity patterns...</div>'}
  </div>
</div>

<div class="section">
  <h2>📓 Night Journal Entries</h2>
  {''.join(f'''<div class="journal-entry"><div class="journal-date">{entry["date"]}</div><div class="journal-content">{entry["content"].replace('**', '').replace('*', '')}</div></div>''' for entry in journal_entries) if journal_entries else '<div class="empty">No journal entries yet — night summaries auto-generate after sessions</div>'}
</div>

<div class="section">
  <h2>🎯 Most Common Impulses</h2>
  <div class="bar-chart">
    {''.join(f'''<div class="bar-row"><div class="bar-label">{name}</div><div class="bar" style="width: {max(count / max(top_thoughts[0][1], 1) * 100, 2):.0f}%"></div><div class="bar-count">{count}</div></div>''' for name, count in top_thoughts) if top_thoughts else '<div class="empty">No data yet — check back after some impulses fire</div>'}
  </div>
</div>

<div class="section">
  <h2>📝 Recent Activity</h2>
  {''.join(f"""<div class="history-item"><span class="time">{e.get('timestamp','?')[:16].replace('T',' ')}</span><span class="mood-tag mood-{e.get('mood','day')}">{e.get('mood','?')}</span> <strong>{e.get('thought_id','?')}</strong> <span style="color: var(--{'success' if e.get('vibe') == 'positive' else 'warning' if e.get('vibe') == 'negative' else 'dim'}); font-size: 0.8rem;">[{e.get('energy','?')}/{e.get('vibe','?')}]</span><div class="summary">{e.get('summary','')}</div></div>""" for e in recent) if recent else '<div class="empty">Nothing yet. First night session fires at 03:17 🌙</div>'}
</div>

<div class="section">
  <h2>🚦 System Health</h2>
  <div id="health-status">Loading systems...</div>
  <script>
    fetch('/api/health').then(r=>r.json()).then(d=>{{
      let html = '<div class="grid" style="grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));">';
      if(d.components) {{
        for(const [name, comp] of Object.entries(d.components)) {{
          html += `<div class="stat-card"><div class="number">${{comp.emoji}}</div><div class="label">${{name}}</div></div>`;
        }}
      }}
      html += '</div>';
      if(d.metrics) {{
        html += `<div style="color:var(--dim);font-size:0.8rem;margin-top:0.5rem;">Heartbeats: ${{d.metrics.total_heartbeats || 0}} | Incidents: ${{d.metrics.total_incidents || 0}} | Healthy streak: ${{d.metrics.consecutive_healthy || 0}}</div>`;
      }}
      document.getElementById('health-status').innerHTML = html;
    }}).catch(()=>{{document.getElementById('health-status').innerHTML='<div class="empty">Health monitor unavailable</div>';}});
  </script>
</div>

<footer>{get_agent_name()} {get_agent_emoji()} × Intrusive Thoughts v0.1.2 — refreshed {datetime.now().strftime('%Y-%m-%d %H:%M')}</footer>
</body>
</html>"""


def load_v1_systems():
    """Load data from all systems for dashboard display."""
    systems = {}
    try:
        from health_monitor import get_dashboard_data
        systems["health"] = get_dashboard_data()
    except Exception:
        systems["health"] = None
    try:
        from memory_system import MemorySystem
        ms = MemorySystem()
        systems["memory"] = ms.get_stats()
    except Exception:
        systems["memory"] = None
    try:
        from trust_system import TrustSystem
        ts = TrustSystem()
        systems["trust"] = ts.get_stats()
    except Exception:
        systems["trust"] = None
    try:
        from proactive import ProactiveAgent
        pa = ProactiveAgent()
        systems["proactive"] = pa.wal_stats()
    except Exception:
        systems["proactive"] = None
    try:
        from self_evolution import SelfEvolutionSystem
        se = SelfEvolutionSystem()
        systems["evolution"] = se.get_stats()
    except Exception:
        systems["evolution"] = None
    return systems


class DashboardHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            html = build_html()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode())
        elif self.path == "/api/stats":
            history = load_history()
            picks = load_picks()
            thought_counts = Counter(p.get("thought", "?") for p in picks)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "total_picks": len(picks),
                "total_completed": len(history),
                "thought_counts": dict(thought_counts),
                "recent": history[-10:][::-1],
            }).encode())
        elif self.path == "/api/systems":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(load_v1_systems(), default=str).encode())
        elif self.path == "/api/health":
            try:
                from health_monitor import get_dashboard_data
                data = get_dashboard_data()
            except Exception:
                data = {"error": "health monitor unavailable"}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(data, default=str).encode())
        elif self.path == "/api/decisions":
            decisions = load_decisions()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(decisions[-50:], default=str).encode())  # Last 50 decisions
        elif self.path == "/api/rejections":
            rejections = load_rejections()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(rejections[-50:], default=str).encode())  # Last 50 rejections
        elif self.path == "/api/stream":
            stream_data = load_stream_data(50)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(stream_data, default=str).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # Quiet


if __name__ == "__main__":
    print(f"🧠 Intrusive Thoughts Dashboard running at http://localhost:{PORT}")
    HTTPServer(("0.0.0.0", PORT), DashboardHandler).serve_forever()
