<p align="center">
  <p align="center">
    <img height=250 src=.resources/spraycharles.jpeg>
  </p>

  <h1 align="center">Spraycharles</h1>
  
  <p align="center">
    <i>
      hey, yo I'm feeling like spraycharles - Chiddy Bang
    </i>
  </p>
  <span align="center">

    
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![PyPi](https://img.shields.io/pypi/v/spraycharles?style=for-the-badge)
    
  </span>
</p>

Low and slow password spraying tool, designed to spray on an interval over a long period of time. 

Includes spraying plugins for `Office365`, `OWA`, `EWS`, `Okta`, `ADFS`, `Cisco SSL VPN`, `Citrix Netscaler`, `Sonciwall`, `NTLM over HTTP`, and `SMB`.

Associated [blog post](https://www.sprocketsecurity.com/blog/how-to-bypass-mfa-all-day) by [@sprocket_ed](https://twitter.com/sprocket_ed) covering NTLM over HTTP, Exchange Web Services and Spraycharles.

### What is this tool?
Spraycharles is a relatively simple password sprayer, designed at a time when there weren't many publicly available tools enabling password spraying to be a non-manual process over the course of a penetration test. Maybe the best feature of Spraycharles is the ability to setup a long running spray using `-a/--attempts` and `-i/--interval`, and let it run over the couse of several days, while periodically checking on it. If you have a one-off service or something unique to spray, it's also very easy to template a new module and start spraying.

### What is this tool not?
Spraycharles was not initially designed with modern authentication/cloud providers in mind. If you're looking for more advanced features, you may want to check out tools such as [CredMaster](https://github.com/knavesec/CredMaster) or [TeamFiltration](https://github.com/Flangvik/TeamFiltration) Spraycharles was not designed to be _fast_ - it is single threaded and geared towards more of a volume/time approach.

## Install
Spraycharles can be installed with `pip3 install spraycharles` or by cloning this repository and running `pip3 install .`

> [!TIP]
> This will register the `spraycharles`, and `sc` for short, aliases in your path. Log and output files are stored in `~/.spraycharles`. An alternative output location can be specified with a CLI flag.

### Using Docker
Execute the following commands to build the Spraycharles Docker container:

```bash
git clone https://github.com/Tw1sm/spraycharles
cd spraycharles/extras
docker build . -t spraycharles
```

Execute the following command to use the Spraycharles Docker container:

```bash
docker run -it -v ~/.spraycharles:/root/.spraycharles spraycharles -h
```

You may need to specify additional volumes based on where username a password lists are being stored.

### Shell Completion
Spraycharles supports tab completion for bash, zsh, fish, and powershell:

```bash
# Auto-detect shell and install
spraycharles completion install

# Or specify shell explicitly
spraycharles completion install zsh

# Show completion script for manual installation
spraycharles completion show bash
```

## Usage
The `spray` subcommand:
```
 Usage: spraycharles spray [OPTIONS] COMMAND [ARGS]...

 Low and slow password spraying

╭─ Options ─────────────────────────────────────────────────────────────────────────────╮
│ --debug                 Enable debug logging (overrides --quiet)                      │
│ --config          TEXT  Configuration file.                                           │
│ --help    -h            Show this message and exit.                                   │
╰───────────────────────────────────────────────────────────────────────────────────────╯
╭─ User/Pass Config ────────────────────────────────────────────────────────────────────╮
│ *  --usernames  -u      TEXT  Filepath of the usernames list [default: None]          │
│                               [required]                                              │
│ *  --passwords  -p      TEXT  Single password to spray or filepath of the passwords   │
│                               list                                                    │
│                               [default: None]                                         │
│                               [required]                                              │
│    --equal      -e            Does 1 spray for each user where password = username    │
╰───────────────────────────────────────────────────────────────────────────────────────╯
╭─ Spray Target ────────────────────────────────────────────────────────────────────────╮
│    --host      -H      TEXT                           Host to password spray (ip or   │
│                                                       hostname). Can by anything when │
│                                                       using Office365 module - only   │
│                                                       used for logfile name           │
│                                                       [default: None]                 │
│ *  --module    -m      [ADFS|CiscoSSLVPN|Citrix|NTLM  Module corresponding to target  │
│                        |Office365|Okta|OWA|SMB|Sonic  host                            │
│                        wall]                          [default: None]                 │
│                                                       [required]                      │
│    --path              TEXT                           NTLM authentication endpoint    │
│                                                       (i.e., rpc or ews)              │
│                                                       [default: None]                 │
│    --port      -P      INTEGER                        Port to connect to on the       │
│                                                       specified host                  │
│                                                       [default: 443]                  │
│    --fireprox  -f      TEXT                           URL of desired fireprox         │
│                                                       interface                       │
│                                                       [default: None]                 │
│    --domain    -d      TEXT                           HTTP - Prepend DOMAIN\ to       │
│                                                       usernames; SMB - Supply domain  │
│                                                       for smb connection              │
│                                                       [default: None]                 │
│    --no-ssl                                           Use HTTP instead of HTTPS       │
╰───────────────────────────────────────────────────────────────────────────────────────╯
╭─ Output ──────────────────────────────────────────────────────────────────────────────╮
│ --output   -o      TEXT  Name and path of result output file [default: None]          │
│ --quiet                  Will not log each login attempt to the console               │
│ --analyze                Run the results analyzer after each spray interval (Early    │
│                          false positives are more likely)                             │
╰───────────────────────────────────────────────────────────────────────────────────────╯
╭─ Spray Behavior ──────────────────────────────────────────────────────────────────────╮
│ --attempts      -a      INTEGER  Number of logins submissions per interval (for each  │
│                                  user) [default: None]                                │
│ --interval      -i      TEXT     Time between login intervals (e.g., 30m, 1h).        │
│                                  Default unit: minutes [default: None]                │
│ --timeout       -t      TEXT     Web request timeout (e.g., 5s, 10s). Default unit:   │
│                                  seconds [default: 5]                                 │
│ --jitter        -j      TEXT     Max jitter time between requests (e.g., 5s, 1m).     │
│                                  Default unit: seconds [default: None]                │
│ --jitter-min    -jm     TEXT     Min jitter time between requests. Default unit:      │
│                                  seconds [default: None]                              │
│ --delay         -D      TEXT     Fixed delay between requests (e.g., 2s, 1m).         │
│                                  Default unit: seconds [default: None]                │
│ --pause                          Pause the spray between intervals if a new           │
│                                  potentially successful login was found               │
│ --no-wait                        Exit when spray completes instead of waiting for     │
│                                  new users/passwords                                  │
│ --poll-timeout          TEXT     Max wait time for new users/passwords (e.g., 1h).    │
│                                  Default unit: minutes [default: None]                │
│ --resume        -r      TEXT     Resume from a previous output file (loads completed  │
│                                  attempts and appends new results) [default: None]    │
│ --skip-guessed  -s               Stop spraying users after successful login detected  │
│                                  (requires --analyze)                                 │
╰───────────────────────────────────────────────────────────────────────────────────────╯
╭─ Notifications ───────────────────────────────────────────────────────────────────────╮
│ --notify   -n      [Slack|Teams|Discord]  Enable notifications for Slack, Teams or    │
│                                           Discord                                     │
│                                           [default: None]                             │
│ --webhook  -w      TEXT                   Webhook used for specified notification     │
│                                           module                                      │
│                                           [default: None]                             │
╰───────────────────────────────────────────────────────────────────────────────────────╯
```

### Config File
Due to the amount of CLI flags often used, an alternative is to populate command line parameters from a yaml file using the `--config` flag. Additionally, each time you use Spraycharles, your CLI options will be written to a yaml file (`last-config.yaml`) in the current directory for easy modification and reuse.

### Notifications
Spraycharles can send notifications to Discord, Slack and Microsoft Teams for the following events:
- Potentially successful login attempts
- Spray queue empty (waiting for new users/passwords)
- Spray complete (when using `--no-wait`)
- Consecutive timeout warnings and stops

You can specify notification settings using the configuration file:

```yaml
notify: Slack
webhook: https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX
```

Notifications include the targeted hostname, useful when spraying multiple targets.

### Updating Username/Password Files
You can modify username and password files while the spray is running. Spraycharles uses a work queue that tracks completed attempts, so:
- **New users** are automatically sprayed with all passwords (including previously-sprayed ones)
- **New passwords** are automatically sprayed against all users
- Completed attempts are never repeated, even across restarts with `--resume`

### Resume and Polling
By default, when the spray queue is empty, Spraycharles waits for new users/passwords to be added to the input files. Use `--no-wait` to exit immediately when complete.

To resume a previous spray session:
```bash
spraycharles spray --resume ~/.spraycharles/out/target_20241205-123456.json -u users.txt -p passwords.txt -m Office365
```

The output file path is logged at startup for easy reference.

### Timeout Handling
When 5 consecutive timeouts occur, Spraycharles will:
1. Send a webhook notification (if configured) and pause for 5 minutes
2. If timeouts continue, pause for 10 minutes
3. If timeouts persist, stop and wait for user confirmation to continue

### Skip Guessed Users
Use `-s/--skip-guessed` with `-A/--analyze` to automatically stop spraying users after a successful login is detected. This prevents unnecessary spraying against accounts you've already guessed and reduces the risk of triggering lockouts.

```bash
spraycharles spray -u users.txt -p passwords.txt -m Office365 -A -s -a 1 -i 60
```

### Time Units
Time-based flags support flexible time specifications with units:
- `s` - seconds (e.g., `5s`, `2.5s`)
- `m` - minutes (e.g., `30m`, `1.5m`)
- `h` - hours (e.g., `1h`, `0.5h`)
- `d` - days (e.g., `1d`)

Plain numbers use flag-specific defaults for backwards compatibility:
- `--interval` and `--poll-timeout` default to minutes
- `--timeout`, `--jitter`, `--jitter-min`, and `--delay` default to seconds

Examples:
```bash
# 30 second jitter, 1 hour interval
spraycharles spray -u users.txt -p passwords.txt -m Office365 -j 30s -a 1 -i 1h

# Fixed 2 second delay between requests
spraycharles spray -u users.txt -p passwords.txt -m Office365 -D 2s -a 1 -i 30m

# Random jitter between 1 and 5 seconds
spraycharles spray -u users.txt -p passwords.txt -m Office365 -jm 1s -j 5s -a 1 -i 30m
```

## Utilities
Spraycharles is packaged with some additional utilities to assist with spraying efforts. Full list of Spraycharles modules:
```
 Usage: spraycharles [OPTIONS] COMMAND [ARGS]...

╭─ Options ─────────────────────────────────────────────────────────────────────────────╮
│ --help  -h        Show this message and exit.                                         │
╰───────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ────────────────────────────────────────────────────────────────────────────╮
│ analyze      Analyze Spraycharles output files for potential spray hits               │
│ completion   Shell completion for bash, zsh, fish, and powershell                     │
│ gen          Generate custom password lists from JSON file                            │
│ modules      List spraying modules                                                    │
│ parse        Parse NTLM over HTTP and SMB endpoints to collect domain information     │
│ spray        Low and slow password spraying                                           │
╰───────────────────────────────────────────────────────────────────────────────────────╯
```

### Generating Custom Spray Lists
The Spraycharles "gen" subcommand will generate a password list based off the specifications provided in extras/list_elements.json

```bash
spraycharles gen extras/list_elements.json custom_passwords.txt
```

### Extracting Domain from NTLM over HTTP and SMB
The Spraycharles parse subcommand will extract the internal domain from both NTLM over HTTP and SMB services using a command similar to the one listed below.

```bash
spraycharles parse https://example.com/ews
spraycharles parse smb://host.domain.local
```

### Analyzing Result Files
The `analyze` submodule can read your output JSON objects and determine response lengths that are statistically relevant. With enough data, it should be able to pull successful logins out of your results file. This is not the only way to determine successful logins, depending on your target site, and I would still recommend checking the data yourself to be sure nothing is missed. For SMB, it will simply find entries with NTSTATUS codes that indicate success.

```bash
spraycharles analyze myresults.json
```

## Disclaimer
This tool is designed for use during penetration testing; usage of this tool for attacking targets without prior mutual consent is illegal. It is the end user's responsibility to obey all applicable local, state and federal laws. Developers assume no liability and are not responsible for any misuse of this program.

## Development
Spraycharles uses Poetry to manage dependencies. Install from source and setup for development with:

```bash
pip3 install poetry
git clone https://github.com/Tw1sm/spraycharles
cd spraycharles
poetry install
```

## Credits
- [@sprocket_ed](https://twitter.com/sprocket_ed) for contributing: several spray modules, many of features that make spraycharles great, and the associated blog post
- [@b17zr](https://twitter.com/b17zr) for the `ntlm_challenger.py` script, which is included in the `utils` folder
