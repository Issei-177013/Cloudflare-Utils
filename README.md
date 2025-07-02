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

## Installation

The primary installation method is using the `install.sh` script, which sets up the tool in `/opt/Cloudflare-Utils`, including a Python virtual environment and necessary configurations.

### Interactive Installation (Recommended for most users)

This method will guide you through the setup process and prompt for necessary information.

**Using cURL:**

```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/Issei-177013/Cloudflare-Utils/main/install.sh)"
```

**Using wget:**

```bash
sudo bash -c "$(wget -O- https://raw.githubusercontent.com/Issei-177013/Cloudflare-Utils/main/install.sh)"
```

During interactive installation, you will be asked for:
1.  Cloudflare API Token
2.  Cloudflare Zone ID
3.  Cloudflare Record Name(s) (comma-separated for multiple records)
4.  Cloudflare IP Addresses (comma-separated list of IPv4 and/or IPv6 addresses)
5.  Preferred scheduler (Cron or Systemd Timer)

These details will be saved to `/opt/Cloudflare-Utils/.env`.

### Non-Interactive Installation

For automated deployments, you can provide all necessary information as command-line arguments to `install.sh`.

```bash
# Example:
# First, download the script:
# curl -fsSL -o /tmp/install.sh https://raw.githubusercontent.com/Issei-177013/Cloudflare-Utils/main/install.sh
# chmod +x /tmp/install.sh
#
# Then run with sudo:
sudo /tmp/install.sh --non-interactive --action install \
  --api-token "YOUR_CLOUDFLARE_API_TOKEN" \
  --zone-id "YOUR_CLOUDFLARE_ZONE_ID" \
  --record-name "record1.example.com,record2.example.com" \
  --ip-addresses "1.1.1.1,2.2.2.2,2606:4700::1,2606:4700::2"
```

**Non-interactive arguments for `install.sh`:**
*   `--non-interactive`: Flag to enable non-interactive mode.
*   `--action <install|remove>`: Specifies the action to perform.
*   `--api-token "<token>"`: Your Cloudflare API Token.
*   `--zone-id "<zone_id>"`: Your Cloudflare Zone ID.
*   `--record-name "<name1,name2>"`: Comma-separated DNS record names.
*   `--ip-addresses "<ip1,ip2>"`: Comma-separated IP addresses.

In non-interactive mode, the installer defaults to using **cron** for scheduling.

### Installing from a Specific Branch (for Development/Testing)

You can install a specific branch (e.g., `dev`) for testing purposes. This will create an isolated installation.

1.  **Download `install.sh`**:
    ```bash
    curl -fsSL -o /tmp/install.sh https://raw.githubusercontent.com/Issei-177013/Cloudflare-Utils/main/install.sh
    # Note: This always fetches install.sh from main. To test changes in install.sh from a dev branch,
    # you'd need to download install.sh specifically from that dev branch:
    # curl -fsSL -o /tmp/install.sh https://raw.githubusercontent.com/Issei-177013/Cloudflare-Utils/dev/install.sh
    chmod +x /tmp/install.sh
    ```

2.  **Run `install.sh` with the `--branch` argument**:
    *   **Interactive example for `dev` branch:**
        ```bash
        sudo /tmp/install.sh --branch dev
        ```
        This will install into `/opt/Cloudflare-Utils-dev/`, use systemd units like `cloudflare-utils-dev.service`, etc. You'll be prompted for configuration as usual, which will be saved to `/opt/Cloudflare-Utils-dev/.env`.

    *   **Non-interactive example for `dev` branch:**
        ```bash
        sudo /tmp/install.sh --non-interactive --action install --branch dev \
          --api-token "YOUR_DEV_CLOUDFLARE_API_TOKEN" \
          # ... other parameters ...
        ```

**Managing Branch Installations:**
*   Each branch installation is isolated in its own directory (e.g., `/opt/Cloudflare-Utils-dev`).
*   Logs, `.env` files, and scheduler entries (cron/systemd) are specific to that branched installation.
*   To **remove** a branched installation, use `install.sh` with the same `--branch` name and `--action remove`:
    ```bash
    sudo /tmp/install.sh --action remove --branch dev 
    ```
    Or for non-interactive removal:
    ```bash
    sudo /tmp/install.sh --non-interactive --action remove --branch dev
    ```
*   Running `install.sh` without `--branch` targets the main installation (`/opt/Cloudflare-Utils`).

### Debian Package (Planned)

Instructions for installing via a `.deb` package will be added here once available.

---

## Configuration

Cloudflare Utils is configured via environment variables, typically stored in `/opt/Cloudflare-Utils/.env`. The script can also accept these as CLI arguments, which will override `.env` values.

**Configuration Variables:**

*   **`CLOUDFLARE_API_TOKEN`** (Required)
    *   Description: Your Cloudflare API token. This token needs permissions to read and edit DNS records for the specified zone.
    *   Example: `"your_api_token_here"`

*   **`CLOUDFLARE_ZONE_ID`** (Required)
    *   Description: The ID of the Cloudflare zone containing the DNS records you want to update.
    *   Example: `"your_zone_id_here"`

*   **`CLOUDFLARE_RECORD_NAME`** (Required)
    *   Description: A comma-separated list of the DNS record names (FQDNs) to update.
    *   Example: `"example.com,sub.example.com"`

*   **`CLOUDFLARE_IP_ADDRESSES`** (Required)
    *   Description: A comma-separated list of IP addresses (both IPv4 and IPv6 are supported) to rotate through for the specified records. The script will automatically select appropriate IP types for A (IPv4) and AAAA (IPv6) records.
    *   Example: `"192.0.2.1,198.51.100.5,2001:db8::1,2001:db8::2"`

---

## Usage

Once installed and configured, Cloudflare Utils primarily runs via the scheduler (cron or systemd) chosen during installation.

### Manual Execution (CLI)

You can also run the tool manually using the `cloudflare-utils` command. This is useful for immediate updates or testing. The command must be run from within the activated virtual environment or by specifying the full path to the executable within the venv (`/opt/Cloudflare-Utils/.venv/bin/cloudflare-utils`). If using cron/systemd, they handle the venv activation via `run.sh`.

```bash
# If venv is active or cloudflare-utils is in PATH:
cloudflare-utils [OPTIONS]
```

**CLI Options:**

*   `--api-token TEXT`: Cloudflare API Token.
*   `--zone-id TEXT`: Cloudflare Zone ID.
*   `--record-names TEXT`: Comma-separated DNS record names.
*   `--ip-addresses TEXT`: Comma-separated IP addresses.
*   `--env-file TEXT`: Path to .env file (default: `/opt/Cloudflare-Utils/.env`).
*   `--log-level [DEBUG|INFO|WARNING|ERROR|CRITICAL]`: Set logging level (default: INFO).
*   `--version`: Show program version and exit.
*   `--help`: Show help message and exit.

**Example CLI Usage:**

```bash
# Run using configuration from /opt/Cloudflare-Utils/.env
sudo /opt/Cloudflare-Utils/run.sh 

# Or, if the venv is activated and in PATH:
# cloudflare-utils

# Override .env file and run with specific record and IPs:
# cloudflare-utils --record-names "new.example.com" --ip-addresses "5.5.5.5"

# Run with debug logging:
# cloudflare-utils --log-level DEBUG
```

### Scheduled Execution

*   **Cron**: If selected, a cron job is set up to run `/opt/Cloudflare-Utils/run.sh` every 30 minutes.
*   **Systemd**: If selected, `cloudflare-utils.timer` is set up to trigger `cloudflare-utils.service` every 30 minutes and on boot.
    *   Check timer status: `sudo systemctl status cloudflare-utils.timer`
    *   Check service logs: `sudo journalctl -u cloudflare-utils.service`

### Logs

*   **Log File**: All operations are logged to `/opt/Cloudflare-Utils/log_file.log`. This includes scheduled runs and manual CLI executions.
*   **Console Output**: When run manually via CLI (`cloudflare-utils`), logs are also output to the console.

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
