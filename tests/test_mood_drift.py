#!/usr/bin/env python3
"""
Tests for mood drift calculation logic (Issue #39).
"""

import pytest
import sys
from pathlib import Path

# Add project root to path so we can import drift module
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from drift import (
    calculate_energy_vibe_scores,
    apply_activity_drift,
    calculate_mood_drift,
    get_mood_name_from_scores,
    get_drift_map
)


class TestEnergyVibeScores:
    """Test energy and vibe score accumulation from activities."""
    
    def test_empty_activity_log(self):
        """No activities should result in zero scores."""
        energy, vibe = calculate_energy_vibe_scores([])
        assert energy == 0
        assert vibe == 0
    
    def test_single_positive_high_activity(self):
        """Single high energy, positive vibe activity."""
        activities = [{'energy': 'high', 'vibe': 'positive'}]
        energy, vibe = calculate_energy_vibe_scores(activities)
        assert energy == 1
        assert vibe == 1
    
    def test_single_negative_low_activity(self):
        """Single low energy, negative vibe activity."""
        activities = [{'energy': 'low', 'vibe': 'negative'}]
        energy, vibe = calculate_energy_vibe_scores(activities)
        assert energy == -1
        assert vibe == -1
    
    def test_neutral_activities(self):
        """Neutral activities contribute zero to scores."""
        activities = [
            {'energy': 'neutral', 'vibe': 'neutral'},
            {'energy': 'neutral', 'vibe': 'positive'},
            {'energy': 'high', 'vibe': 'neutral'},
        ]
        energy, vibe = calculate_energy_vibe_scores(activities)
        assert energy == 1  # Only the high energy contributes
        assert vibe == 1    # Only the positive vibe contributes
    
    def test_multiple_positive_activities(self):
        """Multiple positive activities should increase scores."""
        activities = [
            {'energy': 'high', 'vibe': 'positive'},
            {'energy': 'high', 'vibe': 'positive'},
            {'energy': 'high', 'vibe': 'positive'},
        ]
        energy, vibe = calculate_energy_vibe_scores(activities)
        assert energy == 3
        assert vibe == 3
    
    def test_multiple_negative_activities(self):
        """Multiple negative activities should decrease scores."""
        activities = [
            {'energy': 'low', 'vibe': 'negative'},
            {'energy': 'low', 'vibe': 'negative'},
        ]
        energy, vibe = calculate_energy_vibe_scores(activities)
        assert energy == -2
        assert vibe == -2
    
    def test_mixed_activities(self):
        """Mixed activities should produce correct net scores."""
        activities = [
            {'energy': 'high', 'vibe': 'positive'},   # +1, +1
            {'energy': 'low', 'vibe': 'negative'},    # -1, -1
            {'energy': 'high', 'vibe': 'neutral'},    # +1, 0
            {'energy': 'neutral', 'vibe': 'positive'}, # 0, +1
        ]
        energy, vibe = calculate_energy_vibe_scores(activities)
        assert energy == 1  # 1 - 1 + 1 + 0
        assert vibe == 1    # 1 - 1 + 0 + 1
    
    def test_all_same_energy_vibe(self):
        """Edge case: all activities have same energy/vibe."""
        activities = [
            {'energy': 'neutral', 'vibe': 'neutral'},
            {'energy': 'neutral', 'vibe': 'neutral'},
            {'energy': 'neutral', 'vibe': 'neutral'},
        ]
        energy, vibe = calculate_energy_vibe_scores(activities)
        assert energy == 0
        assert vibe == 0


class TestDriftApplication:
    """Test how individual activities affect mood traits."""
    
    def test_high_positive_drift(self):
        """High energy + positive vibe should boost hyperfocus/chaotic/social."""
        boost, dampen = apply_activity_drift(set(), set(), 'high', 'positive')
        
        expected_boost = {'hyperfocus', 'chaotic', 'social'}
        expected_dampen = {'cozy', 'philosophical'}
        
        assert boost == expected_boost
        assert dampen == expected_dampen
    
    def test_low_negative_drift(self):
        """Low energy + negative vibe should boost cozy/philosophical."""
        boost, dampen = apply_activity_drift(set(), set(), 'low', 'negative')
        
        expected_boost = {'cozy', 'philosophical'}
        expected_dampen = {'chaotic', 'social', 'restless'}
        
        assert boost == expected_boost
        assert dampen == expected_dampen
    
    def test_neutral_energy_no_drift(self):
        """Neutral energy should not trigger drift."""
        initial_boost = {'existing'}
        initial_dampen = {'test'}
        
        boost, dampen = apply_activity_drift(initial_boost, initial_dampen, 'neutral', 'positive')
        
        # Should keep existing traits unchanged
        assert boost == initial_boost
        assert dampen == initial_dampen
    
    def test_neutral_vibe_no_drift(self):
        """Neutral vibe should not trigger drift."""
        initial_boost = {'existing'}
        initial_dampen = {'test'}
        
        boost, dampen = apply_activity_drift(initial_boost, initial_dampen, 'high', 'neutral')
        
        # Should keep existing traits unchanged  
        assert boost == initial_boost
        assert dampen == initial_dampen
    
    def test_contradiction_resolution_boost_wins(self):
        """When new boost conflicts with existing dampen, boost wins."""
        initial_boost = set()
        initial_dampen = {'hyperfocus'}  # This will conflict with new boost
        
        boost, dampen = apply_activity_drift(initial_boost, initial_dampen, 'high', 'positive')
        
        # hyperfocus should be boosted (removed from dampen, added to boost)
        assert 'hyperfocus' in boost
        assert 'hyperfocus' not in dampen
    
    def test_contradiction_resolution_dampen_wins(self):
        """When new dampen conflicts with existing boost, dampen wins.""" 
        initial_boost = {'social'}  # This will conflict with new dampen
        initial_dampen = set()
        
        boost, dampen = apply_activity_drift(initial_boost, initial_dampen, 'high', 'negative')
        
        # social should be dampened (removed from boost, added to dampen)
        assert 'social' not in boost
        assert 'social' in dampen
    
    def test_accumulation_with_existing_traits(self):
        """New traits should accumulate with existing ones."""
        initial_boost = {'existing_boost'}
        initial_dampen = {'existing_dampen'}
        
        boost, dampen = apply_activity_drift(initial_boost, initial_dampen, 'high', 'positive')
        
        # Should contain both existing and new traits
        assert 'existing_boost' in boost
        assert 'hyperfocus' in boost
        assert 'existing_dampen' in dampen
        assert 'cozy' in dampen


class TestCompleteMoodDrift:
    """Test end-to-end mood drift calculation."""
    
    def test_empty_log_no_drift(self):
        """Empty activity log should produce default values."""
        result = calculate_mood_drift([])
        
        assert result['energy_score'] == 0
        assert result['vibe_score'] == 0
        assert result['boosted_traits'] == []
        assert result['dampened_traits'] == []
    
    def test_single_activity_drift(self):
        """Single activity should apply its drift."""
        activities = [{'energy': 'high', 'vibe': 'positive'}]
        result = calculate_mood_drift(activities)
        
        assert result['energy_score'] == 1
        assert result['vibe_score'] == 1
        assert set(result['boosted_traits']) == {'hyperfocus', 'chaotic', 'social'}
        assert set(result['dampened_traits']) == {'cozy', 'philosophical'}
    
    def test_multiple_activities_latest_drift(self):
        """Should apply drift from latest activity only."""
        activities = [
            {'energy': 'high', 'vibe': 'positive'},  # Would boost hyperfocus
            {'energy': 'low', 'vibe': 'negative'},   # Latest - should boost cozy  
        ]
        result = calculate_mood_drift(activities)
        
        assert result['energy_score'] == 0  # 1 - 1 = 0
        assert result['vibe_score'] == 0    # 1 - 1 = 0
        # Drift should be from latest activity (low/negative)
        assert set(result['boosted_traits']) == {'cozy', 'philosophical'}
        assert set(result['dampened_traits']) == {'chaotic', 'social', 'restless'}
    
    def test_with_initial_traits(self):
        """Should preserve and modify initial traits."""
        initial_boost = {'initial_boost'}
        initial_dampen = {'initial_dampen'}
        activities = [{'energy': 'high', 'vibe': 'positive'}]
        
        result = calculate_mood_drift(activities, initial_boost, initial_dampen)
        
        # Should contain both initial and new traits
        boost_set = set(result['boosted_traits'])
        dampen_set = set(result['dampened_traits'])
        
        assert 'initial_boost' in boost_set
        assert 'hyperfocus' in boost_set
        assert 'initial_dampen' in dampen_set
        assert 'cozy' in dampen_set


class TestMoodNameChanges:
    """Test mood name drift based on score thresholds."""
    
    def test_no_change_insufficient_activities(self):
        """Less than 3 activities should not trigger mood change."""
        result = get_mood_name_from_scores(3, 3, activity_count=2)
        assert result is None
    
    def test_hyperfocus_drift(self):
        """High energy + high vibe scores should drift to hyperfocus."""
        result = get_mood_name_from_scores(2, 2, activity_count=3)
        
        assert result is not None
        assert result['drifted_to'] == 'hyperfocus'
        assert 'clicking' in result['drift_note']
    
    def test_cozy_drift(self):
        """Low energy + low vibe scores should drift to cozy."""
        result = get_mood_name_from_scores(-2, -2, activity_count=3)
        
        assert result is not None
        assert result['drifted_to'] == 'cozy'
        assert 'recharge' in result['drift_note']
    
    def test_restless_drift(self):
        """High energy + negative vibe should drift to restless."""
        result = get_mood_name_from_scores(2, -1, activity_count=3)
        
        assert result is not None
        assert result['drifted_to'] == 'restless'
        assert 'frustrated' in result['drift_note']
    
    def test_social_drift(self):
        """High vibe score should drift to social."""
        result = get_mood_name_from_scores(0, 2, activity_count=3)
        
        assert result is not None
        assert result['drifted_to'] == 'social'
        assert 'chatty' in result['drift_note']
    
    def test_no_drift_threshold_not_met(self):
        """Scores below thresholds should not trigger mood change.""" 
        result = get_mood_name_from_scores(1, 1, activity_count=5)
        assert result is None


class TestDriftMapIntegrity:
    """Test that the drift map is well-formed."""
    
    def test_drift_map_structure(self):
        """Drift map should have expected structure."""
        drift_map = get_drift_map()
        
        # Should have all expected keys
        expected_keys = ['high_positive', 'high_negative', 'low_positive', 'low_negative']
        assert set(drift_map.keys()) == set(expected_keys)
        
        # Each entry should have boost and dampen lists
        for key, entry in drift_map.items():
            assert 'boost' in entry
            assert 'dampen' in entry
            assert isinstance(entry['boost'], list)
            assert isinstance(entry['dampen'], list)
    
    def test_drift_map_no_empty_lists(self):
        """All boost/dampen lists should contain at least one trait."""
        drift_map = get_drift_map()
        
        for key, entry in drift_map.items():
            assert len(entry['boost']) > 0, f"{key} has empty boost list"
            assert len(entry['dampen']) > 0, f"{key} has empty dampen list"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])