# Cloudflare Utils

This project contains utilities to interact with Cloudflare DNS records, allowing for automated updates of DNS records using a specified set of IP addresses.

## Features

- **DNS Record Rotation**: Automatically rotate DNS records based on a predefined list of IP addresses.
- **IP Shuffling**: Rotate the IPs among multiple existing DNS records within a zone.
- **Rotate Based on a List of IPs (Multi-Records)**: Rotate a shared list of IPs across multiple DNS records in a synchronized, round-robin manner, with a full management menu for adding, editing, deleting, and viewing logs for configurations.
- **Secure Configuration**: Securely manage Cloudflare API tokens.
- **Automated Updates**: Set up a cron job to periodically update DNS records.
- **Interactive CLI**: A user-friendly command-line interface for managing all features.
- **Zone Management**: A full suite of tools to manage your Cloudflare zones directly from the CLI, including adding, listing, viewing details, deleting zones, and editing zone settings (SSL, Always Use HTTPS, etc.).

## Prerequisites

- Ubuntu Server

---

## Installation

To install and set up the Cloudflare Utils on an Ubuntu server, follow these steps:

### Using cURL

Run the following command to download and execute the installation script using `curl`:

```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/Issei-177013/Cloudflare-Utils/main/install.sh)"
```

### Using wget

Alternatively, you can use `wget` to download and execute the installation script:

```bash
sudo bash -c "$(wget -O- https://raw.githubusercontent.com/Issei-177013/Cloudflare-Utils/main/install.sh)"
```

**Note for Developers:** If you want to install the latest development version, you can do so by specifying the `dev` branch in the URL:

```bash
# Using curl
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/Issei-177013/Cloudflare-Utils/main/install.sh)" _ dev

# Using wget
sudo bash -c "$(wget -O- https://raw.githubusercontent.com/Issei-177013/Cloudflare-Utils/main/install.sh)" _ dev
```

---

## Configuration

During the installation process, or when adding an account via the `cfu` CLI, you will be prompted to provide the following information:

- **Cloudflare API Token**: Your Cloudflare API token for authentication.
  - **Important Security Note**: It is **strongly recommended** to use a scoped **API Token** instead of your Global API Key. API Tokens are more secure because you can grant them specific permissions.
  - When creating a custom token, you will need to grant the following permissions for all features to work correctly:
    - **Zone.Zone**: `Edit`
    - **Zone.DNS**: `Edit`
  - You can create a token from your [Cloudflare Dashboard](https://dash.cloudflare.com/profile/api-tokens). For a detailed guide, please refer to the on-screen instructions when adding an account through the CLI.
  - For more details, see the official Cloudflare documentation: [Creating Cloudflare API tokens](https://developers.cloudflare.com/fundamentals/api/get-started/create-token/).
  - While a Global API Key might work, using it poses a security risk as it grants broad access to your Cloudflare account.
- **Cloudflare Zone ID**: The ID of the Cloudflare zone where your DNS records are located.
- **Cloudflare Record Name**: The name of the DNS record you want to update (e.g., `example.com`).
- **Cloudflare IP Addresses**: A comma-separated list of IP addresses to rotate through.
- **Rotation Interval (Optional)**: The rotation interval in minutes for this specific record. If not provided, a default of 30 minutes will be used.

These values will be stored in `/opt/Cloudflare-Utils/configs.json`.

## Usage

The primary way to interact with Cloudflare Utils is through the command-line interface (CLI).

### Running the CLI

The installation script (`install.sh`) creates a global command `cfu` that allows you to easily run the Cloudflare Utils CLI from anywhere in your terminal.

To start the CLI, simply type:

```bash
cfu
```

Alternatively, you can still run the script directly:

```bash
python3 /opt/Cloudflare-Utils/cli.py
```

or if you've made `cli.py` executable:

```bash
/opt/Cloudflare-Utils/cli.py
```

Using the `cfu` command is the recommended way to access the CLI after installation.

### CLI Menu

The main menu provides access to different modules of the application:

- **1. Manage Cloudflare Accounts**: Add, edit, or delete Cloudflare accounts.
- **2. Manage Zones**: A dedicated menu to manage your Cloudflare zones. You can list all zones, add a new one, view details of a specific zone, or delete a zone.
- **3. IP Rotator Tools**: Access tools for managing DNS-based IP rotation.
- **4. View Application Logs**: View live logs from the application.
- **0. Exit**: Exit the CLI.

#### IP Rotator Tools

This submenu provides three main functionalities:

- **1. Rotate Based on a List of IPs (Single-Record)**: This is the classic rotation feature. You can create, edit, or delete rotation configurations for your DNS records. Each configuration specifies a list of IPs to be rotated on a schedule for a single DNS record.
- **2. Rotate IPs Between Records**: This tool allows you to select multiple `A` or `AAAA` records from a zone and Rotate their current IP addresses among them. This is useful for rotating existing IPs without needing to provide an external list. The action is immediate and not based on a schedule.
- **3. Rotate Based on a List of IPs (Multi-Records)**: This tool allows you to rotate a shared list of IPs across multiple DNS records in a synchronized, round-robin manner.

### Cron Job for DNS Rotation

After installation, a cron job is set up to run the rotation script every minute. The script checks for records due for rotation based on their individually configured intervals.

The script reads your configurations and uses a `rotation_status.json` file to track the last rotation time for each record or group. This ensures that records are only rotated when their configured interval (e.g., 30 minutes) has passed. The minimum configurable rotation interval is 5 minutes.

### Manual DNS Rotation

If you need to manually trigger the DNS rotation for all configured records, you can run:

```bash
python3 /opt/Cloudflare-Utils/config_manager.py
```

### Logs

The output of the cron job and script executions are stored in rotating log files in the `/opt/Cloudflare-Utils/logs/` directory. The main log file is `app.log`. Log files are rotated daily, and up to 7 days of logs are kept. You can check these log files to ensure that the updates are happening as expected.

---

## Updating

To update Cloudflare Utils to the latest version, you can re-run the installation script. It will fetch the latest version from the repository and update your installation.

### Using cURL

```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/Issei-177013/Cloudflare-Utils/main/install.sh)"
```

### Using wget

```bash
sudo bash -c "$(wget -O- https://raw.githubusercontent.com/Issei-177013/Cloudflare-Utils/main/install.sh)"
```

The script will give you an option to install, which will effectively update your current installation if it detects an existing one by pulling the latest changes for the chosen branch. Your existing `.env` configuration file will be preserved.

---

## Contributing

If you wish to contribute to this project, please follow these steps:

1. Fork the repository.
2. Create a new branch with a descriptive name.
3. Make your changes and commit them with clear messages.
4. Push your changes to your forked repository.
5. Create a pull request to the main repository.

---

## Tests

### Running Tests

To run the tests, make sure you have installed `pytest`:

```bash
pip install pytest
```

Then, you can run all the tests using:

```bash
pytest
```

### Test Coverage

The tests are designed to cover various aspects of the Cloudflare Utils project:

- Unit Tests: Tests for individual functions like fetching records, updating records, and IP rotation.
- Integration Tests: Tests that check the interaction between different components, such as fetching records and updating them with rotated IPs.
- Error Handling Tests: Tests to ensure proper error handling in case of API errors or invalid inputs.

### Adding New Tests

If you want to add new tests, follow these steps:

- Create a new test file in the tests/ directory, following the naming convention test\_<feature>.py.
- Write your test cases using unittest or pytest.
- Run the tests locally to ensure they pass before making a pull request.

### Continuous Integration

We use continuous integration (CI) to automatically run tests on each pull request. Make sure all tests pass before merging your changes.

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

```
# Copyright 2024 [Issei-177013]
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

If you encounter any issues or have any questions, please open an issue in the GitHub repository.

---

#### Thanks to [roshdsupp](https://t.me/roshdsupp) for the project idea 🩵