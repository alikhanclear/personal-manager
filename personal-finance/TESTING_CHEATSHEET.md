# pytest Cheat Sheet

## Installation
```bash
pip install pytest pytest-cov pytest-mock pytest-asyncio
```

## Running Tests

| Command | What it does |
|---------|--------------|
| `pytest` | Run all tests |
| `pytest -v` | Verbose output |
| `pytest -vv` | Extra verbose |
| `pytest -s` | Show print statements |
| `pytest -x` | Stop at first failure |
| `pytest --lf` | Run last failed tests |
| `pytest --ff` | Failed first, then rest |
| `pytest tests/test_file.py` | Run specific file |
| `pytest tests/test_file.py::test_func` | Run specific test |
| `pytest -k "pattern"` | Run tests matching pattern |

## Markers

| Command | What it does |
|---------|--------------|
| `pytest -m unit` | Run only unit tests |
| `pytest -m integration` | Run only integration tests |
| `pytest -m "not slow"` | Skip slow tests |
| `pytest -m "unit and not slow"` | Combine markers |

## Coverage

| Command | What it does |
|---------|--------------|
| `pytest --cov=src` | Basic coverage |
| `pytest --cov=src --cov-report=term-missing` | Show missing lines |
| `pytest --cov=src --cov-report=html` | HTML report (htmlcov/index.html) |
| `pytest --cov-fail-under=80` | Fail if coverage < 80% |

## Quick Scripts

| Command | What it does |
|---------|--------------|
| `python run_tests.py` | Run all tests with coverage |
| `python run_tests.py unit` | Run only unit tests |
| `python run_tests.py integration` | Run only integration tests |
| `python run_tests.py coverage` | Generate HTML coverage report |
| `python run_tests.py fast` | Skip slow tests |

## Writing Tests

### Basic Test
```python
def test_something():
    result = my_function("input")
    assert result == "expected"
```

### Test with Fixture
```python
def test_with_database(clean_db):
    # clean_db is a fresh test database
    result = query(clean_db)
    assert len(result) > 0
```

### Parametrized Test
```python
@pytest.mark.parametrize("input,expected", [
    ("a", 1),
    ("b", 2),
])
def test_multiple(input, expected):
    assert my_func(input) == expected
```

### Test Exception
```python
def test_raises_error():
    with pytest.raises(ValueError):
        my_function(invalid_input)
```

### Test with Mock
```python
def test_with_mock(mocker):
    mock_api = mocker.Mock()
    mock_api.get.return_value = "data"
    result = my_function(mock_api)
    assert result == "data"
```

## Test Markers

```python
@pytest.mark.unit          # Fast unit test
@pytest.mark.integration   # Integration test
@pytest.mark.slow          # Slow test (>1 sec)
@pytest.mark.skip          # Skip this test
@pytest.mark.skipif(condition)  # Skip if condition
@pytest.mark.xfail         # Expected to fail
```

## Available Fixtures (conftest.py)

| Fixture | What it provides |
|---------|-----------------|
| `clean_db` | Fresh test database |
| `sample_categories` | Pre-loaded categories |
| `sample_transactions` | Pre-loaded transactions |
| `sample_rules` | Pre-loaded categorization rules |
| `mock_anthropic_client` | Mocked AI client (no API calls) |
| `sample_csv_content` | Sample NatWest CSV data |

## TDD Workflow

1. **RED** - Write failing test
   ```bash
   pytest tests/test_new_feature.py -v
   # ❌ FAILED - function doesn't exist
   ```

2. **GREEN** - Write minimal code to pass
   ```python
   def my_function(x):
       return x  # Simplest implementation
   ```
   ```bash
   pytest tests/test_new_feature.py -v
   # ✅ PASSED
   ```

3. **REFACTOR** - Improve code while keeping tests green
   ```python
   def my_function(x):
       # Better implementation
       return process(x)
   ```
   ```bash
   pytest tests/test_new_feature.py -v
   # ✅ PASSED
   ```

4. **REPEAT** - Add more tests, improve implementation

## Best Practices

- ✅ Write tests before code (TDD)
- ✅ One assertion per test
- ✅ Use descriptive test names
- ✅ Keep unit tests fast (<10ms)
- ✅ Mock external dependencies
- ✅ Use fixtures for setup
- ✅ Test edge cases
- ✅ Aim for 80%+ coverage
- ✅ Run tests frequently
- ❌ Don't test implementation details
- ❌ Don't repeat setup code

## Common Assertions

```python
assert x == y           # Equality
assert x != y           # Inequality
assert x is True        # Identity
assert x is None        # None check
assert x in [1, 2, 3]   # Membership
assert len(x) == 5      # Length
assert x > 0            # Comparison
assert "substring" in x # Substring
```

## Debugging Tests

```bash
# Show full traceback
pytest --tb=long

# Drop into debugger on failure
pytest --pdb

# Show local variables on failure
pytest -l

# Capture warnings
pytest -W error
```

## VS Code Integration

1. Install Python extension
2. Cmd+Shift+P → "Python: Configure Tests"
3. Select "pytest"
4. Tests appear in Testing sidebar
5. Click play button to run
6. Click debug button to debug

## Example Test File

```python
"""tests/test_example.py"""
import pytest

@pytest.mark.unit
class TestExample:
    def test_basic(self):
        """Test basic functionality."""
        result = add(2, 3)
        assert result == 5

    @pytest.mark.parametrize("a,b,expected", [
        (1, 2, 3),
        (0, 0, 0),
        (-1, 1, 0),
    ])
    def test_multiple_cases(self, a, b, expected):
        """Test multiple input combinations."""
        assert add(a, b) == expected

def add(a, b):
    return a + b
```

## Quick Reference Card

```
Run all tests:              pytest
Run with coverage:          pytest --cov=src
Run unit tests:             pytest -m unit
Run fast tests:             pytest -m "not slow"
Stop at first fail:         pytest -x
Run last failed:            pytest --lf
Verbose output:             pytest -v
Show prints:                pytest -s
HTML coverage:              pytest --cov=src --cov-report=html
Watch mode:                 ptw
```

---

**Remember**: The goal of TDD is to have confidence that your code works and to make refactoring safe!
