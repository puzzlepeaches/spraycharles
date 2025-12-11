from enum import Enum
from pathlib import Path
from typing import Optional

import typer
from typer._completion_shared import Shells, get_completion_script, install

try:
    import shellingham
except ImportError:
    shellingham = None

app = typer.Typer()
COMMAND_NAME = "completion"
HELP = "Shell completion for bash, zsh, fish, and powershell"

# Both command names need completion support
PROG_NAMES = ["spraycharles", "sc"]


class Shell(str, Enum):
    bash = "bash"
    zsh = "zsh"
    fish = "fish"
    powershell = "powershell"
    pwsh = "pwsh"


def _detect_shell() -> Optional[str]:
    """Detect the current shell if shellingham is available."""
    if shellingham is not None:
        try:
            shell, _ = shellingham.detect_shell()
            return shell
        except shellingham.ShellDetectionFailure:
            return None
    return None


def _get_complete_var(prog_name: str) -> str:
    """Generate the completion environment variable name."""
    return f"_{prog_name.upper().replace('-', '_')}_COMPLETE"


def _install_for_both_commands(shell_name: str) -> tuple[str, list[Path]]:
    """Install completion for both spraycharles and sc commands."""
    paths = []
    for prog_name in PROG_NAMES:
        complete_var = _get_complete_var(prog_name)
        _, path = install(
            shell=shell_name, prog_name=prog_name, complete_var=complete_var
        )
        paths.append(path)
    return shell_name, paths


@app.command("install")
def install_completion(
    shell: Optional[Shell] = typer.Argument(
        None, help="Shell to install completion for (auto-detected if not specified)"
    ),
):
    """Install shell completion for spraycharles and sc commands."""
    shell_name = shell.value if shell else _detect_shell()

    if shell_name is None:
        typer.echo(
            "Could not auto-detect shell. Please specify: bash, zsh, fish, or powershell",
            err=True,
        )
        raise typer.Exit(1)

    installed_shell, paths = _install_for_both_commands(shell_name)
    typer.secho(f"{installed_shell} completion installed for spraycharles and sc", fg="green")
    for path in paths:
        typer.echo(f"  - {path}")
    typer.echo("Restart your terminal for completion to take effect")


@app.command()
def show(
    shell: Optional[Shell] = typer.Argument(
        None, help="Shell to show completion for (auto-detected if not specified)"
    ),
):
    """Show completion script for manual installation."""
    shell_name = shell.value if shell else _detect_shell()

    if shell_name is None:
        typer.echo(
            "Could not auto-detect shell. Please specify: bash, zsh, fish, or powershell",
            err=True,
        )
        raise typer.Exit(1)

    # Show scripts for both commands
    for prog_name in PROG_NAMES:
        complete_var = _get_complete_var(prog_name)
        script = get_completion_script(
            prog_name=prog_name, complete_var=complete_var, shell=shell_name
        )
        typer.echo(f"# Completion for {prog_name}")
        typer.echo(script)
        typer.echo()
