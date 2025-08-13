# Cloudflare Utils

This project contains a command-line utility to interact with Cloudflare, allowing for automated updates of DNS records, zone management, and IP rotation.

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
```text
--- Main Menu ---
1. 👤 Manage Cloudflare Accounts
2. 🌐 Manage Zones
3. 📜 Manage DNS Records
4. 🔄 IP Rotator Tools
5. 📄 View Application Logs
6. ⚙️ Settings
0. 🚪 Exit
-----------------
👉 Enter your choice:
```

## Features

- **DNS Record Rotation**: Automatically rotate DNS records based on a predefined list of IP addresses.
- **IP Shuffling**: Rotate the IPs among multiple existing DNS records within a zone.
- **Multi-Record Rotation**: Rotate a shared list of IPs across multiple DNS records in a synchronized, round-robin manner.
- **Secure Configuration**: Securely manage Cloudflare API tokens with validation.
- **Automated Updates**: Set up a cron job automatically to periodically update DNS records.
- **Interactive CLI**: A user-friendly command-line interface for managing all features.
- **Zone Management**: A full suite of tools to manage your Cloudflare zones directly from the CLI, including adding, listing, viewing details, deleting zones, and editing zone settings (SSL, Always Use HTTPS, etc.).

## Project Structure
```
.
├── cf-utils.py           # Main CLI entry point
├── install.sh            # Installation script
├── requirements.txt      # Python dependencies
├── src/
│   ├── app.py              # Core application logic and startup
│   ├── cloudflare_api.py   # Wrapper for the Cloudflare API
│   ├── config.py           # Handles loading/saving config files
│   ├── dns_manager.py      # Logic for managing DNS records in config
│   ├── ip_rotator.py       # Core logic for the IP rotation cron job
│   ├── state_manager.py    # Manages state for multi-record rotations
│   ├── menus/              # Contains all CLI menu modules
│   │   ├── main.py
│   │   ├── accounts.py
│   │   ├── dns.py
│   │   ├── zones.py
│   │   └── ...
│   ├── configs.json        # Stores user configurations (accounts, records)
│   └── rotation_status.json # Tracks the state of IP rotations
└── tests/
    └── ...                 # Unit and integration tests
```

## Prerequisites

- **Operating System**: Ubuntu Server (tested), other Debian-based systems may work.
- **Python**: Python 3.6+
- **Dependencies**: The `install.sh` script will attempt to install the following Python packages using `pip`:
  - `cloudflare`
  - `python-dotenv`
  - `coloredlogs`
  - `tabulate`

## Installation

To install and set up the Cloudflare Utils on an Ubuntu server, you can use either `cURL` or `wget`.

### Using cURL

Run the following command to download and execute the installation script:
```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/Issei-177013/Cloudflare-Utils/main/install.sh)"
```

### Using wget

Alternatively, you can use `wget`:
```bash
sudo bash -c "$(wget -O- https://raw.githubusercontent.com/Issei-177013/Cloudflare-Utils/main/install.sh)"
```

The script will:
1. Install necessary system packages (`git`, `python3-pip`).
2. Clone the repository to `/opt/Cloudflare-Utils`.
3. Install required Python packages.
4. Create a global command `cfu` for easy access.
5. Set up a cron job to run the IP rotation script automatically.

## Configuration

### Configuration Files

The application uses two main JSON files located in `/opt/Cloudflare-Utils/src/`:
- `configs.json`: Stores all user-defined configurations, including Cloudflare accounts, zones, and single-record rotation rules.
- `rotation_status.json`: Tracks the last rotation time for each record or group to ensure rotations happen at the correct interval.
- `state.json`: Stores the state for multi-record rotation configurations.

### API Token Permissions

It is **strongly recommended** to use a scoped **API Token**, not your Global API Key. When creating a custom token from your [Cloudflare Dashboard](https://dash.cloudflare.com/profile/api-tokens), you will need to grant the following permissions for all features to work correctly:

| Permission             | Access | Reason                                            |
| ---------------------- | ------ | ------------------------------------------------- |
| **Zone.Zone**          | `Edit` | Required for viewing, adding, and deleting zones. |
| **Zone.DNS**           | `Edit` | Required for viewing, creating, and editing DNS records. |
| **Zone.Zone Settings** | `Edit` | Required for viewing and changing zone settings like SSL and HTTPS. |

The application will verify the token upon entry to ensure it has at least basic read permissions.

## Usage

The primary way to interact with Cloudflare Utils is through the `cfu` command-line interface.

### Running the CLI
```bash
cfu
```

### Example: Adding a DNS Rotation

Here is an example of what it looks like to add a new single-record IP rotation:

```text
$ cfu

--- IP Rotator Tools ---
1. 🔄 Rotate Based on a List of IPs (Single-Record)
2. 🌍 Rotate Based on a List of IPs (Multi-Records)
3. 🔀 Rotate IPs Between Records
0. ⬅️ Return to Main Menu
---------------------
👉 Enter your choice: 1

--- Rotate Based on a List of IPs (Single-Record) ---
...
1. 📝 Create DNS Rotation
...
👉 Enter your choice: 1

Select an account:
1. my-cloudflare-account
👉 Enter your choice: 1

Select a zone from Cloudflare:
1. example.com
👉 Enter your choice: 1

Record name (e.g., vpn.example.com): vpn.example.com
Enter record type (A/AAAA): A
Enter IPs, separated by commas: 1.1.1.1, 8.8.8.8
Enter rotation interval in minutes (or press Enter for default 30): 60

✅ Record added successfully!
```

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