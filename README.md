# Cloudflare Utils

This project contains utilities to interact with Cloudflare DNS records, allowing for automated updates of DNS records using a specified set of IP addresses.

## Features

- Automatically rotate DNS records based on a list of IP addresses.
- Securely manage Cloudflare API tokens and other configuration via environment variables.
- Set up a cron job to periodically update DNS records.

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
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/Issei-177013/Cloudflare-Utils/dev/install.sh)"

# Using wget
sudo bash -c "$(wget -O- https://raw.githubusercontent.com/Issei-177013/Cloudflare-Utils/dev/install.sh)"
```

---

## Configuration

During the installation process, or when adding an account via the `cfutils` CLI, you will be prompted to provide the following information:

- **Cloudflare API Token**: Your Cloudflare API token for authentication.
    - **Important Security Note**: It is **strongly recommended** to use a scoped **API Token** instead of your Global API Key. API Tokens are more secure because you can grant them specific permissions (e.g., only to edit DNS records for a particular zone).
    - You can create an API Token from your Cloudflare Dashboard:
        1. Go to "My Profile" (usually top right of the dashboard).
        2. Select "API Tokens".
        3. Click "Create Token".
        4. You can use a template like "Edit zone DNS" or create a custom token. Ensure it has `Zone:Read` and `DNS:Edit` permissions for the zones you want to manage.
    - For more details, see the official Cloudflare documentation: [Creating Cloudflare API tokens](https://developers.cloudflare.com/fundamentals/api/get-started/create-token/).
    - While the Global API Key will work, using it increases security risks as it grants broad access to your Cloudflare account.
- **Cloudflare Zone ID**: The ID of the Cloudflare zone where your DNS records are located.
- **Cloudflare Record Name**: The name of the DNS record you want to update (e.g., `example.com`).
- **Cloudflare IP Addresses**: A comma-separated list of IP addresses to rotate through.
- **Rotation Interval (Optional)**: The rotation interval in minutes for this specific record. If not provided, a default of 30 minutes will be used.

These values will be stored in `/opt/Cloudflare-Utils/configs.json`.

## Usage

The primary way to interact with Cloudflare Utils is through the command-line interface (CLI).

### Running the CLI

The installation script (`install.sh`) creates a global command `cfutils` that allows you to easily run the Cloudflare Utils CLI from anywhere in your terminal.

To start the CLI, simply type:

```bash
cfutils
```

Alternatively, you can still run the script directly:

```bash
python3 /opt/Cloudflare-Utils/cli.py
```
or if you've made `cli.py` executable:
```bash
/opt/Cloudflare-Utils/cli.py
```

Using the `cfutils` command is the recommended way to access the CLI after installation.

### CLI Menu

The CLI provides the following options:

- **1. Add Account**: Add a new Cloudflare account with its API token.
- **2. Add Zone to Account**: Add a new DNS zone (domain) to an existing account. You will be able to select the account from a list.
- **3. Add Record to Zone**: Add a new DNS record to an existing zone. You will be able to select the account and then the zone from a list.
- **4. List All Records**: Display all configured accounts, zones, and their records.
- **5. Exit**: Exit the CLI.

When adding zones or records, instead of manually typing names, you will be presented with a numbered list of available items to choose from.
When adding a record, you can optionally specify a custom rotation interval in minutes. This interval must be at least 5 minutes. If no interval is provided, it will default to 30 minutes.

### Cron Job for DNS Rotation

After the installation, a cron job is set up to run `config_manager.py` every 5 minutes. This script reads the `configs.json` file and rotates the IP addresses for the configured DNS records based on their individual rotation intervals (which must be 5 minutes or more, or the default 30 minutes if not specified).
The script maintains a `rotation_status.json` file to track the last rotation time for each record, ensuring records are not rotated more frequently than their configured interval.

### Manual DNS Rotation

If you need to manually trigger the DNS rotation for all configured records, you can run:

```bash
python3 /opt/Cloudflare-Utils/config_manager.py
```

### Logs

The output of the cron job and script executions (like `config_manager.py`) will be logged in `/opt/Cloudflare-Utils/log_file.log`. You can check this log file to ensure that the updates are happening as expected.

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

* Unit Tests: Tests for individual functions like fetching records, updating records, and IP rotation.
* Integration Tests: Tests that check the interaction between different components, such as fetching records and updating them with rotated IPs.
* Error Handling Tests: Tests to ensure proper error handling in case of API errors or invalid inputs.

### Adding New Tests
If you want to add new tests, follow these steps:

* Create a new test file in the tests/ directory, following the naming convention test_<feature>.py.
* Write your test cases using unittest or pytest.
* Run the tests locally to ensure they pass before making a pull request.

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