#!/usr/bin/env python3
"""
Tests for weighted thought selection logic (Issue #40).
"""

import pytest
import sys
from pathlib import Path
from collections import Counter
import random
import math

# Add project root to path so we can import thought_selector module
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from thought_selector import (
    apply_mood_bias,
    apply_streak_weights,
    apply_human_mood_influence,
    calculate_thought_weights,
    create_weighted_pool,
    select_weighted_thought,
    get_effective_weights_distribution
)


# Test data fixtures
@pytest.fixture
def sample_thoughts():
    """Sample thought definitions for testing."""
    return [
        {'id': 'high-weight', 'weight': 3, 'prompt': 'High weight thought'},
        {'id': 'medium-weight', 'weight': 2, 'prompt': 'Medium weight thought'}, 
        {'id': 'low-weight', 'weight': 1, 'prompt': 'Low weight thought'},
        {'id': 'zero-weight', 'weight': 0, 'prompt': 'Zero weight thought'},
    ]


@pytest.fixture
def hyperfocus_mood():
    """Hyperfocus mood that boosts certain thoughts."""
    return {
        'id': 'hyperfocus',
        'name': 'Hyperfocus',
        'description': 'Locked in. Everything clicks.',
        'boosted_traits': ['high-weight', 'medium-weight'],
        'dampened_traits': ['low-weight']
    }


@pytest.fixture
def streak_weights():
    """Anti-rut streak weights."""
    return {
        'high-weight': 0.5,    # Dampened by streak
        'medium-weight': 1.5,  # Boosted by streak
        'low-weight': 0.3      # Heavily dampened
    }


@pytest.fixture 
def excited_human_mood():
    """Human mood that affects thought selection."""
    return {
        'mood': 'excited',
        'confidence': 0.8,
        'energy': 'high',
        'vibe': 'positive'
    }


class TestMoodBias:
    """Test mood-based weight adjustments."""
    
    def test_no_mood_no_change(self, sample_thoughts):
        """No mood data should leave weights unchanged."""
        weight, boosts, skips = apply_mood_bias(2.0, 'test-thought', None)
        assert weight == 2.0
        assert boosts == []
        assert skips == []
    
    def test_boosted_trait_increases_weight(self, hyperfocus_mood):
        """Thoughts matching boosted traits should get weight increase."""
        weight, boosts, skips = apply_mood_bias(2.0, 'high-weight', hyperfocus_mood)
        
        assert weight == 2.0 * 1.8  # 1.8x multiplier
        assert len(boosts) == 1
        assert 'Boosted by current mood' in boosts[0]
        assert skips == []
    
    def test_dampened_trait_decreases_weight(self, hyperfocus_mood):
        """Thoughts matching dampened traits should get weight decrease."""
        weight, boosts, skips = apply_mood_bias(2.0, 'low-weight', hyperfocus_mood)
        
        assert weight == 2.0 * 0.5  # 0.5x multiplier
        assert boosts == []
        assert len(skips) == 1
        assert 'dampens low-weight thoughts' in skips[0]
    
    def test_dampened_minimum_weight(self):
        """Dampened thoughts should never go below 0.2."""
        mood = {'boosted_traits': [], 'dampened_traits': ['test']}
        weight, _, _ = apply_mood_bias(0.1, 'test', mood)
        assert weight == 0.2  # Clamped to minimum


class TestStreakWeights:
    """Test anti-rut streak weight adjustments."""
    
    def test_no_streak_weights_no_change(self):
        """Empty streak weights should leave weight unchanged."""
        weight, boosts, skips = apply_streak_weights(2.0, 'test', {})
        assert weight == 2.0
        assert boosts == []
        assert skips == []
    
    def test_streak_dampening(self, streak_weights):
        """Thoughts with low streak multipliers should be dampened."""
        weight, boosts, skips = apply_streak_weights(2.0, 'high-weight', streak_weights)
        
        assert weight == 2.0 * 0.5  # 0.5x multiplier
        assert boosts == []
        assert len(skips) == 1
        assert 'doing this too much lately' in skips[0]
    
    def test_streak_boosting(self, streak_weights):
        """Thoughts with high streak multipliers should be boosted."""
        weight, boosts, skips = apply_streak_weights(2.0, 'medium-weight', streak_weights)
        
        assert weight == 2.0 * 1.5  # 1.5x multiplier
        assert len(boosts) == 1
        assert 'haven\'t done this in a while' in boosts[0]
        assert skips == []


class TestHumanMoodInfluence:
    """Test human mood influence on thought selection."""
    
    def test_low_confidence_no_influence(self):
        """Low confidence human mood should not affect weights."""
        low_conf_mood = {'mood': 'excited', 'confidence': 0.3}
        weight, boosts, skips = apply_human_mood_influence(2.0, 'share-discovery', low_conf_mood)
        
        assert weight == 2.0
        assert boosts == []
        assert skips == []
    
    def test_excited_human_boosts_thoughts(self, excited_human_mood):
        """Excited human should boost share/pitch thoughts."""
        weight, boosts, skips = apply_human_mood_influence(2.0, 'share-discovery', excited_human_mood)
        
        assert weight == 2.0 * 1.5  # 1.5x multiplier
        assert len(boosts) == 1
        assert 'match human\'s excited energy' in boosts[0]
        assert skips == []
    
    def test_stressed_human_dampens_thoughts(self):
        """Stressed human should dampen interrupting thoughts."""
        stressed_mood = {'mood': 'stressed', 'confidence': 0.9}
        weight, boosts, skips = apply_human_mood_influence(2.0, 'random-thought', stressed_mood)
        
        assert weight == 2.0 * 0.5  # 0.5x multiplier
        assert boosts == []
        assert len(skips) == 1
        assert 'give them space' in skips[0]


class TestWeightCalculation:
    """Test complete weight calculation with all factors."""
    
    def test_weight_calculation_no_biases(self, sample_thoughts):
        """With no biases, weights should remain original."""
        candidates = calculate_thought_weights(sample_thoughts)
        
        for candidate in candidates:
            assert candidate['final_weight'] == candidate['original_weight']
            assert candidate['boost_reasons'] == []
            assert candidate['skip_reasons'] == []
    
    def test_weight_calculation_with_mood(self, sample_thoughts, hyperfocus_mood):
        """Mood biases should be applied correctly."""
        candidates = calculate_thought_weights(sample_thoughts, today_mood=hyperfocus_mood)
        
        # Find specific candidates
        high_weight = next(c for c in candidates if c['id'] == 'high-weight')
        low_weight = next(c for c in candidates if c['id'] == 'low-weight')
        
        # high-weight should be boosted
        assert high_weight['final_weight'] > high_weight['original_weight']
        assert len(high_weight['boost_reasons']) > 0
        
        # low-weight should be dampened
        assert low_weight['final_weight'] < low_weight['original_weight']  
        assert len(low_weight['skip_reasons']) > 0
    
    def test_cumulative_effects(self, sample_thoughts, hyperfocus_mood, streak_weights, excited_human_mood):
        """All bias types should stack correctly."""
        candidates = calculate_thought_weights(
            sample_thoughts,
            today_mood=hyperfocus_mood,
            streak_weights=streak_weights,
            human_mood=excited_human_mood
        )
        
        # medium-weight gets boosted by mood AND streak
        medium = next(c for c in candidates if c['id'] == 'medium-weight')
        expected_weight = 2.0 * 1.8 * 1.5  # mood boost * streak boost
        assert medium['final_weight'] == expected_weight
        assert len(medium['boost_reasons']) >= 2


class TestWeightedPool:
    """Test weighted pool creation."""
    
    def test_pool_creation_basic(self):
        """Pool should contain thoughts proportional to their weights."""
        candidates = [
            {'id': 'thought1', 'final_weight': 2.0},
            {'id': 'thought2', 'final_weight': 1.0},
        ]
        
        pool = create_weighted_pool(candidates)
        
        # Count occurrences
        counts = Counter(item['id'] for item in pool)
        
        # thought1 should appear twice as often as thought2
        assert counts['thought1'] == 20  # 2.0 * 10
        assert counts['thought2'] == 10  # 1.0 * 10
    
    def test_minimum_weight_applied(self):
        """Very low weights should still get minimum representation."""
        candidates = [{'id': 'low', 'final_weight': 0.05}]
        pool = create_weighted_pool(candidates)
        
        # Should get at least 1 entry despite very low weight
        assert len(pool) >= 1


class TestThoughtSelection:
    """Test complete thought selection process."""
    
    def test_selection_deterministic_with_seed(self, sample_thoughts):
        """Selection should be deterministic when seeded."""
        result1 = select_weighted_thought(sample_thoughts, random_seed=42)
        result2 = select_weighted_thought(sample_thoughts, random_seed=42)
        
        assert result1['chosen']['id'] == result2['chosen']['id']
    
    def test_selection_returns_complete_info(self, sample_thoughts):
        """Selection should return comprehensive decision information."""
        result = select_weighted_thought(sample_thoughts)
        
        assert 'chosen' in result
        assert 'all_candidates' in result  
        assert 'skipped_thoughts' in result
        assert 'pool_size' in result
        assert 'total_candidates' in result
        
        assert result['chosen']['id'] in [t['id'] for t in sample_thoughts]
        assert result['total_candidates'] == len(sample_thoughts)
    
    def test_heavily_dampened_thoughts_marked_skipped(self, sample_thoughts, hyperfocus_mood):
        """Heavily dampened thoughts should be tracked as skipped.""" 
        result = select_weighted_thought(sample_thoughts, today_mood=hyperfocus_mood)
        
        # low-weight thought should be in skipped (dampened by 50%)
        skipped_ids = [s['id'] for s in result['skipped_thoughts']]
        assert 'low-weight' in skipped_ids


class TestProbabilityDistribution:
    """Test probability distributions from weight calculations."""
    
    def test_base_weights_distribution(self, sample_thoughts):
        """Base weights should produce expected probability ratios."""
        probs = get_effective_weights_distribution(sample_thoughts)
        
        # Verify all thoughts are represented
        thought_ids = [t['id'] for t in sample_thoughts]
        for thought_id in thought_ids:
            if thought_id != 'zero-weight':  # Zero weight might not appear
                assert thought_id in probs
        
        # High weight should be more likely than low weight
        if 'high-weight' in probs and 'low-weight' in probs:
            assert probs['high-weight'] > probs['low-weight']
    
    def test_mood_affects_distribution(self, sample_thoughts, hyperfocus_mood):
        """Mood should significantly alter probability distribution."""
        base_probs = get_effective_weights_distribution(sample_thoughts)
        mood_probs = get_effective_weights_distribution(sample_thoughts, today_mood=hyperfocus_mood)
        
        # Boosted thoughts should have higher probability
        if 'high-weight' in base_probs and 'high-weight' in mood_probs:
            assert mood_probs['high-weight'] > base_probs['high-weight']
        
        # Dampened thoughts should have lower probability  
        if 'low-weight' in base_probs and 'low-weight' in mood_probs:
            assert mood_probs['low-weight'] < base_probs['low-weight']


class TestStatisticalProperties:
    """Statistical tests for thought selection behavior."""
    
    def test_hyperfocus_boosts_vs_dampens_statistical(self, sample_thoughts, hyperfocus_mood):
        """Statistical test: boosted thoughts should appear significantly more than dampened."""
        num_trials = 1000
        boosted_count = 0
        dampened_count = 0
        
        for _ in range(num_trials):
            result = select_weighted_thought(sample_thoughts, today_mood=hyperfocus_mood)
            chosen_id = result['chosen']['id']
            
            if chosen_id in hyperfocus_mood['boosted_traits']:
                boosted_count += 1
            elif chosen_id in hyperfocus_mood['dampened_traits']:
                dampened_count += 1
        
        # Boosted thoughts should appear significantly more often
        # Using a simple ratio test - boosted should be at least 2x more common
        if dampened_count > 0:
            ratio = boosted_count / dampened_count
            assert ratio >= 2.0, f"Boosted/dampened ratio {ratio} is too low"
        
        # Boosted thoughts should appear in at least 30% of trials
        boosted_rate = boosted_count / num_trials
        assert boosted_rate >= 0.3, f"Boosted rate {boosted_rate} is too low"
    
    def test_zero_weight_thoughts_rare(self):
        """Zero or very low weight thoughts should rarely/never get picked."""
        thoughts = [
            {'id': 'normal', 'weight': 3, 'prompt': 'Normal weight'},  # Increased weight
            {'id': 'tiny', 'weight': 0.01, 'prompt': 'Tiny weight'},
            {'id': 'zero', 'weight': 0, 'prompt': 'Zero weight'},
        ]
        
        num_trials = 1000
        tiny_count = 0
        zero_count = 0
        
        for _ in range(num_trials):
            result = select_weighted_thought(thoughts)
            chosen_id = result['chosen']['id']
            
            if chosen_id == 'tiny':
                tiny_count += 1
            elif chosen_id == 'zero':
                zero_count += 1
        
        # Even zero weight gets minimum representation due to the minimum weight of 1
        # So we expect it to be rare but not completely absent
        zero_rate = zero_count / num_trials
        tiny_rate = tiny_count / num_trials
        normal_count = num_trials - tiny_count - zero_count
        normal_rate = normal_count / num_trials
        
        # Normal weight (3) should dominate selections (at least 70%)
        assert normal_rate >= 0.70, f"Normal weight should dominate, got rate: {normal_rate}"
        
        # Zero and tiny should be much less frequent
        assert zero_rate <= 0.15, f"Zero weight selected too often: {zero_rate}"
        assert tiny_rate <= 0.15, f"Tiny weight selected too often: {tiny_rate}"
    
    def test_all_weights_non_negative(self, sample_thoughts, hyperfocus_mood, streak_weights):
        """All final weights should be non-negative."""
        candidates = calculate_thought_weights(
            sample_thoughts,
            today_mood=hyperfocus_mood,
            streak_weights=streak_weights
        )
        
        for candidate in candidates:
            assert candidate['final_weight'] >= 0, f"Negative weight for {candidate['id']}: {candidate['final_weight']}"
    
    def test_selection_frequency_within_tolerance(self, sample_thoughts):
        """Selection frequencies should be within reasonable tolerance of expected probabilities."""
        num_trials = 2000
        expected_probs = get_effective_weights_distribution(sample_thoughts)
        actual_counts = Counter()
        
        for _ in range(num_trials):
            result = select_weighted_thought(sample_thoughts)
            actual_counts[result['chosen']['id']] += 1
        
        # Test each thought's frequency
        for thought_id, expected_prob in expected_probs.items():
            if expected_prob > 0.01:  # Skip very low probability thoughts
                actual_count = actual_counts[thought_id]
                actual_freq = actual_count / num_trials
                
                # Allow 30% tolerance around expected frequency
                tolerance = max(0.05, expected_prob * 0.3)
                lower_bound = expected_prob - tolerance
                upper_bound = expected_prob + tolerance
                
                assert lower_bound <= actual_freq <= upper_bound, \
                    f"Frequency for {thought_id}: expected {expected_prob:.3f}, got {actual_freq:.3f}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])