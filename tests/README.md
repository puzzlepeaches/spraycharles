# Spraycharles Test Suite

This directory contains comprehensive unit and integration tests for the spraycharles project, with a focus on the dynamic spray queue feature.

## Test Structure

```
tests/
├── conftest.py                    # Shared fixtures and test configuration
├── unit/                          # Unit tests (isolated component tests)
│   ├── test_notify.py            # Tests for notification system
│   ├── test_spraycharles.py      # Tests for main spray logic
│   └── test_analyze.py           # Tests for result analysis
└── integration/                   # Integration tests (component interaction)
    └── test_resume_flow.py       # Tests for resume/tracking functionality
```

## Running Tests

### Prerequisites

Install development dependencies:
```bash
poetry install
```

### Run All Tests
```bash
poetry run pytest
```

### Run Unit Tests Only
```bash
poetry run pytest tests/unit -m unit
```

### Run Integration Tests Only
```bash
poetry run pytest tests/integration -m integration
```

### Run with Coverage
```bash
poetry run pytest --cov=spraycharles --cov-report=term --cov-report=html
```

### Run Specific Test File
```bash
poetry run pytest tests/unit/test_notify.py -v
```

### Run Specific Test
```bash
poetry run pytest tests/unit/test_notify.py::TestNotifyType::test_notify_type_values -v
```

## Test Coverage

### Unit Tests

#### `test_notify.py`
Tests for the notification system (`spraycharles/lib/utils/notify.py`):
- NotifyType enum values
- HookSvc enum values
- Slack notification function
- Teams notification function
- Discord notification function
- send_notification dispatcher with all notification types
- Default message handling
- Custom message handling
- Error handling

#### `test_spraycharles.py`
Tests for the main spray logic (`spraycharles/lib/spraycharles.py`):
- `_load_completed_attempts()` - Loading from JSON output
  - Empty files
  - Valid JSON entries
  - Domain-prefixed usernames
  - Blank lines handling
  - Missing fields
  - Malformed JSON handling
- `_build_work_queue()` - Queue construction
  - No completed attempts
  - With domain prefix
  - Excluding completed attempts
  - All completed scenario
  - Order preservation
- `_update_list_from_file()` - File change detection
  - Unchanged files
  - Changed files
  - None file handling
  - List clearing before reload
- `_handle_timeout_escalation()` - Timeout backoff
  - 5 minute pause (stage 0 -> 1)
  - 10 minute pause (stage 1 -> 2)
  - Stop and confirm (stage 2 -> 0)
  - State machine progression
- `_spray_equal_with_tracking()` - Password=username spray
  - No completed attempts
  - With domain prefix
  - Skipping completed
  - All completed scenario
  - Jitter application
- `_hash_file()` - File hashing
  - Consistent hashing
  - Change detection
  - Nonexistent file handling
- `_send_webhook()` - Webhook helper
  - Success cases
  - Custom messages
  - Not configured scenario
  - Exception handling

#### `test_analyze.py`
Tests for result analysis (`spraycharles/lib/analyze.py`):
- Analyzer initialization
- `_send_notification()` - Conditional notifications
  - New hits detected
  - No new hits
  - Fewer hits
  - Not configured
  - Exception handling
- `O365_analyze()` - Office 365 analysis
  - Successful logins
  - No successes
  - Multiple successes
- `smb_analyze()` - SMB analysis
  - Successful logins (STATUS_SUCCESS)
  - Account disabled (valid creds)
  - Password expired (valid creds)
  - Password must change (valid creds)
  - No successes
- `http_analyze()` - HTTP analysis
  - Response length outliers
  - No outliers
  - Timeout filtering
  - Multiple outliers
- `analyze()` - Module routing
  - O365 routing
  - SMB routing
  - HTTP routing

### Integration Tests

#### `test_resume_flow.py`
Tests for the complete resume/tracking workflow:
- Resume loads and skips completed attempts
- Resume with domain prefixes
- Equal spray respects completed attempts
- Resume after partial completion
- Empty output file starts fresh
- Malformed JSON doesn't break resume
- User file update detection
- Password file update detection
- No update when file unchanged
- File updates rebuild work queue
- Full timeout escalation cycle
- Timeout counter resets on success
- Escalation notifications sent correctly
- Complete end-to-end resume workflow

## Test Fixtures

Shared fixtures are defined in `conftest.py`:

- `temp_output_file` - Temporary JSON output file
- `temp_user_file` - Temporary user list file
- `temp_password_file` - Temporary password list file
- `sample_spray_results` - Sample HTTP spray results
- `sample_o365_results` - Sample Office 365 results
- `sample_smb_results` - Sample SMB results

## Continuous Integration

Tests run automatically on every push and pull request via GitHub Actions. The CI workflow:
1. Tests on Python 3.10 and 3.12
2. Runs unit tests
3. Runs integration tests
4. Generates coverage report
5. Runs smoke tests

See `.github/workflows/ci.yml` for details.

## Writing New Tests

### Unit Test Template
```python
import pytest
from unittest.mock import Mock, patch

@pytest.mark.unit
class TestMyFeature:
    def test_my_function(self):
        # Arrange
        # Act
        # Assert
        pass
```

### Integration Test Template
```python
import pytest

@pytest.mark.integration
class TestMyIntegration:
    def test_end_to_end_flow(self, temp_output_file):
        # Arrange
        # Act
        # Assert
        pass
```

## Best Practices

1. Use descriptive test names that explain what is being tested
2. Follow Arrange-Act-Assert pattern
3. Mock external dependencies (network, filesystem where appropriate)
4. Use fixtures for common test data
5. Mark tests with appropriate markers (`@pytest.mark.unit`, `@pytest.mark.integration`)
6. Test edge cases and error conditions
7. Keep tests independent and isolated
