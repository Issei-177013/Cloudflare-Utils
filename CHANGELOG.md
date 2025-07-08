# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/)
and this project adheres to [Semantic Versioning](https://semver.org/).

## [2.2.6-dev] - Unreleased
### Fixed
- Changed `CONFIG_PATH` and `ROTATION_STATUS_PATH` in `config_manager.py` to use dynamically constructed absolute paths. This ensures configuration files (`configs.json`, `rotation_status.json`) are correctly located within the application's installation directory (e.g., `/opt/Cloudflare-Utils/`) regardless of the script's calling directory.

## [2.2.5-dev] - Unreleased
### Fixed
- Resolved a circular import error in `config_manager.py` that prevented `cfutils` from starting.
- Restored missing core configuration functions (`load_config`, `save_config`, `find_account`, `find_zone`, `find_record`) and `CONFIG_PATH` constant to `config_manager.py`. This also resolves a `NameError` when `config_manager.py` is run directly or when `run_rotation` calls `load_config`.

## [2.2.4-dev] - Unreleased
### Added
- Graceful handling of `KeyboardInterrupt` (Ctrl+C) in `cli.py` and `rotate_from_config.py` to prevent tracebacks and allow clean exit.

## [2.2.3-dev] - Unreleased
### Fixed
- Fixed a `TypeError` when listing DNS records from Cloudflare by ensuring the API response (a paginated object) is converted to a list before checking its length or accessing elements.

## [2.2.2-dev] - Unreleased
### Added
- When adding a record via the CLI, existing DNS records for the selected zone are now fetched from Cloudflare and displayed.
- Users can select an existing record name from the list or choose to enter a new record name manually.
### Changed
- Improved user experience during record addition by reducing manual input and potential for typos in record names.

## [2.2.1-dev] - Unreleased
### Changed
- Enforced a minimum rotation interval of 5 minutes in the CLI for custom intervals.
- Updated `install.sh` to set the cron job frequency to every 5 minutes, ensuring timely checks for records with shorter custom intervals.
- Support for per-record custom rotation interval (`rotation_interval_minutes`) (previously part of 2.2.0-dev, now integrated here).
  - Rotation logic honors this interval, defaulting to 30 minutes if not set.
  - Next-rotation tracking is persistent in `rotation_status.json`.
  - CLI allows setting/editing custom intervals (now with 5 min minimum).
- Documentation updated to reflect minimum interval and cron frequency.

## [2.2.0-dev] - Unreleased
### Added
- Support for per-record custom rotation interval (`rotation_interval_minutes`).
- Rotation logic now honors custom intervals, defaulting to 30 minutes if not specified.
- Next-rotation tracking is persistent in `rotation_status.json`.
- CLI updated to allow setting/editing custom rotation intervals.
- Documentation updated for the new feature.

## [2.1.2-dev] - Unreleased
### Fixed
- Clear screen and display art, author, version in CLI.

## [2.1.1-dev] - Unreleased
### Fixed
- Removed unnecessary 'yes/no' confirmation prompts when adding accounts, zones, or records in the CLI.

## [2.1.0-dev] - Unreleased 
### Added
- Interactive CLI for managing Cloudflare accounts, zones, and records.
  - Replaced manual name entry for zones and records with a selection-based UI.
- `cfutils` global command created by `install.sh` to easily run the CLI.
- Confirmation prompts for critical actions in the CLI.

### Changed
- Improved overall user experience in the CLI with a more interactive menu.
- Enhanced `list_all` output in CLI for better readability (includes Zone IDs, proxied status).
- Configuration is now stored in `configs.json` instead of `.env` (change from a previous unreleased version).
- DNS rotation script `rotate_from_config.py` now reads from `configs.json`.

### Fixed
- N/A (for this version, but good to have the section)

### Removed
- N/A (for this version)

## [2.0.0-dev] - Unreleased
### Added
- Support for managing multiple Cloudflare accounts.
- Ability to configure multiple zones per account.
- Ability to configure multiple DNS records (A/CNAME) per zone.
- `cli.py` for managing configurations (accounts, zones, records).
- `config_manager.py` for handling loading/saving of `configs.json`.
- `rotate_from_config.py` to rotate IPs for all configured records.
- `version.py` to store project version.

### Changed
- Configuration moved from `.env` to `configs.json` to support multiple accounts/zones/records.
- Installation script (`install.sh`) updated to handle new structure and `configs.json`.
- `run.sh` now executes `rotate_from_config.py`.

## [1.0.0] - 2025-07-06
### Added
- Initial version of Cloudflare-Utils with support for rotating a single A record using a list of IPs.
- `.env` file support for credentials and IP list.
- Scheduled rotation via `cron`.
- Bash installer script with interactive prompts.