#!/usr/bin/env python3
"""
Thought selection logic extracted from intrusive.sh for testing.
This module provides pure functions for weighted thought selection with mood biases.
"""

import random
import json
from typing import List, Dict, Any, Tuple, Optional


def load_thoughts_data(thoughts_file: str) -> Dict[str, Any]:
    """Load thoughts configuration from JSON file."""
    with open(thoughts_file) as f:
        return json.load(f)


def apply_mood_bias(weight: float, thought_id: str, today_mood: Optional[Dict]) -> Tuple[float, List[str], List[str]]:
    """
    Apply mood-based bias to thought weight.
    
    Args:
        weight: Base weight of the thought
        thought_id: ID of the thought
        today_mood: Today's mood data with boosted_traits and dampened_traits
        
    Returns:
        tuple: (adjusted_weight, boost_reasons, skip_reasons)
    """
    boost_reasons = []
    skip_reasons = []
    
    if not today_mood:
        return weight, boost_reasons, skip_reasons
    
    boosted = today_mood.get('boosted_traits', [])
    dampened = today_mood.get('dampened_traits', [])
    
    if thought_id in boosted:
        weight *= 1.8
        mood_name = today_mood.get('name', 'Unknown')
        mood_desc = today_mood.get('description', '')
        boost_reasons.append(f"Boosted by current mood ({mood_name}): {mood_desc}")
    elif thought_id in dampened:
        weight = max(0.2, weight * 0.5)
        mood_name = today_mood.get('name', 'Unknown')
        mood_desc = today_mood.get('description', 'something else')
        skip_reasons.append(f"Current mood ({mood_name}) dampens {thought_id} thoughts - feeling more like {mood_desc}")
    
    return weight, boost_reasons, skip_reasons


def apply_streak_weights(weight: float, thought_id: str, streak_weights: Dict[str, float]) -> Tuple[float, List[str], List[str]]:
    """
    Apply anti-rut streak-based weight adjustments.
    
    Args:
        weight: Current weight
        thought_id: ID of the thought
        streak_weights: Dict mapping thought IDs to multipliers
        
    Returns:
        tuple: (adjusted_weight, boost_reasons, skip_reasons)
    """
    boost_reasons = []
    skip_reasons = []
    
    if thought_id in streak_weights:
        streak_mult = streak_weights[thought_id]
        weight *= streak_mult
        
        if streak_mult < 0.8:
            skip_reasons.append(f'Anti-rut system dampening {thought_id} - you\'ve been doing this too much lately')
        elif streak_mult > 1.2:
            boost_reasons.append(f'Anti-rut system boosting {thought_id} - haven\'t done this in a while')
    
    return weight, boost_reasons, skip_reasons


def apply_human_mood_influence(weight: float, thought_id: str, human_mood: Optional[Dict]) -> Tuple[float, List[str], List[str]]:
    """
    Apply human mood-based adjustments to thought weight.
    
    Args:
        weight: Current weight
        thought_id: ID of the thought
        human_mood: Human mood data with mood, energy, vibe, confidence
        
    Returns:
        tuple: (adjusted_weight, boost_reasons, skip_reasons)
    """
    boost_reasons = []
    skip_reasons = []
    
    if not human_mood or human_mood.get('confidence', 0) <= 0.4:
        return weight, boost_reasons, skip_reasons
    
    h_mood = human_mood.get('mood', 'neutral')
    
    # Define influence rules
    influence_rules = {
        'stressed': {
            'dampen': ['random-thought', 'ask-opinion', 'ask-preference'],
            'multiplier': 0.5,
            'reason': 'Your human seems stressed - avoiding {thought_id} to give them space'
        },
        'excited': {
            'boost': ['share-discovery', 'pitch-idea', 'moltbook-post'],
            'multiplier': 1.5,
            'reason': 'Boosted to match human\'s excited energy'
        },
        'frustrated': {
            'dampen': ['ask-feedback', 'random-thought'],
            'multiplier': 0.3,
            'reason': 'Your human seems frustrated - staying away from {thought_id} for now'
        },
        'curious': {
            'boost': ['share-discovery', 'ask-opinion', 'learn'],
            'multiplier': 1.4,
            'reason': 'Boosted to feed human\'s curiosity'
        },
        'focused': {
            'dampen': ['random-thought', 'ask-opinion'],
            'multiplier': 0.4,
            'reason': 'Your human is in the zone - not interrupting with {thought_id}'
        },
        'happy': {
            'boost': ['moltbook-social', 'share-discovery', 'creative-chaos'],
            'multiplier': 1.3,
            'reason': 'Boosted to amplify good vibes'
        }
    }
    
    if h_mood in influence_rules:
        rule = influence_rules[h_mood]
        
        if 'dampen' in rule and thought_id in rule['dampen']:
            weight *= rule['multiplier']
            reason = rule['reason'].format(thought_id=thought_id)
            skip_reasons.append(reason)
        elif 'boost' in rule and thought_id in rule['boost']:
            weight *= rule['multiplier']
            reason = rule['reason'].format(thought_id=thought_id)
            boost_reasons.append(reason)
    
    return weight, boost_reasons, skip_reasons


def calculate_thought_weights(thoughts: List[Dict], today_mood: Optional[Dict] = None, 
                            streak_weights: Optional[Dict[str, float]] = None,
                            human_mood: Optional[Dict] = None) -> List[Dict]:
    """
    Calculate final weights for all thoughts with full reasoning.
    
    Args:
        thoughts: List of thought definitions with id, weight, prompt
        today_mood: Current mood data
        streak_weights: Anti-rut weight multipliers
        human_mood: Human mood influence data
        
    Returns:
        List of candidate dicts with full weight calculation details
    """
    if streak_weights is None:
        streak_weights = {}
    
    candidates = []
    
    for thought in thoughts:
        thought_id = thought['id']
        original_weight = float(thought.get('weight', 1))
        current_weight = original_weight
        
        all_boost_reasons = []
        all_skip_reasons = []
        
        # Apply mood bias
        current_weight, boost_reasons, skip_reasons = apply_mood_bias(
            current_weight, thought_id, today_mood
        )
        all_boost_reasons.extend(boost_reasons)
        all_skip_reasons.extend(skip_reasons)
        
        # Apply streak weights
        current_weight, boost_reasons, skip_reasons = apply_streak_weights(
            current_weight, thought_id, streak_weights
        )
        all_boost_reasons.extend(boost_reasons)
        all_skip_reasons.extend(skip_reasons)
        
        # Apply human mood influence
        current_weight, boost_reasons, skip_reasons = apply_human_mood_influence(
            current_weight, thought_id, human_mood
        )
        all_boost_reasons.extend(boost_reasons)
        all_skip_reasons.extend(skip_reasons)
        
        candidate = {
            'id': thought_id,
            'original_weight': original_weight,
            'final_weight': current_weight,
            'boost_reasons': all_boost_reasons,
            'skip_reasons': all_skip_reasons,
            'prompt': thought['prompt']
        }
        
        candidates.append(candidate)
    
    return candidates


def create_weighted_pool(candidates: List[Dict]) -> List[Dict]:
    """
    Create weighted selection pool from candidates.
    
    Args:
        candidates: List of candidate dicts with final_weight
        
    Returns:
        List where each thought appears proportionally to its weight
    """
    pool = []
    
    for candidate in candidates:
        # Scale weight and ensure minimum of 1
        final_weight = max(1, int(candidate['final_weight'] * 10))
        pool.extend([candidate] * final_weight)
    
    return pool


def select_weighted_thought(thoughts: List[Dict], today_mood: Optional[Dict] = None,
                          streak_weights: Optional[Dict[str, float]] = None,
                          human_mood: Optional[Dict] = None,
                          random_seed: Optional[float] = None) -> Dict:
    """
    Select a thought using weighted random selection with all biases applied.
    
    Args:
        thoughts: List of thought definitions
        today_mood: Current mood data
        streak_weights: Anti-rut weight multipliers  
        human_mood: Human mood influence data
        random_seed: Optional seed for deterministic testing
        
    Returns:
        Selection result with chosen thought and decision trace
    """
    # Calculate weights
    candidates = calculate_thought_weights(thoughts, today_mood, streak_weights, human_mood)
    
    # Create weighted pool
    pool = create_weighted_pool(candidates)
    
    # Make selection
    if random_seed is not None:
        random.seed(random_seed)
    
    if not pool:
        raise ValueError("No valid thoughts in pool")
    
    chosen = random.choice(pool)
    
    # Find heavily dampened thoughts for rejection tracking
    skipped_thoughts = []
    for candidate in candidates:
        if (candidate['final_weight'] < candidate['original_weight'] * 0.6 and 
            candidate['skip_reasons']):
            skipped_thoughts.append({
                'id': candidate['id'],
                'original_weight': candidate['original_weight'],
                'final_weight': candidate['final_weight'],
                'reasons': candidate['skip_reasons']
            })
    
    return {
        'chosen': chosen,
        'all_candidates': candidates,
        'skipped_thoughts': skipped_thoughts,
        'pool_size': len(pool),
        'total_candidates': len(candidates)
    }


def get_effective_weights_distribution(thoughts: List[Dict], today_mood: Optional[Dict] = None,
                                     streak_weights: Optional[Dict[str, float]] = None,
                                     human_mood: Optional[Dict] = None) -> Dict[str, float]:
    """
    Get the effective probability distribution for thoughts after all biases.
    
    Args:
        thoughts: List of thought definitions
        today_mood: Current mood data
        streak_weights: Anti-rut weight multipliers
        human_mood: Human mood influence data
        
    Returns:
        Dict mapping thought IDs to their selection probabilities
    """
    candidates = calculate_thought_weights(thoughts, today_mood, streak_weights, human_mood)
    pool = create_weighted_pool(candidates)
    
    if not pool:
        return {}
    
    # Count occurrences in pool
    counts = {}
    for item in pool:
        thought_id = item['id']
        counts[thought_id] = counts.get(thought_id, 0) + 1
    
    # Convert to probabilities
    total = len(pool)
    probabilities = {thought_id: count / total for thought_id, count in counts.items()}
    
    return probabilities