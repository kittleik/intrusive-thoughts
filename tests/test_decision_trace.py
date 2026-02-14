#!/usr/bin/env python3
"""
Test decision trace reconstruction functionality.
Tests the decision_trace.py module to ensure it correctly analyzes decision paths.
"""

import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open
import sys
import os

# Add project root to path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from decision_trace import (
    load_decisions_log,
    load_history,
    find_decision_by_id,
    find_recent_decision,
    find_decision_from_history,
    explain_decision
)


@pytest.fixture
def sample_decisions():
    """Sample decisions.json data with known entries."""
    return [
        {
            "timestamp": "2024-02-10T14:30:00",
            "mood": "day",
            "mood_id": "focused",
            "winner": {
                "id": "share-discovery",
                "prompt": "Share an interesting discovery or insight you found",
                "final_weight": 2.5,
                "boost_reasons": ["Boosted by current mood (Focused): deep work mode, analytical thinking"]
            },
            "all_candidates": [
                {
                    "id": "share-discovery",
                    "original_weight": 1.5,
                    "final_weight": 2.5,
                    "boost_reasons": ["Boosted by current mood (Focused): deep work mode, analytical thinking"],
                    "skip_reasons": [],
                    "prompt": "Share an interesting discovery or insight you found"
                },
                {
                    "id": "random-thought",
                    "original_weight": 2.0,
                    "final_weight": 1.0,
                    "boost_reasons": [],
                    "skip_reasons": ["Current mood (Focused) dampens random-thought thoughts - feeling more like deep work mode"],
                    "prompt": "Share a completely random thought"
                },
                {
                    "id": "ask-opinion",
                    "original_weight": 1.8,
                    "final_weight": 1.8,
                    "boost_reasons": [],
                    "skip_reasons": [],
                    "prompt": "Ask for opinion on something"
                }
            ],
            "skipped_thoughts": [
                {
                    "id": "random-thought",
                    "original_weight": 2.0,
                    "final_weight": 1.0,
                    "reasons": ["Current mood (Focused) dampens random-thought thoughts - feeling more like deep work mode"]
                }
            ],
            "random_roll": 0.123456,
            "total_candidates": 3,
            "pool_size": 62
        },
        {
            "timestamp": "2024-02-11T09:15:00",
            "mood": "day", 
            "mood_id": "creative",
            "winner": {
                "id": "creative-chaos",
                "prompt": "Generate something completely unexpected and creative",
                "final_weight": 3.2,
                "boost_reasons": ["Boosted to amplify good vibes", "Anti-rut system boosting creative-chaos - haven't done this in a while"]
            },
            "all_candidates": [
                {
                    "id": "creative-chaos",
                    "original_weight": 2.0,
                    "final_weight": 3.2,
                    "boost_reasons": ["Boosted to amplify good vibes", "Anti-rut system boosting creative-chaos - haven't done this in a while"],
                    "skip_reasons": [],
                    "prompt": "Generate something completely unexpected and creative"
                }
            ],
            "skipped_thoughts": [],
            "random_roll": 0.654321,
            "total_candidates": 1,
            "pool_size": 32
        }
    ]


@pytest.fixture
def sample_history():
    """Sample history.json data for fallback testing."""
    return [
        {
            "timestamp": "2024-02-09T16:20:00",
            "thought_id": "moltbook-post",
            "prompt": "Write a post for Moltbook",
            "mood": "day",
            "today_mood": "energetic"
        },
        {
            "timestamp": "2024-02-09T18:45:00", 
            "thought_id": "learn",
            "prompt": "Learn something new and share it",
            "mood": "night",
            "today_mood": "curious"
        }
    ]


class TestDecisionTraceLoading:
    """Test loading decision and history data."""
    
    def test_load_decisions_log_success(self, sample_decisions):
        """Test successful loading of decisions.json."""
        with tempfile.TemporaryDirectory() as temp_dir:
            decisions_file = Path(temp_dir) / "log" / "decisions.json"
            decisions_file.parent.mkdir(parents=True)
            decisions_file.write_text(json.dumps(sample_decisions))
            
            with patch('decision_trace.get_data_dir', return_value=Path(temp_dir)):
                result = load_decisions_log()
                assert result == sample_decisions
    
    def test_load_decisions_log_missing_file(self):
        """Test handling of missing decisions.json file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('decision_trace.get_data_dir', return_value=Path(temp_dir)):
                result = load_decisions_log()
                assert result == []
    
    def test_load_decisions_log_invalid_json(self):
        """Test handling of corrupted decisions.json file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            decisions_file = Path(temp_dir) / "log" / "decisions.json"
            decisions_file.parent.mkdir(parents=True)
            decisions_file.write_text("invalid json content")
            
            with patch('decision_trace.get_data_dir', return_value=Path(temp_dir)):
                result = load_decisions_log()
                assert result == []
    
    def test_load_history_success(self, sample_history):
        """Test successful loading of history.json."""
        with tempfile.TemporaryDirectory() as temp_dir:
            history_file = Path(temp_dir) / "history.json"
            history_file.write_text(json.dumps(sample_history))
            
            with patch('decision_trace.get_file_path', return_value=history_file):
                result = load_history()
                assert result == sample_history
    
    def test_load_history_missing_file(self):
        """Test handling of missing history.json file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            history_file = Path(temp_dir) / "history.json"
            
            with patch('decision_trace.get_file_path', return_value=history_file):
                result = load_history()
                assert result == []


class TestDecisionFinding:
    """Test finding specific decisions."""
    
    def test_find_decision_by_id_found(self, sample_decisions):
        """Test finding an existing decision by ID."""
        result = find_decision_by_id(sample_decisions, "share-discovery")
        assert result is not None
        assert result["winner"]["id"] == "share-discovery"
        assert result["mood_id"] == "focused"
    
    def test_find_decision_by_id_not_found(self, sample_decisions):
        """Test searching for a non-existent decision ID."""
        result = find_decision_by_id(sample_decisions, "non-existent")
        assert result is None
    
    def test_find_decision_by_id_empty_list(self):
        """Test finding decision in empty decisions list."""
        result = find_decision_by_id([], "any-id")
        assert result is None
    
    def test_find_recent_decision_success(self, sample_decisions):
        """Test finding the most recent decision."""
        result = find_recent_decision(sample_decisions)
        assert result is not None
        # Should return the one with latest timestamp (2024-02-11)
        assert result["winner"]["id"] == "creative-chaos"
        assert result["timestamp"] == "2024-02-11T09:15:00"
    
    def test_find_recent_decision_empty_list(self):
        """Test finding recent decision in empty list."""
        result = find_recent_decision([])
        assert result is None


class TestHistoryFallback:
    """Test fallback to history.json when decisions.json is unavailable."""
    
    def test_find_decision_from_history_by_id(self, sample_history):
        """Test reconstructing decision from history by ID."""
        result = find_decision_from_history(sample_history, "learn")
        assert result is not None
        assert result["winner"]["id"] == "learn"
        assert result["winner"]["prompt"] == "Learn something new and share it"
        assert result["mood"] == "night"
        assert result["mood_id"] == "curious"
        assert "note" in result
        assert "Reconstructed from history.json" in result["note"]
    
    def test_find_decision_from_history_recent(self, sample_history):
        """Test getting most recent decision from history."""
        result = find_decision_from_history(sample_history, None)
        assert result is not None
        # Should get the last entry
        assert result["winner"]["id"] == "learn"
        assert result["timestamp"] == "2024-02-09T18:45:00"
    
    def test_find_decision_from_history_not_found(self, sample_history):
        """Test searching for non-existent ID in history."""
        result = find_decision_from_history(sample_history, "non-existent")
        assert result is None
    
    def test_find_decision_from_history_empty(self):
        """Test fallback with empty history."""
        result = find_decision_from_history([], None)
        assert result is None


class TestDecisionAnalysis:
    """Test the decision explanation and analysis."""
    
    def test_explain_decision_winner_identification(self, sample_decisions, capsys):
        """Test that decision trace correctly identifies the winner thought."""
        decision = sample_decisions[0]
        explain_decision(decision)
        
        captured = capsys.readouterr()
        assert "🎯 Selected Action:" in captured.out
        assert "share-discovery" in captured.out
        assert "Final Weight: 2.50" in captured.out
    
    def test_explain_decision_candidate_listing(self, sample_decisions, capsys):
        """Test that all candidate thoughts are listed with effective weights."""
        decision = sample_decisions[0]
        explain_decision(decision)
        
        captured = capsys.readouterr()
        assert "⚖️ All Candidate Thoughts" in captured.out
        assert "share-discovery: 1.5 → 2.5" in captured.out
        assert "random-thought: 2.0 → 1.0" in captured.out
        assert "ask-opinion: 1.8 → 1.8" in captured.out
    
    def test_explain_decision_skip_reasons(self, sample_decisions, capsys):
        """Test that skipped thoughts show correct rejection reasons."""
        decision = sample_decisions[0]
        explain_decision(decision)
        
        captured = capsys.readouterr()
        assert "🚫 Heavily Dampened Thoughts:" in captured.out
        assert "random-thought: 2.0 → 1.0" in captured.out
        assert "Current mood (Focused) dampens random-thought" in captured.out
    
    def test_explain_decision_boost_reasons(self, sample_decisions, capsys):
        """Test that boost reasons are shown correctly."""
        decision = sample_decisions[1]  # The creative-chaos decision
        explain_decision(decision)
        
        captured = capsys.readouterr()
        assert "✅ Boosted to amplify good vibes" in captured.out
        assert "✅ Anti-rut system boosting creative-chaos" in captured.out
    
    def test_explain_decision_mood_context(self, sample_decisions, capsys):
        """Test that mood context is displayed."""
        decision = sample_decisions[0]
        explain_decision(decision)
        
        captured = capsys.readouterr()
        assert "🌈 Mood Context:" in captured.out
        assert "day (mood_id: focused)" in captured.out
    
    def test_explain_decision_selection_process(self, sample_decisions, capsys):
        """Test that selection process details are shown."""
        decision = sample_decisions[0]
        explain_decision(decision)
        
        captured = capsys.readouterr()
        assert "📊 Selection Process:" in captured.out
        assert "Total candidate thoughts: 3" in captured.out
        assert "Final pool size (after weighting): 62" in captured.out
        assert "Random roll value: 0.123456" in captured.out
    
    def test_explain_decision_weight_analysis(self, sample_decisions, capsys):
        """Test weight-based probability analysis."""
        # Test high probability selection
        decision = sample_decisions[1]  # creative-chaos with weight 3.2
        explain_decision(decision)
        
        captured = capsys.readouterr()
        assert "High probability selection (weight 3.2)" in captured.out
        assert "strong advantages" in captured.out


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_decision_data(self, capsys):
        """Test handling of empty or minimal decision data."""
        minimal_decision = {
            "timestamp": "2024-02-10T10:00:00",
            "mood": "day",
            "mood_id": "none",
            "winner": {"id": "test", "final_weight": 1.0, "prompt": "Test prompt"},
            "all_candidates": [],
            "skipped_thoughts": [],
            "total_candidates": 0,
            "pool_size": 10,
            "random_roll": 0.5
        }
        
        explain_decision(minimal_decision)
        captured = capsys.readouterr()
        
        # Should not crash and should show basic info
        assert "Decision Trace Analysis" in captured.out
        assert "test" in captured.out
    
    def test_decision_with_missing_fields(self, capsys):
        """Test handling of decisions with missing optional fields."""
        incomplete_decision = {
            "winner": {"id": "test-thought", "final_weight": 1.5}
        }
        
        # Should not crash even with missing fields
        explain_decision(incomplete_decision)
        captured = capsys.readouterr()
        
        assert "Decision Trace Analysis" in captured.out
        assert "test-thought" in captured.out
    
    def test_graceful_handling_missing_decisions_json(self):
        """Test graceful fallback when decisions.json is missing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create history.json but no decisions.json
            history_file = Path(temp_dir) / "history.json"
            history_data = [{
                "timestamp": "2024-02-10T12:00:00",
                "thought_id": "fallback-test",
                "prompt": "Fallback test prompt",
                "mood": "day",
                "today_mood": "testing"
            }]
            history_file.write_text(json.dumps(history_data))
            
            with patch('decision_trace.get_data_dir', return_value=Path(temp_dir)):
                with patch('decision_trace.get_file_path', return_value=history_file):
                    decisions = load_decisions_log()
                    assert decisions == []  # decisions.json doesn't exist
                    
                    # Should fallback to history
                    fallback = find_decision_from_history(history_data, "fallback-test")
                    assert fallback is not None
                    assert fallback["winner"]["id"] == "fallback-test"
    
    def test_most_recent_action_when_no_id_specified(self, sample_decisions):
        """Test that most recent action is returned when no action-id specified."""
        recent = find_recent_decision(sample_decisions)
        assert recent is not None
        # Should be the latest timestamp (2024-02-11)
        assert recent["winner"]["id"] == "creative-chaos"
        assert recent["timestamp"] == "2024-02-11T09:15:00"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])