# Cloudflare Utils

Cloudflare Utils is a Python-based command-line tool designed to automate the rotation of Cloudflare DNS A and AAAA records using a predefined list of IP addresses. It can be run manually, or scheduled via cron or systemd for periodic updates.

## Features

-   **Automated IP Rotation**: Update DNS A and AAAA records with IPs from a specified list.
-   **CLI Interface**: Manage DNS updates directly from the command line.
-   **Flexible Configuration**: Configure via a `.env` file or CLI arguments.
-   **Multiple Record Support**: Update multiple DNS records in a single run.
-   **IPv4/IPv6 Aware**: Correctly handles IP assignment for A (IPv4) and AAAA (IPv6) records.
-   **Virtual Environment**: Uses a Python virtual environment for isolated dependencies.
-   **Choice of Scheduler**: Interactive installer allows choosing between cron and systemd for scheduled tasks.
-   **Non-Interactive Installation**: Supports automated setup via CLI arguments.
-   **Branch-Specific Installations**: Install and test development branches in isolated environments.
-   **Logging**: Comprehensive logging to both file and console (for CLI usage).
-   **(Planned) Debian Package**: For easier deployment on Debian/Ubuntu systems.
-   **(Planned) GitHub Action**: For cloud-based execution.

## Prerequisites

-   Ubuntu Server (primarily tested on Ubuntu, may work on other Debian-based systems).
-   `git`, `python3`, `python3-pip`, `python3-venv`.
-   A Cloudflare account with an API Token.
-   Zone ID of the Cloudflare zone you wish to manage.
-   DNS Record Name(s) you wish to update.
-   A list of IP addresses (IPv4 and/or IPv6) to rotate through.

---

## Installation Methods

The `install.sh` script is the primary way to install Cloudflare-Utils. It handles:
* Cloning the repository (default `main` branch or a specified branch).
* Setting up a Python virtual environment.
* Installing the `cloudflare-utils` package and its dependencies.
* Creating necessary configuration files (e.g., `.env`).
* Setting up a scheduler (cron or systemd timer) for periodic execution.

**Important Notes on Running `install.sh`:**

*   **Interactive Installations:** If the script needs to prompt you for input (e.g., for API keys, scheduler choice), you **must** download `install.sh` first and then run it directly with `sudo`. Piping `curl` directly to `sudo bash -s` (e.g., `curl ... | sudo bash -s`) will prevent interactive prompts from working correctly.
    ```bash
    # Correct way for interactive installs:
    curl -fsSL -o install.sh <URL_to_install.sh>
    chmod +x install.sh
    sudo ./install.sh [flags_like_--branch_dev_if_needed]
    ```

*   **Non-Interactive Installations (One-Liners):** One-liner `curl ... | sudo bash -s -- ...args...` commands are suitable **only** if you provide the `--non-interactive` flag and all other required arguments for a fully automated setup. The `install.sh` script will exit with an error if it attempts to run an interactive menu when input is not a TTY.

---

### 1. Standard Installation (Main Branch - Interactive)

This method installs the latest stable version from the `main` branch into `/opt/Cloudflare-Utils/`. It will guide you through the setup process.

1.  **Download `install.sh` from the `main` branch:**
    ```bash
    curl -fsSL -o install.sh https://raw.githubusercontent.com/Issei-177013/Cloudflare-Utils/main/install.sh
    chmod +x install.sh
    ```
2.  **Run the script with `sudo`:**
    ```bash
    sudo ./install.sh
    ```
    You will be prompted for:
    *   Cloudflare API Token
    *   Cloudflare Zone ID
    *   Cloudflare Record Name(s) (comma-separated)
    *   Cloudflare IP Addresses (comma-separated list)
    *   Preferred scheduler (Cron or Systemd Timer)

    These details will be saved to `/opt/Cloudflare-Utils/.env`.

---

### 2. Non-Interactive Installation (Main Branch)

For automated deployments of the `main` branch, provide all necessary information as command-line arguments.

*   **Using a downloaded `install.sh`:**
    ```bash
    # Download main branch's install.sh first (if not already done)
    # curl -fsSL -o install.sh https://raw.githubusercontent.com/Issei-177013/Cloudflare-Utils/main/install.sh
    # chmod +x install.sh
    
    sudo ./install.sh --non-interactive --action install \
      --api-token "YOUR_CLOUDFLARE_API_TOKEN" \
      --zone-id "YOUR_CLOUDFLARE_ZONE_ID" \
      --record-name "record1.example.com,record2.example.com" \
      --ip-addresses "1.1.1.1,2.2.2.2,2606:4700::1,2606:4700::2"
    ```

*   **Using a one-liner (for fully non-interactive setup only):**
    ```bash
    curl -fsSL https://raw.githubusercontent.com/Issei-177013/Cloudflare-Utils/main/install.sh | sudo bash -s -- \
      --non-interactive --action install \
      --api-token "YOUR_CLOUDFLARE_API_TOKEN" \
      --zone-id "YOUR_CLOUDFLARE_ZONE_ID" \
      --record-name "record1.example.com" \
      --ip-addresses "1.1.1.1,::1"
    ```

**Required non-interactive arguments for `install.sh --action install`:**
*   `--non-interactive`: Flag to enable non-interactive mode.
*   `--api-token "<token>"`
*   `--zone-id "<zone_id>"`
*   `--record-name "<name1,name2>"`
*   `--ip-addresses "<ip1,ip2>"`
*   (Optional) `--branch <branch_name>`: Defaults to `main` if not specified.

In non-interactive mode, the installer defaults to using **cron** for scheduling.

---

### 3. Installing from a Specific Branch (e.g., `dev`)

This allows you to install a specific branch (e.g., `dev`) into an isolated environment (e.g., `/opt/Cloudflare-Utils-dev/`) for testing or development.

*   **Interactive Installation of a Branch:**
    1.  **Download `install.sh` *from that specific branch*:**
        ```bash
        # Example for 'dev' branch
        curl -fsSL -o install-dev.sh https://raw.githubusercontent.com/Issei-177013/Cloudflare-Utils/dev/install.sh
        chmod +x install-dev.sh
        ```
    2.  **Run the downloaded script with `sudo` and the `--branch` flag:**
        ```bash
        sudo ./install-dev.sh --branch dev
        ```
        The script will then guide you through the interactive setup for the `dev` branch version. Configuration will be saved to `/opt/Cloudflare-Utils-dev/.env`.

*   **Non-Interactive Installation of a Branch (One-Liner or Downloaded Script):**
    ```bash
    # Example one-liner for NON-INTERACTIVE 'dev' branch install:
    curl -fsSL https://raw.githubusercontent.com/Issei-177013/Cloudflare-Utils/dev/install.sh | sudo bash -s -- \
      --non-interactive --action install --branch dev \
      --api-token "YOUR_DEV_API_TOKEN" \
      --zone-id "YOUR_DEV_ZONE_ID" \
      --record-name "dev.example.com" \
      --ip-addresses "1.2.3.4,::1"
    ```
    Alternatively, download `install-dev.sh` as above, then run:
    ```bash
    sudo ./install-dev.sh --non-interactive --action install --branch dev \
      --api-token "YOUR_DEV_API_TOKEN" \
      # ... other parameters ...
    ```

**Managing Branch Installations:**
*   Each branch installation is isolated (e.g., directory `/opt/Cloudflare-Utils-dev`, systemd units `cloudflare-utils-dev.service`).
*   To **remove** a branched installation, download `install.sh` (preferably from the same branch it was installed from, or `main`), make it executable, and then run:
    ```bash
    # Example for 'dev' branch removal (interactive confirmation):
    sudo ./install.sh --action remove --branch dev 
    ```
    Or for non-interactive removal:
    ```bash
    sudo ./install.sh --non-interactive --action remove --branch dev
    ```
*   Running `install.sh` without `--branch` targets the main installation (`/opt/Cloudflare-Utils`).

---
### 4. Debian Package (Planned)

Instructions for installing via a `.deb` package will be added here once available.

---

## Configuration

Cloudflare Utils is configured via environment variables. When installed using `install.sh`, these are typically stored in `/opt/Cloudflare-Utils/.env` (or `/opt/Cloudflare-Utils-<branch>/.env` for branched installs). The script can also accept these as CLI arguments, which will override `.env` values.

**Configuration Variables:**

*   **`CLOUDFLARE_API_TOKEN`** (Required)
    *   Description: Your Cloudflare API token. Needs permissions to read and edit DNS records for the specified zone.
    *   Example: `"your_api_token_here"`

*   **`CLOUDFLARE_ZONE_ID`** (Required)
    *   Description: The ID of the Cloudflare zone containing the DNS records.
    *   Example: `"your_zone_id_here"`

*   **`CLOUDFLARE_RECORD_NAME`** (Required)
    *   Description: Comma-separated list of DNS record names (FQDNs) to update.
    *   Example: `"example.com,sub.example.com"`

*   **`CLOUDFLARE_IP_ADDRESSES`** (Required)
    *   Description: Comma-separated list of IP addresses (IPv4 and/or IPv6) to rotate through. The script automatically selects appropriate IP types for A (IPv4) and AAAA (IPv6) records.
    *   Example: `"192.0.2.1,198.51.100.5,2001:db8::1,2001:db8::2"`

---

## Usage

Once installed and configured, Cloudflare Utils primarily runs via the scheduler (cron or systemd) chosen during installation. The `run.sh` script in the installation directory (e.g., `/opt/Cloudflare-Utils/run.sh`) handles virtual environment activation and execution.

### Manual Execution (CLI)

You can run the tool manually using the `cloudflare-utils` command *after* activating its virtual environment, or by directly executing the `run.sh` script for that installation.

*   **Using `run.sh` (handles venv activation):**
    ```bash
    # For main installation:
    sudo /opt/Cloudflare-Utils/run.sh 
    # For a 'dev' branch installation:
    # sudo /opt/Cloudflare-Utils-dev/run.sh 
    ```
    This is the recommended way to manually trigger what cron/systemd would do.

*   **Direct CLI (if venv is active):**
    ```bash
    # First, activate the venv for the specific installation:
    # source /opt/Cloudflare-Utils/.venv/bin/activate 
    # Or for dev: source /opt/Cloudflare-Utils-dev/.venv/bin/activate
    
    # Then run:
    cloudflare-utils [OPTIONS]
    
    # Deactivate venv when done:
    # deactivate
    ```

**CLI Options for `cloudflare-utils`:**

*   `--api-token TEXT`: Cloudflare API Token.
*   `--zone-id TEXT`: Cloudflare Zone ID.
*   `--record-names TEXT`: Comma-separated DNS record names.
*   `--ip-addresses TEXT`: Comma-separated IP addresses.
*   `--env-file TEXT`: Path to .env file (default: `<INSTALL_DIR>/.env`).
*   `--log-level [DEBUG|INFO|WARNING|ERROR|CRITICAL]`: Set logging level (default: INFO).
*   `--version`: Show program version and exit.
*   `--help`: Show help message and exit.

**Example CLI Usage (assuming venv active):**
```bash
# Run using configuration from the installation's .env file
cloudflare-utils

# Override record names and IPs for a specific run:
cloudflare-utils --record-names "new.example.com" --ip-addresses "5.5.5.5"

# Run with debug logging:
cloudflare-utils --log-level DEBUG
```

### Scheduled Execution

The scheduler (cron or systemd) runs the installation-specific `run.sh` script (e.g., `/opt/Cloudflare-Utils/run.sh` or `/opt/Cloudflare-Utils-dev/run.sh`).

*   **Cron**: Runs every 30 minutes by default.
*   **Systemd**: `cloudflare-utils.timer` (or `cloudflare-utils-dev.timer`) triggers the corresponding `.service` every 30 minutes and on boot.
    *   Check timer status: `sudo systemctl status cloudflare-utils.timer` (or `cloudflare-utils-dev.timer`)
    *   Check service logs: `sudo journalctl -u cloudflare-utils.service` (or `cloudflare-utils-dev.service`)

### Logs

*   **Log File**: Operations are logged to `log_file.log` within the respective installation directory (e.g., `/opt/Cloudflare-Utils/log_file.log` or `/opt/Cloudflare-Utils-dev/log_file.log`).
*   **Console Output**: When `cloudflare-utils` is run directly via CLI, logs are also output to the console.

---
## GitHub Action (Experimental)

A CI workflow is included in `.github/workflows/ci.yml` which lints the code and builds the package.

For users wishing to run Cloudflare-Utils via GitHub Actions on a schedule (e.g., from a fork of this repository), an example job `scheduled-dns-update` is provided (commented out) in the CI workflow. To use it:
1.  Uncomment the `scheduled-dns-update` job in `.github/workflows/ci.yml`.
2.  Configure the required secrets in your repository's Settings > Secrets and Variables > Actions:
    *   `CLOUDFLARE_API_TOKEN`
    *   `CLOUDFLARE_ZONE_ID`
    *   `CLOUDFLARE_RECORD_NAME`
    *   `CLOUDFLARE_IP_ADDRESSES`
3.  The action will then run `cloudflare-utils` using these secrets as environment variables.

---

## Contributing

Contributions are welcome! Please follow these steps:

1.  Fork the repository.
2.  Create a new branch (`git checkout -b feature/YourFeature`).
3.  Make your changes and commit them (`git commit -m 'Add some feature'`).
4.  Push to the branch (`git push origin feature/YourFeature`).
5.  Open a Pull Request.

---

## Testing (for Developers)

The project aims to have tests covering various aspects.
(The current "Tests" section in the original README seems like a placeholder for future test suite details. For now, manual testing and the CI linting/build checks are in place.)

### Running Linters
```bash
pip install flake8
flake8 src
```
---

## License

This project is licensed under the Apache License, Version 2.0. See the [LICENSE](LICENSE) file for more details.

```
# Copyright 2024 Issei-177013
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
```

---

## Support

If you encounter any issues or have questions, please open an issue in the GitHub repository.

---

#### Thanks to [roshdsupp](https://t.me/roshdsupp) for the project idea 🩵
