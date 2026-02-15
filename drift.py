#!/usr/bin/env python3
"""
Mood drift calculation logic extracted from log_result.sh for testing.
This module provides pure functions for calculating mood drift from activity logs.
"""

def calculate_energy_vibe_scores(activity_log):
    """
    Calculate energy and vibe scores from activity log.
    
    Args:
        activity_log: List of activities with 'energy' and 'vibe' keys
        
    Returns:
        tuple: (energy_score, vibe_score)
    """
    energy_score = 0
    vibe_score = 0
    
    for activity in activity_log:
        energy = activity.get('energy', 'neutral')
        vibe = activity.get('vibe', 'neutral')
        
        if energy == 'high':
            energy_score += 1
        elif energy == 'low':
            energy_score -= 1
        # neutral contributes 0
        
        if vibe == 'positive':
            vibe_score += 1
        elif vibe == 'negative':
            vibe_score -= 1
        # neutral contributes 0
    
    return energy_score, vibe_score


def get_drift_map():
    """
    Get the drift map that defines how energy/vibe combinations affect mood traits.
    
    Returns:
        dict: Drift map with energy_vibe keys mapping to boost/dampen lists
    """
    return {
        'high_positive': {
            'boost': ['hyperfocus', 'chaotic', 'social'], 
            'dampen': ['cozy', 'philosophical']
        },
        'high_negative': {
            'boost': ['restless', 'determined'], 
            'dampen': ['cozy', 'social']
        },
        'low_positive': {
            'boost': ['cozy', 'philosophical', 'social'], 
            'dampen': ['hyperfocus', 'chaotic']
        },
        'low_negative': {
            'boost': ['cozy', 'philosophical'], 
            'dampen': ['chaotic', 'social', 'restless']
        },
    }


def apply_activity_drift(existing_boost, existing_dampen, energy, vibe):
    """
    Apply drift from a single activity to existing boost/dampen lists.
    
    Args:
        existing_boost: Set of currently boosted traits
        existing_dampen: Set of currently dampened traits  
        energy: 'high', 'neutral', or 'low'
        vibe: 'positive', 'neutral', or 'negative'
        
    Returns:
        tuple: (new_boost_set, new_dampen_set)
    """
    drift_map = get_drift_map()
    
    # Copy existing sets
    new_boost = set(existing_boost)
    new_dampen = set(existing_dampen)
    
    # Apply drift if not neutral
    if energy != 'neutral' or vibe != 'neutral':
        key = f"{energy}_{vibe}" if energy != 'neutral' and vibe != 'neutral' else None
        if key and key in drift_map:
            drift = drift_map[key]
            
            # Add new boosts and dampens
            new_boost.update(drift['boost'])
            new_dampen.update(drift['dampen'])
            
            # Remove contradictions (most recent wins)
            for b in drift['boost']:
                new_dampen.discard(b)
            for d in drift['dampen']:
                new_boost.discard(d)
    
    return new_boost, new_dampen


def calculate_mood_drift(activity_log, initial_boost=None, initial_dampen=None):
    """
    Calculate complete mood drift from activity log.
    
    Args:
        activity_log: List of activities with 'energy' and 'vibe' keys
        initial_boost: Initial set of boosted traits (default: empty)
        initial_dampen: Initial set of dampened traits (default: empty)
        
    Returns:
        dict: Result with energy_score, vibe_score, boosted_traits, dampened_traits
    """
    if initial_boost is None:
        initial_boost = set()
    if initial_dampen is None:
        initial_dampen = set()
    
    energy_score, vibe_score = calculate_energy_vibe_scores(activity_log)
    
    # Apply drift from the most recent activity  
    if activity_log:
        latest = activity_log[-1]
        energy = latest.get('energy', 'neutral')
        vibe = latest.get('vibe', 'neutral')
        
        boosted_traits, dampened_traits = apply_activity_drift(
            initial_boost, initial_dampen, energy, vibe
        )
    else:
        boosted_traits = set(initial_boost)
        dampened_traits = set(initial_dampen)
    
    return {
        'energy_score': energy_score,
        'vibe_score': vibe_score,
        'boosted_traits': list(boosted_traits),
        'dampened_traits': list(dampened_traits)
    }


def get_mood_name_from_scores(energy_score, vibe_score, activity_count=0):
    """
    Determine if mood name should change based on energy/vibe scores.
    
    Args:
        energy_score: Accumulated energy score
        vibe_score: Accumulated vibe score
        activity_count: Number of activities (must be >= 3 for mood change)
        
    Returns:
        dict: {'drifted_to': mood_name, 'drift_note': explanation} or None
    """
    if activity_count < 3:
        return None
    
    if energy_score >= 2 and vibe_score >= 2:
        return {
            'drifted_to': 'hyperfocus',
            'drift_note': 'Riding high — everything is clicking today'
        }
    elif energy_score <= -2 and vibe_score <= -2:
        return {
            'drifted_to': 'cozy', 
            'drift_note': 'Low energy day — pulling back to recharge'
        }
    elif energy_score >= 2 and vibe_score <= -1:
        return {
            'drifted_to': 'restless',
            'drift_note': 'High energy but frustrated — need to channel this'
        }
    elif vibe_score >= 2:
        return {
            'drifted_to': 'social',
            'drift_note': 'Good vibes — feeling chatty'
        }
    
    return None