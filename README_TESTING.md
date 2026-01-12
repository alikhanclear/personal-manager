# Testing Guide for Personal Finance Manager

This guide shows you how to use pytest for Test-Driven Development (TDD).

## Quick Start

### 1. Install pytest
```bash
pip install -r requirements.txt
```

### 2. Run all tests
```bash
pytest
```

### 3. Run with coverage report
```bash
pytest --cov=src --cov-report=html
```

### 4. Open coverage report
```bash
# Open htmlcov/index.html in browser
start htmlcov/index.html  # Windows
open htmlcov/index.html   # Mac
```

## Test-Driven Development (TDD) Workflow

### Step 1: Write a Failing Test
```python
# tests/test_new_feature.py
def test_my_new_feature():
    """Test that doesn't work yet."""
    result = my_new_function("input")
    assert result == "expected output"
```

### Step 2: Run the test (it should fail)
```bash
pytest tests/test_new_feature.py -v
```

### Step 3: Write the minimum code to pass
```python
# src/my_module.py
def my_new_function(input):
    return "expected output"
```

### Step 4: Run the test again (it should pass)
```bash
pytest tests/test_new_feature.py -v
```

### Step 5: Refactor and repeat
Improve your code, run tests to ensure nothing breaks.

## Running Tests

### Run all tests
```bash
pytest
```

### Run specific test file
```bash
pytest tests/test_rule_matcher.py
```

### Run specific test class
```bash
pytest tests/test_rule_matcher.py::TestRuleMatcher
```

### Run specific test function
```bash
pytest tests/test_rule_matcher.py::TestRuleMatcher::test_exact_match
```

### Run tests by marker
```bash
# Run only unit tests (fast)
pytest -m unit

# Run only integration tests
pytest -m integration

# Skip slow tests
pytest -m "not slow"
```

### Run with verbose output
```bash
pytest -v
```

### Run with detailed output
```bash
pytest -vv
```

### Show print statements
```bash
pytest -s
```

### Stop at first failure
```bash
pytest -x
```

### Run last failed tests
```bash
pytest --lf
```

### Run failed tests first
```bash
pytest --ff
```

## Coverage Reports

### Terminal coverage
```bash
pytest --cov=src --cov-report=term-missing
```

### HTML coverage report
```bash
pytest --cov=src --cov-report=html
# Open htmlcov/index.html
```

### Check minimum coverage threshold
```bash
pytest --cov=src --cov-fail-under=80
```

## Test Structure

### Unit Tests (`@pytest.mark.unit`)
- Fast, isolated tests
- No database or external dependencies
- Test single functions/classes
- Example: `test_rule_matcher.py`

### Integration Tests (`@pytest.mark.integration`)
- Test multiple components together
- Use real database (test database)
- Example: `test_database.py`, `test_categorizer.py`

### Slow Tests (`@pytest.mark.slow`)
- Tests that take >1 second
- Can be skipped during development: `pytest -m "not slow"`
- Example: AI API calls, large data processing

## Fixtures

Fixtures are reusable test setups defined in `conftest.py`.

### Available Fixtures

#### `clean_db`
Fresh test database for each test.
```python
def test_something(clean_db):
    # clean_db is path to fresh database
    conn = sqlite3.connect(clean_db)
    ...
```

#### `sample_categories`
Pre-populated categories.
```python
def test_with_categories(clean_db, sample_categories):
    # Database has 5 categories already
    ...
```

#### `sample_transactions`
Pre-populated transactions.
```python
def test_with_transactions(clean_db, sample_transactions):
    # Database has 3 transactions already
    ...
```

#### `sample_rules`
Pre-populated rules.
```python
def test_with_rules(clean_db, sample_rules):
    # Database has 4 rules already
    ...
```

#### `mock_anthropic_client`
Mocked AI client (no API calls).
```python
def test_ai_categorization(mock_anthropic_client):
    # AI calls are mocked, no real API usage
    ...
```

## Parameterized Tests

Test multiple inputs with one test function:
```python
@pytest.mark.parametrize("input,expected", [
    ("TESCO", "groceries"),
    ("MCDONALD", "dining_out"),
    ("UBER", "transportation"),
])
def test_patterns(input, expected):
    result = categorize(input)
    assert result == expected
```

## Mocking

Mock external dependencies to speed up tests:
```python
from unittest.mock import Mock, patch

def test_ai_with_mock(mocker):
    # Mock API client
    mock_client = mocker.Mock()
    mock_client.categorize.return_value = "groceries"

    with patch("src.ai.get_client", return_value=mock_client):
        result = categorize_with_ai("TESCO")
        assert result == "groceries"
```

## Example TDD Session

Let's add a feature: "Detect recurring transactions"

### 1. Write test first
```python
# tests/test_recurring.py
import pytest
from src.core.recurring import detect_recurring_transactions

def test_detect_monthly_recurring(clean_db, sample_transactions):
    """Test detecting monthly recurring transactions."""
    # Add 3 months of "NETFLIX" transactions
    add_netflix_transactions(clean_db, count=3)

    recurring = detect_recurring_transactions(clean_db)

    assert len(recurring) == 1
    assert recurring[0]["description"] == "NETFLIX"
    assert recurring[0]["frequency"] == "monthly"
```

### 2. Run test (fails - function doesn't exist)
```bash
pytest tests/test_recurring.py -v
# ImportError: cannot import name 'detect_recurring_transactions'
```

### 3. Create minimal implementation
```python
# src/core/recurring.py
def detect_recurring_transactions(db_path):
    """Detect recurring transactions."""
    return []  # Placeholder
```

### 4. Run test (fails - returns empty list)
```bash
pytest tests/test_recurring.py -v
# AssertionError: assert 0 == 1
```

### 5. Implement actual logic
```python
# src/core/recurring.py
def detect_recurring_transactions(db_path):
    """Detect recurring transactions."""
    # Query database for transactions
    # Group by description
    # Check for regular intervals
    # Return recurring ones
    ...
    return recurring_list
```

### 6. Run test (passes!)
```bash
pytest tests/test_recurring.py -v
# test_detect_monthly_recurring PASSED
```

### 7. Add more test cases
```python
def test_detect_weekly_recurring(clean_db):
    """Test weekly recurring transactions."""
    ...

def test_ignore_one_time_transactions(clean_db):
    """Test that one-time transactions are not flagged."""
    ...
```

## Best Practices

1. **Write tests first** - Follow TDD: Red → Green → Refactor
2. **One assertion per test** - Keep tests focused
3. **Use descriptive test names** - `test_that_thing_does_this_when_that_happens()`
4. **Use fixtures** - Don't repeat database setup
5. **Mock external dependencies** - No real API calls in tests
6. **Test edge cases** - Empty inputs, null values, errors
7. **Keep tests fast** - Unit tests should run in milliseconds
8. **Run tests often** - After every small change
9. **Aim for high coverage** - 80%+ is good, 90%+ is great
10. **Test behavior, not implementation** - Test what it does, not how

## Troubleshooting

### Tests not found
```bash
# Make sure you're in the project root
cd personal-finance
pytest
```

### Import errors
```bash
# Install package in development mode
pip install -e .
```

### Database lock errors
```bash
# Close all connections in tests
conn.close()
```

### Slow tests
```bash
# Skip slow tests during development
pytest -m "not slow"
```

## Continuous Testing

Run tests automatically on file changes:
```bash
# Install pytest-watch
pip install pytest-watch

# Run continuous testing
ptw
```

## Integration with VS Code

1. Install Python extension
2. Set pytest as test framework
3. Tests appear in "Testing" sidebar
4. Run/debug tests with one click

## Next Steps

1. Run existing tests: `pytest -v`
2. Check coverage: `pytest --cov=src --cov-report=html`
3. Write tests for new features before implementing
4. Aim for 80%+ test coverage
5. Run tests before every commit

Happy testing! 🧪
