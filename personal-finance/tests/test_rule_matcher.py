"""
Unit tests for rule_matcher.py

Tests the pattern matching logic for categorization rules.
These are fast unit tests that don't require database or external dependencies.
"""

import pytest
from src.core.rule_matcher import RuleMatcher, Rule


@pytest.mark.unit
class TestRuleMatcher:
    """Test suite for RuleMatcher class."""

    def test_exact_match(self):
        """Test exact string matching."""
        rules = [
            Rule(pattern="TESCO", category_id="groceries", priority=10)
        ]
        matcher = RuleMatcher(rules)

        result = matcher.match("TESCO STORES 1234")
        assert result is not None
        assert result.category_id == "groceries"
        assert result.confidence == 1.0

    def test_regex_match(self):
        """Test regex pattern matching."""
        rules = [
            Rule(pattern=r"TESCO|SAINSBURY|ASDA", category_id="groceries", priority=10)
        ]
        matcher = RuleMatcher(rules)

        # Test multiple variations
        assert matcher.match("TESCO STORES").category_id == "groceries"
        assert matcher.match("SAINSBURY LOCAL").category_id == "groceries"
        assert matcher.match("ASDA SUPERSTORE").category_id == "groceries"

    def test_no_match(self):
        """Test when no rules match."""
        rules = [
            Rule(pattern="TESCO", category_id="groceries", priority=10)
        ]
        matcher = RuleMatcher(rules)

        result = matcher.match("AMAZON PRIME")
        assert result is None

    def test_priority_ordering(self):
        """Test that higher priority rules are checked first."""
        rules = [
            Rule(pattern=r".*", category_id="catch_all", priority=1),  # Low priority
            Rule(pattern=r"TESCO", category_id="groceries", priority=10),  # High priority
        ]
        matcher = RuleMatcher(rules)

        # Should match specific rule, not catch-all
        result = matcher.match("TESCO STORES")
        assert result.category_id == "groceries"

    def test_case_insensitive_match(self):
        """Test case-insensitive matching."""
        rules = [
            Rule(pattern=r"(?i)tesco", category_id="groceries", priority=10)
        ]
        matcher = RuleMatcher(rules)

        assert matcher.match("TESCO STORES").category_id == "groceries"
        assert matcher.match("Tesco Stores").category_id == "groceries"
        assert matcher.match("tesco stores").category_id == "groceries"

    def test_multiple_rules_first_match_wins(self):
        """Test that first matching rule (by priority) wins."""
        rules = [
            Rule(pattern=r"AMAZON", category_id="shopping", priority=10),
            Rule(pattern=r"AMAZON PRIME", category_id="subscriptions", priority=5),
        ]
        matcher = RuleMatcher(rules)

        # "AMAZON" rule has higher priority, so it matches first
        result = matcher.match("AMAZON PRIME VIDEO")
        assert result.category_id == "shopping"

    def test_empty_rules(self):
        """Test with no rules."""
        matcher = RuleMatcher([])
        result = matcher.match("TESCO STORES")
        assert result is None

    @pytest.mark.parametrize("description,expected_category", [
        ("TESCO STORES 1234", "groceries"),
        ("SAINSBURY LOCAL", "groceries"),
        ("MCDONALD'S", "dining_out"),
        ("KFC RESTAURANT", "dining_out"),
        ("UBER TRIP", "transportation"),
        ("SALARY PAYMENT", "salary"),
    ])
    def test_common_patterns(self, description, expected_category):
        """Test common transaction patterns (parameterized test)."""
        rules = [
            Rule(pattern=r"TESCO|SAINSBURY|ASDA", category_id="groceries", priority=10),
            Rule(pattern=r"MCDONALD|KFC|PIZZA", category_id="dining_out", priority=10),
            Rule(pattern=r"UBER|TAXI|BUS", category_id="transportation", priority=10),
            Rule(pattern=r"SALARY|WAGES", category_id="salary", priority=20),
        ]
        matcher = RuleMatcher(rules)

        result = matcher.match(description)
        assert result is not None
        assert result.category_id == expected_category
