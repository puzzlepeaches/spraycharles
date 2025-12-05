from enum import Enum
import pymsteams
from discord_webhook import DiscordWebhook
import requests


class HookSvc(str, Enum):
    SLACK   = "Slack"
    TEAMS   = "Teams"
    DISCORD = "Discord"


class NotifyType(str, Enum):
    CREDS_FOUND = "creds_found"
    SPRAY_WAITING = "spray_waiting"
    SPRAY_COMPLETE = "spray_complete"
    TIMEOUT_WARNING = "timeout_warning"
    TIMEOUT_STOPPED = "timeout_stopped"


def slack(webhook: str, message: str):
    payload = {"text": message}
    response = requests.post(webhook, json=payload)
    response.raise_for_status()


def teams(webhook: str, message: str):
    notify = pymsteams.connectorcard(webhook)
    notify.text(message)
    notify.send()


def discord(webhook_url: str, message: str):
    notify = DiscordWebhook(url=webhook_url, content=message)
    notify.execute()


def send_notification(webhook: str, service: HookSvc, notify_type: NotifyType, host: str, message: str = None):
    """Send notification to configured webhook service."""
    default_messages = {
        NotifyType.CREDS_FOUND: f"Credentials guessed for host: {host}",
        NotifyType.SPRAY_WAITING: f"Spray queue empty for {host}. Waiting for new users/passwords.",
        NotifyType.SPRAY_COMPLETE: f"Spray complete for {host}. Exiting.",
        NotifyType.TIMEOUT_WARNING: f"5 consecutive timeouts on {host}. Backing off.",
        NotifyType.TIMEOUT_STOPPED: f"Repeated timeouts on {host}. Spray paused, awaiting confirmation.",
    }

    text = message or default_messages.get(notify_type, f"Notification from spraycharles: {host}")

    if service == HookSvc.SLACK:
        slack(webhook, text)
    elif service == HookSvc.TEAMS:
        teams(webhook, text)
    elif service == HookSvc.DISCORD:
        discord(webhook, text)
