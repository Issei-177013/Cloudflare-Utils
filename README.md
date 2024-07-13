برای ایجاد مستندات دقیق جهت نصب و استفاده از اسکریپت‌ها، می‌توانیم فایل `README.md` را به شکلی طراحی کنیم که شامل دستورالعمل‌های نصب، استفاده و توضیحات مربوط به هر قسمت از پروژه باشد.

### محتوای فایل `README.md`

```markdown
# Cloudflare Utils

This project contains utilities to interact with Cloudflare DNS records, allowing for automated updates of DNS records using a specified set of IP addresses.

## Features

- Automatically rotate DNS records based on a list of IP addresses.
- Securely manage Cloudflare API tokens and other configuration via environment variables.
- Set up a cron job to periodically update DNS records.

## Prerequisites

- Ubuntu Server
- Git
- Python 3 and pip

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

## Contributing

If you wish to contribute to this project, please follow these steps:

1. Fork the repository.
2. Create a new branch with a descriptive name.
3. Make your changes and commit them with clear messages.
4. Push your changes to your forked repository.
5. Create a pull request to the main repository.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

## Support

If you encounter any issues or have any questions, please open an issue in the GitHub repository.

```

### توضیحات

- **Features**: ویژگی‌های کلیدی پروژه را توضیح می‌دهد.
- **Prerequisites**: پیش‌نیازهای مورد نیاز برای نصب و راه‌اندازی پروژه.
- **Installation**: دستورالعمل‌های نصب با استفاده از `cURL` و `wget`.
- **Configuration**: توضیحاتی در مورد ورودی‌های لازم در حین نصب.
- **Usage**: نحوه استفاده از اسکریپت‌ها و اجرای دستی آن‌ها.
- **Logs**: محل ذخیره‌سازی لاگ‌ها.
- **Contributing**: دستورالعمل‌های مشارکت در پروژه.
- **License**: اطلاعات مربوط به مجوز پروژه.
- **Support**: راهنمایی برای دریافت پشتیبانی.

با استفاده از این مستندات، کاربران می‌توانند به راحتی پروژه را نصب و استفاده کنند و در صورت نیاز به پشتیبانی یا مشارکت در پروژه، اطلاعات لازم را دریافت کنند.