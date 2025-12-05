import json
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open
import pytest

from spraycharles.lib.spraycharles import Spraycharles
from spraycharles.lib.utils import NotifyType


@pytest.mark.unit
class TestLoadCompletedAttempts:
    """Test _load_completed_attempts method."""

    def test_load_empty_file(self, temp_output_file):
        """Test loading from an empty output file."""
        with patch('spraycharles.lib.spraycharles.Spraycharles.__init__', return_value=None):
            sc = Spraycharles.__new__(Spraycharles)
            sc.output = temp_output_file

            completed = sc._load_completed_attempts()

            assert completed == set()

    def test_load_with_completed_attempts(self, temp_output_file):
        """Test loading completed attempts from output file."""
        # Write some test data
        test_data = [
            {"Username": "user1", "Password": "Password1"},
            {"Username": "user2", "Password": "Password2"},
            {"Username": "user3", "Password": "Password3"}
        ]

        with open(temp_output_file, 'w') as f:
            for item in test_data:
                f.write(json.dumps(item) + '\n')

        with patch('spraycharles.lib.spraycharles.Spraycharles.__init__', return_value=None):
            sc = Spraycharles.__new__(Spraycharles)
            sc.output = temp_output_file

            completed = sc._load_completed_attempts()

            assert len(completed) == 3
            assert ("user1", "Password1") in completed
            assert ("user2", "Password2") in completed
            assert ("user3", "Password3") in completed

    def test_load_with_domain_prefixed_users(self, temp_output_file):
        """Test loading attempts with domain-prefixed usernames."""
        test_data = [
            {"Username": "DOMAIN\\user1", "Password": "Password1"},
            {"Username": "DOMAIN\\user2", "Password": "Password2"}
        ]

        with open(temp_output_file, 'w') as f:
            for item in test_data:
                f.write(json.dumps(item) + '\n')

        with patch('spraycharles.lib.spraycharles.Spraycharles.__init__', return_value=None):
            sc = Spraycharles.__new__(Spraycharles)
            sc.output = temp_output_file

            completed = sc._load_completed_attempts()

            assert len(completed) == 2
            assert ("DOMAIN\\user1", "Password1") in completed
            assert ("DOMAIN\\user2", "Password2") in completed

    def test_load_with_blank_lines(self, temp_output_file):
        """Test that blank lines are ignored."""
        test_data = [
            {"Username": "user1", "Password": "Password1"},
        ]

        with open(temp_output_file, 'w') as f:
            f.write(json.dumps(test_data[0]) + '\n')
            f.write('\n')
            f.write('\n')

        with patch('spraycharles.lib.spraycharles.Spraycharles.__init__', return_value=None):
            sc = Spraycharles.__new__(Spraycharles)
            sc.output = temp_output_file

            completed = sc._load_completed_attempts()

            assert len(completed) == 1

    def test_load_with_missing_fields(self, temp_output_file):
        """Test loading with missing username or password fields."""
        test_data = [
            {"Username": "user1", "Password": "Password1"},
            {"Username": "user2"},  # Missing password
            {"Password": "Password3"},  # Missing username
            {"Username": "", "Password": "Password4"},  # Empty username
        ]

        with open(temp_output_file, 'w') as f:
            for item in test_data:
                f.write(json.dumps(item) + '\n')

        with patch('spraycharles.lib.spraycharles.Spraycharles.__init__', return_value=None):
            sc = Spraycharles.__new__(Spraycharles)
            sc.output = temp_output_file

            completed = sc._load_completed_attempts()

            # Only the first valid entry should be loaded
            assert len(completed) == 1
            assert ("user1", "Password1") in completed

    def test_load_nonexistent_file(self):
        """Test loading when output file doesn't exist yet."""
        with patch('spraycharles.lib.spraycharles.Spraycharles.__init__', return_value=None):
            sc = Spraycharles.__new__(Spraycharles)
            sc.output = Path("/nonexistent/file.json")

            completed = sc._load_completed_attempts()

            assert completed == set()

    def test_load_with_malformed_json(self, temp_output_file):
        """Test handling of malformed JSON lines."""
        with open(temp_output_file, 'w') as f:
            f.write('{"Username": "user1", "Password": "Password1"}\n')
            f.write('malformed json line\n')
            f.write('{"Username": "user2", "Password": "Password2"}\n')

        with patch('spraycharles.lib.spraycharles.Spraycharles.__init__', return_value=None):
            sc = Spraycharles.__new__(Spraycharles)
            sc.output = temp_output_file

            # Should handle the exception and return partial results
            completed = sc._load_completed_attempts()

            # Should still load the first valid line before the error
            assert ("user1", "Password1") in completed


@pytest.mark.unit
class TestBuildWorkQueue:
    """Test _build_work_queue method."""

    def test_build_queue_no_completed(self):
        """Test building work queue with no completed attempts."""
        with patch('spraycharles.lib.spraycharles.Spraycharles.__init__', return_value=None):
            sc = Spraycharles.__new__(Spraycharles)
            sc.passwords = ["Password1", "Password2"]
            sc.usernames = ["user1", "user2"]
            sc.domain = None

            completed = set()
            work_queue = sc._build_work_queue(completed)

            # Should have 4 combinations (2 users * 2 passwords)
            assert len(work_queue) == 4
            assert ("user1", "Password1") in work_queue
            assert ("user1", "Password2") in work_queue
            assert ("user2", "Password1") in work_queue
            assert ("user2", "Password2") in work_queue

    def test_build_queue_with_domain(self):
        """Test building work queue with domain prefix."""
        with patch('spraycharles.lib.spraycharles.Spraycharles.__init__', return_value=None):
            sc = Spraycharles.__new__(Spraycharles)
            sc.passwords = ["Password1"]
            sc.usernames = ["user1", "user2"]
            sc.domain = "TESTDOMAIN"

            completed = set()
            work_queue = sc._build_work_queue(completed)

            assert len(work_queue) == 2
            assert ("TESTDOMAIN\\user1", "Password1") in work_queue
            assert ("TESTDOMAIN\\user2", "Password1") in work_queue

    def test_build_queue_excludes_completed(self):
        """Test that completed attempts are excluded from work queue."""
        with patch('spraycharles.lib.spraycharles.Spraycharles.__init__', return_value=None):
            sc = Spraycharles.__new__(Spraycharles)
            sc.passwords = ["Password1", "Password2"]
            sc.usernames = ["user1", "user2"]
            sc.domain = None

            completed = {("user1", "Password1"), ("user2", "Password2")}
            work_queue = sc._build_work_queue(completed)

            # Should only have 2 remaining combinations
            assert len(work_queue) == 2
            assert ("user1", "Password2") in work_queue
            assert ("user2", "Password1") in work_queue
            assert ("user1", "Password1") not in work_queue
            assert ("user2", "Password2") not in work_queue

    def test_build_queue_all_completed(self):
        """Test work queue when all attempts are completed."""
        with patch('spraycharles.lib.spraycharles.Spraycharles.__init__', return_value=None):
            sc = Spraycharles.__new__(Spraycharles)
            sc.passwords = ["Password1"]
            sc.usernames = ["user1"]
            sc.domain = None

            completed = {("user1", "Password1")}
            work_queue = sc._build_work_queue(completed)

            assert len(work_queue) == 0

    def test_build_queue_preserves_order(self):
        """Test that work queue is organized by password first."""
        with patch('spraycharles.lib.spraycharles.Spraycharles.__init__', return_value=None):
            sc = Spraycharles.__new__(Spraycharles)
            sc.passwords = ["Password1", "Password2"]
            sc.usernames = ["user1", "user2"]
            sc.domain = None

            completed = set()
            work_queue = sc._build_work_queue(completed)

            # First two items should be Password1
            assert work_queue[0] == ("user1", "Password1")
            assert work_queue[1] == ("user2", "Password1")
            # Next two should be Password2
            assert work_queue[2] == ("user1", "Password2")
            assert work_queue[3] == ("user2", "Password2")


@pytest.mark.unit
class TestUpdateListFromFile:
    """Test _update_list_from_file method."""

    def test_update_when_file_unchanged(self, temp_user_file):
        """Test that list is not updated when file hash is unchanged."""
        with patch('spraycharles.lib.spraycharles.Spraycharles.__init__', return_value=None):
            sc = Spraycharles.__new__(Spraycharles)

            current_list = ["user1", "user2"]
            current_hash = Spraycharles._hash_file(temp_user_file)

            new_hash = sc._update_list_from_file(
                temp_user_file, current_hash, current_list, type="usernames"
            )

            assert new_hash == current_hash
            assert current_list == ["user1", "user2"]  # Unchanged

    def test_update_when_file_changed(self, temp_user_file):
        """Test that list is updated when file hash changes."""
        with patch('spraycharles.lib.spraycharles.Spraycharles.__init__', return_value=None):
            sc = Spraycharles.__new__(Spraycharles)

            current_list = ["user1", "user2"]
            current_hash = Spraycharles._hash_file(temp_user_file)

            # Modify the file
            with open(temp_user_file, 'w') as f:
                f.write("user1\nuser2\nuser3\nuser4\n")

            new_hash = sc._update_list_from_file(
                temp_user_file, current_hash, current_list, type="usernames"
            )

            assert new_hash != current_hash
            assert len(current_list) == 4
            assert "user3" in current_list
            assert "user4" in current_list

    def test_update_with_none_file(self):
        """Test that function handles None file path."""
        with patch('spraycharles.lib.spraycharles.Spraycharles.__init__', return_value=None):
            sc = Spraycharles.__new__(Spraycharles)

            current_list = ["user1"]
            current_hash = "somehash"

            new_hash = sc._update_list_from_file(
                None, current_hash, current_list, type="usernames"
            )

            assert new_hash == current_hash
            assert current_list == ["user1"]  # Unchanged

    def test_update_clears_list_before_reload(self, temp_user_file):
        """Test that current list is cleared before reloading."""
        with patch('spraycharles.lib.spraycharles.Spraycharles.__init__', return_value=None):
            sc = Spraycharles.__new__(Spraycharles)

            current_list = ["olduser1", "olduser2"]

            # Use a different hash to trigger update
            current_hash = "differenthash"

            new_hash = sc._update_list_from_file(
                temp_user_file, current_hash, current_list, type="usernames"
            )

            # Old users should be gone
            assert "olduser1" not in current_list
            assert "olduser2" not in current_list
            # New users should be present
            assert "user1" in current_list
            assert "user2" in current_list


@pytest.mark.unit
class TestHandleTimeoutEscalation:
    """Test _handle_timeout_escalation method."""

    @patch('time.sleep')
    def test_first_escalation_5min_pause(self, mock_sleep):
        """Test first escalation: 5 minute pause."""
        with patch('spraycharles.lib.spraycharles.Spraycharles.__init__', return_value=None):
            sc = Spraycharles.__new__(Spraycharles)
            sc.backoff_stage = 0
            sc.consecutive_timeouts = 5
            sc._send_webhook = Mock()

            sc._handle_timeout_escalation()

            # Should send timeout warning notification
            sc._send_webhook.assert_called_once_with(NotifyType.TIMEOUT_WARNING)
            # Should sleep for 5 minutes
            mock_sleep.assert_called_once_with(5 * 60)
            # Should advance backoff stage
            assert sc.backoff_stage == 1
            # Should reset timeout counter
            assert sc.consecutive_timeouts == 0

    @patch('time.sleep')
    def test_second_escalation_10min_pause(self, mock_sleep):
        """Test second escalation: 10 minute pause."""
        with patch('spraycharles.lib.spraycharles.Spraycharles.__init__', return_value=None):
            sc = Spraycharles.__new__(Spraycharles)
            sc.backoff_stage = 1
            sc.consecutive_timeouts = 5
            sc._send_webhook = Mock()

            sc._handle_timeout_escalation()

            # Should NOT send notification on second escalation
            sc._send_webhook.assert_not_called()
            # Should sleep for 10 minutes
            mock_sleep.assert_called_once_with(10 * 60)
            # Should advance backoff stage
            assert sc.backoff_stage == 2
            # Should reset timeout counter
            assert sc.consecutive_timeouts == 0

    @patch('spraycharles.lib.spraycharles.Confirm.ask')
    def test_third_escalation_stops_and_confirms(self, mock_confirm):
        """Test third escalation: stop and require user confirmation."""
        with patch('spraycharles.lib.spraycharles.Spraycharles.__init__', return_value=None):
            sc = Spraycharles.__new__(Spraycharles)
            sc.backoff_stage = 2
            sc.consecutive_timeouts = 5
            sc._send_webhook = Mock()

            sc._handle_timeout_escalation()

            # Should send timeout stopped notification
            sc._send_webhook.assert_called_once_with(NotifyType.TIMEOUT_STOPPED)
            # Should ask for user confirmation
            mock_confirm.assert_called_once()
            # Should reset backoff stage to 0
            assert sc.backoff_stage == 0
            # Should reset timeout counter
            assert sc.consecutive_timeouts == 0

    def test_escalation_state_machine_progression(self):
        """Test that backoff stage progresses through states correctly."""
        with patch('spraycharles.lib.spraycharles.Spraycharles.__init__', return_value=None):
            sc = Spraycharles.__new__(Spraycharles)
            sc.backoff_stage = 0
            sc.consecutive_timeouts = 5
            sc._send_webhook = Mock()

            with patch('time.sleep'):
                # First escalation
                sc._handle_timeout_escalation()
                assert sc.backoff_stage == 1

                # Second escalation
                sc.consecutive_timeouts = 5
                sc._handle_timeout_escalation()
                assert sc.backoff_stage == 2

                # Third escalation - should reset
                sc.consecutive_timeouts = 5
                with patch('spraycharles.lib.spraycharles.Confirm.ask'):
                    sc._handle_timeout_escalation()
                assert sc.backoff_stage == 0


@pytest.mark.unit
class TestSprayEqualWithTracking:
    """Test _spray_equal_with_tracking method."""

    @patch('spraycharles.lib.spraycharles.Progress')
    def test_spray_equal_no_completed(self, mock_progress_class):
        """Test spraying password=username with no completed attempts."""
        mock_progress = MagicMock()
        mock_progress_class.return_value.__enter__.return_value = mock_progress

        with patch('spraycharles.lib.spraycharles.Spraycharles.__init__', return_value=None):
            sc = Spraycharles.__new__(Spraycharles)
            sc.usernames = ["user1", "user2@domain.com"]
            sc.domain = None
            sc._jitter = Mock()
            sc._login = Mock()
            sc.login_attempts = 0

            completed = set()
            sc._spray_equal_with_tracking(completed)

            # Should login twice (once per user)
            assert sc._login.call_count == 2
            # First call should be user1 with password user1
            sc._login.assert_any_call("user1", "user1")
            # Second call should be user2@domain.com with password user2 (stripped @domain)
            sc._login.assert_any_call("user2@domain.com", "user2")

            # Should add both to completed set
            assert len(completed) == 2
            assert ("user1", "user1") in completed
            assert ("user2@domain.com", "user2") in completed

    @patch('spraycharles.lib.spraycharles.Progress')
    def test_spray_equal_with_domain(self, mock_progress_class):
        """Test spraying password=username with domain prefix."""
        mock_progress = MagicMock()
        mock_progress_class.return_value.__enter__.return_value = mock_progress

        with patch('spraycharles.lib.spraycharles.Spraycharles.__init__', return_value=None):
            sc = Spraycharles.__new__(Spraycharles)
            sc.usernames = ["user1", "user2"]
            sc.domain = "TESTDOMAIN"
            sc._jitter = Mock()
            sc._login = Mock()
            sc.login_attempts = 0

            completed = set()
            sc._spray_equal_with_tracking(completed)

            # Should use domain-prefixed usernames
            sc._login.assert_any_call("TESTDOMAIN\\user1", "user1")
            sc._login.assert_any_call("TESTDOMAIN\\user2", "user2")

            assert ("TESTDOMAIN\\user1", "user1") in completed
            assert ("TESTDOMAIN\\user2", "user2") in completed

    @patch('spraycharles.lib.spraycharles.Progress')
    def test_spray_equal_skips_completed(self, mock_progress_class):
        """Test that already completed equal sprays are skipped."""
        mock_progress = MagicMock()
        mock_progress_class.return_value.__enter__.return_value = mock_progress

        with patch('spraycharles.lib.spraycharles.Spraycharles.__init__', return_value=None):
            sc = Spraycharles.__new__(Spraycharles)
            sc.usernames = ["user1", "user2", "user3"]
            sc.domain = None
            sc._jitter = Mock()
            sc._login = Mock()
            sc.login_attempts = 0

            # user1 already completed
            completed = {("user1", "user1")}
            sc._spray_equal_with_tracking(completed)

            # Should only login twice (user2 and user3)
            assert sc._login.call_count == 2
            sc._login.assert_any_call("user2", "user2")
            sc._login.assert_any_call("user3", "user3")

            # Completed set should now have 3 entries
            assert len(completed) == 3

    @patch('spraycharles.lib.spraycharles.Progress')
    def test_spray_equal_all_completed(self, mock_progress_class):
        """Test behavior when all equal sprays are already completed."""
        with patch('spraycharles.lib.spraycharles.Spraycharles.__init__', return_value=None):
            sc = Spraycharles.__new__(Spraycharles)
            sc.usernames = ["user1", "user2"]
            sc.domain = None
            sc._jitter = Mock()
            sc._login = Mock()
            sc.login_attempts = 0

            # All users already completed
            completed = {("user1", "user1"), ("user2", "user2")}
            sc._spray_equal_with_tracking(completed)

            # Should not login at all
            sc._login.assert_not_called()
            # Progress bar should not be created
            mock_progress_class.assert_not_called()

    @patch('spraycharles.lib.spraycharles.Progress')
    def test_spray_equal_applies_jitter(self, mock_progress_class):
        """Test that jitter is applied between attempts (but not before first)."""
        mock_progress = MagicMock()
        mock_progress_class.return_value.__enter__.return_value = mock_progress

        with patch('spraycharles.lib.spraycharles.Spraycharles.__init__', return_value=None):
            sc = Spraycharles.__new__(Spraycharles)
            sc.usernames = ["user1", "user2", "user3"]
            sc.domain = None
            sc._jitter = Mock()
            sc._login = Mock()
            sc.login_attempts = 0

            completed = set()
            sc._spray_equal_with_tracking(completed)

            # Jitter should be called 2 times (for 2nd and 3rd attempts, not 1st)
            assert sc._jitter.call_count == 2


@pytest.mark.unit
class TestHashFile:
    """Test _hash_file static method."""

    def test_hash_file_creates_consistent_hash(self, temp_user_file):
        """Test that hashing the same file produces the same hash."""
        hash1 = Spraycharles._hash_file(temp_user_file)
        hash2 = Spraycharles._hash_file(temp_user_file)

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 produces 64 character hex string

    def test_hash_file_changes_on_content_change(self, temp_user_file):
        """Test that hash changes when file content changes."""
        hash1 = Spraycharles._hash_file(temp_user_file)

        # Modify file
        with open(temp_user_file, 'a') as f:
            f.write("newuser\n")

        hash2 = Spraycharles._hash_file(temp_user_file)

        assert hash1 != hash2

    def test_hash_file_nonexistent_returns_current_hash(self):
        """Test that hashing nonexistent file returns the current hash."""
        nonexistent = Path("/nonexistent/file.txt")
        current_hash = "fallback_hash"

        result = Spraycharles._hash_file(nonexistent, current_hash)

        assert result == current_hash


@pytest.mark.unit
class TestSendWebhook:
    """Test _send_webhook helper method."""

    @patch('spraycharles.lib.spraycharles.send_notification')
    def test_send_webhook_success(self, mock_send_notification):
        """Test successful webhook sending."""
        with patch('spraycharles.lib.spraycharles.Spraycharles.__init__', return_value=None):
            sc = Spraycharles.__new__(Spraycharles)
            sc.webhook = "https://test.webhook.url"
            sc.notify = "Slack"
            sc.host = "test.example.com"

            sc._send_webhook(NotifyType.CREDS_FOUND)

            mock_send_notification.assert_called_once_with(
                "https://test.webhook.url",
                "Slack",
                NotifyType.CREDS_FOUND,
                "test.example.com",
                None
            )

    @patch('spraycharles.lib.spraycharles.send_notification')
    def test_send_webhook_with_custom_message(self, mock_send_notification):
        """Test webhook with custom message."""
        with patch('spraycharles.lib.spraycharles.Spraycharles.__init__', return_value=None):
            sc = Spraycharles.__new__(Spraycharles)
            sc.webhook = "https://test.webhook.url"
            sc.notify = "Teams"
            sc.host = "mail.example.com"

            sc._send_webhook(NotifyType.SPRAY_COMPLETE, "Custom message")

            mock_send_notification.assert_called_once_with(
                "https://test.webhook.url",
                "Teams",
                NotifyType.SPRAY_COMPLETE,
                "mail.example.com",
                "Custom message"
            )

    def test_send_webhook_not_configured(self):
        """Test that webhook is not sent when not configured."""
        with patch('spraycharles.lib.spraycharles.Spraycharles.__init__', return_value=None):
            with patch('spraycharles.lib.spraycharles.send_notification') as mock_send:
                sc = Spraycharles.__new__(Spraycharles)
                sc.webhook = None
                sc.notify = None
                sc.host = "test.example.com"

                sc._send_webhook(NotifyType.CREDS_FOUND)

                # Should not call send_notification
                mock_send.assert_not_called()

    @patch('spraycharles.lib.spraycharles.send_notification')
    def test_send_webhook_handles_exception(self, mock_send_notification):
        """Test that webhook exceptions are handled gracefully."""
        mock_send_notification.side_effect = Exception("Network error")

        with patch('spraycharles.lib.spraycharles.Spraycharles.__init__', return_value=None):
            sc = Spraycharles.__new__(Spraycharles)
            sc.webhook = "https://test.webhook.url"
            sc.notify = "Discord"
            sc.host = "test.example.com"

            # Should not raise exception
            sc._send_webhook(NotifyType.TIMEOUT_WARNING)
