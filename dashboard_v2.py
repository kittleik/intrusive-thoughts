#!/usr/bin/env python3
"""🧠 Intrusive Thoughts Dashboard v2 — System health deep-dive & memory explorer."""

import json
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
from datetime import datetime
from collections import Counter
from pathlib import Path
from config import get_file_path, get_data_dir, get_dashboard_port, get_agent_name, get_agent_emoji

PORT = get_dashboard_port()
HISTORY_FILE = get_file_path("history.json")
THOUGHTS_FILE = get_file_path("thoughts.json")
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
<title>🧠 Intrusive Thoughts Dashboard v2</title>
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
  
  /* Dashboard v2 Styles */
  .tab-nav {{ display: flex; margin-bottom: 1rem; border-bottom: 1px solid var(--border); }}
  .tab-button {{ background: none; border: none; color: var(--dim); padding: 0.8rem 1rem; cursor: pointer; font-size: 0.85rem; border-bottom: 2px solid transparent; }}
  .tab-button:hover {{ color: var(--text); background: var(--border); }}
  .tab-button.active {{ color: var(--accent); border-bottom-color: var(--accent); }}
  .tab-content {{ display: none; }}
  .tab-content.active {{ display: block; }}
  
  /* Memory Explorer */
  .memory-controls {{ display: flex; gap: 1rem; align-items: center; margin-bottom: 1rem; }}
  .memory-controls input {{ flex: 1; padding: 0.5rem; background: var(--border); border: 1px solid var(--border); border-radius: 4px; color: var(--text); }}
  .memory-stats {{ display: flex; gap: 1rem; font-size: 0.8rem; }}
  .memory-stat {{ color: var(--dim); }}
  .memory-list {{ max-height: 400px; overflow-y: auto; }}
  .memory-item {{ background: var(--border); padding: 1rem; border-radius: 8px; margin-bottom: 0.8rem; }}
  .memory-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem; }}
  .memory-type {{ background: var(--accent2); color: white; padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.7rem; text-transform: uppercase; }}
  .memory-timestamp {{ color: var(--dim); font-size: 0.75rem; }}
  .memory-content {{ margin-bottom: 0.5rem; font-size: 0.9rem; }}
  .memory-strength-bar {{ position: relative; height: 6px; background: var(--bg); border-radius: 3px; margin-bottom: 0.5rem; }}
  .strength-fill {{ height: 100%; border-radius: 3px; transition: width 0.3s; }}
  .strength-label {{ font-size: 0.7rem; color: var(--dim); }}
  .memory-emotion, .memory-importance {{ font-size: 0.75rem; color: var(--dim); }}
  
  /* Trust Dashboard */
  .trust-gauge-container {{ text-align: center; margin: 1rem 0; }}
  .trust-gauge svg {{ max-width: 200px; }}
  .trust-score {{ font-size: 24px; font-weight: bold; fill: var(--text); }}
  .trust-breakdown {{ margin: 1rem 0; }}
  .trust-breakdown h3, .trust-events h3 {{ color: var(--accent2); margin-bottom: 0.8rem; }}
  .trust-category {{ display: flex; align-items: center; margin-bottom: 0.5rem; }}
  .category-name {{ width: 120px; font-size: 0.85rem; }}
  .category-bar {{ flex: 1; height: 20px; background: var(--bg); border-radius: 4px; position: relative; }}
  .category-fill {{ height: 100%; border-radius: 4px; }}
  .category-percent {{ position: absolute; right: 5px; top: 2px; font-size: 0.7rem; color: var(--text); }}
  .trust-events {{ margin-top: 1rem; }}
  .trust-event {{ display: flex; gap: 0.5rem; padding: 0.5rem 0; border-bottom: 1px solid var(--border); }}
  .trust-event:last-child {{ border-bottom: none; }}
  .event-time {{ font-size: 0.75rem; color: var(--dim); width: 120px; flex-shrink: 0; }}
  .event-outcome {{ width: 20px; }}
  .event-description {{ font-size: 0.85rem; }}
  
  /* Evolution History */
  .evolution-summary {{ display: flex; gap: 1rem; margin-bottom: 1rem; }}
  .evolution-stat {{ background: var(--border); padding: 0.8rem; border-radius: 6px; font-size: 0.85rem; }}
  .evolution-timeline {{ margin: 1rem 0; }}
  .evolution-timeline h3, .evolution-patterns h3 {{ color: var(--accent2); margin-bottom: 0.8rem; }}
  .evolution-cycle {{ background: var(--border); padding: 0.8rem; border-radius: 6px; margin-bottom: 0.5rem; }}
  .cycle-date {{ font-weight: bold; color: var(--accent); margin-bottom: 0.3rem; }}
  .cycle-stats {{ font-size: 0.8rem; color: var(--dim); }}
  .evolution-patterns {{ margin-top: 1rem; }}
  .evolution-pattern {{ background: var(--border); padding: 0.8rem; border-radius: 6px; margin-bottom: 0.5rem; }}
  .pattern-type {{ font-weight: bold; color: var(--accent); margin-bottom: 0.3rem; }}
  .pattern-desc {{ margin-bottom: 0.3rem; font-size: 0.9rem; }}
  .pattern-confidence {{ font-size: 0.75rem; color: var(--dim); }}
  
  /* Proactive Agent */
  .proactive-stats-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1rem; }}
  .proactive-wal, .proactive-buffer {{ background: var(--border); padding: 1rem; border-radius: 8px; }}
  .proactive-wal h3, .proactive-buffer h3 {{ color: var(--accent2); margin-bottom: 0.8rem; }}
  .wal-stat, .buffer-stat {{ margin-bottom: 0.3rem; font-size: 0.85rem; }}
  .buffer-items {{ margin-top: 0.8rem; }}
  .buffer-item {{ background: var(--bg); padding: 0.5rem; border-radius: 4px; margin-bottom: 0.3rem; display: flex; gap: 0.5rem; align-items: center; }}
  .item-priority {{ padding: 0.2rem 0.4rem; border-radius: 3px; font-size: 0.7rem; text-transform: uppercase; color: white; }}
  .item-priority.high {{ background: #ef4444; }}
  .item-priority.medium {{ background: var(--warning); }}
  .item-priority.low {{ background: var(--dim); }}
  .item-content {{ font-size: 0.8rem; }}
  .proactive-recent {{ margin-top: 1rem; }}
  .proactive-recent h3 {{ color: var(--accent2); margin-bottom: 0.8rem; }}
  .proactive-entry {{ display: flex; gap: 0.5rem; padding: 0.5rem 0; border-bottom: 1px solid var(--border); }}
  .proactive-entry:last-child {{ border-bottom: none; }}
  .entry-time {{ font-size: 0.75rem; color: var(--dim); width: 120px; flex-shrink: 0; }}
  .entry-outcome {{ width: 20px; }}
  .entry-content {{ font-size: 0.85rem; }}
  
  /* Health Monitor */
  .health-components {{ margin-bottom: 1rem; }}
  .health-components h3, .health-metrics h3, .health-incidents h3 {{ color: var(--accent2); margin-bottom: 0.8rem; }}
  .health-component {{ display: flex; align-items: center; gap: 1rem; padding: 0.8rem; background: var(--border); border-radius: 6px; margin-bottom: 0.5rem; }}
  .component-status {{ font-size: 1.2rem; }}
  .component-name {{ font-weight: bold; }}
  .component-message {{ color: var(--dim); font-size: 0.85rem; }}
  .health-metrics {{ margin-bottom: 1rem; }}
  .health-metric {{ margin-bottom: 0.3rem; font-size: 0.85rem; }}
  .health-incident {{ display: flex; gap: 0.5rem; padding: 0.5rem 0; border-bottom: 1px solid var(--border); }}
  .health-incident:last-child {{ border-bottom: none; }}
  .incident-id {{ font-weight: bold; color: var(--accent); width: 80px; flex-shrink: 0; }}
  .incident-status {{ width: 20px; }}
  .incident-desc {{ font-size: 0.85rem; }}
  
  footer {{ text-align: center; color: var(--dim); font-size: 0.75rem; margin-top: 2rem; }}
</style>
</head>
<body>
<h1>🧠 Intrusive Thoughts Dashboard v2</h1>
<p class="subtitle">System health deep-dive & memory explorer — now with full system visibility</p>

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

<div class="section">
  <h2>🔬 System Health Deep-Dive & Memory Explorer</h2>
  
  <!-- Tab Navigation -->
  <div class="tab-nav">
    <button class="tab-button active" onclick="showTab('memory')">🧠 Memory Explorer</button>
    <button class="tab-button" onclick="showTab('trust')">🛡️ Trust Dashboard</button>
    <button class="tab-button" onclick="showTab('evolution')">🧬 Evolution History</button>
    <button class="tab-button" onclick="showTab('proactive')">⚡ Proactive Agent</button>
    <button class="tab-button" onclick="showTab('health')">🚦 Health Monitor</button>
  </div>
  
  <!-- Memory Explorer Tab -->
  <div id="tab-memory" class="tab-content active">
    <div class="memory-controls">
      <input type="text" id="memory-search" placeholder="Search memories..." onkeyup="filterMemories()">
      <div class="memory-stats" id="memory-stats">Loading...</div>
    </div>
    <div id="memory-list" class="memory-list">Loading memories...</div>
  </div>
  
  <!-- Trust Dashboard Tab -->
  <div id="tab-trust" class="tab-content">
    <div class="trust-gauge-container">
      <div class="trust-gauge" id="trust-gauge">
        <svg viewBox="0 0 200 120" width="200" height="120">
          <path d="M 20 100 A 80 80 0 0 1 180 100" stroke="var(--border)" stroke-width="8" fill="none"/>
          <path id="trust-arc" d="M 20 100 A 80 80 0 0 1 180 100" stroke="var(--accent)" stroke-width="8" fill="none" stroke-dasharray="251.3" stroke-dashoffset="251.3"/>
          <text x="100" y="85" text-anchor="middle" class="trust-score" id="trust-score">--%</text>
        </svg>
      </div>
    </div>
    <div id="trust-breakdown" class="trust-breakdown">Loading...</div>
    <div id="trust-events" class="trust-events">Loading...</div>
  </div>
  
  <!-- Evolution History Tab -->
  <div id="tab-evolution" class="tab-content">
    <div id="evolution-summary" class="evolution-summary">Loading...</div>
    <div id="evolution-timeline" class="evolution-timeline">Loading...</div>
    <div id="evolution-patterns" class="evolution-patterns">Loading...</div>
  </div>
  
  <!-- Proactive Agent Tab -->
  <div id="tab-proactive" class="tab-content">
    <div class="proactive-stats-grid">
      <div class="proactive-wal" id="proactive-wal">Loading...</div>
      <div class="proactive-buffer" id="proactive-buffer">Loading...</div>
    </div>
    <div id="proactive-recent" class="proactive-recent">Loading...</div>
  </div>
  
  <!-- Health Monitor Tab -->
  <div id="tab-health" class="tab-content">
    <div id="health-components" class="health-components">Loading...</div>
    <div id="health-metrics" class="health-metrics">Loading...</div>
    <div id="health-incidents" class="health-incidents">Loading...</div>
  </div>
  
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

<script>
let memoryData = [];

// Tab switching
function showTab(tabName) {{
  /* Hide all tabs */
  document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
  document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
  
  /* Show selected tab */
  document.getElementById('tab-' + tabName).classList.add('active');
  event.target.classList.add('active');
  
  /* Load data for the selected tab */
  loadTabData(tabName);
}}

function loadTabData(tabName) {{
  if (tabName === 'memory') {{
    loadMemoryData();
  }} else if (tabName === 'trust') {{
    loadTrustData();
  }} else if (tabName === 'evolution') {{
    loadEvolutionData();
  }} else if (tabName === 'proactive') {{
    loadProactiveData();
  }} else if (tabName === 'health') {{
    loadHealthData();
  }}
}}

function loadMemoryData() {{
  fetch('/api/memory')
    .then(r => r.json())
    .then(data => {{
      if (data.error) {{
        document.getElementById('memory-list').innerHTML = '<div class="empty">' + data.error + '</div>';
        return;
      }}
      
      memoryData = data.memories || [];
      const stats = data.stats || {{}};
      
      /* Update stats */
      const storeSizes = stats.store_sizes || {{}};
      document.getElementById('memory-stats').innerHTML = 
        '<div class="memory-stat"><strong>Total:</strong> ' + (storeSizes.total || 0) + '</div>' +
        '<div class="memory-stat"><strong>Episodic:</strong> ' + (storeSizes.episodic || 0) + '</div>' +
        '<div class="memory-stat"><strong>Semantic:</strong> ' + (storeSizes.semantic || 0) + '</div>' +
        '<div class="memory-stat"><strong>Procedural:</strong> ' + (storeSizes.procedural || 0) + '</div>' +
        '<div class="memory-stat"><strong>Working:</strong> ' + (storeSizes.working || 0) + '</div>';
      
      displayMemories(memoryData);
    }})
    .catch(err => {{
      document.getElementById('memory-list').innerHTML = '<div class="empty">Failed to load memory data</div>';
    }});
}}

function displayMemories(memories) {{
  if (!memories.length) {{
    document.getElementById('memory-list').innerHTML = '<div class="empty">No memories found</div>';
    return;
  }}
  
  let html = '';
  memories.forEach(memory => {{
    const strengthColor = memory.strength > 0.7 ? 'var(--success)' : memory.strength > 0.3 ? 'var(--warning)' : '#ef4444';
    const strengthPercent = Math.round(memory.strength * 100);
    const timestamp = new Date(memory.timestamp * 1000).toLocaleString();
    const content = memory.content || memory.action || 'Unknown content';
    
    html += '<div class="memory-item">' +
            '<div class="memory-header">' +
            '<span class="memory-type">' + memory.memory_type + '</span>' +
            '<span class="memory-timestamp">' + timestamp + '</span>' +
            '</div>' +
            '<div class="memory-content">' + content + '</div>' +
            '<div class="memory-strength-bar">' +
            '<div class="strength-fill" style="width: ' + strengthPercent + '%; background-color: ' + strengthColor + ';"></div>' +
            '<span class="strength-label">Strength: ' + strengthPercent + '%</span>' +
            '</div>' +
            (memory.emotion ? '<div class="memory-emotion">Emotion: ' + memory.emotion + '</div>' : '') +
            (memory.importance ? '<div class="memory-importance">Importance: ' + Math.round(memory.importance * 100) + '%</div>' : '') +
            '</div>';
  }});
  
  document.getElementById('memory-list').innerHTML = html;
}}

function filterMemories() {{
  const query = document.getElementById('memory-search').value.toLowerCase();
  if (!query) {{
    displayMemories(memoryData);
    return;
  }}
  
  const filtered = memoryData.filter(memory => {{
    const content = (memory.content || memory.action || '').toLowerCase();
    return content.includes(query) || 
           (memory.memory_type || '').toLowerCase().includes(query) ||
           (memory.emotion || '').toLowerCase().includes(query);
  }});
  
  displayMemories(filtered);
}}

function loadTrustData() {{
  fetch('/api/trust')
    .then(r => r.json())
    .then(data => {{
      if (data.error) {{
        document.getElementById('trust-breakdown').innerHTML = '<div class="empty">' + data.error + '</div>';
        return;
      }}
      
      /* Update trust gauge */
      const trustScore = Math.round((data.global_trust || 0) * 100);
      const arc = document.getElementById('trust-arc');
      const scoreText = document.getElementById('trust-score');
      const circumference = 251.3;
      const offset = circumference * (1 - (data.global_trust || 0));
      
      arc.style.strokeDashoffset = offset;
      scoreText.textContent = trustScore + '%';
      
      /* Color based on trust level */
      if (trustScore >= 70) {{
        arc.style.stroke = 'var(--success)';
      }} else if (trustScore >= 30) {{
        arc.style.stroke = 'var(--warning)';
      }} else {{
        arc.style.stroke = '#ef4444';
      }}
      
      /* Trust breakdown */
      let breakdownHtml = '<h3>Trust by Category</h3>';
      const categoryTrust = data.category_trust || {{}};
      for (const [category, trust] of Object.entries(categoryTrust)) {{
        const percent = Math.round(trust * 100);
        const color = percent >= 70 ? 'var(--success)' : percent >= 30 ? 'var(--warning)' : '#ef4444';
        breakdownHtml += '<div class="trust-category">' +
                        '<span class="category-name">' + category.replace('_', ' ') + '</span>' +
                        '<div class="category-bar">' +
                        '<div class="category-fill" style="width: ' + percent + '%; background-color: ' + color + ';"></div>' +
                        '<span class="category-percent">' + percent + '%</span>' +
                        '</div>' +
                        '</div>';
      }}
      document.getElementById('trust-breakdown').innerHTML = breakdownHtml;
      
      /* Recent events */
      const events = data.recent_events || [];
      let eventsHtml = '<h3>Recent Trust Events</h3>';
      if (events.length === 0) {{
        eventsHtml += '<div class="empty">No recent events</div>';
      }} else {{
        events.slice(0, 5).forEach(event => {{
          const outcomeIcon = event.outcome === 'success' ? '✅' : event.outcome === 'failure' ? '❌' : '⏳';
          eventsHtml += '<div class="trust-event">' +
                       '<span class="event-time">' + new Date(event.timestamp).toLocaleString() + '</span>' +
                       '<span class="event-outcome">' + outcomeIcon + '</span>' +
                       '<span class="event-description">' + event.description + '</span>' +
                       '</div>';
        }});
      }}
      document.getElementById('trust-events').innerHTML = eventsHtml;
    }})
    .catch(err => {{
      document.getElementById('trust-breakdown').innerHTML = '<div class="empty">Failed to load trust data</div>';
    }});
}}

function loadEvolutionData() {{
  fetch('/api/evolution')
    .then(r => r.json())
    .then(data => {{
      if (data.error) {{
        document.getElementById('evolution-summary').innerHTML = '<div class="empty">' + data.error + '</div>';
        return;
      }}
      
      const stats = data.stats || {{}};
      
      /* Summary */
      document.getElementById('evolution-summary').innerHTML = 
        '<div class="evolution-stat"><strong>Total Patterns:</strong> ' + (stats.total_patterns || 0) + '</div>' +
        '<div class="evolution-stat"><strong>Evolution Cycles:</strong> ' + (stats.evolution_cycles || 0) + '</div>' +
        '<div class="evolution-stat"><strong>Weight Adjustments:</strong> ' + ((stats.weight_adjustments && stats.weight_adjustments.moods || 0) + (stats.weight_adjustments && stats.weight_adjustments.thoughts || 0)) + '</div>' +
        '<div class="evolution-stat"><strong>Data Quality:</strong> ' + (stats.data_quality && stats.data_quality.activities || 0) + ' activities</div>';
      
      /* Timeline */
      const history = data.evolution_history || [];
      let timelineHtml = '<h3>Evolution Timeline</h3>';
      if (history.length === 0) {{
        timelineHtml += '<div class="empty">No evolution cycles yet</div>';
      }} else {{
        history.slice(-5).forEach(cycle => {{
          timelineHtml += '<div class="evolution-cycle">' +
                         '<div class="cycle-date">' + new Date(cycle.timestamp).toLocaleDateString() + '</div>' +
                         '<div class="cycle-stats">' +
                         'Patterns: ' + (cycle.new_patterns_discovered || 0) + ' | ' +
                         'Adjustments: ' + (cycle.weight_adjustments_made || 0) + ' |' +
                         'Ruts: ' + (cycle.ruts_detected || 0) +
                         '</div>' +
                         '</div>';
        }});
      }}
      document.getElementById('evolution-timeline').innerHTML = timelineHtml;
      
      /* Patterns */
      const patterns = data.patterns || [];
      let patternsHtml = '<h3>Discovered Patterns</h3>';
      if (patterns.length === 0) {{
        patternsHtml += '<div class="empty">No patterns discovered yet</div>';
      }} else {{
        patterns.slice(-10).forEach(pattern => {{
          const confidence = Math.round((pattern.confidence || 0) * 100);
          patternsHtml += '<div class="evolution-pattern">' +
                         '<div class="pattern-type">' + pattern.type + '</div>' +
                         '<div class="pattern-desc">' + pattern.description + '</div>' +
                         '<div class="pattern-confidence">Confidence: ' + confidence + '%</div>' +
                         '</div>';
        }});
      }}
      document.getElementById('evolution-patterns').innerHTML = patternsHtml;
    }})
    .catch(err => {{
      document.getElementById('evolution-summary').innerHTML = '<div class="empty">Failed to load evolution data</div>';
    }});
}}

function loadProactiveData() {{
  fetch('/api/proactive')
    .then(r => r.json())
    .then(data => {{
      if (data.error) {{
        document.getElementById('proactive-wal').innerHTML = '<div class="empty">' + data.error + '</div>';
        return;
      }}
      
      const walStats = data.wal_stats || {{}};
      const buffer = data.buffer || {{}};
      
      /* WAL Stats */
      document.getElementById('proactive-wal').innerHTML = 
        '<h3>Write-Ahead Log</h3>' +
        '<div class="wal-stat"><strong>Total Entries:</strong> ' + (walStats.total_entries || 0) + '</div>' +
        '<div class="wal-stat"><strong>Success Rate:</strong> ' + Math.round((walStats.success_rate || 0) * 100) + '%</div>' +
        '<div class="wal-stat"><strong>Most Productive Mood:</strong> ' + (walStats.most_productive_mood || 'Unknown') + '</div>' +
        '<div class="wal-stat"><strong>Avg Energy Cost:</strong> ' + (walStats.avg_energy_cost || 0) + '</div>' +
        '<div class="wal-stat"><strong>Avg Value Generated:</strong> ' + (walStats.avg_value_generated || 0) + '</div>';
      
      /* Buffer Status */
      let bufferHtml = '<h3>Working Buffer</h3>' +
        '<div class="buffer-stat"><strong>Active Items:</strong> ' + (buffer.active_items || []).length + '</div>' +
        '<div class="buffer-stat"><strong>Completed:</strong> ' + (buffer.completed_count || 0) + '</div>' +
        '<div class="buffer-stat"><strong>Expired:</strong> ' + (buffer.expired_count || 0) + '</div>' +
        '<div class="buffer-items">';
      
      (buffer.active_items || []).slice(0, 3).forEach(item => {{
        bufferHtml += '<div class="buffer-item">' +
                     '<span class="item-priority ' + item.priority + '">' + item.priority + '</span>' +
                     '<span class="item-content">' + item.content + '</span>' +
                     '</div>';
      }});
      bufferHtml += '</div>';
      document.getElementById('proactive-buffer').innerHTML = bufferHtml;
      
      /* Recent entries */
      const recentEntries = data.recent_entries || [];
      let recentHtml = '<h3>Recent Decisions</h3>';
      if (recentEntries.length === 0) {{
        recentHtml += '<div class="empty">No recent entries</div>';
      }} else {{
        recentEntries.forEach(entry => {{
          const outcomeIcon = entry.outcome === 'success' ? '✅' : entry.outcome === 'failure' ? '❌' : '⏳';
          recentHtml += '<div class="proactive-entry">' +
                       '<span class="entry-time">' + new Date(entry.timestamp).toLocaleString() + '</span>' +
                       '<span class="entry-outcome">' + outcomeIcon + '</span>' +
                       '<span class="entry-content">' + entry.content + '</span>' +
                       '</div>';
        }});
      }}
      document.getElementById('proactive-recent').innerHTML = recentHtml;
    }})
    .catch(err => {{
      document.getElementById('proactive-wal').innerHTML = '<div class="empty">Failed to load proactive data</div>';
    }});
}}

function loadHealthData() {{
  fetch('/api/health')
    .then(r => r.json())
    .then(data => {{
      if (data.error) {{
        document.getElementById('health-components').innerHTML = '<div class="empty">' + data.error + '</div>';
        return;
      }}
      
      /* Components */
      let componentsHtml = '<h3>System Components</h3>';
      if (data.components) {{
        for (const [name, comp] of Object.entries(data.components)) {{
          componentsHtml += '<div class="health-component">' +
                           '<div class="component-status">' + comp.emoji + '</div>' +
                           '<div class="component-name">' + name.replace('_', ' ') + '</div>' +
                           '<div class="component-message">' + (comp.message || 'OK') + '</div>' +
                           '</div>';
        }}
      }}
      document.getElementById('health-components').innerHTML = componentsHtml;
      
      /* Metrics */
      const metrics = data.metrics || {{}};
      document.getElementById('health-metrics').innerHTML = 
        '<h3>System Metrics</h3>' +
        '<div class="health-metric"><strong>Heartbeats:</strong> ' + (metrics.total_heartbeats || 0) + '</div>' +
        '<div class="health-metric"><strong>Incidents:</strong> ' + (metrics.total_incidents || 0) + '</div>' +
        '<div class="health-metric"><strong>Healthy Streak:</strong> ' + (metrics.consecutive_healthy || 0) + '</div>' +
        '<div class="health-metric"><strong>24h Heartbeats:</strong> ' + (data.heartbeat_count_24h || 0) + '</div>';
      
      /* Recent incidents */
      const incidents = data.recent_incidents || [];
      let incidentsHtml = '<h3>Recent Incidents</h3>';
      if (incidents.length === 0) {{
        incidentsHtml += '<div class="empty">No recent incidents</div>';
      }} else {{
        incidents.forEach(incident => {{
          const resolvedIcon = incident.resolved ? '✅' : '❌';
          incidentsHtml += '<div class="health-incident">' +
                          '<span class="incident-id">' + incident.id + '</span>' +
                          '<span class="incident-status">' + resolvedIcon + '</span>' +
                          '<span class="incident-desc">' + incident.description + '</span>' +
                          '</div>';
        }});
      }}
      document.getElementById('health-incidents').innerHTML = incidentsHtml;
    }})
    .catch(err => {{
      document.getElementById('health-components').innerHTML = '<div class="empty">Failed to load health data</div>';
    }});
}}

/* Load initial tab data */
document.addEventListener('DOMContentLoaded', function() {{
  loadMemoryData();
}});
</script>

<footer>{get_agent_name()} {get_agent_emoji()} × Intrusive Thoughts Dashboard v2 — refreshed {datetime.now().strftime('%Y-%m-%d %H:%M')}</footer>
</body>
</html>"""


def load_v1_systems():
    """Load data from all v1.0 systems for dashboard display."""
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
        elif self.path == "/api/memory":
            try:
                from memory_system import MemorySystem
                ms = MemorySystem()
                # Get all memories from all stores
                episodic = ms._load_store(ms.episodic_path)
                semantic = ms._load_store(ms.semantic_path)
                procedural = ms._load_store(ms.procedural_path)
                working = ms._load_store(ms.working_path)
                
                # Add memory type and calculate strength for episodic memories
                current_time = ms._get_timestamp()
                memories = []
                
                for memory in episodic:
                    strength = ms._calculate_decay(
                        memory["timestamp"],
                        memory["decay_rate"],
                        memory["reinforcement_count"]
                    )
                    memory_data = memory.copy()
                    memory_data["memory_type"] = "episodic"
                    memory_data["strength"] = strength
                    memories.append(memory_data)
                
                for memory in semantic:
                    memory_data = memory.copy()
                    memory_data["memory_type"] = "semantic"
                    memory_data["strength"] = memory.get("strength", 1.0)
                    memories.append(memory_data)
                
                for memory in procedural:
                    memory_data = memory.copy()
                    memory_data["memory_type"] = "procedural"
                    memory_data["strength"] = min(1.0, memory.get("reinforcement_count", 1) / 10.0)
                    memories.append(memory_data)
                
                for memory in working:
                    memory_data = memory.copy()
                    memory_data["memory_type"] = "working"
                    memory_data["strength"] = 1.0  # Working memory is always at full strength
                    memories.append(memory_data)
                
                data = {
                    "memories": memories,
                    "stats": ms.get_stats()
                }
            except Exception as e:
                data = {"error": f"memory system unavailable: {e}"}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(data, default=str).encode())
        elif self.path == "/api/trust":
            try:
                from trust_system import TrustSystem
                ts = TrustSystem()
                data = ts.get_stats()
                # Add trust events/history
                history = ts.get_history(limit=20)
                data["recent_events"] = history
            except Exception as e:
                data = {"error": f"trust system unavailable: {e}"}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(data, default=str).encode())
        elif self.path == "/api/evolution":
            try:
                from self_evolution import SelfEvolutionSystem
                se = SelfEvolutionSystem()
                stats = se.get_stats()
                # Add evolution history and patterns
                data = {
                    "stats": stats,
                    "evolution_history": se.learnings.get("evolution_history", []),
                    "patterns": se.learnings.get("patterns", []),
                    "weight_adjustments": se.get_learned_weights()
                }
            except Exception as e:
                data = {"error": f"evolution system unavailable: {e}"}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(data, default=str).encode())
        elif self.path == "/api/proactive":
            try:
                from proactive import ProactiveAgent
                pa = ProactiveAgent()
                stats = pa.wal_stats()
                # Add buffer status
                buffer_data = pa._load_buffer()
                pa._prune_expired_items(buffer_data)
                data = {
                    "wal_stats": stats,
                    "buffer": {
                        "active_items": buffer_data["active_items"],
                        "completed_count": len(buffer_data["completed"]),
                        "expired_count": len(buffer_data["expired"])
                    },
                    "recent_entries": pa.wal_search(limit=10)
                }
            except Exception as e:
                data = {"error": f"proactive system unavailable: {e}"}
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