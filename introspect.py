#!/usr/bin/env python3
"""
System Introspection - Full state dump of all agent subsystems.
Provides comprehensive JSON output of current system state.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from config import get_file_path, get_data_dir, load_config

def get_mood_state():
    """Get current mood state and drift information."""
    today_mood_file = get_file_path("today_mood.json")
    mood_history_file = get_file_path("mood_history.json")
    
    mood_state = {
        "current_mood": None,
        "drift_state": None,
        "mood_history_entries": 0
    }
    
    try:
        if today_mood_file.exists():
            today_mood = json.loads(today_mood_file.read_text())
            mood_state["current_mood"] = {
                "id": today_mood.get("id"),
                "name": today_mood.get("name"),
                "emoji": today_mood.get("emoji"),
                "description": today_mood.get("description"),
                "energy_score": today_mood.get("energy_score", 0),
                "vibe_score": today_mood.get("vibe_score", 0),
                "set_at": today_mood.get("set_at"),
                "drifted_to": today_mood.get("drifted_to"),
                "drift_threshold": today_mood.get("drift_threshold"),
                "boosted_traits": today_mood.get("boosted_traits", []),
                "dampened_traits": today_mood.get("dampened_traits", []),
                "activity_count": len(today_mood.get("activity_log", []))
            }
            
            mood_state["drift_state"] = {
                "has_drifted": "drifted_to" in today_mood,
                "original_mood": today_mood.get("id"),
                "current_mood": today_mood.get("drifted_to", today_mood.get("id")),
                "drift_threshold": today_mood.get("drift_threshold"),
                "current_energy": today_mood.get("energy_score", 0),
                "current_vibe": today_mood.get("vibe_score", 0)
            }
    except:
        pass
    
    try:
        if mood_history_file.exists():
            history = json.loads(mood_history_file.read_text())
            mood_state["mood_history_entries"] = len(history.get("history", []))
    except:
        pass
        
    return mood_state

def get_memory_stats():
    """Get memory system statistics."""
    memory_dir = get_data_dir() / "memory_store"
    
    memory_stats = {
        "episodic": {"count": 0, "health": "unknown"},
        "semantic": {"count": 0, "health": "unknown"},
        "procedural": {"count": 0, "health": "unknown"},
        "working": {"count": 0, "health": "unknown"},
        "total_memories": 0,
        "recent_memories": []
    }
    
    if not memory_dir.exists():
        return memory_stats
    
    # Check each memory store
    for store_name in ["episodic", "semantic", "procedural", "working"]:
        store_file = memory_dir / f"{store_name}.json"
        if store_file.exists():
            try:
                data = json.loads(store_file.read_text())
                memory_stats[store_name]["count"] = len(data)
                memory_stats[store_name]["health"] = "healthy"
                
                # Collect recent memories (last 3 from each store)
                if isinstance(data, list) and data:
                    recent = sorted(data, key=lambda x: x.get('timestamp', 0), reverse=True)[:3]
                    for mem in recent:
                        memory_stats["recent_memories"].append({
                            "store": store_name,
                            "type": mem.get("type", "unknown"),
                            "content": mem.get("content", "")[:100] + "..." if len(mem.get("content", "")) > 100 else mem.get("content", ""),
                            "timestamp": mem.get("timestamp"),
                            "strength": mem.get("strength", 0)
                        })
            except Exception as e:
                memory_stats[store_name]["health"] = f"error: {str(e)}"
    
    memory_stats["total_memories"] = sum(store["count"] for store in memory_stats.values() if isinstance(store, dict) and "count" in store)
    
    # Sort recent memories by timestamp
    memory_stats["recent_memories"].sort(key=lambda x: x.get("timestamp", 0), reverse=True)
    memory_stats["recent_memories"] = memory_stats["recent_memories"][:10]  # Keep top 10
    
    return memory_stats

def get_trust_level():
    """Get current trust levels and factors."""
    trust_dir = get_data_dir() / "trust_store"
    trust_file = trust_dir / "trust_data.json"
    
    trust_info = {
        "global_trust": 0.5,
        "category_trust": {},
        "recent_actions": [],
        "escalation_count": 0
    }
    
    if trust_file.exists():
        try:
            trust_data = json.loads(trust_file.read_text())
            trust_info["global_trust"] = trust_data.get("trust_level", 0.5)
            
            # Category trust scores
            categories = trust_data.get("action_categories", {})
            for category, stats in categories.items():
                trust_info["category_trust"][category] = {
                    "trust": stats["trust"],
                    "successes": stats["successes"],
                    "failures": stats["failures"],
                    "escalations": stats["escalations"],
                    "total_actions": stats["successes"] + stats["failures"],
                    "success_rate": stats["successes"] / (stats["successes"] + stats["failures"]) if (stats["successes"] + stats["failures"]) > 0 else 0
                }
            
            # Recent action history
            history = trust_data.get("history", [])
            trust_info["recent_actions"] = history[-5:]  # Last 5 actions
            
            # Total escalations
            trust_info["escalation_count"] = sum(stats["escalations"] for stats in categories.values())
            
        except Exception as e:
            trust_info["error"] = str(e)
    
    return trust_info

def get_evolution_metrics():
    """Get self-evolution system metrics."""
    evolution_dir = get_data_dir().parent / "evolution"
    learnings_file = evolution_dir / "learnings.json"
    weights_file = evolution_dir / "learned_weights.json"
    
    evolution_metrics = {
        "cycles_completed": 0,
        "patterns_discovered": 0,
        "weight_adjustments": {"moods": {}, "thoughts": {}},
        "last_evolution": None,
        "evolution_history": []
    }
    
    if learnings_file.exists():
        try:
            learnings = json.loads(learnings_file.read_text())
            evolution_metrics["cycles_completed"] = len(learnings.get("evolution_history", []))
            evolution_metrics["patterns_discovered"] = len(learnings.get("patterns", []))
            evolution_metrics["last_evolution"] = learnings.get("last_evolution")
            evolution_metrics["evolution_history"] = learnings.get("evolution_history", [])[-3:]  # Last 3
        except:
            pass
    
    if weights_file.exists():
        try:
            weights = json.loads(weights_file.read_text())
            evolution_metrics["weight_adjustments"] = weights
        except:
            pass
    
    return evolution_metrics

def get_health_status():
    """Get health monitor status."""
    health_dir = get_data_dir() / "health"
    status_file = health_dir / "status.json"
    
    health_status = {
        "overall": "unknown",
        "components": {},
        "metrics": {},
        "last_check": None
    }
    
    if status_file.exists():
        try:
            status = json.loads(status_file.read_text())
            health_status = {
                "overall": status.get("overall", "unknown"),
                "components": status.get("components", {}),
                "metrics": status.get("metrics", {}),
                "last_check": status.get("last_updated"),
                "uptime_since": status.get("uptime_since")
            }
        except Exception as e:
            health_status["error"] = str(e)
    
    return health_status

def get_recent_wal_entries():
    """Get recent WAL entries."""
    wal_dir = get_data_dir() / "wal"
    recent_entries = []
    
    if wal_dir.exists():
        # Find current month's WAL file
        now = datetime.now()
        wal_file = wal_dir / f"wal-{now.year}-{now.month:02d}.json"
        
        if wal_file.exists():
            try:
                lines = wal_file.read_text().strip().split('\n')
                entries = []
                for line in lines:
                    if line.strip():
                        entries.append(json.loads(line))
                
                # Get last 5 entries
                recent_entries = entries[-5:]
                
            except:
                pass
    
    return recent_entries

def get_active_streaks():
    """Get current streak information."""
    streaks_file = get_file_path("streaks.json")
    
    streaks_info = {
        "active_streaks": {},
        "total_streaks": 0
    }
    
    if streaks_file.exists():
        try:
            streaks = json.loads(streaks_file.read_text())
            streaks_info = streaks
        except:
            pass
    
    return streaks_info

def get_earned_achievements():
    """Get earned achievements."""
    achievements_file = get_file_path("achievements_earned.json")
    
    achievements = {
        "earned_count": 0,
        "recent_achievements": []
    }
    
    if achievements_file.exists():
        try:
            earned = json.loads(achievements_file.read_text())
            if isinstance(earned, list):
                achievements["earned_count"] = len(earned)
                achievements["recent_achievements"] = earned[-5:]  # Last 5
            elif isinstance(earned, dict):
                achievements["earned_count"] = len(earned)
                achievements["recent_achievements"] = list(earned.items())[-5:]
        except:
            pass
    
    return achievements

def get_todays_schedule():
    """Get today's schedule if it exists."""
    schedule = {"has_schedule": False, "events": []}
    
    # Check for today's schedule file
    today = datetime.now().strftime("%Y-%m-%d")
    schedule_file = get_data_dir() / f"schedule_{today}.json"
    
    if schedule_file.exists():
        try:
            schedule_data = json.loads(schedule_file.read_text())
            schedule = {
                "has_schedule": True,
                "events": schedule_data.get("events", []),
                "total_events": len(schedule_data.get("events", [])),
                "created_at": schedule_data.get("created_at")
            }
        except:
            pass
    
    return schedule

def get_current_thought_weights():
    """Get current effective thought weights after mood modifiers."""
    thoughts_file = get_file_path("thoughts.json")
    today_mood_file = get_file_path("today_mood.json")
    streaks_file = get_file_path("streaks.json")
    
    thought_weights = {
        "day_thoughts": {},
        "night_thoughts": {},
        "mood_modifiers_active": False
    }
    
    if not thoughts_file.exists():
        return thought_weights
    
    try:
        thoughts_data = json.loads(thoughts_file.read_text())
        today_mood = None
        streak_weights = {}
        
        if today_mood_file.exists():
            today_mood = json.loads(today_mood_file.read_text())
            thought_weights["mood_modifiers_active"] = True
        
        if streaks_file.exists():
            streaks = json.loads(streaks_file.read_text())
            streak_weights = streaks.get("anti_rut_weights", {})
        
        # Calculate effective weights for each mood (day/night)
        for mood_name, mood_data in thoughts_data.get("moods", {}).items():
            effective_weights = {}
            
            for thought in mood_data["thoughts"]:
                base_weight = thought["weight"]
                effective_weight = base_weight
                modifiers = []
                
                # Apply mood bias
                if today_mood:
                    thought_id = thought["id"]
                    boosted = today_mood.get("boosted_traits", [])
                    dampened = today_mood.get("dampened_traits", [])
                    
                    if thought_id in boosted:
                        effective_weight *= 1.8
                        modifiers.append("mood_boosted_1.8x")
                    elif thought_id in dampened:
                        effective_weight = max(0.2, effective_weight * 0.5)
                        modifiers.append("mood_dampened_0.5x")
                
                # Apply streak weights
                if thought["id"] in streak_weights:
                    streak_mult = streak_weights[thought["id"]]
                    effective_weight *= streak_mult
                    modifiers.append(f"streak_{streak_mult:.2f}x")
                
                effective_weights[thought["id"]] = {
                    "base_weight": base_weight,
                    "effective_weight": effective_weight,
                    "modifiers": modifiers,
                    "prompt": thought["prompt"][:100] + "..." if len(thought["prompt"]) > 100 else thought["prompt"]
                }
            
            thought_weights[f"{mood_name}_thoughts"] = effective_weights
    
    except Exception as e:
        thought_weights["error"] = str(e)
    
    return thought_weights

def main():
    """Generate full system introspection."""
    
    introspection = {
        "timestamp": datetime.now().isoformat(),
        "agent_version": "intrusive-thoughts-v2",
        "mood_state": get_mood_state(),
        "memory_stats": get_memory_stats(),
        "trust_level": get_trust_level(),
        "evolution_metrics": get_evolution_metrics(),
        "health_status": get_health_status(),
        "recent_wal_entries": get_recent_wal_entries(),
        "active_streaks": get_active_streaks(),
        "earned_achievements": get_earned_achievements(),
        "todays_schedule": get_todays_schedule(),
        "current_thought_weights": get_current_thought_weights(),
        "system_config": {
            "data_dir": str(get_data_dir()),
            "config_loaded": True
        }
    }
    
    print(json.dumps(introspection, indent=2, default=str))

if __name__ == "__main__":
    main()