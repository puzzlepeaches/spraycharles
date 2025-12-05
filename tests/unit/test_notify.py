import pytest
from unittest.mock import Mock, patch, MagicMock
from spraycharles.lib.utils.notify import (
    HookSvc,
    NotifyType,
    send_notification,
    slack,
    teams,
    discord
)


@pytest.mark.unit
class TestNotifyType:
    """Test NotifyType enum values."""

    def test_notify_type_values(self):
        """Test that all NotifyType enum values are correct."""
        assert NotifyType.CREDS_FOUND == "creds_found"
        assert NotifyType.SPRAY_WAITING == "spray_waiting"
        assert NotifyType.SPRAY_COMPLETE == "spray_complete"
        assert NotifyType.TIMEOUT_WARNING == "timeout_warning"
        assert NotifyType.TIMEOUT_STOPPED == "timeout_stopped"

    def test_notify_type_is_string_enum(self):
        """Test that NotifyType values are strings."""
        for notify_type in NotifyType:
            assert isinstance(notify_type.value, str)


@pytest.mark.unit
class TestHookSvc:
    """Test HookSvc enum values."""

    def test_hook_svc_values(self):
        """Test that all HookSvc enum values are correct."""
        assert HookSvc.SLACK == "Slack"
        assert HookSvc.TEAMS == "Teams"
        assert HookSvc.DISCORD == "Discord"


@pytest.mark.unit
class TestSlackNotification:
    """Test Slack notification function."""

    @patch('spraycharles.lib.utils.notify.requests.post')
    def test_slack_success(self, mock_post):
        """Test successful Slack notification."""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        webhook = "https://hooks.slack.com/services/TEST"
        message = "Test message"

        slack(webhook, message)

        mock_post.assert_called_once_with(
            webhook,
            json={"text": message}
        )
        mock_response.raise_for_status.assert_called_once()

    @patch('spraycharles.lib.utils.notify.requests.post')
    def test_slack_http_error(self, mock_post):
        """Test Slack notification with HTTP error."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("HTTP 404")
        mock_post.return_value = mock_response

        webhook = "https://hooks.slack.com/services/TEST"
        message = "Test message"

        with pytest.raises(Exception):
            slack(webhook, message)


@pytest.mark.unit
class TestTeamsNotification:
    """Test Teams notification function."""

    @patch('spraycharles.lib.utils.notify.pymsteams.connectorcard')
    def test_teams_success(self, mock_connector):
        """Test successful Teams notification."""
        mock_card = Mock()
        mock_connector.return_value = mock_card

        webhook = "https://outlook.office.com/webhook/TEST"
        message = "Test message"

        teams(webhook, message)

        mock_connector.assert_called_once_with(webhook)
        mock_card.text.assert_called_once_with(message)
        mock_card.send.assert_called_once()


@pytest.mark.unit
class TestDiscordNotification:
    """Test Discord notification function."""

    @patch('spraycharles.lib.utils.notify.DiscordWebhook')
    def test_discord_success(self, mock_webhook_class):
        """Test successful Discord notification."""
        mock_webhook = Mock()
        mock_webhook_class.return_value = mock_webhook

        webhook_url = "https://discord.com/api/webhooks/TEST"
        message = "Test message"

        discord(webhook_url, message)

        mock_webhook_class.assert_called_once_with(
            url=webhook_url,
            content=message
        )
        mock_webhook.execute.assert_called_once()


@pytest.mark.unit
class TestSendNotification:
    """Test send_notification dispatcher function."""

    @patch('spraycharles.lib.utils.notify.slack')
    def test_send_notification_slack_with_default_message(self, mock_slack):
        """Test sending Slack notification with default message."""
        webhook = "https://hooks.slack.com/services/TEST"
        service = HookSvc.SLACK
        notify_type = NotifyType.CREDS_FOUND
        host = "test.example.com"

        send_notification(webhook, service, notify_type, host)

        expected_message = f"Credentials guessed for host: {host}"
        mock_slack.assert_called_once_with(webhook, expected_message)

    @patch('spraycharles.lib.utils.notify.teams')
    def test_send_notification_teams_with_custom_message(self, mock_teams):
        """Test sending Teams notification with custom message."""
        webhook = "https://outlook.office.com/webhook/TEST"
        service = HookSvc.TEAMS
        notify_type = NotifyType.SPRAY_COMPLETE
        host = "test.example.com"
        custom_message = "Custom completion message"

        send_notification(webhook, service, notify_type, host, custom_message)

        mock_teams.assert_called_once_with(webhook, custom_message)

    @patch('spraycharles.lib.utils.notify.discord')
    def test_send_notification_discord_timeout_warning(self, mock_discord):
        """Test sending Discord notification for timeout warning."""
        webhook = "https://discord.com/api/webhooks/TEST"
        service = HookSvc.DISCORD
        notify_type = NotifyType.TIMEOUT_WARNING
        host = "192.168.1.1"

        send_notification(webhook, service, notify_type, host)

        expected_message = f"5 consecutive timeouts on {host}. Backing off."
        mock_discord.assert_called_once_with(webhook, expected_message)

    @patch('spraycharles.lib.utils.notify.slack')
    def test_send_notification_spray_waiting(self, mock_slack):
        """Test sending notification for spray waiting state."""
        webhook = "https://hooks.slack.com/services/TEST"
        service = HookSvc.SLACK
        notify_type = NotifyType.SPRAY_WAITING
        host = "mail.example.com"

        send_notification(webhook, service, notify_type, host)

        expected_message = f"Spray queue empty for {host}. Waiting for new users/passwords."
        mock_slack.assert_called_once_with(webhook, expected_message)

    @patch('spraycharles.lib.utils.notify.teams')
    def test_send_notification_timeout_stopped(self, mock_teams):
        """Test sending notification for timeout stopped state."""
        webhook = "https://outlook.office.com/webhook/TEST"
        service = HookSvc.TEAMS
        notify_type = NotifyType.TIMEOUT_STOPPED
        host = "10.0.0.1"

        send_notification(webhook, service, notify_type, host)

        expected_message = f"Repeated timeouts on {host}. Spray paused, awaiting confirmation."
        mock_teams.assert_called_once_with(webhook, expected_message)

    @patch('spraycharles.lib.utils.notify.slack')
    def test_send_notification_unknown_type_uses_default(self, mock_slack):
        """Test that unknown notification type uses generic default message."""
        webhook = "https://hooks.slack.com/services/TEST"
        service = HookSvc.SLACK
        # Create a mock notify_type that's not in the default_messages dict
        notify_type = "unknown_type"
        host = "test.example.com"

        # This will use the fallback message
        send_notification(webhook, service, notify_type, host)

        expected_message = f"Notification from spraycharles: {host}"
        mock_slack.assert_called_once_with(webhook, expected_message)

    @patch('spraycharles.lib.utils.notify.slack')
    @patch('spraycharles.lib.utils.notify.teams')
    @patch('spraycharles.lib.utils.notify.discord')
    def test_send_notification_only_calls_correct_service(self, mock_discord, mock_teams, mock_slack):
        """Test that only the specified service is called."""
        webhook = "https://hooks.slack.com/services/TEST"
        service = HookSvc.SLACK
        notify_type = NotifyType.CREDS_FOUND
        host = "test.example.com"

        send_notification(webhook, service, notify_type, host)

        mock_slack.assert_called_once()
        mock_teams.assert_not_called()
        mock_discord.assert_not_called()
