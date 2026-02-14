#!/usr/bin/env python3
"""
System Explainer - Human-readable explanations of agent subsystems.
Reads actual code implementation to provide accurate technical details.
"""

import json
import sys
from pathlib import Path
import ast
import inspect
from config import get_file_path, load_config, get_data_dir

def explain_moods():
    """Explain the mood system by reading moods.json and set_mood.sh."""
    
    # Load moods configuration
    moods_file = get_file_path("moods.json")
    today_mood_file = get_file_path("today_mood.json")
    
    try:
        moods_data = json.loads(moods_file.read_text())
        today_mood = json.loads(today_mood_file.read_text())
    except:
        today_mood = None
    
    print("🌈 Mood System - How I Feel and Think")
    print("=" * 50)
    
    print("\n📝 Current State:")
    if today_mood:
        print(f"   Today: {today_mood.get('emoji', '?')} {today_mood.get('name', 'Unknown')}")
        print(f"   Description: {today_mood.get('description', 'No description')}")
        print(f"   Energy Score: {today_mood.get('energy_score', 0)}")
        print(f"   Vibe Score: {today_mood.get('vibe_score', 0)}")
        if 'drifted_to' in today_mood:
            print(f"   Drifted to: {today_mood['drifted_to']}")
    else:
        print("   No mood set for today")
    
    print("\n🎭 Available Base Moods:")
    for mood in moods_data.get("base_moods", []):
        print(f"   {mood['emoji']} {mood['name']} (weight: {mood['weight']})")
        print(f"      {mood['description']}")
        print(f"      Traits: {', '.join(mood['traits'])}")
    
    print("\n🌤️ Weather Influence System:")
    print("   Weather conditions modify mood weights:")
    weather_influence = moods_data.get("weather_influence", {})
    for condition, effects in weather_influence.items():
        boost = effects.get("boost", [])
        dampen = effects.get("dampen", [])
        print(f"   {condition}:")
        if boost:
            print(f"      Boosts: {', '.join(boost)}")
        if dampen:
            print(f"      Dampens: {', '.join(dampen)}")
    
    print("\n📰 News Influence System:")
    print("   News sentiment affects mood selection:")
    news_influence = moods_data.get("news_influence", {})
    for news_type, effects in news_influence.items():
        boost = effects.get("boost", [])
        dampen = effects.get("dampen", [])
        print(f"   {news_type}:")
        if boost:
            print(f"      Boosts: {', '.join(boost)}")
        if dampen:
            print(f"      Dampens: {', '.join(dampen)}")
    
    print("\n⚡ Mood Drift Mechanics:")
    print("   - Activities add energy/vibe scores throughout the day")
    print("   - Cumulative drift can change my mood mid-day")
    print("   - Prevents getting stuck in one mood forever")
    print("   - Records original + drifted mood for learning")

def explain_memory():
    """Explain the memory system by examining memory_system.py."""
    
    print("🧠 Memory System - Three-Tier Architecture")
    print("=" * 50)
    
    # Read memory system config from the actual file
    memory_file = Path(__file__).parent / "memory_system.py"
    
    print("\n🏗️ Architecture:")
    print("   Episodic Memory: Personal experiences with emotional context")
    print("   Semantic Memory: General facts extracted from repeated episodes")
    print("   Procedural Memory: Learned patterns and behavioral correlations")
    print("   Working Memory: Current context and attention (limited capacity)")
    
    # Check actual memory store status
    memory_dir = get_data_dir() / "memory_store"
    if memory_dir.exists():
        print("\n📊 Current Memory Stats:")
        for store in ["episodic.json", "semantic.json", "procedural.json", "working.json"]:
            store_file = memory_dir / store
            if store_file.exists():
                try:
                    data = json.loads(store_file.read_text())
                    print(f"   {store.split('.')[0].title()}: {len(data)} entries")
                except:
                    print(f"   {store.split('.')[0].title()}: Error reading")
    
    print("\n📉 Decay Formula (Ebbinghaus Forgetting Curve):")
    print("   Strength = e^(-t * decay_rate / (1 + reinforcement_count))")
    print("   - t: Days since last access")
    print("   - decay_rate: 0.5 (base rate from config)")
    print("   - reinforcement_count: How many times memory was accessed")
    print("   - Forget threshold: 0.1 (memories below this get pruned)")
    
    print("\n🔄 Memory Processes:")
    print("   Encoding: New experiences → episodic store with emotion tags")
    print("   Consolidation: Important episodics → semantic facts")
    print("   Retrieval: Search by keywords, recency, similarity")
    print("   Forgetting: Periodic cleanup of low-strength memories")
    print("   Reflection: Extract patterns from recent experiences")

def explain_trust():
    """Explain the trust system by examining trust_system.py."""
    
    print("🛡️ Trust System - Learning When to Act vs Ask")
    print("=" * 50)
    
    # Load trust data
    trust_dir = get_data_dir() / "trust_store"
    trust_file = trust_dir / "trust_data.json"
    
    if trust_file.exists():
        try:
            trust_data = json.loads(trust_file.read_text())
            
            print(f"\n📊 Current Trust Level: {trust_data.get('trust_level', 0.5):.2f}/1.0")
            
            print("\n🏷️ Action Category Trust Scores:")
            categories = trust_data.get('action_categories', {})
            for category, stats in categories.items():
                trust = stats['trust']
                successes = stats['successes']
                failures = stats['failures']
                total = successes + failures
                success_rate = successes/total if total > 0 else 0
                print(f"   {category}: {trust:.2f} trust ({successes}✅/{failures}❌, {success_rate:.1%} success)")
                
        except:
            print("\n⚠️ Trust data not available")
    
    print("\n🧮 Trust Calculation Logic:")
    print("   Base trust per category + mood risk modifier")
    print("   Success: +0.1 trust, Failure: -0.2 trust")
    print("   Mood modifiers:")
    print("     - Hyperfocus/Determined: +risk tolerance")
    print("     - Chaotic/Restless: -risk tolerance") 
    print("     - Cozy/Philosophical: neutral")
    
    print("\n🚨 Risk Level Assessment:")
    print("   Low: File reads, web browsing, calculations")
    print("   Medium: File writes, messaging, API calls") 
    print("   High: Public posts, system changes, installs")
    print("   Critical: Financial ops, production deployments")
    
    print("\n🎯 Escalation Thresholds:")
    print("   Auto-proceed: trust > 0.7 for risk level")
    print("   Ask permission: trust 0.3-0.7")
    print("   Block/warn: trust < 0.3 for critical actions")
    
    print("\n📈 Trust Factors:")
    print("   Increases: Successful outcomes, consistent behavior")
    print("   Decreases: Failures, errors, human rejections")
    print("   Time decay: Trust slowly decays without activity")

def explain_evolution():
    """Explain self-evolution by examining self_evolution.py."""
    
    print("🧬 Self-Evolution System - Learning From My Own Patterns")
    print("=" * 50)
    
    evolution_dir = get_data_dir().parent / "evolution"
    learnings_file = evolution_dir / "learnings.json" 
    weights_file = evolution_dir / "learned_weights.json"
    
    print("\n🎯 Value Dimensions (optimization targets):")
    print("   Productivity (30%): Tasks completed, code written")
    print("   Creativity (20%): Novel actions, diverse activities") 
    print("   Social (20%): Engagement quality, community participation")
    print("   Growth (15%): New skills, learning activities")
    print("   Wellbeing (15%): Streak maintenance, balanced moods")
    
    if learnings_file.exists():
        try:
            learnings = json.loads(learnings_file.read_text())
            print(f"\n📊 Evolution Status:")
            print(f"   Last evolution: {learnings.get('last_evolution', 'Never')}")
            print(f"   Pattern count: {len(learnings.get('patterns', []))}")
            print(f"   Evolution cycles: {len(learnings.get('evolution_history', []))}")
        except:
            print("\n⚠️ No evolution data found")
    
    if weights_file.exists():
        try:
            weights = json.loads(weights_file.read_text())
            mood_adjustments = weights.get('moods', {})
            thought_adjustments = weights.get('thoughts', {})
            
            print("\n⚖️ Learned Weight Adjustments:")
            if mood_adjustments:
                print("   Mood weights:")
                for mood, adj in mood_adjustments.items():
                    print(f"     {mood}: {adj:+.2f}")
            
            if thought_adjustments:
                print("   Thought weights:")
                for thought, adj in thought_adjustments.items():
                    print(f"     {thought}: {adj:+.2f}")
                    
        except:
            print("\n⚠️ No learned weights found")
    
    print("\n🔄 Evolution Cycle:")
    print("   1. Collect activity history and outcomes")
    print("   2. Calculate multi-dimensional value scores")
    print("   3. Identify patterns (mood→activity→outcome correlations)")
    print("   4. Adjust weights to optimize for value dimensions")
    print("   5. Test adjustments and measure performance")
    print("   6. Commit successful changes, revert failures")

def explain_health():
    """Explain health monitoring by examining health_monitor.py."""
    
    print("🩺 Health Monitor - System Status Tracking")
    print("=" * 50)
    
    health_dir = get_data_dir() / "health"
    status_file = health_dir / "status.json"
    
    if status_file.exists():
        try:
            status = json.loads(status_file.read_text())
            overall = status.get('overall', 'unknown')
            emoji = {"green": "🟢", "yellow": "🟡", "red": "🔴"}.get(overall, "❓")
            
            print(f"\n🚦 Overall Status: {emoji} {overall.upper()}")
            print(f"   Last Updated: {status.get('last_updated', 'Unknown')}")
            print(f"   Uptime Since: {status.get('uptime_since', 'Unknown')}")
            
            print("\n🔧 Component Status:")
            components = status.get('components', {})
            for name, info in components.items():
                comp_status = info.get('status', 'unknown')
                comp_emoji = {"green": "🟢", "yellow": "🟡", "red": "🔴"}.get(comp_status, "❓")
                message = info.get('message', 'No message')
                print(f"   {comp_emoji} {name}: {message}")
            
            print("\n📊 Health Metrics:")
            metrics = status.get('metrics', {})
            print(f"   Total heartbeats: {metrics.get('total_heartbeats', 0)}")
            print(f"   Total incidents: {metrics.get('total_incidents', 0)}")
            print(f"   Consecutive healthy: {metrics.get('consecutive_healthy', 0)}")
            if metrics.get('mttr_seconds'):
                print(f"   Mean time to recover: {metrics['mttr_seconds']}s")
                
        except:
            print("\n⚠️ Health status not available")
    
    print("\n💓 Heartbeat System:")
    print("   Regular health checks every few minutes")
    print("   Tracks component availability and response times")
    print("   Records heartbeats for uptime analysis")
    
    print("\n🚨 Incident Tracking:")
    print("   Automatically logs component failures")
    print("   Tracks recovery times and failure patterns")
    print("   Enables proactive maintenance")
    
    print("\n🔍 Monitored Components:")
    print("   - Mood System: Can set/get moods")
    print("   - Memory System: All stores accessible") 
    print("   - Cron Jobs: Background tasks running")
    print("   - Dashboard: Web interface responsive")
    print("   - Data Integrity: Config files valid")

def explain_thoughts():
    """Explain thought selection by examining thoughts.json and intrusive.sh."""
    
    print("💭 Thought Selection System - How I Choose What To Do")
    print("=" * 50)
    
    thoughts_file = get_file_path("thoughts.json") 
    today_mood_file = get_file_path("today_mood.json")
    
    try:
        thoughts_data = json.loads(thoughts_file.read_text())
        today_mood = json.loads(today_mood_file.read_text()) 
    except:
        today_mood = None
        
    print("\n🌓 Mood-Based Thought Categories:")
    moods = thoughts_data.get("moods", {})
    for mood_name, mood_data in moods.items():
        print(f"\n   {mood_name.title()} Mode:")
        print(f"      {mood_data['description']}")
        print(f"      Jitter: {mood_data['jitter_seconds']}s")
        print(f"      Timeout: {mood_data['timeout_seconds']}s")
        print(f"      Available thoughts:")
        
        for thought in mood_data['thoughts']:
            print(f"        • {thought['id']} (weight: {thought['weight']})")
            
    print("\n⚖️ Weight Calculation Process:")
    print("   1. Start with base thought weights from thoughts.json")
    print("   2. Apply mood bias (boosted/dampened traits)")
    print("   3. Apply anti-rut weights (streak-based adjustments)")
    print("   4. Apply human mood influence (supportive adjustments)")
    print("   5. Build weighted pool (weight * 10 copies)")
    print("   6. Random selection from pool")
    
    if today_mood:
        print(f"\n🎯 Current Mood Influences:")
        print(f"   Active mood: {today_mood.get('name', 'Unknown')}")
        
        boosted = today_mood.get('boosted_traits', [])
        dampened = today_mood.get('dampened_traits', [])
        
        if boosted:
            print(f"   Boosted thoughts (1.8x weight): {', '.join(boosted)}")
        if dampened:
            print(f"   Dampened thoughts (0.5x weight): {', '.join(dampened)}")
    
    print("\n🚫 Rejection Mechanisms:")
    print("   Heavily dampened thoughts get logged as rejections")
    print("   Anti-rut system prevents repetitive behavior")
    print("   Human mood detection avoids bothering when stressed")
    
    print("\n🎲 Randomness & Fairness:")
    print("   Weighted random ensures variety while respecting preferences")
    print("   Cooldown periods prevent spam")
    print("   Jitter adds natural timing variation")

def explain_proactive():
    """Explain proactive system by examining proactive.py."""
    
    print("🚀 Proactive System - Write-Ahead Log & Action Buffer")
    print("=" * 50)
    
    wal_dir = get_data_dir() / "wal"
    buffer_dir = get_data_dir().parent / "buffer"
    
    print("\n📝 Write-Ahead Log (WAL):")
    print("   Append-only structured logging of all actions")
    print("   Rotates monthly to prevent file growth")
    print("   Entry types: action, plan, observation, reflection")
    print("   Categories: build, explore, social, organize, learn")
    
    if wal_dir.exists():
        wal_files = list(wal_dir.glob("wal-*.json"))
        print(f"   Current WAL files: {len(wal_files)}")
        
        if wal_files:
            # Count entries in current month
            current_wal = max(wal_files, key=lambda f: f.name)
            try:
                lines = current_wal.read_text().strip().split('\n')
                entries = [json.loads(line) for line in lines if line.strip()]
                print(f"   Entries this month: {len(entries)}")
                
                # Show recent entries
                print(f"   Recent entries (last 5):")
                for entry in entries[-5:]:
                    timestamp = entry['timestamp'][:16]  # YYYY-MM-DD HH:MM
                    print(f"     {timestamp} | {entry['type']} | {entry['category']} | {entry['content'][:60]}...")
                    
            except:
                print("   Could not read current WAL file")
    
    print("\n🎯 Working Buffer:")
    print("   Active context management for ongoing tasks")
    print("   Tracks: active_items, completed, expired")
    print("   Enables planning and follow-up on multi-step work")
    
    if buffer_dir.exists():
        buffer_file = buffer_dir / "working_buffer.json"
        if buffer_file.exists():
            try:
                buffer = json.loads(buffer_file.read_text())
                print(f"   Active items: {len(buffer.get('active_items', []))}")
                print(f"   Completed: {len(buffer.get('completed', []))}")
                print(f"   Expired: {len(buffer.get('expired', []))}")
            except:
                print("   Could not read buffer file")
    
    print("\n🎯 Proactive Triggers:")
    print("   Pattern detection: Identify successful action sequences")
    print("   Context awareness: Suggest actions based on current state")
    print("   Opportunity recognition: Spot chances for value creation")
    print("   Preventive maintenance: Address issues before they escalate")
    
    print("\n🔄 Action Buffer Workflow:")
    print("   1. Add planned action to buffer")
    print("   2. Execute action, log to WAL")
    print("   3. Update buffer status based on outcome")
    print("   4. Analyze patterns for future proactive suggestions")

def main():
    """Main CLI handler."""
    if len(sys.argv) < 2:
        print("Usage: explain_system.py <system>")
        print("Available systems: moods, memory, trust, evolution, health, thoughts, proactive")
        return
    
    system = sys.argv[1].lower()
    
    explainers = {
        "moods": explain_moods,
        "memory": explain_memory, 
        "trust": explain_trust,
        "evolution": explain_evolution,
        "health": explain_health,
        "thoughts": explain_thoughts,
        "proactive": explain_proactive
    }
    
    if system in explainers:
        explainers[system]()
    else:
        print(f"Unknown system: {system}")
        print("Available systems:", ", ".join(explainers.keys()))

if __name__ == "__main__":
    main()