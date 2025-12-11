import json
from unittest.mock import Mock, patch, MagicMock
import pytest

from spraycharles.lib.analyze import Analyzer
from spraycharles.lib.utils import NotifyType, HookSvc


@pytest.mark.unit
class TestAnalyzerInit:
    """Test Analyzer initialization."""

    def test_analyzer_init_with_defaults(self):
        """Test Analyzer initialization with default values."""
        analyzer = Analyzer(
            resultsfile="test.json",
            notify=HookSvc.SLACK,
            webhook="https://test.url",
            host="test.example.com"
        )

        assert analyzer.resultsfile == "test.json"
        assert analyzer.notify == HookSvc.SLACK
        assert analyzer.webhook == "https://test.url"
        assert analyzer.host == "test.example.com"
        assert analyzer.hit_count == 0

    def test_analyzer_init_with_hit_count(self):
        """Test Analyzer initialization with hit_count."""
        analyzer = Analyzer(
            resultsfile="test.json",
            notify=HookSvc.TEAMS,
            webhook="https://test.url",
            host="test.example.com",
            hit_count=5
        )

        assert analyzer.hit_count == 5


@pytest.mark.unit
class TestSendNotification:
    """Test _send_notification method."""

    @patch('spraycharles.lib.analyze.send_notification')
    def test_send_notification_with_new_hits(self, mock_send_notification):
        """Test sending notification when new hits are found."""
        analyzer = Analyzer(
            resultsfile="test.json",
            notify=HookSvc.SLACK,
            webhook="https://webhook.url",
            host="test.example.com",
            hit_count=2
        )

        # New hit total is greater than previous hit_count
        analyzer._send_notification(hit_total=5)

        mock_send_notification.assert_called_once_with(
            "https://webhook.url",
            HookSvc.SLACK,
            NotifyType.CREDS_FOUND,
            "test.example.com"
        )

    @patch('spraycharles.lib.analyze.send_notification')
    def test_send_notification_no_new_hits(self, mock_send_notification):
        """Test that notification is not sent when no new hits."""
        analyzer = Analyzer(
            resultsfile="test.json",
            notify=HookSvc.TEAMS,
            webhook="https://webhook.url",
            host="test.example.com",
            hit_count=5
        )

        # Same hit total - no new hits
        analyzer._send_notification(hit_total=5)

        mock_send_notification.assert_not_called()

    @patch('spraycharles.lib.analyze.send_notification')
    def test_send_notification_fewer_hits(self, mock_send_notification):
        """Test that notification is not sent when hit total decreases."""
        analyzer = Analyzer(
            resultsfile="test.json",
            notify=HookSvc.DISCORD,
            webhook="https://webhook.url",
            host="test.example.com",
            hit_count=10
        )

        # Fewer hits than before
        analyzer._send_notification(hit_total=5)

        mock_send_notification.assert_not_called()

    def test_send_notification_no_webhook_configured(self):
        """Test that notification is not sent when webhook not configured."""
        with patch('spraycharles.lib.analyze.send_notification') as mock_send:
            analyzer = Analyzer(
                resultsfile="test.json",
                notify=None,
                webhook=None,
                host="test.example.com",
                hit_count=0
            )

            analyzer._send_notification(hit_total=5)

            mock_send.assert_not_called()

    @patch('spraycharles.lib.analyze.send_notification')
    def test_send_notification_handles_exception(self, mock_send_notification):
        """Test that exceptions during notification are handled."""
        mock_send_notification.side_effect = Exception("Network error")

        analyzer = Analyzer(
            resultsfile="test.json",
            notify=HookSvc.SLACK,
            webhook="https://webhook.url",
            host="test.example.com",
            hit_count=0
        )

        # Should not raise exception
        analyzer._send_notification(hit_total=5)


@pytest.mark.unit
class TestO365Analyze:
    """Test O365_analyze method."""

    @patch('spraycharles.lib.analyze.console.print')
    def test_o365_analyze_with_success(self, mock_print, sample_o365_results):
        """Test O365 analysis with successful logins."""
        analyzer = Analyzer(
            resultsfile="test.json",
            notify=None,
            webhook=None,
            host="login.microsoftonline.com",
            hit_count=0
        )
        analyzer._send_notification = Mock()

        count, users = analyzer.O365_analyze(sample_o365_results)

        # Should find 1 success
        assert count == 1
        assert "user2@example.com" in users
        # Should send notification
        analyzer._send_notification.assert_called_once_with(1)
        # Should print table
        mock_print.assert_called_once()

    @patch('spraycharles.lib.analyze.console.print')
    def test_o365_analyze_no_success(self, mock_print):
        """Test O365 analysis with no successful logins."""
        results = [
            {
                "Username": "user1@example.com",
                "Password": "Password1",
                "Result": "Failed",
                "Message": "Invalid credentials",
                "Module": "Office365"
            }
        ]

        analyzer = Analyzer(
            resultsfile="test.json",
            notify=None,
            webhook=None,
            host="login.microsoftonline.com"
        )

        count, users = analyzer.O365_analyze(results)

        assert count == 0
        assert len(users) == 0
        # Should not print success table
        assert mock_print.call_count == 0

    @patch('spraycharles.lib.analyze.console.print')
    def test_o365_analyze_multiple_successes(self, mock_print):
        """Test O365 analysis with multiple successful logins."""
        results = [
            {"Username": "user1@example.com", "Password": "Pass1", "Result": "Success", "Message": "Valid"},
            {"Username": "user2@example.com", "Password": "Pass2", "Result": "Failed", "Message": "Invalid"},
            {"Username": "user3@example.com", "Password": "Pass3", "Result": "Success", "Message": "Valid"},
            {"Username": "user4@example.com", "Password": "Pass4", "Result": "Success", "Message": "Valid"}
        ]

        analyzer = Analyzer(
            resultsfile="test.json",
            notify=None,
            webhook=None,
            host="login.microsoftonline.com"
        )
        analyzer._send_notification = Mock()

        count, users = analyzer.O365_analyze(results)

        assert count == 3
        assert len(users) == 3
        analyzer._send_notification.assert_called_once_with(3)


@pytest.mark.unit
class TestSMBAnalyze:
    """Test smb_analyze method."""

    @patch('spraycharles.lib.analyze.console.print')
    def test_smb_analyze_with_success(self, mock_print, sample_smb_results):
        """Test SMB analysis with successful login."""
        analyzer = Analyzer(
            resultsfile="test.json",
            notify=None,
            webhook=None,
            host="192.168.1.1"
        )
        analyzer._send_notification = Mock()

        count, users = analyzer.smb_analyze(sample_smb_results)

        # Should find 1 success (STATUS_SUCCESS)
        assert count == 1
        assert len(users) == 1
        analyzer._send_notification.assert_called_once_with(1)

    @patch('spraycharles.lib.analyze.console.print')
    def test_smb_analyze_no_success(self, mock_print):
        """Test SMB analysis with no successful logins."""
        results = [
            {
                "Username": "DOMAIN\\user1",
                "Password": "Password1",
                "SMB Login": "STATUS_LOGON_FAILURE",
                "Module": "SMB"
            }
        ]

        analyzer = Analyzer(
            resultsfile="test.json",
            notify=None,
            webhook=None,
            host="192.168.1.1"
        )

        count, users = analyzer.smb_analyze(results)

        assert count == 0
        assert len(users) == 0

    @patch('spraycharles.lib.analyze.console.print')
    def test_smb_analyze_account_disabled(self, mock_print):
        """Test SMB analysis recognizes STATUS_ACCOUNT_DISABLED as success."""
        results = [
            {
                "Username": "DOMAIN\\user1",
                "Password": "Password1",
                "SMB Login": "STATUS_ACCOUNT_DISABLED",
                "Module": "SMB"
            }
        ]

        analyzer = Analyzer(
            resultsfile="test.json",
            notify=None,
            webhook=None,
            host="192.168.1.1"
        )
        analyzer._send_notification = Mock()

        count, users = analyzer.smb_analyze(results)

        # Account disabled means valid credentials
        assert count == 1
        assert len(users) == 1

    @patch('spraycharles.lib.analyze.console.print')
    def test_smb_analyze_password_expired(self, mock_print):
        """Test SMB analysis recognizes PASSWORD_EXPIRED as success."""
        results = [
            {
                "Username": "DOMAIN\\user1",
                "Password": "Password1",
                "SMB Login": "STATUS_PASSWORD_EXPIRED",
                "Module": "SMB"
            }
        ]

        analyzer = Analyzer(
            resultsfile="test.json",
            notify=None,
            webhook=None,
            host="192.168.1.1"
        )
        analyzer._send_notification = Mock()

        count, users = analyzer.smb_analyze(results)

        # Expired password means valid credentials
        assert count == 1
        assert len(users) == 1

    @patch('spraycharles.lib.analyze.console.print')
    def test_smb_analyze_password_must_change(self, mock_print):
        """Test SMB analysis recognizes PASSWORD_MUST_CHANGE as success."""
        results = [
            {
                "Username": "DOMAIN\\user1",
                "Password": "Password1",
                "SMB Login": "STATUS_PASSWORD_MUST_CHANGE",
                "Module": "SMB"
            }
        ]

        analyzer = Analyzer(
            resultsfile="test.json",
            notify=None,
            webhook=None,
            host="192.168.1.1"
        )
        analyzer._send_notification = Mock()

        count, users = analyzer.smb_analyze(results)

        # Password must change means valid credentials
        assert count == 1
        assert len(users) == 1


@pytest.mark.unit
class TestHTTPAnalyze:
    """Test http_analyze method."""

    @patch('spraycharles.lib.analyze.console.print')
    def test_http_analyze_with_outliers(self, mock_print):
        """Test HTTP analysis finds response length outliers."""
        # Need more data points with clear outlier
        results = [
            {"Username": "user1", "Password": "Pass1", "Response Code": "200", "Response Length": "1000"},
            {"Username": "user2", "Password": "Pass2", "Response Code": "200", "Response Length": "1000"},
            {"Username": "user3", "Password": "Pass3", "Response Code": "200", "Response Length": "1000"},
            {"Username": "user4", "Password": "Pass4", "Response Code": "200", "Response Length": "1000"},
            {"Username": "user5", "Password": "Pass5", "Response Code": "200", "Response Length": "1000"},
            {"Username": "user6", "Password": "Pass6", "Response Code": "200", "Response Length": "10000"},  # Outlier
        ]

        analyzer = Analyzer(
            resultsfile="test.json",
            notify=None,
            webhook=None,
            host="test.example.com"
        )
        analyzer._send_notification = Mock()

        count, users = analyzer.http_analyze(results)

        # Should find 1 outlier (10000 vs multiple 1000s)
        assert count == 1
        assert len(users) == 1
        analyzer._send_notification.assert_called_once_with(1)

    @patch('spraycharles.lib.analyze.console.print')
    def test_http_analyze_no_outliers(self, mock_print):
        """Test HTTP analysis with no outliers."""
        results = [
            {"Username": "user1", "Password": "Pass1", "Response Code": "200", "Response Length": "1234"},
            {"Username": "user2", "Password": "Pass2", "Response Code": "200", "Response Length": "1235"},
            {"Username": "user3", "Password": "Pass3", "Response Code": "200", "Response Length": "1233"}
        ]

        analyzer = Analyzer(
            resultsfile="test.json",
            notify=None,
            webhook=None,
            host="test.example.com"
        )

        count, users = analyzer.http_analyze(results)

        assert count == 0
        assert len(users) == 0

    @patch('spraycharles.lib.analyze.console.print')
    def test_http_analyze_filters_timeouts(self, mock_print):
        """Test that timeout responses are filtered out."""
        results = [
            {"Username": "user1", "Password": "Pass1", "Response Code": "200", "Response Length": "1234"},
            {"Username": "user2", "Password": "Pass2", "Response Code": "TIMEOUT", "Response Length": "0"},
            {"Username": "user3", "Password": "Pass3", "Response Code": "200", "Response Length": "1234"}
        ]

        analyzer = Analyzer(
            resultsfile="test.json",
            notify=None,
            webhook=None,
            host="test.example.com"
        )

        count, users = analyzer.http_analyze(results)

        # Timeout should be filtered out before analysis
        assert count == 0
        assert len(users) == 0

    @patch('spraycharles.lib.analyze.console.print')
    def test_http_analyze_multiple_outliers(self, mock_print):
        """Test HTTP analysis with multiple outliers."""
        # Need significant outliers beyond 2 standard deviations
        # Mean of [1000*15, 100000*2] = ~12882, SD = ~24588
        # Mean + 2*SD = ~62059, so 100000 is well beyond
        results = []
        for i in range(15):
            results.append({"Username": f"user{i}", "Password": f"Pass{i}", "Response Code": "200", "Response Length": "1000"})
        results.append({"Username": "user15", "Password": "Pass15", "Response Code": "200", "Response Length": "100000"})
        results.append({"Username": "user16", "Password": "Pass16", "Response Code": "200", "Response Length": "100000"})

        analyzer = Analyzer(
            resultsfile="test.json",
            notify=None,
            webhook=None,
            host="test.example.com"
        )
        analyzer._send_notification = Mock()

        count, users = analyzer.http_analyze(results)

        # Should find 2 outliers (both 100000s are well beyond 2 SD from mean)
        assert count == 2
        assert len(users) == 2


@pytest.mark.unit
class TestAnalyzeRouter:
    """Test the main analyze method that routes to specific analyzers."""

    def test_analyze_routes_to_o365(self, temp_output_file, sample_o365_results):
        """Test that Office365 module routes to O365_analyze."""
        # Write test data
        with open(temp_output_file, 'w') as f:
            for item in sample_o365_results:
                f.write(json.dumps(item) + '\n')

        analyzer = Analyzer(
            resultsfile=temp_output_file,
            notify=None,
            webhook=None,
            host="login.microsoftonline.com"
        )

        with patch.object(analyzer, 'O365_analyze', return_value=5) as mock_o365:
            result = analyzer.analyze()

            mock_o365.assert_called_once()
            assert result == 5

    def test_analyze_routes_to_smb(self, temp_output_file, sample_smb_results):
        """Test that SMB module routes to smb_analyze."""
        # Write test data
        with open(temp_output_file, 'w') as f:
            for item in sample_smb_results:
                f.write(json.dumps(item) + '\n')

        analyzer = Analyzer(
            resultsfile=temp_output_file,
            notify=None,
            webhook=None,
            host="192.168.1.1"
        )

        with patch.object(analyzer, 'smb_analyze', return_value=3) as mock_smb:
            result = analyzer.analyze()

            mock_smb.assert_called_once()
            assert result == 3

    def test_analyze_routes_to_http(self, temp_output_file, sample_spray_results):
        """Test that other modules route to http_analyze."""
        # Write test data
        with open(temp_output_file, 'w') as f:
            for item in sample_spray_results:
                f.write(json.dumps(item) + '\n')

        analyzer = Analyzer(
            resultsfile=temp_output_file,
            notify=None,
            webhook=None,
            host="test.example.com"
        )

        with patch.object(analyzer, 'http_analyze', return_value=2) as mock_http:
            result = analyzer.analyze()

            mock_http.assert_called_once()
            assert result == 2
