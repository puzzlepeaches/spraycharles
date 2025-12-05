import json
import tempfile
from pathlib import Path
import pytest


@pytest.fixture
def temp_output_file():
    """Create a temporary output file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = Path(f.name)
    yield temp_path
    if temp_path.exists():
        temp_path.unlink()


@pytest.fixture
def temp_user_file():
    """Create a temporary user file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        temp_path = Path(f.name)
        f.write("user1\nuser2\nuser3\n")
    yield temp_path
    if temp_path.exists():
        temp_path.unlink()


@pytest.fixture
def temp_password_file():
    """Create a temporary password file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        temp_path = Path(f.name)
        f.write("Password1\nPassword2\n")
    yield temp_path
    if temp_path.exists():
        temp_path.unlink()


@pytest.fixture
def sample_spray_results():
    """Sample spray results in JSON format."""
    return [
        {
            "Timestamp": "2024-01-01 12:00:00",
            "Username": "user1",
            "Password": "Password1",
            "Response Code": "200",
            "Response Length": "1234",
            "Module": "OWA",
            "Host": "test.example.com"
        },
        {
            "Timestamp": "2024-01-01 12:00:05",
            "Username": "user2",
            "Password": "Password1",
            "Response Code": "200",
            "Response Length": "1234",
            "Module": "OWA",
            "Host": "test.example.com"
        },
        {
            "Timestamp": "2024-01-01 12:00:10",
            "Username": "user3",
            "Password": "Password1",
            "Response Code": "200",
            "Response Length": "5678",
            "Module": "OWA",
            "Host": "test.example.com"
        }
    ]


@pytest.fixture
def sample_o365_results():
    """Sample O365 spray results."""
    return [
        {
            "Timestamp": "2024-01-01 12:00:00",
            "Username": "user1@example.com",
            "Password": "Password1",
            "Result": "Failed",
            "Message": "Invalid credentials",
            "Module": "Office365",
            "Host": "login.microsoftonline.com"
        },
        {
            "Timestamp": "2024-01-01 12:00:05",
            "Username": "user2@example.com",
            "Password": "Password2",
            "Result": "Success",
            "Message": "Valid credentials",
            "Module": "Office365",
            "Host": "login.microsoftonline.com"
        }
    ]


@pytest.fixture
def sample_smb_results():
    """Sample SMB spray results."""
    return [
        {
            "Timestamp": "2024-01-01 12:00:00",
            "Username": "DOMAIN\\user1",
            "Password": "Password1",
            "SMB Login": "STATUS_LOGON_FAILURE",
            "Module": "SMB",
            "Host": "192.168.1.1"
        },
        {
            "Timestamp": "2024-01-01 12:00:05",
            "Username": "DOMAIN\\user2",
            "Password": "Password2",
            "SMB Login": "STATUS_SUCCESS",
            "Module": "SMB",
            "Host": "192.168.1.1"
        }
    ]
