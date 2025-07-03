# Cloudflare Utils

Cloudflare Utils is a Python-based command-line tool designed to automate the rotation of Cloudflare DNS A and AAAA records using a predefined list of IP addresses. It can be run manually or scheduled via cron or systemd for periodic updates.

This tool is managed by `cfu-manager`, an interactive CLI for easy installation, configuration, updates, and overall management of Cloudflare-Utils instances.

## Features

-   **Easy Management with `cfu-manager`**:
    -   Interactive menu for all common operations.
    -   Simplified installation and updates.
    -   Side-by-side installation of different branches (e.g., `main`, `dev`).
    -   Configuration management (TODO).
    -   Log viewing (TODO).
    -   Scheduler management (TODO).
-   **Automated IP Rotation**: Update DNS A and AAAA records with IPs from a specified list.
-   **Flexible Configuration**: Each instance configured via its own `.env` file.
-   **Multiple Record Support**: Update multiple DNS records in a single run.
-   **IPv4/IPv6 Aware**: Correctly handles IP assignment for A (IPv4) and AAAA (IPv6) records.
-   **Isolated Virtual Environments**: Each instance uses its own Python virtual environment.
-   **Choice of Scheduler**: Interactive installer (via `cfu-manager` or initial setup) allows choosing between cron and systemd.
-   **Logging**: Comprehensive logging to instance-specific files.

## Prerequisites

-   **Operating System**: Primarily tested on Ubuntu/Debian-based systems.
-   **System Packages**: `curl`, `git`, `python3` (version 3.7+), `python3-pip`, `python3-venv`.
    -   The installer script (`install.sh`) attempts to install these on Debian/Ubuntu.
-   **Cloudflare Account**:
    -   An API Token with permissions to read and edit DNS records for your zone.
    -   The Zone ID of the Cloudflare zone you wish to manage.
    -   The DNS Record Name(s) you wish to update (e.g., `example.com`, `sub.example.com`).
    -   A list of IP addresses (IPv4 and/or IPv6) to rotate through.

---

## Quick Installation (Recommended)

This one-liner command installs the `main` branch of Cloudflare-Utils and the `cfu-manager` tool:

```bash
curl -fsSL https://raw.githubusercontent.com/Issei-177013/Cloudflare-Utils/main/install.sh | sudo bash -s
```

-   This will install Cloudflare-Utils (main branch) to `/opt/Cloudflare-Utils/`.
-   It will also make the `cfu-manager` command globally available.
-   The script will prompt you for initial configuration details (API Token, Zone ID, etc.) and scheduler choice for the `main` instance.
-   If you need to pass parameters for a non-interactive setup (e.g., for automation), you can append them:
    ```bash
    curl -fsSL https://raw.githubusercontent.com/Issei-177013/Cloudflare-Utils/main/install.sh | sudo bash -s -- \
      --non-interactive --action install \
      --api-token "YOUR_CLOUDFLARE_API_TOKEN" \
      --zone-id "YOUR_CLOUDFLARE_ZONE_ID" \
      --record-name "record1.example.com" \
      --ip-addresses "1.1.1.1,::1"
    ```
    *(Note: Non-interactive installs currently default to the 'cron' scheduler within install.sh).*

After installation, manage your Cloudflare-Utils instances using `cfu-manager`.

---

## Using `cfu-manager`

`cfu-manager` is your primary tool for managing Cloudflare-Utils installations.

**Open the interactive menu:**

```bash
sudo cfu-manager menu
```
*(Run with `sudo` if `cfu-manager` needs to perform system-level operations like installing files to `/opt` or managing system schedulers).*

The menu provides options for:
-   Installing new instances (from different branches) or reinstalling existing ones.
-   Uninstalling instances.
-   Listing all installed instances.
-   Updating instances.
-   Rolling back instances to a previous version.
-   (Coming Soon) Managing configurations, logs, and schedulers.

**Direct Commands (Examples):**

You can also use `cfu-manager` with direct commands:

-   **Install a specific branch (e.g., `dev`):**
    ```bash
    sudo cfu-manager install --branch dev
    ```
    This will install the `dev` branch into `/opt/Cloudflare-Utils-dev/`. You'll be prompted for its configuration separately.

-   **List all installed instances:**
    ```bash
    sudo cfu-manager list
    ```

-   **Update an instance (e.g., `main` branch):**
    ```bash
    sudo cfu-manager update --branch main
    ```

-   **Rollback an instance (e.g., `dev` branch, 1 commit back):**
    ```bash
    sudo cfu-manager rollback --branch dev --steps 1
    ```

-   **Uninstall an instance (e.g., `dev` branch):**
    ```bash
    sudo cfu-manager uninstall --branch dev
    ```

For detailed command options, use `cfu-manager [command] --help`.

---

## Configuration

Each Cloudflare-Utils instance (e.g., `main`, `dev`) has its own configuration file located within its installation directory:
-   Main instance: `/opt/Cloudflare-Utils/.env`
-   `dev` branch instance: `/opt/Cloudflare-Utils-dev/.env`

This `.env` file stores:
*   `CLOUDFLARE_API_TOKEN`
*   `CLOUDFLARE_ZONE_ID`
*   `CLOUDFLARE_RECORD_NAME` (comma-separated FQDNs)
*   `CLOUDFLARE_IP_ADDRESSES` (comma-separated IPs)

The initial installation (via `curl ... | sudo bash -s` or `cfu-manager install`) will guide you through setting these up for the new instance.
A future version of `cfu-manager` will include a `config` command for easier editing of these files.

---

## Instance Management

### Multiple Branches

You can install multiple branches of Cloudflare-Utils side-by-side. Each will reside in its own directory:
-   `main` branch: `/opt/Cloudflare-Utils/`
-   `<branch_name>` branch: `/opt/Cloudflare-Utils-<branch_name>/` (e.g., `/opt/Cloudflare-Utils-dev/`)

Each instance has its own virtual environment, configuration, logs, and scheduler setup. Use `cfu-manager` to manage these individual instances.

### Updates

To update an instance to the latest commit of its respective branch:
```bash
sudo cfu-manager update --branch <branch_name>
```
Example: `sudo cfu-manager update --branch main`

This will:
1.  Navigate to the instance's directory (e.g., `/opt/Cloudflare-Utils/`).
2.  Run `git pull` to fetch the latest code for that branch.
3.  Re-install the package within its virtual environment to apply changes and update dependencies.
4.  (TODO) Restart its associated scheduler.

### Rollback

To revert an instance to a previous state (based on git commits):
```bash
sudo cfu-manager rollback --branch <branch_name> --steps <number_of_commits>
```
Example: `sudo cfu-manager rollback --branch dev --steps 1` (rolls back `dev` instance by one commit)

This will:
1.  Navigate to the instance's directory.
2.  Run `git reset --hard HEAD~<steps>`. **Warning: This discards local uncommitted changes in that directory.**
3.  Re-install the package within its virtual environment.
4.  (TODO) Restart its associated scheduler.

---
## Usage of an Instance

Cloudflare-Utils instances are typically run automatically by a scheduler (cron or systemd) chosen during installation.

### Manual Execution

To manually trigger an update for a specific instance:
1.  **Identify the instance's run script**:
    -   Main instance: `/opt/Cloudflare-Utils/run.sh`
    -   `dev` branch instance: `/opt/Cloudflare-Utils-dev/run.sh`
2.  **Execute the script with `sudo`**:
    ```bash
    sudo /opt/Cloudflare-Utils/run.sh  # For main instance
    # or
    sudo /opt/Cloudflare-Utils-dev/run.sh # For dev instance
    ```
    This script activates the instance's virtual environment and runs `cloudflare-utils`.
    *(A `cfu-manager run --branch <name>` command is planned for easier manual runs).*

### Scheduled Execution

The scheduler runs the instance-specific `run.sh` script periodically (default: every 30 minutes and on boot).
-   **Systemd**: Timers are named like `cloudflare-utils.timer` or `cloudflare-utils-dev.timer`.
    -   Check status: `sudo systemctl status cloudflare-utils-<branch_name>.timer`
    -   View logs: `sudo journalctl -u cloudflare-utils-<branch_name>.service` (use `main` for the default instance, or the sanitized branch name).
-   **Cron**: Jobs are added to the root user's crontab (by default, when using `sudo` for install).
    -   View cron jobs: `sudo crontab -l | grep Cloudflare-Utils`

### Logs

Each instance logs its activity to `log_file.log` within its directory:
-   Main instance: `/opt/Cloudflare-Utils/log_file.log`
-   `dev` branch instance: `/opt/Cloudflare-Utils-dev/log_file.log`
*(A `cfu-manager logs --branch <name>` command is planned for easier log viewing).*

---

## Troubleshooting

-   **`cfu-manager: command not found`**:
    -   Ensure the initial installation (`curl ... | sudo bash -s`) completed successfully. This step creates the symlink for `cfu-manager` in `/usr/local/bin/`.
    -   Check if `/usr/local/bin` is in your system's `PATH`.
    -   The `cfu-manager` script itself is located inside the virtual environment of the *first* Cloudflare-Utils instance installed (usually `/opt/Cloudflare-Utils/.venv/bin/cfu-manager`).

-   **Permission Issues**:
    -   Most `cfu-manager` commands that modify system files (in `/opt/`, scheduler configs) or instance files owned by another user may require `sudo`.
    -   If `git pull` or `pip install` fails within `cfu-manager update/rollback` due to permissions, ensure the files in `/opt/Cloudflare-Utils-<branch>` are owned by a user `cfu-manager` can operate as (or run `cfu-manager` with `sudo`). The `install.sh` script attempts to set user ownership correctly during cloning.

-   **Python Version Errors during `install.sh`**:
    -   The script requires Python 3.7+. Ensure you have a compatible `python3` command available.

-   **`InquirerPy` or other dependency issues for `cfu-manager menu`**:
    -   The interactive menu requires `inquirerpy` and its dependencies (`rich`, `typer`). These are installed as optional dependencies when `cloudflare-utils[manager]` is installed by `install.sh`.
    -   If they are missing, you might need to manually install them into the venv where `cfu-manager` resides:
        ```bash
        # Example for the default main instance:
        sudo /opt/Cloudflare-Utils/.venv/bin/pip install "typer[all]" rich inquirerpy
        ```
    Or reinstall the main instance, ensuring `cfu-manager` is properly set up.

---

## Contributing

Contributions are welcome! Please follow these steps:
1.  Fork the repository.
2.  Create a new branch (`git checkout -b feature/your-feature`).
3.  Make your changes.
4.  Commit your changes (`git commit -m 'Add some feature'`).
5.  Push to the branch (`git push origin feature/your-feature`).
6.  Open a Pull Request.

---

## License

This project is licensed under the Apache License, Version 2.0. See the [LICENSE](LICENSE) file for more details.
```

---

#### Thanks to [roshdsupp](https://t.me/roshdsupp) for the project idea 🩵
