"""
Template for writing new tests.

Copy this file and rename it to test_<your_feature>.py
Replace the examples with your actual test cases.

TDD Workflow:
1. Write test (it will fail)
2. Write minimal code to pass test
3. Refactor
4. Repeat
"""

import pytest


# ============================================================================
# UNIT TESTS - Fast, isolated tests with no database or external dependencies
# ============================================================================

@pytest.mark.unit
class TestMyFeature:
    """Test suite for my new feature."""

    def test_basic_functionality(self):
        """Test the basic behavior."""
        # Arrange - Set up test data
        input_data = "test input"

        # Act - Call the function
        result = my_function(input_data)

        # Assert - Check the result
        assert result == "expected output"

    def test_edge_case_empty_input(self):
        """Test with empty input."""
        result = my_function("")
        assert result is None  # or whatever expected behavior

    def test_edge_case_none_input(self):
        """Test with None input."""
        with pytest.raises(ValueError):
            my_function(None)

    @pytest.mark.parametrize("input,expected", [
        ("input1", "output1"),
        ("input2", "output2"),
        ("input3", "output3"),
    ])
    def test_multiple_inputs(self, input, expected):
        """Test multiple input cases."""
        result = my_function(input)
        assert result == expected


# ============================================================================
# INTEGRATION TESTS - Tests that use database or multiple components
# ============================================================================

@pytest.mark.integration
class TestMyFeatureIntegration:
    """Integration tests for my feature."""

    def test_with_database(self, clean_db, sample_categories):
        """Test with real database."""
        # clean_db is a fresh test database
        # sample_categories are pre-loaded

        # Your test logic here
        result = query_database(clean_db)
        assert len(result) > 0

    def test_with_mock_api(self, mocker):
        """Test with mocked external API."""
        # Mock external dependency
        mock_api = mocker.Mock()
        mock_api.get_data.return_value = {"status": "success"}

        # Test with mock
        result = my_function_that_uses_api(mock_api)
        assert result["status"] == "success"


# ============================================================================
# SLOW TESTS - Tests that take >1 second (mark as slow)
# ============================================================================

@pytest.mark.slow
class TestMyFeatureSlow:
    """Slow tests that can be skipped during development."""

    def test_large_dataset(self):
        """Test with large dataset (slow)."""
        large_data = generate_large_dataset()
        result = process_data(large_data)
        assert len(result) == len(large_data)


# ============================================================================
# HELPER FUNCTIONS - Reusable test utilities
# ============================================================================

def my_function(input_data):
    """
    Placeholder function - replace with your actual implementation.

    In TDD:
    1. This function doesn't exist yet when you write the test
    2. You create it to make the test pass
    3. You refactor it while keeping tests green
    """
    # TODO: Implement actual logic
    return "expected output"


def generate_large_dataset():
    """Helper to generate test data."""
    return [i for i in range(10000)]


# ============================================================================
# EXAMPLE: Real-world test for transaction categorization
# ============================================================================

@pytest.mark.unit
class TestTransactionCategorization:
    """Example: Testing transaction categorization."""

    @pytest.mark.parametrize("description,expected_category", [
        ("TESCO STORES 1234", "groceries"),
        ("SAINSBURY LOCAL", "groceries"),
        ("MCDONALD'S RESTAURANT", "dining_out"),
        ("SALARY PAYMENT", "salary"),
        ("UNKNOWN MERCHANT", "uncategorized"),
    ])
    def test_categorize_by_description(self, description, expected_category):
        """Test that transactions are categorized correctly."""
        # This test would fail initially because categorize() doesn't exist
        # Then you implement categorize() to make it pass
        result = categorize(description)
        assert result == expected_category


def categorize(description: str) -> str:
    """
    Example implementation that makes the test pass.

    In TDD, you'd start with a failing test, then implement this.
    """
    if any(store in description.upper() for store in ["TESCO", "SAINSBURY"]):
        return "groceries"
    elif any(rest in description.upper() for rest in ["MCDONALD", "KFC"]):
        return "dining_out"
    elif "SALARY" in description.upper():
        return "salary"
    else:
        return "uncategorized"


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

"""
Run these tests:

    # Run all tests in this file
    pytest tests/test_template.py -v

    # Run only unit tests
    pytest tests/test_template.py -m unit -v

    # Run only integration tests
    pytest tests/test_template.py -m integration -v

    # Run specific test class
    pytest tests/test_template.py::TestMyFeature -v

    # Run specific test function
    pytest tests/test_template.py::TestMyFeature::test_basic_functionality -v

    # Skip slow tests
    pytest tests/test_template.py -m "not slow" -v
"""
