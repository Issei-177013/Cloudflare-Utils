# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/)
and this project adheres to [Semantic Versioning](https://semver.org/).

---

## [2.5.0-dev.20250731.2+cf-Rotate] - 2025-07-31

### Fixed
- **Rotate IPs Between Records**: Fixed a bug that caused a `TypeError` when confirming the IP rotation. The menu was calling itself recursively instead of calling the actual rotation function.

---

## [2.5.0-dev.20250731.1+cf-Rotate] - 2025-07-31

### Changed
- **Rotate IPs Between Records**: Now the user can specify the rotation order and better functions name and menu.

---

## [2.5.0-dev.20250731+cf-Rotate] - 2025-07-31

### Added
- **Rotate IPs Between Records**: New tool in the "IP Rotator Tools" menu that allows shuffling the IP addresses among multiple selected DNS records within the same zone. This provides a way to rotate existing IPs without needing a predefined list.

---

## [2.4.5] - 2025-07-18

### Fixed
- Fix `install.sh`.

### Changed
- Update `README.md`.

---

## [2.4.4-dev] - 2025-07-18

### Fixed
- Fix logging issue where logs appeared at the top of menus.

---

## [2.4.3-dev] - 2025-07-18

### Changed
- Rename the CLI command from `cfutils` to `cfu`.
- Update the author information to a GitHub URL.
- Fix the version display.
- Improve the menu section names.
- Remove "List All Cloudflare Data" from the menu.

---

## [2.4.1-dev] - 2025-07-15

### Changed
- Overall change and improvement.

---

## [2.4.1-dev] - 2025-07-14

### Fixed
- Handle system `typing-extensions` package conflict during installation.
  - Detect if `python3-typing-extensions` is installed via apt.
  - Prompt user to remove it to avoid pip installation conflicts.
  - Abort installation if user refuses or removal fails.
  - Proceed with pip package installation only if no conflict remains.

---

## [2.4.0-dev] - 2025-07-14

### Changed
- Created a `src` directory to house the core application logic.
- Modularized code by breaking down `cli.py` and `config_manager.py` into smaller modules: `app.py`, `config.py`, `cloudflare_api.py`, `dns_manager.py`, `ip_rotator.py`.
- Refactored code to use the new modular structure.
- Implemented dependency injection where appropriate.
- Added logging to all modules.
- Updated entry point to `cf-utils.py`, calling main from `src/app.py`.
- Updated `install.sh` to reflect new structure.
- Unable to add unit tests due to file system error preventing `tests` directory creation.

---

## [2.3.0-dev] - Unreleased

### Added
- **Record Management in CLI**:
  - Edit Record: modify IPs, record type, proxied status, rotation interval.
  - Delete Record: remove DNS records from config.
- **Enhanced IP Rotation Logic**:
  - Avoid rotating to the same IP if alternatives exist.

### Changed
- Consolidated `rotate_from_config.py` into `config_manager.py`.
- Updated CLI menu options and documentation.

### Fixed
- `list_all` in CLI now correctly shows rotation interval.

---

## [2.2.9-dev] - Unreleased

### Fixed
- Add `--break-system-packages` to pip install.

---

## [2.2.8-dev] - Unreleased

### Changed
- Update cron job frequency to run every minute.

---

## [2.2.7-dev] - Unreleased

### Changed
- Recommend using Cloudflare API Tokens instead of Global API Keys.

---

## [2.2.6-dev] - Unreleased

### Fixed
- Use dynamically constructed absolute paths for `CONFIG_PATH` and `ROTATION_STATUS_PATH`.

---

## [2.2.5-dev] - Unreleased

### Fixed
- Fix circular import in `config_manager.py`.
- Restore missing configuration functions and constants.

---

## [2.2.4-dev] - Unreleased

### Added
- Graceful handling of `KeyboardInterrupt` in `cli.py` and `config_manager.py`.

---

## [2.2.3-dev] - Unreleased

### Fixed
- Fix `TypeError` when listing DNS records by converting paginated response to a list.

---

## [2.2.2-dev] - Unreleased

### Added
- Show existing DNS records when adding a new record.
- Allow selecting from existing record names or entering manually.

### Changed
- Improve UX and reduce typos during record addition.

---

## [2.2.1-dev] - Unreleased

### Changed
- Enforce minimum rotation interval of 5 minutes in CLI.
- Update cron frequency accordingly.
- Add support for custom rotation intervals per record.
- Document new behavior and cron limitations.

---

## [2.2.0-dev] - Unreleased

### Added
- Support for per-record custom rotation interval (`rotation_interval_minutes`).
- Persistent next-rotation tracking in `rotation_status.json`.
- CLI support for custom intervals.

### Changed
- Update documentation to reflect the above.

---

## [2.1.2-dev] - Unreleased

### Fixed
- Clear screen and display art, author, version in CLI.

---

## [2.1.1-dev] - Unreleased

### Fixed
- Remove unnecessary prompts during CLI setup.

---

## [2.1.0-dev] - Unreleased

### Added
- Interactive CLI for managing accounts, zones, and records.
- Global `cfutils` command via `install.sh`.

### Changed
- Improve CLI UX and `list_all` readability.
- Switch config from `.env` to `configs.json`.
- Rotation script now reads from `configs.json`.

### Fixed
- N/A

### Removed
- N/A

---

## [2.0.0-dev] - Unreleased

### Added
- Multi-account support.
- Multi-zone and multi-record support.
- `cli.py`, `config_manager.py`, `version.py`.

### Changed
- Switch from `.env` to `configs.json`.
- Update `install.sh` and `run.sh`.

---

## [1.0.0] - 2025-07-06

### Added
- Initial version with:
  - A-record IP rotation.
  - `.env` for config.
  - Cron-based scheduling.
  - Bash installer.
