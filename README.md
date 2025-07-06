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

---

## Configuration

During the installation process, you will be prompted to provide the following information:

- **Cloudflare API Token**: Your Cloudflare API token for authentication.
- **Cloudflare Zone ID**: The ID of the Cloudflare zone where your DNS records are located.
- **Cloudflare Record Name**: The name of the DNS record you want to update (e.g., `example.com`).
- **Cloudflare IP Addresses**: A comma-separated list of IP addresses to rotate through.

These values will be stored in your `~/.bashrc` file as environment variables.

## Usage

After the installation is complete, the setup script will automatically create a cron job that runs every 30 minutes. This cron job will execute the `run.sh` script, which in turn runs the `change_dns.py` script to update the DNS records.

### Manual Execution

If you need to manually trigger the DNS update, you can run the following command:

```bash
/opt/Cloudflare-Utils/run.sh
```

### Logs

The output of the cron job and the script executions will be logged in `/opt/Cloudflare-Utils/log_file.log`. You can check this log file to ensure that the updates are happening as expected.

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


