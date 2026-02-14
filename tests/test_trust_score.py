#!/usr/bin/env python3
"""
Test suite for trust score calculation in TrustSystem

Tests trust score updates, bounds checking, and statistics generation.
"""

import json
import os
import tempfile
import pytest
import time
from unittest.mock import patch, mock_open

# Add parent directory to path for imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from trust_system import TrustSystem


class TestTrustScore:
    """Test trust score calculation and management."""
    
    def setup_method(self):
        """Set up test environment with temporary directory."""
        self.test_dir = tempfile.mkdtemp()
        self.trust_system = TrustSystem(data_dir=self.test_dir)
    
    def teardown_method(self):
        """Clean up test directory."""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_initial_trust_score_at_configured_default(self):
        """Test that initial trust scores are set to configured defaults."""
        # Check global trust level
        global_trust = self.trust_system.get_trust_level()
        assert global_trust == 0.5, f"Expected global trust 0.5, got {global_trust}"
        
        # Check category trust levels match initialization
        expected_categories = {
            "file_operations": 0.8,
            "messaging": 0.6,
            "external_api": 0.3,
            "system_changes": 0.4,
            "web_operations": 0.7,
            "code_execution": 0.5
        }
        
        for category, expected_trust in expected_categories.items():
            actual_trust = self.trust_system.get_trust_level(category)
            assert actual_trust == expected_trust, \
                f"Expected {category} trust {expected_trust}, got {actual_trust}"
    
    def test_successful_actions_increase_trust(self):
        """Test that successful actions increase trust scores."""
        category = "file_operations"
        initial_trust = self.trust_system.get_trust_level(category)
        initial_global = self.trust_system.get_trust_level()
        
        # Log a successful action
        self.trust_system.log_action(category, "Created test file", "success")
        
        # Check that trust increased
        new_trust = self.trust_system.get_trust_level(category)
        new_global = self.trust_system.get_trust_level()
        
        assert new_trust > initial_trust, \
            f"Category trust should increase: {initial_trust} -> {new_trust}"
        assert new_global > initial_global, \
            f"Global trust should increase: {initial_global} -> {new_global}"
        
        # Check the specific formula: increase = 0.02 * (1 - current_trust)
        expected_increase = 0.02 * (1 - initial_trust)
        expected_new_trust = min(1.0, initial_trust + expected_increase)
        
        assert abs(new_trust - expected_new_trust) < 0.0001, \
            f"Expected trust {expected_new_trust}, got {new_trust}"
    
    def test_failed_actions_decrease_trust(self):
        """Test that failed actions decrease trust scores."""
        category = "external_api"
        initial_trust = self.trust_system.get_trust_level(category)
        initial_global = self.trust_system.get_trust_level()
        
        # Log a failed action
        self.trust_system.log_action(category, "API call timeout", "failure")
        
        # Check that trust decreased
        new_trust = self.trust_system.get_trust_level(category)
        new_global = self.trust_system.get_trust_level()
        
        assert new_trust < initial_trust, \
            f"Category trust should decrease: {initial_trust} -> {new_trust}"
        assert new_global < initial_global, \
            f"Global trust should decrease: {initial_global} -> {new_global}"
        
        # Check the specific formula: decrease = 0.1 * current_trust
        expected_decrease = 0.1 * initial_trust
        expected_new_trust = max(0.0, initial_trust - expected_decrease)
        
        assert abs(new_trust - expected_new_trust) < 0.0001, \
            f"Expected trust {expected_new_trust}, got {new_trust}"
    
    def test_trust_never_goes_below_zero_or_above_one(self):
        """Test trust score boundaries (0.0 to 1.0)."""
        category = "system_changes"
        
        # Test upper bound - many successes
        for i in range(100):  # Many successes to try to exceed 1.0
            self.trust_system.log_action(category, f"Success {i}", "success")
        
        trust = self.trust_system.get_trust_level(category)
        assert trust <= 1.0, f"Trust should not exceed 1.0, got {trust}"
        assert trust >= 0.0, f"Trust should not be negative, got {trust}"
        
        # Reset to test lower bound
        self.trust_system.data["action_categories"][category]["trust"] = 0.1
        self.trust_system.save_data()
        
        # Test lower bound - many failures
        for i in range(50):  # Many failures to try to go below 0.0
            self.trust_system.log_action(category, f"Failure {i}", "failure")
        
        trust = self.trust_system.get_trust_level(category)
        assert trust >= 0.0, f"Trust should not go below 0.0, got {trust}"
        assert trust <= 1.0, f"Trust should not exceed 1.0, got {trust}"
    
    def test_multiple_positive_events_compound_correctly(self):
        """Test that multiple positive events compound according to formula."""
        category = "web_operations"
        initial_trust = self.trust_system.get_trust_level(category)
        
        # Log multiple successes
        trust_history = [initial_trust]
        
        for i in range(5):
            self.trust_system.log_action(category, f"Web success {i}", "success")
            current_trust = self.trust_system.get_trust_level(category)
            trust_history.append(current_trust)
        
        # Each success should increase trust, but with diminishing returns
        # Formula: new_trust = min(1.0, old_trust + 0.02 * (1 - old_trust))
        for i in range(1, len(trust_history)):
            previous = trust_history[i-1]
            current = trust_history[i]
            expected_increase = 0.02 * (1 - previous)
            expected = min(1.0, previous + expected_increase)
            
            assert abs(current - expected) < 0.0001, \
                f"Success {i}: expected {expected}, got {current}"
    
    def test_multiple_negative_events_compound_correctly(self):
        """Test that multiple negative events compound according to formula."""
        category = "messaging"
        
        # Start with high trust to see the decay pattern
        self.trust_system.data["action_categories"][category]["trust"] = 0.9
        self.trust_system.save_data()
        
        initial_trust = self.trust_system.get_trust_level(category)
        trust_history = [initial_trust]
        
        # Log multiple failures
        for i in range(5):
            self.trust_system.log_action(category, f"Message failure {i}", "failure")
            current_trust = self.trust_system.get_trust_level(category)
            trust_history.append(current_trust)
        
        # Each failure should decrease trust proportionally
        # Formula: new_trust = max(0.0, old_trust - 0.1 * old_trust)
        for i in range(1, len(trust_history)):
            previous = trust_history[i-1]
            current = trust_history[i]
            expected_decrease = 0.1 * previous
            expected = max(0.0, previous - expected_decrease)
            
            assert abs(current - expected) < 0.0001, \
                f"Failure {i}: expected {expected}, got {current}"
    
    def test_mixed_events_produce_expected_net_score(self):
        """Test that alternating success/failure events produce expected results."""
        category = "code_execution"
        initial_trust = self.trust_system.get_trust_level(category)
        
        # Alternate success and failure
        actions = [
            ("success", "Code ran successfully"),
            ("failure", "Syntax error"),
            ("success", "Fixed and ran"),
            ("failure", "Runtime error"),
            ("success", "Final fix worked")
        ]
        
        expected_trust = initial_trust
        
        for outcome, description in actions:
            self.trust_system.log_action(category, description, outcome)
            
            # Calculate expected trust manually
            if outcome == "success":
                increase = 0.02 * (1 - expected_trust)
                expected_trust = min(1.0, expected_trust + increase)
            else:  # failure
                decrease = 0.1 * expected_trust
                expected_trust = max(0.0, expected_trust - decrease)
        
        actual_trust = self.trust_system.get_trust_level(category)
        
        assert abs(actual_trust - expected_trust) < 0.0001, \
            f"Mixed events: expected {expected_trust}, got {actual_trust}"
    
    def test_trust_factors_contribute_to_composite_score(self):
        """Test that category stats are tracked correctly."""
        category = "file_operations"
        
        # Log various outcomes
        self.trust_system.log_action(category, "Create file", "success")
        self.trust_system.log_action(category, "Delete file", "success") 
        self.trust_system.log_action(category, "Permission denied", "failure")
        
        # Check that counters are updated
        stats = self.trust_system.data["action_categories"][category]
        
        assert stats["successes"] == 2, f"Expected 2 successes, got {stats['successes']}"
        assert stats["failures"] == 1, f"Expected 1 failure, got {stats['failures']}"
        
        # Trust should reflect the 2:1 success ratio but with the specific formula
        expected_trust = 0.8  # Initial
        
        # First success: 0.8 + 0.02 * (1 - 0.8) = 0.8 + 0.004 = 0.804
        expected_trust = min(1.0, expected_trust + 0.02 * (1 - expected_trust))
        
        # Second success: 0.804 + 0.02 * (1 - 0.804) = 0.804 + 0.00392 = 0.80792
        expected_trust = min(1.0, expected_trust + 0.02 * (1 - expected_trust))
        
        # One failure: 0.80792 - 0.1 * 0.80792 = 0.80792 * 0.9 = 0.727128
        expected_trust = max(0.0, expected_trust - 0.1 * expected_trust)
        
        actual_trust = self.trust_system.get_trust_level(category)
        
        assert abs(actual_trust - expected_trust) < 0.0001, \
            f"Expected trust {expected_trust}, got {actual_trust}"
    
    def test_get_stats_returns_correct_structure(self):
        """Test that get_stats() returns the expected data structure."""
        # Add some test data
        self.trust_system.log_action("file_operations", "Test action", "success")
        self.trust_system.log_action("messaging", "Send message", "failure")
        
        stats = self.trust_system.get_stats()
        
        # Check required top-level keys
        required_keys = [
            "global_trust", "category_trust", "category_stats", 
            "total_actions", "success_rate", "recent_actions",
            "total_escalations", "current_mood", "mood_risk_modifier"
        ]
        
        for key in required_keys:
            assert key in stats, f"Missing key in stats: {key}"
        
        # Check data types and ranges
        assert isinstance(stats["global_trust"], float), "global_trust should be float"
        assert 0.0 <= stats["global_trust"] <= 1.0, "global_trust should be in [0,1]"
        
        assert isinstance(stats["category_trust"], dict), "category_trust should be dict"
        assert isinstance(stats["category_stats"], dict), "category_stats should be dict"
        
        assert isinstance(stats["total_actions"], int), "total_actions should be int"
        assert stats["total_actions"] >= 0, "total_actions should be non-negative"
        
        assert isinstance(stats["success_rate"], float), "success_rate should be float"
        assert 0.0 <= stats["success_rate"] <= 1.0, "success_rate should be in [0,1]"
        
        # Check that category stats have required sub-keys
        for category, cat_stats in stats["category_stats"].items():
            required_cat_keys = ["trust", "successes", "failures", "escalations"]
            for key in required_cat_keys:
                assert key in cat_stats, f"Missing key in {category} stats: {key}"
    
    def test_escalation_affects_trust_correctly(self):
        """Test that escalations affect trust based on human response."""
        category = "system_changes"
        initial_trust = self.trust_system.get_trust_level(category)
        
        # Test positive escalation response ("yes")
        self.trust_system.log_escalation(category, "Install package", "yes, go ahead")
        
        trust_after_yes = self.trust_system.get_trust_level(category)
        assert trust_after_yes > initial_trust, \
            f"Trust should increase after positive escalation: {initial_trust} -> {trust_after_yes}"
        
        # Test negative escalation response ("no")
        current_trust = trust_after_yes
        self.trust_system.log_escalation(category, "Delete system file", "no, don't do that")
        
        trust_after_no = self.trust_system.get_trust_level(category)
        assert trust_after_no < current_trust, \
            f"Trust should decrease after negative escalation: {current_trust} -> {trust_after_no}"
        
        # Check escalation counter
        stats = self.trust_system.data["action_categories"][category]
        assert stats["escalations"] == 2, f"Expected 2 escalations, got {stats['escalations']}"
    
    def test_trust_adjustment_manual(self):
        """Test manual trust adjustment functionality."""
        category = "external_api"
        initial_trust = self.trust_system.get_trust_level(category)
        initial_global = self.trust_system.get_trust_level()
        
        # Manually increase trust
        self.trust_system.adjust_trust(category, 0.1, "Manual increase for testing")
        
        new_trust = self.trust_system.get_trust_level(category)
        expected = min(1.0, initial_trust + 0.1)
        
        assert abs(new_trust - expected) < 0.0001, \
            f"Manual adjustment: expected {expected}, got {new_trust}"
        
        # Test global trust adjustment
        self.trust_system.adjust_trust("global", -0.05, "Manual decrease")
        
        new_global = self.trust_system.get_trust_level()
        expected_global = max(0.0, initial_global - 0.05)
        
        assert abs(new_global - expected_global) < 0.0001, \
            f"Global adjustment: expected {expected_global}, got {new_global}"
    
    def test_time_decay_toward_neutral(self):
        """Test that trust decays toward 0.5 over time."""
        category = "web_operations" 
        
        # Set high trust
        self.trust_system.data["action_categories"][category]["trust"] = 0.9
        self.trust_system.data["trust_level"] = 0.8
        
        # Mock time passage (25+ hours to trigger decay)
        with patch('time.time') as mock_time:
            # Initial time
            mock_time.return_value = 1000000
            self.trust_system.data["last_decay"] = 1000000
            
            # 25 hours later
            mock_time.return_value = 1000000 + (25 * 3600)
            
            # Apply decay
            self.trust_system.apply_time_decay()
            
            # Check that high values moved toward 0.5
            category_trust = self.trust_system.get_trust_level(category)
            global_trust = self.trust_system.get_trust_level()
            
            assert category_trust < 0.9, f"High trust should decay: {category_trust}"
            assert category_trust > 0.5, f"Should not decay below 0.5: {category_trust}"
            
            assert global_trust < 0.8, f"High global trust should decay: {global_trust}"
            assert global_trust > 0.5, f"Should not decay below 0.5: {global_trust}"
        
        # Test low trust decaying up toward 0.5
        self.trust_system.data["action_categories"][category]["trust"] = 0.1
        self.trust_system.data["trust_level"] = 0.2
        
        with patch('time.time') as mock_time:
            mock_time.return_value = 2000000
            self.trust_system.data["last_decay"] = 2000000
            
            # 25 hours later
            mock_time.return_value = 2000000 + (25 * 3600)
            
            self.trust_system.apply_time_decay()
            
            category_trust = self.trust_system.get_trust_level(category)
            global_trust = self.trust_system.get_trust_level()
            
            assert category_trust > 0.1, f"Low trust should increase: {category_trust}"
            assert category_trust < 0.5, f"Should not exceed 0.5: {category_trust}"
            
            assert global_trust > 0.2, f"Low global trust should increase: {global_trust}"
            assert global_trust < 0.5, f"Should not exceed 0.5: {global_trust}"
    
    def test_unknown_category_returns_default(self):
        """Test that unknown categories return default trust level."""
        unknown_trust = self.trust_system.get_trust_level("unknown_category")
        assert unknown_trust == 0.5, f"Unknown category should return 0.5, got {unknown_trust}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])