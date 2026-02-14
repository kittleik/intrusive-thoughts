#!/usr/bin/env python3
"""
Decision Trace - Explain why a specific action was selected.
Reads from log/decisions.json or history.json to trace decision paths.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from config import get_file_path, get_data_dir

def load_decisions_log():
    """Load decision log entries."""
    decisions_file = get_data_dir() / "log" / "decisions.json"
    
    if decisions_file.exists():
        try:
            return json.loads(decisions_file.read_text())
        except:
            return []
    return []

def load_history():
    """Load general history as fallback."""
    history_file = get_file_path("history.json")
    
    if history_file.exists():
        try:
            return json.loads(history_file.read_text())
        except:
            return []
    return []

def find_decision_by_id(decisions, action_id):
    """Find a specific decision by action ID."""
    for decision in decisions:
        if decision.get("winner", {}).get("id") == action_id:
            return decision
    return None

def find_recent_decision(decisions):
    """Find the most recent decision."""
    if not decisions:
        return None
    
    # Sort by timestamp, most recent first
    sorted_decisions = sorted(decisions, key=lambda d: d.get("timestamp", ""), reverse=True)
    return sorted_decisions[0] if sorted_decisions else None

def explain_decision(decision):
    """Generate human-readable explanation of a decision."""
    
    print("🧠 Decision Trace Analysis")
    print("=" * 50)
    
    timestamp = decision.get("timestamp", "Unknown")
    mood = decision.get("mood", "Unknown")
    mood_id = decision.get("mood_id", "none")
    
    print(f"\n⏰ When: {timestamp}")
    print(f"🌈 Mood Context: {mood} (mood_id: {mood_id})")
    
    # Winner information
    winner = decision.get("winner", {})
    print(f"\n🎯 Selected Action:")
    print(f"   ID: {winner.get('id', 'Unknown')}")
    try:
        print(f"   Final Weight: {float(winner.get('final_weight', 0)):.2f}")
    except (ValueError, TypeError):
        print(f"   Final Weight: {winner.get('final_weight', 'N/A')}")
    print(f"   Prompt: {winner.get('prompt', 'No prompt available')}")
    
    boost_reasons = winner.get("boost_reasons", [])
    if boost_reasons:
        print(f"   Boost Reasons:")
        for reason in boost_reasons:
            print(f"     • {reason}")
    
    # Pool information
    total_candidates = decision.get("total_candidates", 0)
    pool_size = decision.get("pool_size", 0)
    random_roll = decision.get("random_roll", 0)
    
    print(f"\n📊 Selection Process:")
    print(f"   Total candidate thoughts: {total_candidates}")
    print(f"   Final pool size (after weighting): {pool_size}")
    print(f"   Random roll value: {random_roll:.6f}")
    
    # All candidates analysis
    all_candidates = decision.get("all_candidates", [])
    if all_candidates:
        print(f"\n⚖️ All Candidate Thoughts (ranked by final weight):")
        
        # Sort candidates by final weight
        sorted_candidates = sorted(all_candidates, key=lambda c: c.get("final_weight", 0), reverse=True)
        
        for i, candidate in enumerate(sorted_candidates, 1):
            thought_id = candidate.get("id", "unknown")
            base_weight = candidate.get("original_weight", 0)
            final_weight = candidate.get("final_weight", 0)
            skip_reasons = candidate.get("skip_reasons", [])
            boost_reasons = candidate.get("boost_reasons", [])
            
            status_icon = "🏆" if thought_id == winner.get("id") else f"{i:2d}."
            weight_change = final_weight - base_weight
            weight_indicator = f"({weight_change:+.1f})" if weight_change != 0 else ""
            
            print(f"   {status_icon} {thought_id}: {base_weight:.1f} → {final_weight:.1f} {weight_indicator}")
            
            if boost_reasons:
                for reason in boost_reasons:
                    print(f"       ✅ {reason}")
            
            if skip_reasons:
                for reason in skip_reasons:
                    print(f"       ❌ {reason}")
    
    # Skipped thoughts (heavily dampened)
    skipped_thoughts = decision.get("skipped_thoughts", [])
    if skipped_thoughts:
        print(f"\n🚫 Heavily Dampened Thoughts:")
        for skipped in skipped_thoughts:
            thought_id = skipped.get("id", "unknown")
            original = skipped.get("original_weight", 0)
            final = skipped.get("final_weight", 0)
            reasons = skipped.get("reasons", [])
            
            print(f"   {thought_id}: {original:.1f} → {final:.1f}")
            for reason in reasons:
                print(f"     • {reason}")
    
    print(f"\n🎲 Why This Specific Choice:")
    winner_weight = winner.get("final_weight", 0)
    
    if winner_weight > 2.0:
        print(f"   High probability selection (weight {winner_weight:.1f})")
        print(f"   This thought had strong advantages in current context")
    elif winner_weight > 1.0:
        print(f"   Moderate probability selection (weight {winner_weight:.1f})")
        print(f"   This thought was reasonably well-suited to current mood/context")
    else:
        print(f"   Low probability selection (weight {winner_weight:.1f})")
        print(f"   This was a less likely choice - possibly dampened but still selected")
    
    if boost_reasons:
        print(f"   Boosted by: {', '.join(boost_reasons)}")
    
    pool_share = (winner_weight * 10) / pool_size if pool_size > 0 else 0
    print(f"   Pool representation: {winner_weight * 10} out of {pool_size} ({pool_share:.1%} chance)")

def find_decision_from_history(history, action_id):
    """Try to reconstruct decision from history.json (fallback)."""
    
    # Find the history entry
    target_entry = None
    if action_id:
        for entry in history:
            if entry.get("thought_id") == action_id:
                target_entry = entry
                break
    else:
        # Most recent entry
        if history:
            target_entry = history[-1]
    
    if not target_entry:
        return None
    
    # Reconstruct basic decision info
    return {
        "timestamp": target_entry.get("timestamp", "Unknown"),
        "mood": target_entry.get("mood", "Unknown"),
        "mood_id": target_entry.get("today_mood", "none"),
        "winner": {
            "id": target_entry.get("thought_id", "Unknown"),
            "prompt": target_entry.get("prompt", "No prompt available"),
            "final_weight": "unknown (from history)"
        },
        "note": "Reconstructed from history.json - limited detail available"
    }

def main():
    """Main CLI handler."""
    action_id = sys.argv[1] if len(sys.argv) > 1 else None
    
    # Try to load from decisions log first
    decisions = load_decisions_log()
    decision = None
    
    if decisions:
        if action_id:
            decision = find_decision_by_id(decisions, action_id)
            if not decision:
                print(f"❌ No decision found for action ID: {action_id}")
                print("Recent available action IDs:")
                for d in decisions[-5:]:
                    winner_id = d.get("winner", {}).get("id", "unknown")
                    timestamp = d.get("timestamp", "unknown")[:16]
                    print(f"  {winner_id} ({timestamp})")
                return
        else:
            decision = find_recent_decision(decisions)
    
    # Fallback to history.json
    if not decision:
        print("📝 No detailed decision log found, checking history.json...")
        history = load_history()
        decision = find_decision_from_history(history, action_id)
    
    if not decision:
        print("❌ No decision information found.")
        print("Make sure the agent has made at least one decision, or specify a valid action ID.")
        return
    
    if "note" in decision:
        print(f"⚠️ Note: {decision['note']}")
        print()
    
    explain_decision(decision)

if __name__ == "__main__":
    main()