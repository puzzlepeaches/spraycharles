import typer
from rich.console import Console
from rich.syntax import Syntax
from rich.table import Table
from pathlib import Path

from spraycharles.lib.config import global_config
from spraycharles.lib.logger import console as log_console

app = typer.Typer()
COMMAND_NAME = 'config'
HELP = 'Manage Spraycharles configuration'

@app.callback(no_args_is_help=True, invoke_without_command=True)
def main():
    """Manage global configuration for Spraycharles"""
    pass

@app.command()
def show():
    """Show current configuration"""
    config_yaml = global_config.show()
    syntax = Syntax(config_yaml, "yaml", theme="monokai", line_numbers=True)
    log_console.print(f"\n[bold cyan]Global Configuration[/bold cyan]")
    log_console.print(f"[dim]Location: {global_config.config_file}[/dim]\n")
    log_console.print(syntax)

@app.command()
def path():
    """Show configuration file path"""
    log_console.print(f"[bold cyan]Configuration file:[/bold cyan] {global_config.config_file}")
    if global_config.config_file.exists():
        log_console.print("[green]✓[/green] File exists")
    else:
        log_console.print("[yellow]![/yellow] File will be created on first use")

@app.command()
def set(key: str = typer.Argument(..., help="Configuration key (e.g., notifications.webhook)"),
        value: str = typer.Argument(..., help="Value to set")):
    """Set a configuration value"""
    # Handle boolean values
    if value.lower() in ['true', 'yes', 'on']:
        value = True
    elif value.lower() in ['false', 'no', 'off']:
        value = False
    elif value.lower() == 'none':
        value = None
    # Try to convert to int if possible
    elif value.isdigit():
        value = int(value)
    
    global_config.set(key, value)
    log_console.print(f"[green]✓[/green] Set [cyan]{key}[/cyan] = [yellow]{value}[/yellow]")

@app.command()
def get(key: str = typer.Argument(..., help="Configuration key (e.g., notifications.webhook)")):
    """Get a configuration value"""
    value = global_config.get(key)
    if value is None:
        log_console.print(f"[yellow]![/yellow] Key [cyan]{key}[/cyan] not found or is None")
    else:
        log_console.print(f"[cyan]{key}[/cyan] = [yellow]{value}[/yellow]")

@app.command()
def reset():
    """Reset configuration to defaults"""
    if typer.confirm("Are you sure you want to reset to default configuration?"):
        global_config.config = global_config.DEFAULT_CONFIG.copy()
        global_config.save()
        log_console.print("[green]✓[/green] Configuration reset to defaults")
    else:
        log_console.print("[yellow]![/yellow] Reset cancelled")

@app.command()
def notifications(
    enable: bool = typer.Option(None, '--enable/--disable', help="Enable or disable notifications"),
    provider: str = typer.Option(None, '-p', '--provider', help="Notification provider (slack/teams/discord)"),
    webhook: str = typer.Option(None, '-w', '--webhook', help="Webhook URL"),
    on_success: bool = typer.Option(None, '--on-success/--no-on-success', help="Notify on successful login"),
    on_completion: bool = typer.Option(None, '--on-completion/--no-on-completion', help="Notify on spray completion"),
    on_pause: bool = typer.Option(None, '--on-pause/--no-on-pause', help="Notify when spray pauses")):
    """Configure notification settings"""
    
    updated = False
    
    if enable is not None:
        global_config.set('notifications.enabled', enable)
        updated = True
        log_console.print(f"[green]✓[/green] Notifications {'enabled' if enable else 'disabled'}")
    
    if provider:
        if provider.lower() not in ['slack', 'teams', 'discord']:
            log_console.print(f"[red]✗[/red] Invalid provider. Choose from: slack, teams, discord")
            return
        global_config.set('notifications.provider', provider.lower())
        updated = True
        log_console.print(f"[green]✓[/green] Provider set to [cyan]{provider}[/cyan]")
    
    if webhook:
        global_config.set('notifications.webhook', webhook)
        updated = True
        log_console.print(f"[green]✓[/green] Webhook URL configured")
    
    if on_success is not None:
        global_config.set('notifications.notify_on_success', on_success)
        updated = True
    
    if on_completion is not None:
        global_config.set('notifications.notify_on_completion', on_completion)
        updated = True
    
    if on_pause is not None:
        global_config.set('notifications.notify_on_pause', on_pause)
        updated = True
    
    if not updated:
        # Show current notification settings
        table = Table(title="Notification Settings")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="yellow")
        
        notif_config = global_config.get_notification_config()
        for key, value in notif_config.items():
            table.add_row(key, str(value))
        
        log_console.print(table)
    else:
        log_console.print("\n[bold]Current notification configuration:[/bold]")
        notif_config = global_config.get_notification_config()
        for key, value in notif_config.items():
            log_console.print(f"  [cyan]{key}:[/cyan] [yellow]{value}[/yellow]")