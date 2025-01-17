# Changelog

## [v1.0.8] - 4/26/2022
### Fixed
- All spraying modules were broken after the addition of the list submodule. Changed list to modules to fix issue.

## [v1.0.7] - 4/21/2022
### Added
- Output for `gen` submodule

### Changed
- Versioning to X.X.X

## [v1.0.6] - 4/17/2022
### Added
- Made spraycharles a package usable as a CLI utility. (spraycharles, sc)
- Started supported test harnesses (pytest) to project for later use
- Started prepping spraycharles for publishing to the PyPi package repository

### Changed
- Converted all included scripts as submodules to spraycharles
- All included scripts can no longer be called as standalone tools
- Started storing logfiles and csv output in user home directory
- Moved Dockerfile and list_elements.json to extras directory
- Updated Dockerfile
- Updated README.md to reflect changes

## [v1.0.5] - 4/13/2022
### Changed
- Improved handling of NTSTATUS values returned by SMB logins
- Analysis of SMB logins

## [v1.0.4] - 4/8/2022
### Changed
- Fixed bug related to spray modules inheriting methods from BaseHttpTarget parent that refereced vars not set in formdata

## [v1.0.3] - 3/29/2022
### Added
- Okta target module (needs testing)
### Changed
- In Office365 module: spelling fixes, removed "WindowsPowerShell" for user-agent string and minor edits

## [v1.0.2] - 3/27/2022
### Added
- Added a base class for HTTP targets so that most target modules can inherit classes to print output, headers, etc
### Changed
- Refactored spraycharles.py to utilize a class
- Fixed reference to port CLI flag
- Fixed http_analyze function to also send notifications
- Made the ADFS, Ciscosslvpn, Citrix, Ntlm, Owa and Sonicwall targets subclasses of BaseHttpTarget to minimize code reuse

## [v1.0.1] - 3/26/2022
### Added
- Utilize the rich library for terminal output
- Progress bar during spray attempt
- Pre-commit hooks for formatting
### Changed
- Code reformatted using black library
- Internal variable names in spraycharles.py to allow config file variable names to match CLI flag names
### Removed
- OpenVPN module

## [v1.0.0] - 3/9/2022
### Added
- Support for Slack, Teams and Discord notitications via webhooks when a successful spray hit is identified
- `--notify` and `--webhook` arguments to support notifications
- `--path` argument to support the NTLM module
- `ntlm_challenger.py`
- `utils` folder and added spraycharles' auxiliary resources there
- `--pause` flag to optionally stop spraying and ask for confirmation to continue after a hit has been identified
- Changelog
- Versioning
### Changed
- Switched from Argpase to Click in both `analyze.py` and `spraycharles.py`
- Updated `list_elements.json` for 2022
- Refactored EWS module to be a generic NTLM over HTTP module
