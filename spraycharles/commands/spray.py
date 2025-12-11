import typer
from typer_config import use_yaml_config
from typer_config.decorators import dump_yaml_config
from rich.prompt import Confirm
from pathlib import Path

from spraycharles import ascii
from spraycharles.lib.logger import logger, init_logger, console
from spraycharles.targets import Target, all
from spraycharles.lib.spraycharles import Spraycharles
from spraycharles.lib.utils import HookSvc, parse_time

app = typer.Typer()
COMMAND_NAME = 'spray'
HELP =  'Low and slow password spraying'

@app.callback(no_args_is_help=True, invoke_without_command=True)
@use_yaml_config()
@dump_yaml_config('last-config.yaml')
def main(
    usernames:  str     = typer.Option(..., '-u', '--usernames', help="Filepath of the usernames list", rich_help_panel="User/Pass Config"),
    passwords:  str     = typer.Option(..., '-p', '--passwords', help="Single password to spray or filepath of the passwords list", rich_help_panel="User/Pass Config"),
    host:       str     = typer.Option(None, '-H', '--host', help="Host to password spray (ip or hostname). Can by anything when using Office365 module - only used for logfile name", rich_help_panel="Spray Target"),
    module:     Target  = typer.Option(..., '-m', '--module', case_sensitive=False, help="Module corresponding to target host", rich_help_panel="Spray Target"),
    path:       str     = typer.Option(None, help="NTLM authentication endpoint (i.e., rpc or ews)", rich_help_panel="Spray Target"),
    output:     str     = typer.Option(None, '-o', '--output', help="Name and path of result output file", rich_help_panel="Output"),
    quiet:      bool    = typer.Option(False, '-q', '--quiet', help="Will not log each login attempt to the console", rich_help_panel="Output"),
    attempts:   int     = typer.Option(None, '-a', '--attempts', help="Number of logins submissions per interval (for each user)", rich_help_panel="Spray Behavior"),
    interval:   str     = typer.Option(None, '-i', '--interval', help="Time between login intervals (e.g., 30m, 1h). Default unit: minutes", rich_help_panel="Spray Behavior"),
    equal:      bool    = typer.Option(False, '-e', '--equal', help="Does 1 spray for each user where password = username", rich_help_panel="User/Pass Config"),
    timeout:    str     = typer.Option("5", '-t', '--timeout', help="Web request timeout (e.g., 5s, 10s). Default unit: seconds", rich_help_panel="Spray Behavior"),
    port:       int     = typer.Option(443, '-P','--port', help="Port to connect to on the specified host", rich_help_panel="Spray Target"),
    fireprox:   str     = typer.Option(None, '-f', '--fireprox', help="URL of desired fireprox interface", rich_help_panel="Spray Target"),
    domain:     str     = typer.Option(None, '-d', '--domain', help="HTTP - Prepend DOMAIN\\ to usernames; SMB - Supply domain for smb connection", rich_help_panel="Spray Target"),
    analyze:    bool    = typer.Option(False, '-A', '--analyze', help="Run the results analyzer after each spray interval (Early false positives are more likely)", rich_help_panel="Output"),
    jitter:     str     = typer.Option(None, '-j', '--jitter', help="Max jitter time between requests (e.g., 5s, 1m). Default unit: seconds", rich_help_panel="Spray Behavior"),
    jitter_min: str     = typer.Option(None, '-jm', '--jitter-min', help="Min jitter time between requests. Default unit: seconds", rich_help_panel="Spray Behavior"),
    notify:     HookSvc = typer.Option(None, '-n', '--notify', case_sensitive=False, help="Enable notifications for Slack, Teams or Discord", rich_help_panel="Notifications"),
    webhook:    str     = typer.Option(None, '-w', '--webhook', help="Webhook used for specified notification module", rich_help_panel="Notifications"),
    pause:      bool    = typer.Option(False, '--pause', help="Pause the spray between intervals if a new potentially successful login was found", rich_help_panel="Spray Behavior"),
    no_ssl:     bool    = typer.Option(False, '--no-ssl', help="Use HTTP instead of HTTPS", rich_help_panel="Spray Target"),
    no_wait:    bool    = typer.Option(False, '--no-wait', help="Exit when spray completes instead of waiting for new users/passwords", rich_help_panel="Spray Behavior"),
    poll_timeout: str   = typer.Option(None, '--poll-timeout', help="Max wait time for new users/passwords (e.g., 1h). Default unit: minutes", rich_help_panel="Spray Behavior"),
    resume:     str     = typer.Option(None, '-r', '--resume', help="Resume from a previous output file (loads completed attempts and appends new results)", rich_help_panel="Spray Behavior"),
    skip_guessed: bool = typer.Option(False, '-s', '--skip-guessed', help="Stop spraying users after a successful login is detected (requires --analyze)", rich_help_panel="Spray Behavior"),
    delay:      str     = typer.Option(None, '-D', '--delay', help="Fixed delay between requests (e.g., 2s, 1m). Default unit: seconds", rich_help_panel="Spray Behavior"),
    debug:      bool    = typer.Option(False, '--debug', help="Enable debug logging (overrides --quiet)")):


    init_logger(debug)

    #
    #  Suppress SSL warnings
    #
    try:
        import requests.packages.urllib3

        requests.packages.urllib3.disable_warnings()
    except Exception:
        pass

    #
    # Read username list and password [list]
    #
    try:
        logger.debug(f"Reading usernames from file {usernames}")
        user_list = Path(usernames).read_text().splitlines()
    except Exception as e:
        logger.error(f"Failed to read usernames from {usernames}: {e}")
        exit()
    
    if Path(passwords).exists():
        logger.debug(f"Password list detected, reading passwords from file {passwords}")
        password_list = Path(passwords).read_text().splitlines()
    else:
        logger.debug("Single password detected")
        password_list = [passwords]
        
        #
        # Set to None so it's not checked for file changes
        #
        passwords = None

    #
    # Host arg is required for all modules except Office365
    #
    if module != Target.office365 and host is None:
        logger.error("Hostname (-H) of target (mail.targetdomain.com) is required for all modules execept Office365")
        exit()
    
    elif module == Target.office365 and host is None:
        #
        # Set host to Office365 for the logfile name
        #
        host = "Office365"  
    


    # 
    # Check that interval and attempt args are supplied together
    #
    if (attempts is None) ^ (interval is None):
        logger.error("[!] Number of login attempts per interval (-a) and interval (-i) must be supplied together")
        exit()

    #
    # Parse time values
    #
    timeout_seconds = parse_time(timeout, default_unit="s")
    interval_seconds = parse_time(interval, default_unit="m") if interval else None
    poll_timeout_seconds = parse_time(poll_timeout, default_unit="m") if poll_timeout else None
    jitter_seconds = parse_time(jitter, default_unit="s") if jitter else None
    jitter_min_seconds = parse_time(jitter_min, default_unit="s") if jitter_min else 0.0
    delay_seconds = parse_time(delay, default_unit="s") if delay else None

    #
    # Delay and jitter are mutually exclusive
    #
    if delay_seconds is not None and jitter_seconds is not None:
        logger.error("--delay and --jitter are mutually exclusive. Use one or the other.")
        exit()

    #
    # jitter-min requires jitter
    #
    if jitter_min and not jitter:
        logger.error("--jitter-min requires --jitter to be set")
        exit()

    #
    # Validate that jitter is greater than or equal to jitter_min
    #
    if jitter_seconds is not None and jitter_min_seconds > jitter_seconds:
        logger.error(f"--jitter ({jitter}) must be greater than or equal to --jitter-min ({jitter_min})")
        exit()

    #
    # Fireprox, port and timeout are ignored when spraying over SMB
    #
    if module == Target.smb and (timeout_seconds != 5 or fireprox is not None or port != 443):
        logger.warning("Fireprox (-f), port (-P) and timeout (-t) are incompatible when spraying over SMB")

    #
    # Path flag must be set for NTLM authentication module
    #
    if module == Target.ntlm and path is None:
        logger.error("Must set --path to use the NTLM authentication module")
        exit()

    #
    # Notify flag requires a webhook
    #
    if notify is not None and webhook is None:
        logger.error("Must specify a Webhook URL when the notify flag is used.")
        exit()

    #
    # Pause only takes effect during analysis, which can only happen inbetween intervals
    #
    if pause and not (analyze and interval is not None):
        logger.warning("--pause flag can only takes effect when analyze/interval options are set")

    #
    # Skip guessed requires analyze to detect successful logins
    #
    if skip_guessed and not analyze:
        logger.error("--skip-guessed requires --analyze to detect successful logins")
        exit()

    #
    # Resume file must exist if specified
    #
    if resume is not None and not Path(resume).exists():
        logger.error(f"Resume file not found: {resume}")
        exit()

    #
    # Warn user if interval and attempts are not supplied and password list is provided
    #
    if interval is None and attempts is None and len(password_list) > 1:
        logger.warning("You have not provided spray attempts/interval. This may lead to account lockouts!")
        print()

        Confirm.ask(
            "[yellow]Press enter to continue anyways",
            default=True,
            show_choices=False,
            show_default=False,
        )
        print()

    #
    # Finally validated, lets spray
    #
    spraycharles = Spraycharles(
        user_list=user_list,
        user_file=usernames,
        password_list=password_list,
        password_file=passwords,
        host=host,
        module=module,
        path=path,
        output=output,
        attempts=attempts,
        interval=interval_seconds,
        equal=equal,
        timeout=timeout_seconds,
        port=port,
        fireprox=fireprox,
        domain=domain,
        analyze=analyze,
        jitter=jitter_seconds,
        jitter_min=jitter_min_seconds,
        notify=notify,
        webhook=webhook,
        pause=pause,
        no_ssl=no_ssl,
        debug=debug,
        quiet=quiet,
        no_wait=no_wait,
        poll_timeout=poll_timeout_seconds,
        resume=resume,
        skip_guessed=skip_guessed,
        delay=delay_seconds
    )

    spraycharles.initialize_module()
    console.print(ascii())
    spraycharles.pre_spray_info()
    spraycharles.spray()