#!/usr/bin/env python3
"""
📊 ROI Tracker - Which thoughts actually ship?
GitHub Issue #3

Analyzes history.json to calculate:
- Completion rate per thought_id
- Average energy/vibe per thought_id  
- Which thought_ids produce "shipped" results most often
- Output as simple JSON to log/roi.json

Usage:
    python3 roi_tracker.py             # Generate ROI report
    python3 roi_tracker.py --json      # JSON output only
"""

import json
import sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timedelta

SCRIPT_DIR = Path(__file__).parent
HISTORY_FILE = SCRIPT_DIR / "history.json"
ROI_OUTPUT_FILE = SCRIPT_DIR / "log" / "roi.json"

def load_history():
    """Load history.json file."""
    if not HISTORY_FILE.exists():
        return []
    
    with open(HISTORY_FILE) as f:
        return json.load(f)

SHIP_KEYWORDS = [
    'shipped', 'deployed', 'committed', 'pushed', 'merged', 'published',
    'created', 'built', 'fixed', 'added', 'implemented', 'completed',
    'installed', 'configured', 'wrote', 'designed', 'launched', 'released',
    'posted', 'submitted', 'opened pr', 'pull request', 'refactored',
]

UNSHIP_KEYWORDS = [
    'failed', 'couldn\'t', 'blocked', 'skipped', 'abandoned', 'gave up',
    'no progress', 'deferred', 'nothing', 'explored but', 'just browsed',
]

def infer_shipped(entry):
    """Smart inference: did this activity produce concrete output?"""
    # Explicit flag always wins
    if entry.get('shipped') is True:
        return True
    
    summary = entry.get('summary', '').lower()
    energy = entry.get('energy', 'neutral')
    vibe = entry.get('vibe', 'neutral')
    
    # Check for negative signals first
    for kw in UNSHIP_KEYWORDS:
        if kw in summary:
            return False
    
    # Check for positive signals
    ship_signals = sum(1 for kw in SHIP_KEYWORDS if kw in summary)
    
    # High energy + positive vibe + ship keywords = shipped
    if ship_signals >= 1 and energy == 'high' and vibe == 'positive':
        return True
    
    # Multiple ship keywords even with neutral energy
    if ship_signals >= 2:
        return True
    
    # Single keyword with positive vibe
    if ship_signals >= 1 and vibe == 'positive':
        return True
    
    return entry.get('shipped', False)


def calculate_roi_metrics(history):
    """Calculate ROI metrics from history data."""
    if not history:
        return {}
    
    # Group entries by thought_id
    thought_groups = defaultdict(list)
    for entry in history:
        thought_id = entry.get('thought_id', 'unknown')
        thought_groups[thought_id].append(entry)
    
    roi_data = {}
    
    for thought_id, entries in thought_groups.items():
        if not entries:
            continue
            
        total_entries = len(entries)
        shipped_entries = [e for e in entries if infer_shipped(e)]
        shipped_count = len(shipped_entries)
        
        # Calculate completion/shipping rate
        completion_rate = (shipped_count / total_entries) * 100 if total_entries > 0 else 0
        
        # Calculate average energy (convert to numeric)
        energy_values = []
        for entry in entries:
            energy = entry.get('energy', 'neutral')
            if energy == 'high':
                energy_values.append(1)
            elif energy == 'low':
                energy_values.append(-1)
            else:  # neutral
                energy_values.append(0)
        
        avg_energy = sum(energy_values) / len(energy_values) if energy_values else 0
        
        # Calculate average vibe (convert to numeric)
        vibe_values = []
        for entry in entries:
            vibe = entry.get('vibe', 'neutral')
            if vibe == 'positive':
                vibe_values.append(1)
            elif vibe == 'negative':
                vibe_values.append(-1)
            else:  # neutral
                vibe_values.append(0)
        
        avg_vibe = sum(vibe_values) / len(vibe_values) if vibe_values else 0
        
        # Calculate recent performance (last 30 days)
        recent_cutoff = datetime.now() - timedelta(days=30)
        recent_entries = []
        for entry in entries:
            try:
                entry_time = datetime.fromisoformat(entry.get('timestamp', '').replace('Z', '+00:00'))
                if entry_time > recent_cutoff:
                    recent_entries.append(entry)
            except:
                continue
        
        recent_shipped = len([e for e in recent_entries if e.get('shipped', False)])
        recent_completion_rate = (recent_shipped / len(recent_entries)) * 100 if recent_entries else 0
        
        roi_data[thought_id] = {
            'total_entries': total_entries,
            'shipped_count': shipped_count,
            'completion_rate': round(completion_rate, 1),
            'avg_energy': round(avg_energy, 2),
            'avg_vibe': round(avg_vibe, 2),
            'recent_entries': len(recent_entries),
            'recent_completion_rate': round(recent_completion_rate, 1),
            'roi_score': round((completion_rate * 0.6 + (avg_energy + 1) * 25 + (avg_vibe + 1) * 15), 1),
            'last_shipped': max([e.get('timestamp', '') for e in shipped_entries]) if shipped_entries else None
        }
    
    return roi_data

def generate_summary(roi_data):
    """Generate human-readable summary of ROI data."""
    if not roi_data:
        return "No ROI data available - no history entries found."
    
    # Sort by ROI score
    sorted_thoughts = sorted(roi_data.items(), key=lambda x: x[1]['roi_score'], reverse=True)
    
    summary = []
    summary.append("📊 ROI Analysis - Which thoughts actually ship?")
    summary.append("=" * 50)
    summary.append("")
    
    # Top performers
    summary.append("🏆 Top Performers (by ROI score):")
    for i, (thought_id, data) in enumerate(sorted_thoughts[:5]):
        summary.append(f"  {i+1}. {thought_id}")
        summary.append(f"     ROI Score: {data['roi_score']}/100")
        summary.append(f"     Completion Rate: {data['completion_rate']}% ({data['shipped_count']}/{data['total_entries']})")
        summary.append(f"     Avg Energy: {data['avg_energy']:.1f}, Avg Vibe: {data['avg_vibe']:.1f}")
        if data['last_shipped']:
            summary.append(f"     Last Shipped: {data['last_shipped'][:10]}")
        summary.append("")
    
    # Shipping champions
    shipping_sorted = sorted(roi_data.items(), key=lambda x: x[1]['completion_rate'], reverse=True)
    summary.append("🚢 Best Shipping Rate:")
    for i, (thought_id, data) in enumerate(shipping_sorted[:3]):
        if data['completion_rate'] > 0:
            summary.append(f"  {i+1}. {thought_id}: {data['completion_rate']}% shipping rate")
    summary.append("")
    
    # Energy champions  
    energy_sorted = sorted(roi_data.items(), key=lambda x: x[1]['avg_energy'], reverse=True)
    summary.append("⚡ Highest Energy Thoughts:")
    for i, (thought_id, data) in enumerate(energy_sorted[:3]):
        if data['avg_energy'] > 0:
            energy_label = 'High' if data['avg_energy'] > 0.5 else 'Medium-High'
            summary.append(f"  {i+1}. {thought_id}: {energy_label} energy ({data['avg_energy']:.1f})")
    summary.append("")
    
    # Recent trends
    recent_sorted = sorted(roi_data.items(), key=lambda x: x[1]['recent_completion_rate'], reverse=True)
    summary.append("📈 Recent Trends (last 30 days):")
    for i, (thought_id, data) in enumerate(recent_sorted[:3]):
        if data['recent_entries'] > 0:
            summary.append(f"  {i+1}. {thought_id}: {data['recent_completion_rate']}% recent shipping ({data['recent_entries']} entries)")
    summary.append("")
    
    # Recommendations
    summary.append("💡 Recommendations:")
    high_roi = [t for t, d in roi_data.items() if d['roi_score'] > 70]
    low_roi = [t for t, d in roi_data.items() if d['roi_score'] < 30 and d['total_entries'] >= 3]
    
    if high_roi:
        summary.append(f"  • Focus more on: {', '.join(high_roi[:3])}")
    if low_roi:
        summary.append(f"  • Consider reducing: {', '.join(low_roi[:3])}")
    
    total_shipped = sum(d['shipped_count'] for d in roi_data.values())
    total_attempts = sum(d['total_entries'] for d in roi_data.values())
    overall_rate = (total_shipped / total_attempts) * 100 if total_attempts > 0 else 0
    
    summary.append("")
    summary.append(f"📊 Overall Stats:")
    summary.append(f"  • Total activities: {total_attempts}")
    summary.append(f"  • Total shipped: {total_shipped}")
    summary.append(f"  • Overall shipping rate: {overall_rate:.1f}%")
    
    return "\n".join(summary)

def dashboard_summary(roi_data, history):
    """Compact summary for dashboard consumption."""
    if not roi_data:
        return {'top': [], 'overall': {}, 'skills': {}}
    
    # Top 5 by ROI score
    sorted_thoughts = sorted(roi_data.items(), key=lambda x: x[1]['roi_score'], reverse=True)
    top = [{'id': t, **d} for t, d in sorted_thoughts[:8]]
    
    # Overall stats
    total_shipped = sum(d['shipped_count'] for d in roi_data.values())
    total_attempts = sum(d['total_entries'] for d in roi_data.values())
    overall_rate = (total_shipped / total_attempts) * 100 if total_attempts > 0 else 0
    
    # Skills breakdown
    skills_count = defaultdict(lambda: {'used': 0, 'shipped': 0})
    for entry in history:
        shipped = infer_shipped(entry)
        for skill in entry.get('skills_used', []):
            skills_count[skill]['used'] += 1
            if shipped:
                skills_count[skill]['shipped'] += 1
    
    skills = {k: {**v, 'rate': round(v['shipped']/v['used']*100, 1) if v['used'] > 0 else 0} 
              for k, v in sorted(skills_count.items(), key=lambda x: -x[1]['used'])}
    
    # Time-of-day analysis
    tod = defaultdict(lambda: {'count': 0, 'shipped': 0})
    for entry in history:
        try:
            hour = datetime.fromisoformat(entry.get('timestamp', '').replace('Z', '+00:00')).hour
            slot = 'night' if hour < 7 else 'morning' if hour < 12 else 'afternoon' if hour < 18 else 'evening'
            tod[slot]['count'] += 1
            if infer_shipped(entry):
                tod[slot]['shipped'] += 1
        except:
            continue
    
    time_of_day = {k: {**v, 'rate': round(v['shipped']/v['count']*100, 1) if v['count'] > 0 else 0}
                   for k, v in tod.items()}
    
    return {
        'top': top,
        'overall': {
            'total': total_attempts,
            'shipped': total_shipped,
            'rate': round(overall_rate, 1),
            'unique_thoughts': len(roi_data)
        },
        'skills': skills,
        'time_of_day': time_of_day
    }


def main():
    """Main CLI entry point."""
    args = sys.argv[1:]
    json_only = '--json' in args
    dashboard_mode = '--dashboard' in args
    
    # Load history
    history = load_history()
    
    # Calculate ROI metrics
    roi_data = calculate_roi_metrics(history)
    
    # Ensure output directory exists
    ROI_OUTPUT_FILE.parent.mkdir(exist_ok=True)
    
    # Save to JSON file
    output = {
        'generated_at': datetime.now().isoformat(),
        'total_history_entries': len(history),
        'thoughts_analyzed': len(roi_data),
        'roi_data': roi_data
    }
    
    with open(ROI_OUTPUT_FILE, 'w') as f:
        json.dump(output, f, indent=2)
    
    if dashboard_mode:
        print(json.dumps(dashboard_summary(roi_data, history), indent=2))
    elif json_only:
        print(json.dumps(output, indent=2))
    else:
        summary = generate_summary(roi_data)
        print(summary)
        print(f"\n💾 ROI data saved to {ROI_OUTPUT_FILE}")

if __name__ == "__main__":
    main()