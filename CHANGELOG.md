# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/)
and this project adheres to [Semantic Versioning](https://semver.org/).

## [2.4.5] - 7/18/2025
- Update readme

## [2.4.4-dev] - 7/18/2025
- Fix logging issue where logs appeared at the top of menus

## [2.4.3-dev] - 7/18/2025
- rename the CLI command from `cfutils` to `cfu`.
- update the author information to a GitHub URL.
- fix the version display.
- improve the menu section names.
- remove 'List All Cloudflare Data' from the menu.

## [2.4.1-dev] - 7/15/2025
- Overall change and improvement.


## [2.4.1-dev] - 7/14/2025
### Fixed
-handle system typing-extensions package conflict during installation
  - Detect if 'python3-typing-extensions' is installed via apt
  - Prompt user to remove it to avoid pip installation conflicts
  - Abort installation if user refuses or removal fails
  - Proceed with pip package installation only if no conflict remains
This prevents pip errors when upgrading typing-extensions and improves install reliability.

## [2.4.0-dev] - 7/14/2025
### Changed
- I created a `src` directory to house the core application logic.
- I modularized the code by breaking down `cli.py` and `config_manager.py` into smaller, more focused modules: `app.py`, `config.py`, `cloudflare_api.py`, `dns_manager.py`, and `ip_rotator.py`.
- I moved the code from `config_manager.py` and `cli.py` to the new modules.
- I refactored the code to use the new modular structure, including updating imports and function calls.
- I implemented dependency injection where appropriate.
- I added logging to all modules.
- I updated the main entry point to `cf-utils.py` and updated it to call the main function in `src/app.py`.
- I updated the `install.sh` script to reflect the new file structure.
- I was unable to add unit tests due to a persistent file system error that prevented me from creating files in the `tests` directory.

## [2.3.0-dev] - Unreleased
### Added
- **Record Management in CLI**:
  - Added "Edit Record" functionality to the CLI (`cli.py`) allowing modification of IPs, record type, proxied status, and rotation interval.
  - Added "Delete Record" functionality to the CLI (`cli.py`) allowing removal of records from the local configuration.
- **Enhanced IP Rotation Logic**:
  - Modified the IP rotation logic in `config_manager.py` (`rotate_ip` function) to select a different IP if the standard rotation choice results in the same IP that is currently live on Cloudflare, provided other distinct IPs are available in the list. This prevents re-using the same IP immediately if alternatives exist.

### Changed
- **Consolidated Rotation Script**:
  - Removed `rotate_from_config.py` and consolidated its IP rotation logic into `config_manager.py`.
  - Updated `install.sh`, `README.md`, and `CHANGELOG.md` to refer to `config_manager.py` for rotation tasks.
- Updated CLI menu options to reflect new Edit/Delete record features.

### Fixed
- Ensured `list_all` in `cli.py` correctly displays the rotation interval (was already functional).

## [2.2.9-dev] - Unreleased
### Fix
- Add --break-system-packages to pip install

## [2.2.8-dev] - Unreleased
### Changed
- Update cron job frequency to run every minute

## [2.2.7-dev] - Unreleased
### Changed
- Updated CLI and README to recommend using Cloudflare API Tokens instead of Global API Keys for enhanced security.

## [2.2.6-dev] - Unreleased
### Fixed
- Changed `CONFIG_PATH` and `ROTATION_STATUS_PATH` in `config_manager.py` to use dynamically constructed absolute paths. This ensures configuration files (`configs.json`, `rotation_status.json`) are correctly located within the application's installation directory (e.g., `/opt/Cloudflare-Utils/`) regardless of the script's calling directory.

## [2.2.5-dev] - Unreleased
### Fixed
- Resolved a circular import error in `config_manager.py` that prevented `cfutils` from starting.
- Restored missing core configuration functions (`load_config`, `save_config`, `find_account`, `find_zone`, `find_record`) and `CONFIG_PATH` constant to `config_manager.py`. This also resolves a `NameError` when `config_manager.py` is run directly or when `run_rotation` calls `load_config`.

## [2.2.4-dev] - Unreleased
### Added
- Graceful handling of `KeyboardInterrupt` (Ctrl+C) in `cli.py` and `config_manager.py` (formerly `rotate_from_config.py`) to prevent tracebacks and allow clean exit.

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
- DNS rotation script (`config_manager.py`, formerly `rotate_from_config.py`) now reads from `configs.json`.

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
- `config_manager.py` (formerly `rotate_from_config.py`) to rotate IPs for all configured records.
- `version.py` to store project version.

### Changed
- Configuration moved from `.env` to `configs.json` to support multiple accounts/zones/records.
- Installation script (`install.sh`) updated to handle new structure and `configs.json`.
- `run.sh` now executes `config_manager.py`.

## [1.0.0] - 2025-07-06
### Added
- Initial version of Cloudflare-Utils with support for rotating a single A record using a list of IPs.
- `.env` file support for credentials and IP list.
- Scheduled rotation via `cron`.
- Bash installer script with interactive prompts.