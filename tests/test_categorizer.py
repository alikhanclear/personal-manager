"""
Integration tests for categorizer.py

Tests the hybrid categorization system (rules + AI).
"""

import pytest
from unittest.mock import Mock, patch
from src.core.categorizer import HybridCategorizer
from src.core.rule_matcher import Rule


@pytest.mark.integration
class TestHybridCategorizer:
    """Test the hybrid categorization system."""

    def test_rule_based_categorization(self, clean_db, sample_categories, sample_rules):
        """Test that rule-based categorization works."""
        categorizer = HybridCategorizer(clean_db)

        result = categorizer.categorize("TESCO STORES 1234")

        assert result.category_id == "groceries"
        assert result.confidence == 1.0
        assert result.source == "rule"

    def test_ai_fallback_when_no_rule_matches(self, clean_db, sample_categories, mock_anthropic_client):
        """Test that AI is used when no rule matches."""
        with patch("src.ml.ai_categorizer.Anthropic", return_value=mock_anthropic_client):
            categorizer = HybridCategorizer(clean_db)

            result = categorizer.categorize("UNKNOWN MERCHANT")

            assert result.category_id == "groceries"  # From mock
            assert result.confidence == 0.95
            assert result.source == "ai"

    def test_rule_takes_precedence_over_ai(self, clean_db, sample_categories, sample_rules, mock_anthropic_client):
        """Test that rules take precedence over AI."""
        with patch("src.ml.ai_categorizer.Anthropic", return_value=mock_anthropic_client):
            categorizer = HybridCategorizer(clean_db)

            # "TESCO" matches a rule, so AI should not be called
            result = categorizer.categorize("TESCO STORES")

            assert result.source == "rule"
            assert result.confidence == 1.0

    @pytest.mark.slow
    def test_batch_categorization(self, clean_db, sample_categories, sample_rules):
        """Test categorizing multiple transactions in batch."""
        categorizer = HybridCategorizer(clean_db)

        transactions = [
            "TESCO STORES",
            "SAINSBURY LOCAL",
            "MCDONALD'S",
            "UNKNOWN MERCHANT",
        ]

        results = categorizer.categorize_batch(transactions)

        assert len(results) == 4
        assert results[0].category_id == "groceries"
        assert results[1].category_id == "groceries"
        assert results[2].category_id == "dining_out"

    def test_categorization_with_confidence_threshold(self, clean_db, sample_categories, mock_anthropic_client):
        """Test that low-confidence AI results are flagged."""
        # Mock low confidence response
        mock_anthropic_client.messages.create.return_value.content[0].text = '{"category": "groceries", "confidence": 0.4}'

        with patch("src.ml.ai_categorizer.Anthropic", return_value=mock_anthropic_client):
            categorizer = HybridCategorizer(clean_db, confidence_threshold=0.5)

            result = categorizer.categorize("AMBIGUOUS MERCHANT")

            # Should still return result, but flag it as low confidence
            assert result.confidence < 0.5
            assert result.needs_review is True


@pytest.mark.unit
class TestCategorizerEdgeCases:
    """Test edge cases in categorization logic."""

    def test_empty_description(self, clean_db, sample_categories):
        """Test categorizing empty description."""
        categorizer = HybridCategorizer(clean_db)

        result = categorizer.categorize("")

        assert result.category_id == "uncategorized"

    def test_whitespace_only_description(self, clean_db, sample_categories):
        """Test categorizing whitespace-only description."""
        categorizer = HybridCategorizer(clean_db)

        result = categorizer.categorize("   ")

        assert result.category_id == "uncategorized"

    def test_special_characters_in_description(self, clean_db, sample_categories, sample_rules):
        """Test categorizing descriptions with special characters."""
        categorizer = HybridCategorizer(clean_db)

        # Should still match rules despite special characters
        result = categorizer.categorize("TESCO #1234 @LONDON (UK)")

        assert result.category_id == "groceries"

    def test_case_sensitivity(self, clean_db, sample_categories, sample_rules):
        """Test that categorization handles different cases."""
        categorizer = HybridCategorizer(clean_db)

        # Should match regardless of case (if rules use (?i) flag)
        assert categorizer.categorize("TESCO").category_id == "groceries"
        assert categorizer.categorize("tesco").category_id == "groceries"
        assert categorizer.categorize("Tesco").category_id == "groceries"
