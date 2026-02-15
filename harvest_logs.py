#!/usr/bin/env python3
"""🔄 Log Harvester — auto-extract intrusive-thoughts activity from OpenClaw session logs.

Scans completed cron sessions, extracts what happened, and populates history.json.
No agent cooperation needed — logging is automatic.

Usage: python3 harvest_logs.py [--force] [--dry-run]
  --force    Re-process all sessions (ignore last harvest timestamp)
  --dry-run  Show what would be harvested without writing
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
HISTORY_FILE = SCRIPT_DIR / "history.json"
HARVEST_STATE_FILE = SCRIPT_DIR / "harvest_state.json"
SESSIONS_DIR = Path.home() / ".openclaw/agents/main/sessions"
CRON_JOBS_FILE = Path.home() / ".openclaw/cron/jobs.json"

# Known intrusive-thoughts cron job IDs (loaded dynamically)
def get_it_cron_ids():
    """Get cron job IDs that belong to intrusive-thoughts."""
    try:
        data = json.loads(CRON_JOBS_FILE.read_text())
        jobs = data.get("jobs", data if isinstance(data, list) else [])
        ids = set()
        for j in jobs:
            name = (j.get("name", "") or "").lower()
            text = (j.get("payload", {}).get("message", "") or "").lower()
            if any(kw in name or kw in text for kw in [
                "intrusive", "ember", "mood", "night workshop", "pop-in", "morning mood"
            ]):
                ids.add(j["id"])
        return ids
    except Exception as e:
        print(f"Warning: Could not load cron jobs: {e}", file=sys.stderr)
        return set()

def load_harvest_state():
    try:
        return json.loads(HARVEST_STATE_FILE.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {"last_harvest_ms": 0, "harvested_sessions": []}

def save_harvest_state(state):
    HARVEST_STATE_FILE.write_text(json.dumps(state, indent=2))

def load_history():
    try:
        data = json.loads(HISTORY_FILE.read_text())
        return data if isinstance(data, list) else []
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_history(history):
    HISTORY_FILE.write_text(json.dumps(history, indent=2))

def extract_session_data(session_path):
    """Extract activity data from a session log file."""
    messages = []
    cron_id = None
    cron_name = None
    thought_id = None
    tools_used = set()
    skills_used = set()
    total_cost = 0.0
    total_tokens = 0
    tool_call_count = 0
    first_timestamp = None
    last_timestamp = None
    assistant_texts = []
    model_used = None
    
    # Skill detection from tool calls
    skill_indicators = {
        "moltbook": ["moltbook", "moltbook-post"],
        "github": ["gh ", "github"],
        "network-recon": ["nmap", "arp-scan"],
        "screenshot": ["chromium", "screenshot"],
        "docker-basics": ["docker"],
        "systemd-services": ["systemctl"],
        "git-workflow": ["git "],
        "webserver-debug": ["curl", "httpie"],
        "intrusive-thoughts": ["intrusive.sh", "set_mood", "log_result", "select_mood"],
    }
    
    try:
        with open(session_path) as f:
            for line in f:
                try:
                    d = json.loads(line.strip())
                except json.JSONDecodeError:
                    continue
                
                if d.get("type") == "message":
                    msg = d.get("message", {})
                    role = msg.get("role", "")
                    ts = d.get("timestamp", "")
                    
                    if ts:
                        if not first_timestamp:
                            first_timestamp = ts
                        last_timestamp = ts
                    
                    if role == "user":
                        # Check if this is a cron-triggered session
                        content = msg.get("content", [])
                        if isinstance(content, list):
                            for c in content:
                                text = c.get("text", "")
                                if "[cron:" in text:
                                    # Extract cron job ID
                                    import re
                                    match = re.search(r'\[cron:([a-f0-9-]+)', text)
                                    if match:
                                        cron_id = match.group(1)
                                    # Extract cron name
                                    name_match = re.search(r'\[cron:[a-f0-9-]+ ([^\]]+)\]', text)
                                    if name_match:
                                        cron_name = name_match.group(1)
                    
                    elif role == "assistant":
                        content = msg.get("content", [])
                        if isinstance(content, list):
                            for c in content:
                                if c.get("type") == "text" and c.get("text", "").strip():
                                    assistant_texts.append(c["text"].strip())
                                elif c.get("type") == "toolCall":
                                    tool_call_count += 1
                                    tool_name = c.get("toolName", "")
                                    if tool_name:
                                        tools_used.add(tool_name)
                                    # Check arguments for skill indicators
                                    args = json.dumps(c.get("arguments", {})).lower()
                                    for skill, indicators in skill_indicators.items():
                                        for ind in indicators:
                                            if ind in args:
                                                skills_used.add(skill)
                    
                    elif role == "toolResult":
                        content = msg.get("content", [])
                        if isinstance(content, list):
                            for c in content:
                                text = c.get("text", "").lower()
                                for skill, indicators in skill_indicators.items():
                                    for ind in indicators:
                                        if ind in text:
                                            skills_used.add(skill)
                
                elif d.get("type") == "model_change":
                    model_used = d.get("modelId", model_used)
                
                # Extract cost/token info from custom events
                elif d.get("type") == "custom":
                    if "cost" in d:
                        total_cost += d.get("cost", 0)
                    if "tokens" in d:
                        total_tokens += d.get("tokens", 0)
    
    except Exception as e:
        print(f"Error reading {session_path}: {e}", file=sys.stderr)
        return None
    
    if not cron_id:
        return None  # Not a cron-triggered session
    
    # Extract thought_id from the intrusive.sh output in tool results
    # Look for JSON output containing "id" field
    try:
        with open(session_path) as f:
            for line in f:
                d = json.loads(line.strip())
                if d.get("type") == "message" and d.get("message", {}).get("role") == "toolResult":
                    content = d["message"].get("content", [])
                    for c in content:
                        text = c.get("text", "")
                        if '"id"' in text and '"prompt"' in text:
                            try:
                                # Find JSON in the output
                                import re
                                json_match = re.search(r'\{[^}]*"id"[^}]*\}', text)
                                if json_match:
                                    thought_data = json.loads(json_match.group())
                                    thought_id = thought_data.get("id", thought_id)
                            except:
                                pass
    except:
        pass
    
    # Generate summary from last meaningful assistant text
    summary = ""
    for text in reversed(assistant_texts):
        if len(text) > 20 and not text.startswith("```"):
            summary = text[:200]
            break
    
    if not summary and assistant_texts:
        summary = assistant_texts[-1][:200]
    
    # Calculate duration
    duration_sec = 0
    if first_timestamp and last_timestamp:
        try:
            t1 = datetime.fromisoformat(first_timestamp.replace("Z", "+00:00"))
            t2 = datetime.fromisoformat(last_timestamp.replace("Z", "+00:00"))
            duration_sec = int((t2 - t1).total_seconds())
        except:
            pass
    
    session_id = session_path.stem
    
    return {
        "timestamp": first_timestamp,
        "session_id": session_id,
        "cron_id": cron_id,
        "cron_name": cron_name,
        "thought_id": thought_id or "unknown",
        "mood": "unknown",  # Could be extracted from today_mood.json at that time
        "summary": summary,
        "energy": "neutral",
        "vibe": "neutral",
        "tools_used": sorted(tools_used),
        "skills_used": sorted(skills_used),
        "tool_call_count": tool_call_count,
        "duration_sec": duration_sec,
        "model": model_used,
        "type": "cron_activity",
        "harvested": True
    }

def harvest(force=False, dry_run=False):
    """Main harvest function."""
    it_cron_ids = get_it_cron_ids()
    if not it_cron_ids:
        print("No intrusive-thoughts cron jobs found")
        return
    
    state = load_harvest_state()
    history = load_history()
    
    # Get existing session IDs to avoid duplicates
    existing_sessions = {e.get("session_id") for e in history if e.get("session_id")}
    
    # Scan session files
    if not SESSIONS_DIR.exists():
        print(f"Sessions directory not found: {SESSIONS_DIR}")
        return
    
    new_entries = []
    session_files = sorted(SESSIONS_DIR.glob("*.jsonl"), key=lambda p: p.stat().st_mtime)
    
    for session_path in session_files:
        session_id = session_path.stem
        
        # Skip already harvested
        if not force and session_id in existing_sessions:
            continue
        if not force and session_id in state.get("harvested_sessions", []):
            continue
        
        # Skip files older than last harvest (unless force)
        if not force and state["last_harvest_ms"] > 0:
            file_mtime_ms = int(session_path.stat().st_mtime * 1000)
            if file_mtime_ms < state["last_harvest_ms"] - 60000:  # 1min buffer
                continue
        
        # Extract data
        data = extract_session_data(session_path)
        if data is None:
            continue
        
        # Check if this is an intrusive-thoughts cron job
        if data["cron_id"] not in it_cron_ids:
            continue
        
        new_entries.append(data)
        state["harvested_sessions"].append(session_id)
    
    if new_entries:
        if dry_run:
            print(f"Would harvest {len(new_entries)} new entries:")
            for e in new_entries:
                print(f"  {e['timestamp'][:16]} | {e['cron_name']} | {e['thought_id']} | tools:{e['tool_call_count']} | skills:{','.join(e['skills_used'])}")
                print(f"    Summary: {e['summary'][:100]}")
        else:
            history.extend(new_entries)
            history.sort(key=lambda x: x.get("timestamp", ""))
            save_history(history)
            
            state["last_harvest_ms"] = int(datetime.now(timezone.utc).timestamp() * 1000)
            # Keep only last 200 session IDs in state to prevent bloat
            state["harvested_sessions"] = state["harvested_sessions"][-200:]
            save_harvest_state(state)
            
            print(f"✅ Harvested {len(new_entries)} new entries (total: {len(history)})")
            for e in new_entries:
                skills = ",".join(e["skills_used"]) if e["skills_used"] else "none"
                print(f"  {e['timestamp'][:16]} | {e.get('cron_name','?')} | thought:{e['thought_id']} | skills:{skills}")
    else:
        print("No new entries to harvest")

if __name__ == "__main__":
    force = "--force" in sys.argv
    dry_run = "--dry-run" in sys.argv
    harvest(force=force, dry_run=dry_run)
