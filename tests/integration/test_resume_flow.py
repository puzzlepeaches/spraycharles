import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest

from spraycharles.lib.spraycharles import Spraycharles
from spraycharles.lib.utils import NotifyType


@pytest.mark.integration
class TestResumeFlow:
    """Integration tests for the resume flow."""

    def test_resume_loads_and_skips_completed(self, temp_output_file, temp_user_file, temp_password_file):
        """Test that resume flow loads completed attempts and skips them."""
        # Setup: Write some completed attempts to output file
        completed_attempts = [
            {"Username": "user1", "Password": "Password1", "Response Code": "200"},
            {"Username": "user2", "Password": "Password1", "Response Code": "200"}
        ]

        with open(temp_output_file, 'w') as f:
            for attempt in completed_attempts:
                f.write(json.dumps(attempt) + '\n')

        # Initialize Spraycharles instance
        with patch('spraycharles.lib.spraycharles.Spraycharles.__init__', return_value=None):
            sc = Spraycharles.__new__(Spraycharles)
            sc.output = temp_output_file
            sc.usernames = ["user1", "user2", "user3"]
            sc.passwords = ["Password1", "Password2"]
            sc.domain = None
            sc.skip_guessed = False
            sc.guessed_users = set()

            # Load completed attempts
            completed = sc._load_completed_attempts()

            # Verify loaded correctly
            assert len(completed) == 2
            assert ("user1", "Password1") in completed
            assert ("user2", "Password1") in completed

            # Build work queue
            work_queue = sc._build_work_queue(completed)

            # Verify completed attempts are skipped
            assert len(work_queue) == 4  # 3 users * 2 passwords - 2 completed = 4
            assert ("user1", "Password1") not in work_queue
            assert ("user2", "Password1") not in work_queue
            assert ("user3", "Password1") in work_queue
            assert ("user1", "Password2") in work_queue
            assert ("user2", "Password2") in work_queue
            assert ("user3", "Password2") in work_queue

    def test_resume_with_domain_prefix(self, temp_output_file):
        """Test resume flow with domain-prefixed usernames."""
        # Setup: Completed attempts with domain prefix
        completed_attempts = [
            {"Username": "TESTDOMAIN\\user1", "Password": "Password1"},
            {"Username": "TESTDOMAIN\\user2", "Password": "Password1"}
        ]

        with open(temp_output_file, 'w') as f:
            for attempt in completed_attempts:
                f.write(json.dumps(attempt) + '\n')

        with patch('spraycharles.lib.spraycharles.Spraycharles.__init__', return_value=None):
            sc = Spraycharles.__new__(Spraycharles)
            sc.output = temp_output_file
            sc.usernames = ["user1", "user2", "user3"]
            sc.passwords = ["Password1", "Password2"]
            sc.domain = "TESTDOMAIN"
            sc.skip_guessed = False
            sc.guessed_users = set()

            # Load and build queue
            completed = sc._load_completed_attempts()
            work_queue = sc._build_work_queue(completed)

            # Verify domain-prefixed completed attempts are skipped
            assert ("TESTDOMAIN\\user1", "Password1") not in work_queue
            assert ("TESTDOMAIN\\user2", "Password1") not in work_queue
            assert ("TESTDOMAIN\\user3", "Password1") in work_queue

    def test_resume_equal_spray_skips_completed(self, temp_output_file):
        """Test that equal spray (password=username) respects completed attempts."""
        # Setup: Some users already sprayed with password=username
        completed_attempts = [
            {"Username": "user1", "Password": "user1"},
            {"Username": "user2", "Password": "user2"}
        ]

        with open(temp_output_file, 'w') as f:
            for attempt in completed_attempts:
                f.write(json.dumps(attempt) + '\n')

        with patch('spraycharles.lib.spraycharles.Spraycharles.__init__', return_value=None):
            with patch('spraycharles.lib.spraycharles.Progress'):
                sc = Spraycharles.__new__(Spraycharles)
                sc.output = temp_output_file
                sc.usernames = ["user1", "user2", "user3"]
                sc.domain = None
                sc._jitter = Mock()
                sc._login = Mock()
                sc.login_attempts = 0

                # Load completed
                completed = sc._load_completed_attempts()

                # Spray equal
                sc._spray_equal_with_tracking(completed)

                # Should only login for user3 (user1 and user2 already done)
                assert sc._login.call_count == 1
                sc._login.assert_called_with("user3", "user3")

    def test_resume_after_partial_completion(self, temp_output_file):
        """Test resuming after partial spray completion."""
        # Scenario: Sprayed Password1 for all users, Password2 for user1 only
        completed_attempts = [
            {"Username": "user1", "Password": "Password1"},
            {"Username": "user2", "Password": "Password1"},
            {"Username": "user3", "Password": "Password1"},
            {"Username": "user1", "Password": "Password2"}
        ]

        with open(temp_output_file, 'w') as f:
            for attempt in completed_attempts:
                f.write(json.dumps(attempt) + '\n')

        with patch('spraycharles.lib.spraycharles.Spraycharles.__init__', return_value=None):
            sc = Spraycharles.__new__(Spraycharles)
            sc.output = temp_output_file
            sc.usernames = ["user1", "user2", "user3"]
            sc.passwords = ["Password1", "Password2", "Password3"]
            sc.domain = None
            sc.skip_guessed = False
            sc.guessed_users = set()

            completed = sc._load_completed_attempts()
            work_queue = sc._build_work_queue(completed)

            # Should have 5 remaining: user2+Pass2, user3+Pass2, all users+Pass3
            assert len(work_queue) == 5
            assert ("user1", "Password1") not in work_queue
            assert ("user1", "Password2") not in work_queue
            assert ("user2", "Password2") in work_queue
            assert ("user3", "Password2") in work_queue
            assert ("user1", "Password3") in work_queue
            assert ("user2", "Password3") in work_queue
            assert ("user3", "Password3") in work_queue

    def test_empty_output_file_starts_fresh(self, temp_output_file):
        """Test that empty output file results in full work queue."""
        # Empty file - no completed attempts
        with patch('spraycharles.lib.spraycharles.Spraycharles.__init__', return_value=None):
            sc = Spraycharles.__new__(Spraycharles)
            sc.output = temp_output_file
            sc.usernames = ["user1", "user2"]
            sc.passwords = ["Password1", "Password2"]
            sc.domain = None
            sc.skip_guessed = False
            sc.guessed_users = set()

            completed = sc._load_completed_attempts()
            work_queue = sc._build_work_queue(completed)

            # Should have all combinations
            assert len(completed) == 0
            assert len(work_queue) == 4

    def test_malformed_json_doesnt_break_resume(self, temp_output_file):
        """Test that malformed JSON in output file doesn't break resume."""
        # Mix of valid and invalid JSON
        with open(temp_output_file, 'w') as f:
            f.write('{"Username": "user1", "Password": "Password1"}\n')
            f.write('invalid json line\n')
            f.write('{"Username": "user2", "Password": "Password1"}\n')

        with patch('spraycharles.lib.spraycharles.Spraycharles.__init__', return_value=None):
            sc = Spraycharles.__new__(Spraycharles)
            sc.output = temp_output_file
            sc.usernames = ["user1", "user2", "user3"]
            sc.passwords = ["Password1"]
            sc.domain = None

            # Should handle gracefully and load what it can
            completed = sc._load_completed_attempts()

            # At least user1 should be loaded (before the error)
            assert ("user1", "Password1") in completed


@pytest.mark.integration
class TestFileUpdateDetection:
    """Integration tests for file update detection during spray."""

    def test_user_file_update_detected(self, temp_user_file):
        """Test that user file changes are detected."""
        with patch('spraycharles.lib.spraycharles.Spraycharles.__init__', return_value=None):
            sc = Spraycharles.__new__(Spraycharles)
            sc.user_file = temp_user_file
            sc.usernames = ["user1", "user2", "user3"]

            # Get initial hash
            initial_hash = Spraycharles._hash_file(temp_user_file)
            sc.user_file_hash = initial_hash

            # Modify file
            with open(temp_user_file, 'w') as f:
                f.write("user1\nuser2\nuser3\nuser4\nuser5\n")

            # Update list from file
            new_hash = sc._update_list_from_file(
                temp_user_file, sc.user_file_hash, sc.usernames, type="usernames"
            )

            # Verify changes detected
            assert new_hash != initial_hash
            assert len(sc.usernames) == 5
            assert "user4" in sc.usernames
            assert "user5" in sc.usernames

    def test_password_file_update_detected(self, temp_password_file):
        """Test that password file changes are detected."""
        with patch('spraycharles.lib.spraycharles.Spraycharles.__init__', return_value=None):
            sc = Spraycharles.__new__(Spraycharles)
            sc.password_file = temp_password_file
            sc.passwords = ["Password1", "Password2"]

            # Get initial hash
            initial_hash = Spraycharles._hash_file(temp_password_file)
            sc.password_file_hash = initial_hash

            # Modify file
            with open(temp_password_file, 'w') as f:
                f.write("Password1\nPassword2\nPassword3\n")

            # Update list from file
            new_hash = sc._update_list_from_file(
                temp_password_file, sc.password_file_hash, sc.passwords, type="passwords"
            )

            # Verify changes detected
            assert new_hash != initial_hash
            assert len(sc.passwords) == 3
            assert "Password3" in sc.passwords

    def test_no_update_when_file_unchanged(self, temp_user_file):
        """Test that unchanged file doesn't trigger update."""
        with patch('spraycharles.lib.spraycharles.Spraycharles.__init__', return_value=None):
            sc = Spraycharles.__new__(Spraycharles)
            sc.user_file = temp_user_file
            sc.usernames = ["user1", "user2", "user3"]

            # Get initial hash
            initial_hash = Spraycharles._hash_file(temp_user_file)
            sc.user_file_hash = initial_hash

            # Don't modify file
            new_hash = sc._update_list_from_file(
                temp_user_file, sc.user_file_hash, sc.usernames, type="usernames"
            )

            # Verify no changes
            assert new_hash == initial_hash
            assert len(sc.usernames) == 3

    def test_file_update_rebuilds_work_queue(self, temp_user_file, temp_output_file):
        """Test that file updates trigger work queue rebuild."""
        # Setup completed attempts
        completed_attempts = [
            {"Username": "user1", "Password": "Password1"}
        ]

        with open(temp_output_file, 'w') as f:
            for attempt in completed_attempts:
                f.write(json.dumps(attempt) + '\n')

        with patch('spraycharles.lib.spraycharles.Spraycharles.__init__', return_value=None):
            sc = Spraycharles.__new__(Spraycharles)
            sc.output = temp_output_file
            sc.user_file = temp_user_file
            sc.usernames = ["user1", "user2", "user3"]
            sc.passwords = ["Password1"]
            sc.domain = None
            sc.user_file_hash = Spraycharles._hash_file(temp_user_file)
            sc.skip_guessed = False
            sc.guessed_users = set()

            # Load completed and build initial queue
            completed = sc._load_completed_attempts()
            initial_queue = sc._build_work_queue(completed)
            assert len(initial_queue) == 2  # user2, user3

            # Add new user to file
            with open(temp_user_file, 'w') as f:
                f.write("user1\nuser2\nuser3\nuser4\n")

            # Update from file
            sc.user_file_hash = sc._update_list_from_file(
                temp_user_file, sc.user_file_hash, sc.usernames, type="usernames"
            )

            # Rebuild queue
            new_queue = sc._build_work_queue(completed)
            assert len(new_queue) == 3  # user2, user3, user4
            assert ("user4", "Password1") in new_queue


@pytest.mark.integration
class TestTimeoutEscalationFlow:
    """Integration tests for timeout escalation state machine."""

    @patch('time.sleep')
    def test_full_escalation_cycle(self, mock_sleep):
        """Test complete escalation cycle through all stages."""
        with patch('spraycharles.lib.spraycharles.Spraycharles.__init__', return_value=None):
            sc = Spraycharles.__new__(Spraycharles)
            sc.backoff_stage = 0
            sc.consecutive_timeouts = 0
            sc._send_webhook = Mock()

            # Stage 0 -> 1: First escalation (5 min)
            sc.consecutive_timeouts = 5
            sc._handle_timeout_escalation()
            assert sc.backoff_stage == 1
            assert sc.consecutive_timeouts == 0
            mock_sleep.assert_called_with(5 * 60)

            # Stage 1 -> 2: Second escalation (10 min)
            sc.consecutive_timeouts = 5
            sc._handle_timeout_escalation()
            assert sc.backoff_stage == 2
            assert sc.consecutive_timeouts == 0
            mock_sleep.assert_called_with(10 * 60)

            # Stage 2 -> 0: Third escalation (confirm and reset)
            sc.consecutive_timeouts = 5
            with patch('spraycharles.lib.spraycharles.Confirm.ask'):
                sc._handle_timeout_escalation()
            assert sc.backoff_stage == 0
            assert sc.consecutive_timeouts == 0

    @patch('time.sleep')
    def test_timeout_counter_resets_on_success(self, mock_sleep):
        """Test that timeout counter resets after successful login."""
        with patch('spraycharles.lib.spraycharles.Spraycharles.__init__', return_value=None):
            sc = Spraycharles.__new__(Spraycharles)
            sc.backoff_stage = 0
            sc.consecutive_timeouts = 4
            sc._send_webhook = Mock()
            sc.target = Mock()
            sc.target.login = Mock(return_value={"status": "success"})
            sc.target.print_response = Mock()
            sc.output = Path("/tmp/test.json")
            sc.print = False

            # Simulate successful login
            sc._login("user1", "Password1")

            # Timeout counter should reset
            assert sc.consecutive_timeouts == 0
            assert sc.backoff_stage == 0

    def test_escalation_notifications_sent_correctly(self):
        """Test that correct notifications are sent at each stage."""
        with patch('spraycharles.lib.spraycharles.Spraycharles.__init__', return_value=None):
            with patch('time.sleep'):
                sc = Spraycharles.__new__(Spraycharles)
                sc.backoff_stage = 0
                sc.consecutive_timeouts = 5
                sc._send_webhook = Mock()

                # First escalation sends TIMEOUT_WARNING
                sc._handle_timeout_escalation()
                sc._send_webhook.assert_called_with(NotifyType.TIMEOUT_WARNING)

                # Second escalation sends nothing
                sc._send_webhook.reset_mock()
                sc.consecutive_timeouts = 5
                sc._handle_timeout_escalation()
                sc._send_webhook.assert_not_called()

                # Third escalation sends TIMEOUT_STOPPED
                sc.consecutive_timeouts = 5
                with patch('spraycharles.lib.spraycharles.Confirm.ask'):
                    sc._handle_timeout_escalation()
                sc._send_webhook.assert_called_with(NotifyType.TIMEOUT_STOPPED)


@pytest.mark.integration
class TestEndToEndResumeScenario:
    """End-to-end integration test for resume functionality."""

    def test_complete_resume_workflow(self, temp_output_file, temp_user_file, temp_password_file):
        """Test complete workflow: spray -> interrupt -> resume."""
        # Phase 1: Initial spray (simulated partial completion)
        initial_attempts = [
            {"Username": "user1", "Password": "Password1"},
            {"Username": "user2", "Password": "Password1"},
            {"Username": "user1", "Password": "user1"},
            {"Username": "user2", "Password": "user2"}
        ]

        with open(temp_output_file, 'w') as f:
            for attempt in initial_attempts:
                f.write(json.dumps(attempt) + '\n')

        # Phase 2: Resume spray
        with patch('spraycharles.lib.spraycharles.Spraycharles.__init__', return_value=None):
            with patch('spraycharles.lib.spraycharles.Progress'):
                sc = Spraycharles.__new__(Spraycharles)
                sc.output = temp_output_file
                sc.user_file = temp_user_file
                sc.password_file = temp_password_file
                sc.usernames = ["user1", "user2", "user3"]
                sc.passwords = ["Password1", "Password2"]
                sc.domain = None
                sc._jitter = Mock()
                sc._login = Mock()
                sc.login_attempts = 0
                sc.skip_guessed = False
                sc.guessed_users = set()

                # Load completed attempts
                completed = sc._load_completed_attempts()
                assert len(completed) == 4

                # Test equal spray resume
                sc._spray_equal_with_tracking(completed)
                # Should only spray user3 (user1 and user2 already done)
                assert sc._login.call_count == 1
                sc._login.assert_called_with("user3", "user3")

                # Reset for main spray test
                sc._login.reset_mock()

                # Build work queue
                work_queue = sc._build_work_queue(completed)

                # Should skip already completed combinations
                # Completed: user1+Pass1, user2+Pass1, user1+user1, user2+user2
                # Remaining from Pass1: user3+Pass1 (1)
                # Remaining from Pass2: user1+Pass2, user2+Pass2, user3+Pass2 (3)
                # Total: 4
                assert len(work_queue) == 4
                assert ("user1", "Password1") not in work_queue
                assert ("user2", "Password1") not in work_queue
                assert ("user3", "Password1") in work_queue
                assert ("user1", "Password2") in work_queue
                assert ("user2", "Password2") in work_queue
                assert ("user3", "Password2") in work_queue


@pytest.mark.integration
class TestTimeParsingIntegration:
    """Integration tests for time parsing in spray.py."""

    def test_jitter_uses_uniform_random_for_floats(self):
        """Test that jitter uses random.uniform for float support."""
        with patch('spraycharles.lib.spraycharles.Spraycharles.__init__', return_value=None):
            with patch('spraycharles.lib.spraycharles.sleep') as mock_sleep:
                with patch('spraycharles.lib.spraycharles.random.uniform') as mock_uniform:
                    mock_uniform.return_value = 1.5

                    sc = Spraycharles.__new__(Spraycharles)
                    sc.jitter = 5.0  # 5 seconds max
                    sc.jitter_min = 1.0  # 1 second min
                    sc.delay = None

                    sc._jitter()

                    mock_uniform.assert_called_once_with(1.0, 5.0)
                    mock_sleep.assert_called_once_with(1.5)

    def test_delay_uses_fixed_sleep(self):
        """Test that delay uses fixed sleep time instead of random."""
        with patch('spraycharles.lib.spraycharles.Spraycharles.__init__', return_value=None):
            with patch('spraycharles.lib.spraycharles.sleep') as mock_sleep:
                sc = Spraycharles.__new__(Spraycharles)
                sc.jitter = None
                sc.jitter_min = 0.0
                sc.delay = 2.5  # 2.5 seconds fixed delay

                sc._jitter()

                mock_sleep.assert_called_once_with(2.5)

    def test_delay_takes_precedence_over_jitter(self):
        """Test that delay is used when both are set (shouldn't happen per CLI validation)."""
        with patch('spraycharles.lib.spraycharles.Spraycharles.__init__', return_value=None):
            with patch('spraycharles.lib.spraycharles.sleep') as mock_sleep:
                sc = Spraycharles.__new__(Spraycharles)
                sc.jitter = 5.0
                sc.jitter_min = 1.0
                sc.delay = 2.0  # Delay should win

                sc._jitter()

                # Should use fixed delay, not random jitter
                mock_sleep.assert_called_once_with(2.0)

    def test_jitter_alone_defaults_min_to_zero(self):
        """Test that jitter without jitter_min uses 0 as minimum."""
        with patch('spraycharles.lib.spraycharles.Spraycharles.__init__', return_value=None):
            with patch('spraycharles.lib.spraycharles.sleep'):
                with patch('spraycharles.lib.spraycharles.random.uniform') as mock_uniform:
                    mock_uniform.return_value = 2.5

                    sc = Spraycharles.__new__(Spraycharles)
                    sc.jitter = 5.0  # Max 5 seconds
                    sc.jitter_min = 0.0  # Default to 0
                    sc.delay = None

                    sc._jitter()

                    # Should call uniform with 0 to 5
                    mock_uniform.assert_called_once_with(0.0, 5.0)

    def test_no_sleep_when_no_delay_or_jitter(self):
        """Test that no sleep occurs when neither delay nor jitter is set."""
        with patch('spraycharles.lib.spraycharles.Spraycharles.__init__', return_value=None):
            with patch('spraycharles.lib.spraycharles.sleep') as mock_sleep:
                sc = Spraycharles.__new__(Spraycharles)
                sc.jitter = None
                sc.jitter_min = 0.0
                sc.delay = None

                sc._jitter()

                # No sleep should be called
                mock_sleep.assert_not_called()
