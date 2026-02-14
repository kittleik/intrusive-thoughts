#!/usr/bin/env python3
"""🧠 Intrusive Thoughts Dashboard — what Ember does when you're not looking."""

import json
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
from datetime import datetime
from collections import Counter
from pathlib import Path

PORT = 3117
BASE = Path(__file__).parent
HISTORY_FILE = BASE / "history.json"
THOUGHTS_FILE = BASE / "thoughts.json"
PICKS_LOG = BASE / "log" / "picks.log"


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


def build_html():
    history = load_history()
    picks = load_picks()
    thoughts = load_thoughts()

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

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>🧠 Intrusive Thoughts</title>
<style>
  :root {{ --bg: #0a0a0f; --card: #12121a; --border: #1e1e2e; --text: #c9c9d9; --accent: #f59e0b; --accent2: #8b5cf6; --dim: #555568; }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ background: var(--bg); color: var(--text); font-family: 'SF Mono', 'Fira Code', monospace; padding: 2rem; max-width: 1200px; margin: 0 auto; }}
  h1 {{ color: var(--accent); font-size: 1.8rem; margin-bottom: 0.3rem; }}
  .subtitle {{ color: var(--dim); margin-bottom: 2rem; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem; }}
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
  footer {{ text-align: center; color: var(--dim); font-size: 0.75rem; margin-top: 2rem; }}
</style>
</head>
<body>
<h1>🧠 Intrusive Thoughts</h1>
<p class="subtitle">What Ember does when you're not looking</p>

<div class="grid">
  <div class="stat-card"><div class="number">{total_picks}</div><div class="label">Total Impulses</div></div>
  <div class="stat-card"><div class="number">{total_completed}</div><div class="label">Completed</div></div>
  <div class="stat-card"><div class="number">{mood_counts.get('night', 0)}</div><div class="label">🌙 Night Sessions</div></div>
  <div class="stat-card"><div class="number">{mood_counts.get('day', 0)}</div><div class="label">☀️ Day Sessions</div></div>
</div>

<div class="section">
  <h2>🎯 Most Common Impulses</h2>
  <div class="bar-chart">
    {''.join(f'''<div class="bar-row"><div class="bar-label">{name}</div><div class="bar" style="width: {max(count / max(top_thoughts[0][1], 1) * 100, 2):.0f}%"></div><div class="bar-count">{count}</div></div>''' for name, count in top_thoughts) if top_thoughts else '<div class="empty">No data yet — check back after some impulses fire</div>'}
  </div>
</div>

<div class="section">
  <h2>📝 Recent Activity</h2>
  {''.join(f"""<div class="history-item"><span class="time">{e.get('timestamp','?')[:16].replace('T',' ')}</span><span class="mood-tag mood-{e.get('mood','day')}">{e.get('mood','?')}</span> <strong>{e.get('thought_id','?')}</strong><div class="summary">{e.get('summary','')}</div></div>""" for e in recent) if recent else '<div class="empty">Nothing yet. First night session fires at 03:17 🌙</div>'}
</div>

<div class="section">
  <h2>🎰 Thought Catalog</h2>
  {''.join(f"""<div class="thought-item"><div class="prompt"><span class="mood-tag mood-{t['mood']}">{t['mood']}</span> <strong>{t['id']}</strong><br>{t['prompt'][:120]}{'...' if len(t['prompt']) > 120 else ''}</div><div class="meta">w:{t['weight']}<br>{t['times_picked']}x picked</div></div>""" for t in sorted(all_thoughts, key=lambda x: -x['times_picked']))}
</div>

<footer>Ember 🦞 × Intrusive Thoughts v1 — refreshed {datetime.now().strftime('%Y-%m-%d %H:%M')}</footer>
</body>
</html>"""


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
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # Quiet


if __name__ == "__main__":
    print(f"🧠 Intrusive Thoughts Dashboard running at http://localhost:{PORT}")
    HTTPServer(("0.0.0.0", PORT), DashboardHandler).serve_forever()
