#!/usr/bin/env python3
"""🧠 Intrusive Thoughts Dashboard v2 — Interactive tuning controls."""

import json
import os
import subprocess
from http.server import HTTPServer, SimpleHTTPRequestHandler
from datetime import datetime
from collections import Counter
from pathlib import Path
from config import get_file_path, get_data_dir, get_dashboard_port, get_agent_name, get_agent_emoji

PORT = get_dashboard_port()
HISTORY_FILE = get_file_path("history.json")
THOUGHTS_FILE = get_file_path("thoughts.json")
MOODS_FILE = get_file_path("moods.json")
TODAY_MOOD_FILE = get_file_path("today_mood.json")
TODAY_SCHEDULE_FILE = get_file_path("today_schedule.json")
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


def load_moods():
    try:
        return json.loads(MOODS_FILE.read_text())
    except:
        return {}


def save_thoughts(data):
    """Save updated thoughts data."""
    THOUGHTS_FILE.write_text(json.dumps(data, indent=2))


def save_today_mood(data):
    """Save updated today mood data."""
    TODAY_MOOD_FILE.write_text(json.dumps(data, indent=2))


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
        return json.loads(TODAY_MOOD_FILE.read_text())
    except:
        return {}


def load_today_schedule():
    try:
        return json.loads(TODAY_SCHEDULE_FILE.read_text())
    except:
        return {}


def load_presets():
    """Load all preset files."""
    presets = []
    presets_dir = Path(__file__).parent / "presets"
    if presets_dir.exists():
        for preset_file in presets_dir.glob("*.json"):
            try:
                data = json.loads(preset_file.read_text())
                data["filename"] = preset_file.name
                presets.append(data)
            except:
                continue
    return presets


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


def trigger_impulse():
    """Run intrusive.sh day command and return result."""
    try:
        result = subprocess.run(['./intrusive.sh', 'day'], 
                              cwd=Path(__file__).parent,
                              capture_output=True, text=True, timeout=30)
        return {"success": True, "output": result.stdout, "error": result.stderr}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_effective_weight(thought_weight, thought_id, today_mood_data, moods_data):
    """Calculate effective weight with mood modifiers."""
    if not today_mood_data or not moods_data:
        return thought_weight
    
    mood_id = today_mood_data.get("id")
    if not mood_id:
        return thought_weight
    
    # Find the mood data
    mood_info = None
    for mood in moods_data.get("base_moods", []):
        if mood["id"] == mood_id:
            mood_info = mood
            break
    
    if not mood_info:
        return thought_weight
    
    # Simple modifier based on whether thought appears in boosted/dampened traits
    boosted_traits = today_mood_data.get("boosted_traits", [])
    dampened_traits = today_mood_data.get("dampened_traits", [])
    
    modifier = 1.0
    if thought_id in boosted_traits:
        modifier = 1.5
    elif thought_id in dampened_traits:
        modifier = 0.7
    
    return round(thought_weight * modifier, 2)


def build_html():
    history = load_history()
    picks = load_picks()
    thoughts = load_thoughts()
    moods_data = load_moods()
    today_mood = load_today_mood()
    mood_history = load_mood_history()
    streaks = load_streaks()
    achievements = load_achievements()
    soundtracks = load_soundtracks()
    journal_entries = load_journal_entries()
    productivity_stats = get_productivity_stats()
    presets = load_presets()
    schedule = load_today_schedule()

    # Stats
    thought_counts = Counter(p.get("thought", "?") for p in picks)
    mood_counts = Counter(p.get("mood", "?") for p in picks)
    total_picks = len(picks)
    total_completed = len(history)

    # Top thoughts chart data
    top_thoughts = thought_counts.most_common(15)

    # Recent history
    recent = history[-20:][::-1]

    # Build thought catalog with effective weights
    all_thoughts = []
    for mood_name, mood_data in thoughts.get("moods", {}).items():
        for t in mood_data.get("thoughts", []):
            weight = t.get("weight", 1)
            effective_weight = get_effective_weight(weight, t["id"], today_mood, moods_data)
            all_thoughts.append({
                "id": t["id"],
                "mood": mood_name,
                "weight": weight,
                "effective_weight": effective_weight,
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
<title>🧠 Intrusive Thoughts v2</title>
<style>
  :root {{ --bg: #0a0a0f; --card: #12121a; --border: #1e1e2e; --text: #c9c9d9; --accent: #f59e0b; --accent2: #8b5cf6; --dim: #555568; --success: #22c55e; --warning: #eab308; --danger: #ef4444; }}
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
  .soundtrack {{ background: linear-gradient(135deg, var(--accent2), var(--accent)); padding: 1rem; border-radius: 12px; text-align: center; color: white; margin-bottom: 2rem; }}

  /* NEW v2 STYLES */
  .weight-editor {{ display: flex; align-items: center; gap: 1rem; padding: 0.8rem 0; border-bottom: 1px solid var(--border); }}
  .weight-editor:last-child {{ border: none; }}
  .weight-editor .thought-info {{ flex: 1; }}
  .weight-editor .thought-id {{ color: var(--accent); font-size: 0.9rem; font-weight: bold; }}
  .weight-editor .thought-prompt {{ color: var(--text); font-size: 0.8rem; margin-top: 0.2rem; }}
  .weight-editor .weight-controls {{ display: flex; align-items: center; gap: 0.5rem; }}
  .weight-input {{ background: var(--border); color: var(--text); border: 1px solid var(--dim); border-radius: 6px; padding: 0.4rem; width: 70px; text-align: center; }}
  .weight-bar {{ height: 8px; background: linear-gradient(90deg, var(--accent2), var(--accent)); border-radius: 4px; min-width: 4px; }}
  .save-btn {{ background: var(--success); color: white; border: none; padding: 0.4rem 0.8rem; border-radius: 6px; cursor: pointer; font-size: 0.8rem; }}
  .save-btn:hover {{ opacity: 0.8; }}
  .save-btn:disabled {{ background: var(--dim); cursor: not-allowed; }}

  .mood-selector {{ display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem; }}
  .mood-dropdown {{ background: var(--border); color: var(--text); border: 1px solid var(--dim); border-radius: 6px; padding: 0.5rem; }}
  .set-mood-btn, .trigger-btn {{ background: var(--accent2); color: white; border: none; padding: 0.5rem 1rem; border-radius: 6px; cursor: pointer; }}
  .set-mood-btn:hover, .trigger-btn:hover {{ opacity: 0.8; }}
  .trigger-result {{ background: var(--border); padding: 1rem; border-radius: 8px; margin-top: 1rem; font-family: monospace; font-size: 0.8rem; white-space: pre-wrap; }}

  .mood-viewer {{ margin-bottom: 1.5rem; }}
  .mood-viewer h3 {{ color: var(--accent); font-size: 1rem; margin-bottom: 0.5rem; }}
  .mood-traits {{ display: flex; flex-wrap: wrap; gap: 0.3rem; margin-bottom: 0.8rem; }}
  .mood-traits .boost {{ background: var(--success); color: white; padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.7rem; }}
  .mood-traits .dampen {{ background: var(--danger); color: white; padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.7rem; }}

  .schedule-item {{ display: flex; align-items: center; gap: 1rem; padding: 0.5rem; border-radius: 6px; margin-bottom: 0.5rem; }}
  .schedule-item.fired {{ background: var(--border); }}
  .schedule-item.upcoming {{ background: var(--success); color: white; }}
  .schedule-time {{ font-weight: bold; min-width: 60px; }}
  .schedule-status {{ font-size: 0.8rem; padding: 0.2rem 0.5rem; border-radius: 4px; }}
  .status-fired {{ background: var(--dim); color: white; }}
  .status-upcoming {{ background: var(--warning); color: black; }}

  .preset-item {{ background: var(--border); padding: 1rem; border-radius: 8px; margin-bottom: 1rem; }}
  .preset-header {{ display: flex; justify-content: space-between; align-items: start; margin-bottom: 0.5rem; }}
  .preset-name {{ color: var(--accent); font-weight: bold; }}
  .preset-desc {{ color: var(--text); font-size: 0.9rem; margin-bottom: 0.5rem; }}
  .preset-weights {{ color: var(--dim); font-size: 0.8rem; }}
  .apply-btn {{ background: var(--accent); color: white; border: none; padding: 0.5rem 1rem; border-radius: 6px; cursor: pointer; }}
  .apply-btn:hover {{ opacity: 0.8; }}

  footer {{ text-align: center; color: var(--dim); font-size: 0.75rem; margin-top: 2rem; }}
</style>
</head>
<body>
<h1>🧠 Intrusive Thoughts v2</h1>
<p class="subtitle">Interactive tuning controls — now with weight editing, mood overrides, and preset management</p>

{f'<div class="soundtrack">{today_soundtrack}</div>' if today_soundtrack else ''}

<div class="grid">
  <div class="stat-card"><div class="number">{total_picks}</div><div class="label">Total Impulses</div></div>
  <div class="stat-card"><div class="number">{total_completed}</div><div class="label">Completed</div></div>
  <div class="stat-card"><div class="number">{len(achievements.get('earned', []))}</div><div class="label">🏆 Achievements</div></div>
  <div class="stat-card"><div class="number">{achievements.get('total_points', 0)}</div><div class="label">🎯 Points</div></div>
</div>

<!-- NEW v2 SECTIONS -->

<div class="grid-2">
  <div class="section">
    <h2>🎛️ Thought Weight Editor</h2>
    <div id="weight-editor">
      {''.join(f'''
      <div class="weight-editor">
        <div class="thought-info">
          <div class="thought-id">{t["id"]}</div>
          <div class="thought-prompt">{t["prompt"][:80]}{'...' if len(t["prompt"]) > 80 else ''}</div>
        </div>
        <div class="weight-controls">
          <span style="font-size: 0.8rem; color: var(--dim);">Base: {t["weight"]}</span>
          <input type="number" class="weight-input" value="{t["weight"]}" min="0.1" max="3.0" step="0.1" data-thought-id="{t["id"]}" data-mood="{t["mood"]}">
          <span style="font-size: 0.8rem; color: var(--accent);">Effective: {t["effective_weight"]}</span>
          <div class="weight-bar" style="width: {min(t["effective_weight"] * 30, 100)}px;"></div>
          <button class="save-btn" onclick="saveWeight('{t["id"]}', '{t["mood"]}')">Save</button>
        </div>
      </div>
      ''' for t in all_thoughts)}
    </div>
  </div>

  <div class="section">
    <h2>🌊 Mood Boost/Dampen Viewer</h2>
    {''.join(f'''
    <div class="mood-viewer">
      <h3>{mood.get("emoji", "")} {mood.get("name", "")} (weight: {mood.get("weight", 1)})</h3>
      <div class="mood-traits">
        {f'<span class="boost">Boosted: {", ".join(mood.get("traits", []))}</span>' if mood.get("traits") else ''}
      </div>
    </div>
    ''' for mood in moods_data.get("base_moods", [])) if moods_data.get("base_moods") else '<div class="empty">No mood data available</div>'}
  </div>
</div>

<div class="grid-2">
  <div class="section">
    <h2>🎯 Live Mood Override</h2>
    <div class="mood-selector">
      <select class="mood-dropdown" id="mood-select">
        <option value="">Select mood...</option>
        {''.join(f'<option value="{mood["id"]}" {"selected" if today_mood.get("id") == mood["id"] else ""}>{mood["emoji"]} {mood["name"]}</option>' for mood in moods_data.get("base_moods", []))}
      </select>
      <button class="set-mood-btn" onclick="setMood()">Set Mood</button>
      <button class="trigger-btn" onclick="triggerImpulse()">Trigger Impulse Now</button>
    </div>
    <div id="current-mood">
      {f'<strong>Current:</strong> {today_mood.get("emoji", "")} {today_mood.get("name", "None")} ({today_mood.get("date", "")})<br><em>{today_mood.get("description", "")}</em>' if today_mood else '<em>No mood set for today</em>'}
    </div>
    <div id="trigger-result"></div>
  </div>

  <div class="section">
    <h2>📅 Today's Schedule</h2>
    <div id="schedule-viewer">
      {f'''
      <div style="margin-bottom: 1rem; color: var(--dim); font-size: 0.8rem;">Generated: {schedule.get("generated_at", "Unknown")}</div>
      {''.join(f"""
      <div class="schedule-item {'fired' if item.get('fired') else 'upcoming'}">
        <div class="schedule-time">{item.get('time', '??:??')}</div>
        <div style="flex: 1;">{item.get('thought_type', 'Unknown')}</div>
        <div class="schedule-status {'status-fired' if item.get('fired') else 'status-upcoming'}">
          {'Fired' if item.get('fired') else 'Upcoming'}
        </div>
      </div>
      """ for item in schedule.get('schedule', []))}
      ''' if schedule.get('schedule') else '<div class="empty">No schedule available. Run morning ritual to generate.</div>'}
    </div>
  </div>
</div>

<div class="section">
  <h2>🎨 Preset Browser</h2>
  <div id="preset-browser">
    {''.join(f'''
    <div class="preset-item">
      <div class="preset-header">
        <div>
          <div class="preset-name">{preset.get("emoji", "⚙️")} {preset.get("name", "Unnamed")}</div>
        </div>
        <button class="apply-btn" onclick="applyPreset('{preset.get("filename", "")}')">Apply</button>
      </div>
      <div class="preset-weights">Mood weights: {", ".join([f"{k}={v}" for k, v in preset.get("mood_weights", {}).items()])}</div>
    </div>
    ''' for preset in presets) if presets else '<div class="empty">No presets found</div>'}
  </div>
</div>

<!-- ORIGINAL SECTIONS -->

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
// Weight editor functionality
function saveWeight(thoughtId, mood) {{
  const input = document.querySelector(`input[data-thought-id="${{thoughtId}}"]`);
  const weight = parseFloat(input.value);
  
  if (weight < 0.1 || weight > 3.0) {{
    alert('Weight must be between 0.1 and 3.0');
    return;
  }}
  
  fetch('/api/thought-weight', {{
    method: 'PUT',
    headers: {{ 'Content-Type': 'application/json' }},
    body: JSON.stringify({{ thought_id: thoughtId, mood: mood, weight: weight }})
  }})
  .then(r => r.json())
  .then(data => {{
    if (data.success) {{
      alert('Weight updated!');
      location.reload();
    }} else {{
      alert('Failed to update: ' + (data.error || 'Unknown error'));
    }}
  }})
  .catch(e => alert('Error: ' + e));
}}

// Mood override functionality
function setMood() {{
  const select = document.getElementById('mood-select');
  const moodId = select.value;
  
  if (!moodId) {{
    alert('Please select a mood');
    return;
  }}
  
  fetch('/api/set-mood', {{
    method: 'POST',
    headers: {{ 'Content-Type': 'application/json' }},
    body: JSON.stringify({{ mood_id: moodId }})
  }})
  .then(r => r.json())
  .then(data => {{
    if (data.success) {{
      alert('Mood set!');
      location.reload();
    }} else {{
      alert('Failed to set mood: ' + (data.error || 'Unknown error'));
    }}
  }})
  .catch(e => alert('Error: ' + e));
}}

// Trigger impulse functionality
function triggerImpulse() {{
  const resultDiv = document.getElementById('trigger-result');
  resultDiv.innerHTML = 'Triggering impulse...';
  
  fetch('/api/trigger', {{
    method: 'POST'
  }})
  .then(r => r.json())
  .then(data => {{
    if (data.success) {{
      resultDiv.innerHTML = `<div class="trigger-result">Output:\\n${{data.output}}${{data.error ? '\\n\\nErrors:\\n' + data.error : ''}}</div>`;
    }} else {{
      resultDiv.innerHTML = `<div class="trigger-result" style="color: var(--danger);">Error: ${{data.error}}</div>`;
    }}
  }})
  .catch(e => {{
    resultDiv.innerHTML = `<div class="trigger-result" style="color: var(--danger);">Network error: ${{e}}</div>`;
  }});
}}

// Preset application
function applyPreset(filename) {{
  if (!confirm('Apply this preset? This will override current mood weights.')) {{
    return;
  }}
  
  fetch('/api/preset-apply', {{
    method: 'POST',
    headers: {{ 'Content-Type': 'application/json' }},
    body: JSON.stringify({{ filename: filename }})
  }})
  .then(r => r.json())
  .then(data => {{
    if (data.success) {{
      alert('Preset applied!');
      location.reload();
    }} else {{
      alert('Failed to apply preset: ' + (data.error || 'Unknown error'));
    }}
  }})
  .catch(e => alert('Error: ' + e));
}}
</script>

<footer>{get_agent_name()} {get_agent_emoji()} × Intrusive Thoughts v2.0 — refreshed {datetime.now().strftime('%Y-%m-%d %H:%M')}</footer>
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
        elif self.path == "/api/presets":
            # GET /api/presets — returns all preset files
            presets = load_presets()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(presets).encode())
        elif self.path == "/api/schedule":
            # GET /api/schedule — returns today_schedule.json
            schedule = load_today_schedule()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(schedule).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_PUT(self):
        if self.path == "/api/thought-weight":
            # PUT /api/thought-weight — accepts {thought_id, mood, weight}, updates thoughts.json
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                thought_id = data.get('thought_id')
                mood = data.get('mood')
                weight = float(data.get('weight'))
                
                if not thought_id or not mood or weight < 0.1 or weight > 3.0:
                    raise ValueError("Invalid parameters")
                
                # Load current thoughts
                thoughts = load_thoughts()
                
                # Find and update the thought
                updated = False
                for mood_data in thoughts.get("moods", {}).values():
                    for thought in mood_data.get("thoughts", []):
                        if thought["id"] == thought_id:
                            thought["weight"] = weight
                            updated = True
                            break
                    if updated:
                        break
                
                if updated:
                    save_thoughts(thoughts)
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"success": True}).encode())
                else:
                    self.send_response(404)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"success": False, "error": "Thought not found"}).encode())
            
            except Exception as e:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/api/set-mood":
            # POST /api/set-mood — accepts {mood_id}, updates today_mood.json
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                mood_id = data.get('mood_id')
                
                if not mood_id:
                    raise ValueError("Missing mood_id")
                
                # Load moods data to get mood info
                moods_data = load_moods()
                mood_info = None
                for mood in moods_data.get("base_moods", []):
                    if mood["id"] == mood_id:
                        mood_info = mood
                        break
                
                if not mood_info:
                    raise ValueError("Invalid mood_id")
                
                # Create new today_mood data
                today_mood = {
                    "id": mood_id,
                    "name": mood_info["name"],
                    "emoji": mood_info["emoji"],
                    "description": f"Manually set to {mood_info['name']}",
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "weather": "manual override",
                    "news_vibes": ["Manual mood override"],
                    "boosted_traits": mood_info.get("traits", []),
                    "dampened_traits": [],
                    "activity_log": [],
                    "energy_score": 1,
                    "vibe_score": 1,
                    "last_drift": datetime.now().isoformat()
                }
                
                save_today_mood(today_mood)
                
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": True}).encode())
            
            except Exception as e:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode())

        elif self.path == "/api/trigger":
            # POST /api/trigger — runs intrusive.sh day and returns result
            try:
                result = trigger_impulse()
                
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(result).encode())
            
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode())

        elif self.path == "/api/preset-apply":
            # POST /api/preset-apply — accepts {filename}, applies preset
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                filename = data.get('filename')
                
                if not filename:
                    raise ValueError("Missing filename")
                
                # Load preset
                preset_path = Path(__file__).parent / "presets" / filename
                if not preset_path.exists():
                    raise ValueError("Preset not found")
                
                preset = json.loads(preset_path.read_text())
                
                # Apply preset mood weights to moods.json
                moods_data = load_moods()
                if "mood_weights" in preset:
                    for mood in moods_data.get("base_moods", []):
                        if mood["id"] in preset["mood_weights"]:
                            mood["weight"] = preset["mood_weights"][mood["id"]]
                
                # Save updated moods
                MOODS_FILE.write_text(json.dumps(moods_data, indent=2))
                
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": True}).encode())
            
            except Exception as e:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # Quiet


if __name__ == "__main__":
    print(f"🧠 Intrusive Thoughts Dashboard v2 running at http://localhost:{PORT}")
    HTTPServer(("0.0.0.0", PORT), DashboardHandler).serve_forever()