# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/)
and this project adheres to [Semantic Versioning](https://semver.org/).

---

## [2.6.4] - 2025-08-02

### 🚀 Added
- **New Rotation Engine**: Global IP pool rotation for multiple DNS records.
- **`rotate_ips_with_pool` Function**: Replaces old `rotate_ips_between_records`; supports coordinated multi-record rotation.
- **Shared IP Pool Support**: Each rotation group can now share an IP pool.
- **Persistent Global Index**: Rotation index is now stored and restored from `.cfutils-state.json`.

### 🛠 Changed
- Refactored `run_rotation()` to use the new global rotation logic.
- Updated configuration manager to store `rotation_index` as a global value.
- Extended CLI interface:
  - `add_rotation_group_menu` and `edit_rotation_group_menu` now allow IP pool configuration.
- Updated display: `list_rotation_groups()` shows shared IP pool in CLI table.

### 🐛 Fixed
- Fixed rotation index bug where order was not consistent across runs.
- Fixed CLI crashes when record or IP list exceeded display width.
- Fixed UI bugs caused by legacy rotation logic in config updates.

### 📚 Docs
- Updated `README.md` with new usage instructions and updated example.
- Clarified cron setup recommendation for 1-minute rotation interval.

---

This release improves flexibility and reliability of the rotation system by enabling coordinated rotation across multiple DNS records using a single IP pool. It sets the foundation for intelligent bandwidth-aware rotation in upcoming versions.

## [2.6.4-dev] - 2025-08-01

### Fixed
- **IP Rotation Logic**: Corrected the multi-record IP rotation logic to increment the rotation index instead of decrementing it, ensuring the IP window slides forward as expected. A unit test has been added to verify this behavior.
- **Documentation Accuracy**: The `README.md` has been updated to accurately reflect that the cron job runs every minute.
- The table view for "Rotate Based on a List of IPs (Multi-Records)" and other lists would break when the "Records" or "IP Pool" columns contained a large number of items. This has been fixed by summarizing long lists to show the first and last items.

## [2.6.3-dev] - 2025-08-01

### Fixed

- The table view for "Rotate Based on a List of IPs (Multi-Records)" and other lists would break when the "Records" or "IP Pool" columns contained a large number of items. This has been fixed by summarizing long lists to show the first and last items.

## [2.6.2-dev] - 2025-08-01

### Changed

- Renamed the IP rotation tools for clarity and consistency across the application.
  - "Manage Multi-Records Global Rotations" is now "Rotate Based on a List of IPs (Multi-Records)".
  - "Rotate Based on a List of IPs" is now "Rotate Based on a List of IPs (Single-Record)".
- Renamed the corresponding functions in `src/app.py` to match the new tool names.
- Updated `README.md` to reflect the new tool names.

## [2.6.1-dev2] - 2025-08-01

### Fixed

- Modified `src/logger.py` to only redirect `sys.stdout` and `sys.stderr` when the `LOG_TO_FILE` environment variable is set to `'true'`.
- Updated `install.sh` to set `LOG_TO_FILE=true` in the `run.sh` script that is executed by cron.

This ensures that the non-interactive cron job continues to have its output captured in the log files, while the interactive `cfu` command functions correctly by writing to the console.

## [2.6.1-dev1] - 2025-08-01

### Changed

- Replaced the simple file redirection for logging with a robust, application-level logging system using Python's `logging` module.
- Configured a `TimedRotatingFileHandler` to create a new log file daily, store it in a `logs/` directory, and automatically delete logs older than 7 days.
- Redirected `sys.stdout` and `sys.stderr` to the logger to ensure all script output, including uncaught exceptions, is captured.
- Updated the `install.sh` script to remove the old `log_file.log` and to call the application without shell-level output redirection.
- Updated `README.md` to reflect the new logging mechanism and location.

## [2.6.0-dev3] - 2025-08-01

### Removed

- remove timestamp logging from run script

## [2.6.0-dev2] - 2025-08-01

### Added

- **🌍 Rotate Based on a List of IPs (Multi-Records) Management**: A full management menu for the Multi-Records global rotation feature, including the ability to add, edit, delete, and view logs for global rotation configurations.
  - The feature is now integrated with the automated rotation system, allowing for scheduled rotations.

## [2.6.0-dev] - 2025-08-01

### Added

- **🌍 Rotate Based on a List of IPs (Multi-Records)**: A new tool in the "IP Rotator Tools" menu that allows rotating a shared list of IPs across multiple DNS records in a synchronized, round-robin manner.
  - The rotation state (index) is persisted in a new `.cfutils-state.json` file, ensuring that the rotation continues from where it left off on each run.

## [2.5.0] - 2025-07-31

### Added

- **🔁 Rotate IPs Between Records Tool**: A major new feature in the "IP Rotator Tools" menu.
  - Allows rotating the current IPs among multiple A/AAAA DNS records within the same zone — no need for a predefined list.
  - Perfect for scenarios where you're cycling live IPs (e.g. load balancing, traffic obfuscation).
- **🗓 Scheduled Rotation Groups**:
  - Create groups of records and schedule automatic IP rotations.
  - Includes a full CLI management UI for creating, editing, deleting groups, and viewing logs.
- **📐 Custom Rotation Order**:
  - Manual rotations now allow specifying the exact order of rotation for better control.

### Changed

- Improved menu structure and function names for better clarity and extensibility.
- Rotation command now supports user-defined order of how IPs are shifted between records.

### Fixed

- ✅ Fixed a `TypeError` caused by recursive confirmation menu calls instead of executing the rotation logic.
- ✅ Fixed another `TypeError` when fetching records from the Cloudflare API due to paginated responses not being properly converted to lists.

## [2.5.0-dev.20250731.4+cf-Rotate] - 2025-07-31

### Fixed

- Fixes TypeError when rotating IPs between records due to a paginated API response not being converted to a list.

## [2.5.0-dev.20250731.3+cf-Rotate] - 2025-07-31

### Added

- **Scheduled Rotation for Record Groups**: The "Rotate IPs Between Records" feature now supports scheduled execution. This includes a new management menu for creating, editing, and deleting scheduled rotation groups, as well as viewing logs.

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
- Multi-zone and Multi-Records support.
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
