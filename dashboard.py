#!/usr/bin/env python3
"""🧠 Intrusive Thoughts Dashboard v2 — Night workshop & journal viewer edition."""

import json
import os
import subprocess
import re
import markdown
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


def get_journal_dates():
    """Get all available journal dates."""
    try:
        journal_dir = get_data_dir() / "journal"
        if not journal_dir.exists():
            return []
        dates = []
        for file in journal_dir.glob("*.md"):
            dates.append(file.stem)
        return sorted(dates, reverse=True)
    except:
        return []


def get_journal_entry(date):
    """Get full journal entry for a specific date."""
    try:
        journal_dir = get_data_dir() / "journal"
        journal_file = journal_dir / f"{date}.md"
        if journal_file.exists():
            content = journal_file.read_text()
            # Convert markdown to HTML
            html_content = markdown.markdown(content, extensions=['extra', 'codehilite'])
            
            # Get mood context for that date
            mood_context = get_mood_context_for_date(date)
            
            return {
                "date": date,
                "content": content,
                "html_content": html_content,
                "mood_context": mood_context
            }
        return None
    except:
        return None


def get_mood_context_for_date(date):
    """Get mood context (emoji, name, weather, news) for a date."""
    mood_history = load_mood_history()
    moods_data = load_moods()
    
    for entry in mood_history:
        if entry.get("date") == date:
            mood_id = entry.get("mood_id", "")
            # Find mood details
            for mood in moods_data.get("base_moods", []):
                if mood.get("id") == mood_id:
                    return {
                        "emoji": mood.get("emoji", "🤔"),
                        "name": mood.get("name", mood_id),
                        "description": mood.get("description", ""),
                        "weather": entry.get("weather", ""),
                        "news_vibe": entry.get("news_vibe", "")
                    }
    
    return {"emoji": "🤔", "name": "Unknown", "description": ""}


def get_night_workshop_timeline():
    """Get timeline of all night workshop sessions."""
    history = load_history()
    night_entries = [entry for entry in history if entry.get("mood") == "night"]
    
    # Sort by timestamp
    night_entries.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    
    return night_entries


def get_day_vs_night_stats():
    """Compare day vs night activity stats."""
    history = load_history()
    day_entries = [e for e in history if e.get("mood") == "day"]
    night_entries = [e for e in history if e.get("mood") == "night"]
    
    def get_stats(entries):
        if not entries:
            return {"count": 0, "avg_energy": 0, "avg_vibe": 0, "energy_dist": {}, "vibe_dist": {}}
        
        energy_values = {"low": 1, "medium": 2, "high": 3}
        vibe_values = {"negative": 1, "neutral": 2, "positive": 3}
        
        energies = [energy_values.get(e.get("energy"), 2) for e in entries]
        vibes = [vibe_values.get(e.get("vibe"), 2) for e in entries]
        
        energy_dist = Counter(e.get("energy", "medium") for e in entries)
        vibe_dist = Counter(e.get("vibe", "neutral") for e in entries)
        
        return {
            "count": len(entries),
            "avg_energy": sum(energies) / len(energies),
            "avg_vibe": sum(vibes) / len(vibes),
            "energy_dist": dict(energy_dist),
            "vibe_dist": dict(vibe_dist)
        }
    
    day_stats = get_stats(day_entries)
    night_stats = get_stats(night_entries)
    
    # Determine best mood for each
    best_day_insight = "Not enough data"
    best_night_insight = "Not enough data"
    
    if day_stats["count"] > 0 and night_stats["count"] > 0:
        if day_stats["avg_energy"] > night_stats["avg_energy"]:
            best_day_insight = "Day work shows higher energy levels"
        else:
            best_night_insight = "Night work shows higher energy levels"
    
    return {
        "day": day_stats,
        "night": night_stats,
        "insights": {
            "best_day": best_day_insight,
            "best_night": best_night_insight
        }
    }


def get_recent_night_commits():
    """Get recent commits made during night hours (22:00-08:00)."""
    try:
        # Check if we're in a git repository
        result = subprocess.run(['git', 'rev-parse', '--is-inside-work-tree'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            return []
        
        # Get commits from last 7 days during night hours
        night_commits = []
        for days_ago in range(7):
            date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
            
            # Morning commits (00:00-08:00)
            morning_cmd = ['git', 'log', '--since', f'{date} 00:00', '--until', f'{date} 08:00', 
                          '--format=%H|%s|%ai', '--no-merges']
            
            # Evening commits (22:00-23:59)
            evening_cmd = ['git', 'log', '--since', f'{date} 22:00', '--until', f'{date} 23:59',
                          '--format=%H|%s|%ai', '--no-merges']
            
            for cmd in [morning_cmd, evening_cmd]:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                if result.returncode == 0 and result.stdout.strip():
                    for line in result.stdout.strip().split('\n'):
                        if '|' in line:
                            parts = line.split('|', 2)
                            if len(parts) == 3:
                                night_commits.append({
                                    "hash": parts[0][:8],
                                    "message": parts[1],
                                    "timestamp": parts[2]
                                })
        
        # Sort by timestamp, most recent first
        night_commits.sort(key=lambda x: x["timestamp"], reverse=True)
        return night_commits[:10]  # Limit to 10 most recent
        
    except Exception:
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


def build_html():
    history = load_history()
    picks = load_picks()
    thoughts = load_thoughts()
    mood_history = load_mood_history()
    streaks = load_streaks()
    all_achievements = load_all_achievements()
    earned_achievements = load_earned_achievements()
    soundtracks = load_soundtracks()
    today_mood = load_today_mood()
    journal_dates = get_journal_dates()
    night_timeline = get_night_workshop_timeline()
    day_vs_night = get_day_vs_night_stats()
    night_commits = get_recent_night_commits()
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

    # Build achievement showcase
    achievements_data = all_achievements.get("achievements", {})
    tiers_data = all_achievements.get("tiers", {})
    earned_list = earned_achievements.get("earned", [])
    earned_ids = set(a.get("id") for a in earned_list)
    total_points = earned_achievements.get("total_points", 0)

    # Create achievement display list
    achievement_showcase = []
    for aid, achievement in achievements_data.items():
        is_earned = aid in earned_ids
        tier = achievement.get("tier", "bronze")
        tier_info = tiers_data.get(tier, {"emoji": "🏆", "color": "#888"})
        
        achievement_showcase.append({
            "id": aid,
            "name": achievement.get("name", "Unknown"),
            "description": achievement.get("description", ""),
            "tier": tier,
            "points": achievement.get("points", 0),
            "emoji": tier_info.get("emoji", "🏆"),
            "color": tier_info.get("color", "#888"),
            "is_earned": is_earned
        })

    # Sort achievements: earned first, then by tier
    tier_order = {"platinum": 4, "gold": 3, "silver": 2, "bronze": 1}
    achievement_showcase.sort(key=lambda x: (x["is_earned"], tier_order.get(x["tier"], 0)), reverse=True)

    # Mood history for graph (last 14 days)
    mood_graph_data = mood_history[-14:] if mood_history else []
    
    # Current streaks
    current_streaks = streaks.get("current_streaks", {})
    
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
<title>🧠 Intrusive Thoughts v2</title>
<style>
  :root {{ --bg: #0a0a0f; --card: #12121a; --border: #1e1e2e; --text: #c9c9d9; --accent: #f59e0b; --accent2: #8b5cf6; --dim: #555568; --success: #22c55e; --warning: #eab308; --danger: #ef4444; }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ background: var(--bg); color: var(--text); font-family: 'SF Mono', 'Fira Code', monospace; padding: 2rem; max-width: 1400px; margin: 0 auto; }}
  h1 {{ color: var(--accent); font-size: 2rem; margin-bottom: 0.3rem; }}
  .subtitle {{ color: var(--dim); margin-bottom: 2rem; }}
  .nav-tabs {{ display: flex; gap: 0.5rem; margin-bottom: 2rem; }}
  .nav-tab {{ padding: 0.8rem 1.5rem; background: var(--card); border: 1px solid var(--border); border-radius: 8px; cursor: pointer; transition: all 0.3s; }}
  .nav-tab.active {{ background: var(--accent); color: var(--bg); }}
  .nav-tab:hover {{ background: var(--border); }}
  .tab-content {{ display: none; }}
  .tab-content.active {{ display: block; }}
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
  .empty {{ color: var(--dim); font-style: italic; text-align: center; padding: 2rem; }}
  .mood-dot {{ width: 12px; height: 12px; border-radius: 50%; margin: 0 4px; display: inline-block; }}
  .achievement-item {{ display: flex; align-items: center; margin-bottom: 0.8rem; padding: 1rem; border-radius: 8px; transition: all 0.3s; border: 2px solid transparent; }}
  .achievement-item.earned {{ background: linear-gradient(135deg, var(--card), #1a1a2e); border-color: var(--accent); box-shadow: 0 0 20px rgba(245, 158, 11, 0.3); }}
  .achievement-item.unearned {{ background: var(--border); opacity: 0.6; }}
  .achievement-tier {{ margin-right: 1rem; font-size: 1.5rem; }}
  .achievement-info h4 {{ color: var(--accent); margin-bottom: 0.3rem; }}
  .achievement-info .desc {{ color: var(--dim); font-size: 0.85rem; margin-bottom: 0.3rem; }}
  .achievement-info .points {{ color: var(--accent2); font-size: 0.8rem; font-weight: bold; }}
  .journal-nav {{ display: flex; justify-content: center; gap: 1rem; margin-bottom: 1.5rem; }}
  .journal-nav button {{ padding: 0.5rem 1rem; background: var(--card); border: 1px solid var(--border); border-radius: 6px; color: var(--text); cursor: pointer; }}
  .journal-nav button:hover {{ background: var(--border); }}
  .journal-nav button:disabled {{ opacity: 0.5; cursor: not-allowed; }}
  .journal-entry {{ background: var(--border); border-radius: 8px; padding: 1.5rem; margin-bottom: 1rem; }}
  .journal-date {{ color: var(--accent); font-size: 1.1rem; margin-bottom: 1rem; display: flex; align-items: center; gap: 0.5rem; }}
  .journal-content {{ line-height: 1.6; }}
  .journal-content h1, .journal-content h2, .journal-content h3 {{ color: var(--accent); margin: 1rem 0 0.5rem; }}
  .journal-content p {{ margin-bottom: 1rem; }}
  .journal-content ul, .journal-content ol {{ margin: 0.5rem 0 1rem 2rem; }}
  .journal-content code {{ background: var(--card); padding: 0.2rem 0.4rem; border-radius: 4px; }}
  .journal-content pre {{ background: var(--card); padding: 1rem; border-radius: 8px; overflow-x: auto; margin: 1rem 0; }}
  .mood-context {{ display: flex; align-items: center; gap: 0.5rem; font-size: 0.9rem; color: var(--dim); }}
  .timeline-item {{ border-left: 3px solid var(--border); padding: 1rem 0 1rem 1.5rem; position: relative; }}
  .timeline-item::before {{ content: ''; width: 10px; height: 10px; border-radius: 50%; position: absolute; left: -6px; top: 1.2rem; }}
  .timeline-item.positive::before {{ background: var(--success); }}
  .timeline-item.negative::before {{ background: var(--danger); }}
  .timeline-item.neutral::before {{ background: var(--dim); }}
  .timeline-item .timestamp {{ color: var(--accent); font-size: 0.8rem; }}
  .timeline-item .thought-id {{ font-weight: bold; margin: 0.3rem 0; }}
  .timeline-item .energy-vibe {{ font-size: 0.8rem; color: var(--dim); }}
  .commit-item {{ background: var(--border); padding: 0.8rem; border-radius: 8px; margin-bottom: 0.5rem; }}
  .commit-hash {{ color: var(--accent); font-family: monospace; font-size: 0.8rem; }}
  .commit-message {{ margin-top: 0.3rem; }}
  .commit-time {{ color: var(--dim); font-size: 0.75rem; margin-top: 0.3rem; }}
  .stats-comparison {{ display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; }}
  .stats-column h3 {{ text-align: center; margin-bottom: 1rem; }}
  .stats-column.day h3 {{ color: #fbbf24; }}
  .stats-column.night h3 {{ color: #a78bfa; }}
  .stats-metric {{ display: flex; justify-content: space-between; margin-bottom: 0.5rem; padding: 0.5rem; background: var(--border); border-radius: 4px; }}
  .insight-box {{ background: linear-gradient(135deg, var(--accent2), var(--accent)); color: white; padding: 1rem; border-radius: 8px; margin-top: 1rem; text-align: center; }}
  footer {{ text-align: center; color: var(--dim); font-size: 0.75rem; margin-top: 2rem; }}
  .loading {{ text-align: center; color: var(--dim); padding: 2rem; }}
</style>
</head>
<body>
<h1>🧠 Intrusive Thoughts v2</h1>
<p class="subtitle">Night workshop & journal viewer — what Ember builds when you're sleeping 🌙</p>

{f'<div class="section"><div style="background: linear-gradient(135deg, var(--accent2), var(--accent)); padding: 1rem; border-radius: 12px; text-align: center; color: white; font-weight: bold;">{today_soundtrack}</div></div>' if today_soundtrack else ''}

<div class="nav-tabs">
  <div class="nav-tab active" onclick="switchTab('overview')">📊 Overview</div>
  <div class="nav-tab" onclick="switchTab('journal')">📓 Journal</div>
  <div class="nav-tab" onclick="switchTab('night-workshop')">🌙 Night Workshop</div>
  <div class="nav-tab" onclick="switchTab('achievements')">🏆 Achievements</div>
  <div class="nav-tab" onclick="switchTab('stats')">📈 Day vs Night</div>
</div>

<div id="overview" class="tab-content active">
  <div class="grid">
    <div class="stat-card"><div class="number">{total_picks}</div><div class="label">Total Impulses</div></div>
    <div class="stat-card"><div class="number">{total_completed}</div><div class="label">Completed</div></div>
    <div class="stat-card"><div class="number">{len(earned_achievements.get('earned', []))}</div><div class="label">🏆 Achievements</div></div>
    <div class="stat-card"><div class="number">{total_points}</div><div class="label">🎯 Points</div></div>
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
      {f'''<div style="background: var(--border); padding: 0.8rem; border-radius: 8px; margin-bottom: 0.5rem;"><strong>Activity:</strong> {current_streaks.get('activity_type', ['none'])[0]} × {len(current_streaks.get('activity_type', []))}</div>''' if current_streaks.get('activity_type') else ''}
      {f'''<div style="background: var(--border); padding: 0.8rem; border-radius: 8px; margin-bottom: 0.5rem;"><strong>Mood:</strong> {current_streaks.get('mood', ['none'])[0]} × {len(current_streaks.get('mood', []))}</div>''' if current_streaks.get('mood') else ''}
      {'<div class="empty">No active streaks</div>' if not current_streaks.get('activity_type') and not current_streaks.get('mood') else ''}
    </div>
  </div>

  {"<div class='section'><h2>💻 What I Built Last Night</h2>" + (''.join(f'<div class="commit-item"><div class="commit-hash">{commit["hash"]}</div><div class="commit-message">{commit["message"]}</div><div class="commit-time">{commit["timestamp"]}</div></div>' for commit in night_commits) if night_commits else '<div class="empty">No night commits found — either git is not available or I haven\'t been coding after hours</div>') + "</div>"}

  <div class="section">
    <h2>🎯 Most Common Impulses</h2>
    <div class="bar-chart">
      {''.join(f'''<div class="bar-row"><div class="bar-label">{name}</div><div class="bar" style="width: {max(count / max(top_thoughts[0][1], 1) * 100, 2):.0f}%"></div><div class="bar-count">{count}</div></div>''' for name, count in top_thoughts) if top_thoughts else '<div class="empty">No data yet — check back after some impulses fire</div>'}
    </div>
  </div>

  <div class="section">
    <h2>📝 Recent Activity</h2>
    {''.join(f"""<div class="history-item"><span class="time">{e.get('timestamp','?')[:16].replace('T',' ')}</span><span class="mood-tag mood-{e.get('mood','day')}">{e.get('mood','?')}</span> <strong>{e.get('thought_id','?')}</strong> <span style="color: var(--{'success' if e.get('vibe') == 'positive' else 'danger' if e.get('vibe') == 'negative' else 'dim'}); font-size: 0.8rem;">[{e.get('energy','?')}/{e.get('vibe','?')}]</span><div class="summary">{e.get('summary','')}</div></div>""" for e in recent) if recent else '<div class="empty">Nothing yet. First night session fires at 03:17 🌙</div>'}
  </div>
</div>

<div id="journal" class="tab-content">
  <div class="section">
    <h2>📓 Full Journal Viewer</h2>
    {f'<div class="journal-nav"><button onclick="prevJournalDate()" id="prevBtn">← Previous</button><button onclick="nextJournalDate()" id="nextBtn">Next →</button></div>' if journal_dates else ''}
    <div id="journal-viewer">
      {"<div class='loading'>Loading journal...</div>" if journal_dates else '<div class="empty">📖 No journal entries yet.<br><br>💡 <strong>Journals are generated after night workshops</strong><br><br>Your intrusive thoughts get processed into reflective journal entries during night sessions. Come back after some late-night productivity!</div>'}
    </div>
  </div>
</div>

<div id="night-workshop" class="tab-content">
  <div class="section">
    <h2>🌙 Night Workshop Timeline</h2>
    {''.join(f'''<div class="timeline-item {e.get('vibe', 'neutral')}"><div class="timestamp">{e.get('timestamp', '?')[:16].replace('T', ' ')}</div><div class="thought-id">{e.get('thought_id', '?')}</div><div class="energy-vibe">Energy: {e.get('energy', '?')} | Vibe: {e.get('vibe', '?')}</div><div style="margin-top: 0.5rem;">{e.get('summary', '')}</div></div>''' for e in night_timeline) if night_timeline else '<div class="empty">🌙 No night workshop sessions yet<br><br>Night workshops happen when the mood is set to "night" — these are deep focus sessions that happen after hours. Your timeline will populate as you work through the night.</div>'}
  </div>
</div>

<div id="achievements" class="tab-content">
  <div class="section">
    <h2>🏆 Achievement Gallery</h2>
    <div style="text-align: center; margin-bottom: 2rem; font-size: 1.2rem; color: var(--accent);">
      <strong>Total Points: {total_points}</strong>
    </div>
    {''.join(f'''<div class="achievement-item {'earned' if ach['is_earned'] else 'unearned'}"><div class="achievement-tier">{ach['emoji']}</div><div class="achievement-info"><h4>{ach['name']}</h4><div class="desc">{ach['description']}</div><div class="points">+{ach['points']} points</div></div></div>''' for ach in achievement_showcase) if achievement_showcase else '<div class="empty">No achievements defined yet</div>'}
  </div>
</div>

<div id="stats" class="tab-content">
  <div class="section">
    <h2>📈 Day vs Night Comparison</h2>
    <div class="stats-comparison">
      <div class="stats-column day">
        <h3>☀️ Day Work ({day_vs_night['day']['count']} sessions)</h3>
        <div class="stats-metric"><span>Avg Energy:</span><span>{day_vs_night['day']['avg_energy']:.1f}/3</span></div>
        <div class="stats-metric"><span>Avg Vibe:</span><span>{day_vs_night['day']['avg_vibe']:.1f}/3</span></div>
        <div style="margin-top: 1rem;">
          <strong>Energy Distribution:</strong>
          {''.join(f'<div class="stats-metric"><span>{energy.title()}:</span><span>{count}</span></div>' for energy, count in day_vs_night['day']['energy_dist'].items())}
        </div>
      </div>
      <div class="stats-column night">
        <h3>🌙 Night Work ({day_vs_night['night']['count']} sessions)</h3>
        <div class="stats-metric"><span>Avg Energy:</span><span>{day_vs_night['night']['avg_energy']:.1f}/3</span></div>
        <div class="stats-metric"><span>Avg Vibe:</span><span>{day_vs_night['night']['avg_vibe']:.1f}/3</span></div>
        <div style="margin-top: 1rem;">
          <strong>Energy Distribution:</strong>
          {''.join(f'<div class="stats-metric"><span>{energy.title()}:</span><span>{count}</span></div>' for energy, count in day_vs_night['night']['energy_dist'].items())}
        </div>
      </div>
    </div>
    <div class="insight-box">
      <strong>💡 Insights:</strong><br>
      {day_vs_night['insights']['best_day']}<br>
      {day_vs_night['insights']['best_night']}
    </div>
  </div>
</div>

<script>
let currentJournalIndex = 0;
const journalDates = {json.dumps(journal_dates)};

function switchTab(tabName) {{
  // Hide all tab contents
  document.querySelectorAll('.tab-content').forEach(content => {{
    content.classList.remove('active');
  }});
  
  // Deactivate all tabs
  document.querySelectorAll('.nav-tab').forEach(tab => {{
    tab.classList.remove('active');
  }});
  
  // Show selected tab content
  document.getElementById(tabName).classList.add('active');
  
  // Activate selected tab
  event.target.classList.add('active');
  
  // Load journal if switching to journal tab
  if (tabName === 'journal' && journalDates.length > 0) {{
    loadJournalEntry();
  }}
}}

function loadJournalEntry() {{
  if (journalDates.length === 0) return;
  
  const date = journalDates[currentJournalIndex];
  const viewer = document.getElementById('journal-viewer');
  viewer.innerHTML = '<div class="loading">Loading journal entry...</div>';
  
  fetch(`/api/journal?date=${{date}}`)
    .then(r => r.json())
    .then(data => {{
      if (data.error) {{
        viewer.innerHTML = '<div class="empty">Failed to load journal entry</div>';
        return;
      }}
      
      const moodContext = data.mood_context || {{}};
      let contextHtml = '';
      if (moodContext.emoji) {{
        contextHtml = `<div class="mood-context">${{moodContext.emoji}} ${{moodContext.name}}`;
        if (moodContext.description) {{
          contextHtml += ` — ${{moodContext.description}}`;
        }}
        if (moodContext.weather) {{
          contextHtml += ` | Weather: ${{moodContext.weather}}`;
        }}
        if (moodContext.news_vibe) {{
          contextHtml += ` | News: ${{moodContext.news_vibe}}`;
        }}
        contextHtml += '</div>';
      }}
      
      viewer.innerHTML = `
        <div class="journal-entry">
          <div class="journal-date">${{data.date}} ${{contextHtml}}</div>
          <div class="journal-content">${{data.html_content}}</div>
        </div>
      `;
      
      updateJournalNavButtons();
    }})
    .catch(() => {{
      viewer.innerHTML = '<div class="empty">Failed to load journal entry</div>';
    }});
}}

function prevJournalDate() {{
  if (currentJournalIndex < journalDates.length - 1) {{
    currentJournalIndex++;
    loadJournalEntry();
  }}
}}

function nextJournalDate() {{
  if (currentJournalIndex > 0) {{
    currentJournalIndex--;
    loadJournalEntry();
  }}
}}

function updateJournalNavButtons() {{
  const prevBtn = document.getElementById('prevBtn');
  const nextBtn = document.getElementById('nextBtn');
  
  if (prevBtn) prevBtn.disabled = currentJournalIndex >= journalDates.length - 1;
  if (nextBtn) nextBtn.disabled = currentJournalIndex <= 0;
}}

// Initialize journal if dates exist
if (journalDates.length > 0) {{
  updateJournalNavButtons();
}}
</script>

<footer>{get_agent_name()} {get_agent_emoji()} × Intrusive Thoughts v2.0 — refreshed {datetime.now().strftime('%Y-%m-%d %H:%M')}</footer>
</body>
</html>"""


class DashboardHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        query_params = parse_qs(parsed_url.query)
        
        if path == "/" or path == "/index.html":
            html = build_html()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode())
            
        elif path == "/api/journal":
            date = query_params.get('date', [''])[0]
            if date:
                entry = get_journal_entry(date)
                if entry:
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps(entry).encode())
                else:
                    self.send_response(404)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "Journal entry not found"}).encode())
            else:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Date parameter required"}).encode())
                
        elif path == "/api/journal/list":
            dates = get_journal_dates()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"dates": dates}).encode())
            
        elif path == "/api/achievements":
            all_achievements = load_all_achievements()
            earned_achievements = load_earned_achievements()
            earned_ids = set(a.get("id") for a in earned_achievements.get("earned", []))
            
            # Build response with earned status
            achievements_with_status = {}
            for aid, achievement in all_achievements.get("achievements", {}).items():
                achievements_with_status[aid] = {
                    **achievement,
                    "is_earned": aid in earned_ids
                }
            
            response = {
                "achievements": achievements_with_status,
                "tiers": all_achievements.get("tiers", {}),
                "earned": earned_achievements.get("earned", []),
                "total_points": earned_achievements.get("total_points", 0)
            }
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
        elif path == "/api/night-stats":
            stats = get_day_vs_night_stats()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(stats).encode())
            
        elif path == "/api/stats":
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
            
        elif path == "/api/health":
            try:
                from health_monitor import get_dashboard_data
                data = get_dashboard_data()
            except Exception:
                data = {"error": "health monitor unavailable"}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(data, default=str).encode())
            
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # Quiet


if __name__ == "__main__":
    print(f"🧠 Intrusive Thoughts Dashboard v2 running at http://localhost:{PORT}")
    HTTPServer(("0.0.0.0", PORT), DashboardHandler).serve_forever()