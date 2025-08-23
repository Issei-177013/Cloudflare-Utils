# Cloudflare Utils

This project contains a command-line utility to interact with Cloudflare, allowing for automated updates of DNS records, zone management, and IP rotation.

## Table of Contents
- [Quick Start](#quick-start)
- [Features](#features)
- [Trigger System](#trigger-system)
  - [How it Works](#how-it-works)
  - [Managing Triggers](#managing-triggers)
- [Monitoring Agent](#monitoring-agent)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
  - [Standard Installation](#standard-installation)
  - [Developer Installation](#developer-installation)
- [Configuration](#configuration)
  - [Configuration Files](#configuration-files)
  - [API Token Permissions](#api-token-permissions)
- [Usage (CLI Menus)](#usage-cli-menus)
  - [Main Menu](#main-menu)
  - [Manage Cloudflare Accounts](#manage-cloudflare-accounts)
  - [Manage Zones](#manage-zones)
  - [Manage DNS Records](#manage-dns-records)
  - [IP Rotator Tools](#ip-rotator-tools)
- [Troubleshooting](#troubleshooting)
- [License](#license)

## Quick Start

For the impatient user, here's how to get up and running quickly on an Ubuntu server.

**1. Install**

Run the following command to download and execute the installation script:
```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/Issei-177013/Cloudflare-Utils/main/install.sh)"
```

**2. Configure Your First Account**

The first time you run the tool, it will prompt you to add a Cloudflare account.
```bash
cfu
```
```text
👋 Welcome to Cloudflare Utils!
It looks like this is your first time, or you don't have any accounts configured yet.
Let's add your first Cloudflare account.

Press Enter to continue...
```
Follow the on-screen instructions to add your API Token.

**3. Use the Tool**

Once installed, you can manage your Cloudflare setup through the interactive menu:
```bash
cfu
```

## Features

- **DNS Record Rotation**: Automatically rotate DNS records based on a predefined list of IP addresses.
- **IP Shuffling**: Rotate the IPs among multiple existing DNS records within a zone.
- **Multi-Record Rotation**: Rotate a shared list of IPs across multiple DNS records in a synchronized, round-robin manner.
- **Direct DNS Management**: Add, edit, and delete DNS records directly on Cloudflare.
- **Secure Configuration**: Securely manage Cloudflare API tokens with validation.
- **Automated Updates**: Set up a cron job automatically to periodically update DNS records.
- **Interactive CLI**: A user-friendly command-line interface for managing all features.
- **Zone Management**: A full suite of tools to manage your Cloudflare zones directly from the CLI, including adding, listing, viewing details, deleting zones, and editing zone settings (SSL, Always Use HTTPS, etc.).
- **Monitoring Agent**: An optional companion agent to monitor server traffic usage.
- **Self-Monitoring**: The main utility can monitor the local server's traffic usage without needing a separate agent.

## Trigger System

The Cloudflare-Utils application includes a powerful trigger system that allows you to monitor data usage from your agents and receive alerts when certain thresholds are met. This is useful for keeping track of bandwidth usage and avoiding unexpected costs.

### How it Works

The trigger system runs as a background service that periodically checks the data usage of your configured agents. When the usage exceeds a specified limit within a given time period (e.g., 100GB in a month), a trigger is activated.

Key components of the trigger system:
- **Background Service**: A service that runs every 5 minutes to evaluate all configured triggers.
- **Triggers**: A set of rules that define the conditions for an alert. Each trigger consists of:
    - An **agent** to monitor.
    - A **time period** (daily, weekly, or monthly).
    - A **data volume** threshold (in GB).
    - An **alert** that is logged when the trigger is activated.
- **State Management**: The application uses a `state.json` file to keep track of fired triggers, ensuring that you only receive one alert per period for each trigger.

### Managing Triggers

You can manage triggers through the interactive CLI:
1. Run `cfu` to open the main menu.
2. Select "Traffic Monitoring".
3. Select "Manage Triggers" to open the trigger management menu.

From the trigger management menu, you can add, edit, and delete triggers.

## Monitoring Agent

The Cloudflare-Utils suite includes a lightweight monitoring agent, `Cloudflare-Utils-Agent`, designed to run on your servers and report traffic usage. This is particularly useful for users who need to track bandwidth on servers behind Cloudflare.

### Agent Features

- **Lightweight**: The agent has a small footprint and minimal dependencies.
- **Secure**: Communication with the agent is secured with an API key.
- **Easy to Install**: The agent is installed using the same `install.sh` script as the main `Cloudflare-Utils` program.

### Agent Installation

The agent can be installed by running the main `install.sh` script and choosing the "Install/Update Agent" option from the menu. The script will guide you through the process of selecting a network interface to monitor and will automatically configure and start the agent as a `systemd` service.

### Managing the Agent

Once installed, the agent runs in the background. You can manage it using standard `systemctl` commands:

- **Check Status**: `sudo systemctl status cloudflare-utils-agent.service`
- **Start**: `sudo systemctl start cloudflare-utils-agent.service`
- **Stop**: `sudo systemctl stop cloudflare-utils-agent.service`
- **View Logs**: `sudo journalctl -u cloudflare-utils-agent.service`

### Managing the Agent with `cfu-agent`

In addition to using `systemctl`, you can manage the agent directly using the `cfu-agent` command-line tool. This tool provides more specific control over the agent's functions.

**Available Commands:**

-   **`cfu-agent token`**: Manage the agent's API token.
    -   `display`: Show the current token (masked by default).
    -   `change`: Generate a new API token.
-   **`cfu-agent service`**: Control the agent's `systemd` service.
    -   `start`, `stop`, `restart`, `status`.
-   **`cfu-agent logs`**: View the agent's logs.
    -   Use `-f` to follow the logs in real-time.
-   **`cfu-agent version`**: Display the agent's version.
-   **`cfu-agent stats`**: Show traffic statistics for the monitored interface.
    -   `reset`: Clear the statistics for the interface.
-   **`cfu-agent config`**: Manage the agent's configuration.
    -   `show`: Display the current configuration (with the API token masked).

For more detailed help on any command, you can use `cfu-agent <command> --help`.

## Telegram Bot

Cloudflare Utils includes an optional Telegram bot that can be configured to allow management from a Telegram chat. The bot runs as a separate background service and does not interfere with the CLI.

### Setting up the Bot

All bot management is done from within the CLI.

1.  Navigate to the settings menu: `cfu` -> `7. Settings`.
2.  Select `4. Telegram Bot` to open the bot management menu.

### Bot Management Menu

From the Telegram Bot Settings menu, you can:

-   **Enable/Disable the Bot**: A global switch to turn the bot on or off. The bot service will not run if this is disabled.
-   **Set/Update Token**: Set your Telegram bot token, obtained from BotFather. For security, the token is not displayed in full. You will be prompted to restart the service after changing the token.
-   **Manage Allowed User IDs**: Control who can use the bot.
    -   **Add/Remove IDs**: Add or remove individual Telegram user IDs.
    -   **Import from CSV**: Bulk import a list of user IDs from a CSV file.
    -   **Access Control Policy**:
        -   If the list of allowed IDs is **empty**, **any user** can interact with the bot.
        -   If the list contains **one or more IDs**, only users with those specific IDs can interact with the bot. All others will receive a rejection message.
-   **Manage Service**: Control the bot's background service.

### Service Management

The bot runs as a background service. The application supports two modes:

-   **systemd Mode (Recommended)**: If your system uses `systemd`, you can install a systemd service for the bot. This is the most reliable way to run the bot, as it will automatically restart on failure or system reboot. From the "Manage Service" menu, you can install, uninstall, start, stop, and restart the service. Installation requires root privileges.
-   **Background Process Mode (Fallback)**: If `systemd` is not available, the bot can be run as a simple background process. The "Manage Service" menu will provide options to start and stop this process. This method is less robust and the bot will not restart automatically on system reboot.

### Security Guidance

-   **Token Security**: Treat your bot token like a password. Do not share it or commit it to public repositories. If you believe your token has been compromised, use the "Set/Update Token" option to generate a new one from BotFather and update it in the settings.
-   **Access Control**: It is highly recommended to populate the "Allowed User IDs" list to ensure only authorized individuals can access your Cloudflare management functions through the bot.

## Project Structure
```
.
├── cf-utils.py           # Main CLI entry point
├── install.sh            # Installation script
├── requirements.txt      # Python dependencies
├── src/
│   ├── app.py              # Core application logic and startup
│   ├── background_service.py # Background service for trigger monitoring
│   ├── cloudflare_api.py   # Wrapper for the Cloudflare API
│   ├── config.py           # Handles loading/saving config files
│   ├── dns_manager.py      # Logic for managing DNS records in config
│   ├── ip_rotator.py       # Core logic for the IP rotation cron job
│   ├── state_manager.py    # Manages state for rotations and triggers
│   ├── triggers.py         # Logic for managing triggers
│   ├── menus/              # Contains all CLI menu modules
│   │   ├── main.py
│   │   └── ...
│   ├── agent/              # Source code for the monitoring agent
│   │   ├── cfu-agent.py    # CLI entry point for the agent
│   │   └── ...
│   ├── configs.json        # Stores user configurations
│   ├── rotation_status.json # Tracks the state of IP rotations
│   └── state.json          # Stores the state of fired triggers
└── tests/
    └── ...                 # Unit and integration tests
```

## Prerequisites

- **Operating System**: Ubuntu Server (tested), other Debian-based systems may work.
- **Python**: Python 3.6+
- **Dependencies**: The `install.sh` script will attempt to install the required Python packages.

## Installation

### Standard Installation

To install and set up the Cloudflare Utils on an Ubuntu server, you can use either `cURL` or `wget`.

**Using cURL:**
```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/Issei-177013/Cloudflare-Utils/main/install.sh)"
```

**Using wget:**
```bash
sudo bash -c "$(wget -O- https://raw.githubusercontent.com/Issei-177013/Cloudflare-Utils/main/install.sh)"
```

The script will present a menu allowing you to:
1. Install the main `Cloudflare-Utils` controller.
2. Install the `Cloudflare-Utils-Agent`.
3. Remove either component.

The controller installation will:
1. Install necessary system packages (`git`, `python3-pip`).
2. Clone the repository to `/opt/Cloudflare-Utils`.
3. Install required Python packages.
4. Create a global command `cfu` for easy access.
5. Set up a cron job to run the IP rotation script automatically.

### Developer Installation

If you want to install the latest development version, you can do so by specifying the `dev` branch in the URL:

**Using cURL:**
```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/Issei-177013/Cloudflare-Utils/main/install.sh)" _ dev
```

**Using wget:**
```bash
sudo bash -c "$(wget -O- https://raw.githubusercontent.com/Issei-177013/Cloudflare-Utils/main/install.sh)" _ dev
```

## Configuration

### Configuration Files

The application uses two main JSON files located in `/opt/Cloudflare-Utils/src/`:
- `configs.json`: Stores all user-defined configurations, including Cloudflare accounts, zones, and single-record rotation rules.
- `rotation_status.json`: Tracks the last rotation time for each record or group to ensure rotations happen at the correct interval.
- `state.json`: Stores state for multi-record rotations and fired triggers.

### API Token Permissions

It is **strongly recommended** to use a scoped **API Token**, not your Global API Key. When creating a custom token from your [Cloudflare Dashboard](https://dash.cloudflare.com/profile/api-tokens), you will need to grant the following permissions for all features to work correctly:

| Permission             | Access | Reason                                            |
| ---------------------- | ------ | ------------------------------------------------- |
| **Zone.Zone**          | `Edit` | Required for viewing, adding, and deleting zones. |
| **Zone.DNS**           | `Edit` | Required for viewing, creating, and editing DNS records. |
| **Zone.Zone Settings** | `Edit` | Required for viewing and changing zone settings like SSL and HTTPS. |

The application will verify the token upon entry to ensure it has at least basic read permissions.

## Usage (CLI Menus)

The primary way to interact with Cloudflare Utils is through the `cfu` command-line interface.

### Main Menu
This is the central navigation hub of the application.
```text
--- Main Menu ---
1. 👤 Manage Cloudflare Accounts
2. 🌐 Manage Zones
3. 📜 Manage DNS Records
4. 🔄 IP Rotator Tools
5. 📡 Traffic Monitoring
6. 📄 View Application Logs
7. ⚙️ Settings
0. 🚪 Exit
-----------------
👉 Enter your choice:
```

### Manage Cloudflare Accounts
This menu allows you to add, edit, and delete the Cloudflare accounts (API tokens) that the application uses.

### Manage Zones
This menu allows you to interact with your Cloudflare zones directly. You can list all zones, view details for a specific zone, add a new domain to your account, or delete a zone.

### Manage DNS Records
This tool allows you to manage your DNS records directly on Cloudflare for a chosen zone. This is for standard DNS management and is separate from the IP Rotator tools.

**Example: Adding a new A record**
```text
$ cfu
👉 Enter your choice: 3

--- (DNS Management) for Account: my-cloudflare-account ---
--- Available Zones ---
| # | Domain      |
|---|-------------|
| 1 | example.com |
👉 Enter the # of the zone to manage DNS records for: 1

--- DNS Records for example.com ---
...
Choose an option:
1) Add a new DNS record
...
👉 Enter your choice: 1

--- Add New DNS Record ---
Enter record type (A, AAAA, CNAME, TXT, MX, etc.): A
Enter record name (e.g., www, @, mail): test
Enter record content (IP address, domain, etc.): 192.0.2.1
Enter TTL (or press Enter for default):
Enable Cloudflare Proxy? (yes/no): no

Creating DNS record...
✅ DNS record created successfully!
```

### IP Rotator Tools
This submenu provides three main functionalities for IP rotation:

- **1. Rotate Based on a List of IPs (Single-Record)**: This is the classic rotation feature. You can create, edit, or delete rotation configurations for your DNS records. Each configuration specifies a list of IPs to be rotated on a schedule for a single DNS record.
- **2. Rotate Based on a List of IPs (Multi-Records)**: This tool allows you to rotate a shared list of IPs across multiple DNS records in a synchronized, round-robin manner.
- **3. Rotate IPs Between Records**: This tool allows you to select multiple `A` or `AAAA` records from a zone and rotate their current IP addresses among them. This is useful for rotating existing IPs without needing to provide an external list.

## Troubleshooting

### MissingPermissionError
If you see an error like `❌ Token is missing required permission: 'Zone.Zone'`, it means your API token lacks the necessary permissions.
- **Solution**: Go to your [Cloudflare API Tokens page](https://dash.cloudflare.com/profile/api-tokens), edit your token, and ensure it has the permissions listed in the **API Token Permissions** section above.

### Cloudflare API Errors
Errors like `❌ Invalid Token. Cloudflare API Error: ...` usually indicate a problem with your token itself.
- **Solution**:
  1.  Verify that the token you entered is correct and has not expired.
  2.  Ensure you are using an API Token and not the Global API Key.
  3.  Check your internet connection and Cloudflare's system status.

### Cron Job Not Running
If you notice your IPs are not rotating automatically:
- **Solution**:
  1.  Check the application logs for errors: `cfu` -> `View Application Logs`.
  2.  Verify the cron job is installed by running `crontab -l`. You should see an entry for `/opt/Cloudflare-Utils/run.sh`.
  3.  Manually run the rotation script to see if it produces errors: `sudo python3 /opt/Cloudflare-Utils/src/ip_rotator.py`.

## License

This project is licensed under the Apache License, Version 2.0. See the [LICENSE](LICENSE) file for more details.