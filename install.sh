#!/bin/bash
set -e

PROGRAM_NAME="Cloudflare-Utils"
DEFAULT_BRANCH="dev"
BRANCH="${1:-$DEFAULT_BRANCH}"
PROGRAM_DIR="/opt/$PROGRAM_NAME"
VERSION_TAG=""

# نصب وابستگی‌ها
install_packages() {
    echo -e "\e[1;34mInstalling dependencies...\e[0m"
    sudo apt-get update
    sudo apt-get install -y git python3-pip
    pip3 install --break-system-packages cloudflare python-dotenv
}

# کلون کردن سورس
clone_repository() {
    echo -e "\e[1;34mCloning from branch '$BRANCH'...\e[0m"
    if [ -d "$PROGRAM_DIR/.git" ]; then
        cd "$PROGRAM_DIR"
        git fetch origin
        git checkout "$BRANCH"
        git pull origin "$BRANCH"
    else
        git clone --branch "$BRANCH" https://github.com/Issei-177013/Cloudflare-Utils.git "$PROGRAM_DIR"
    fi

    cd "$PROGRAM_DIR"
    VERSION_TAG=$(git describe --tags --abbrev=0 2>/dev/null || git rev-parse --short HEAD)
    cd - > /dev/null
}

# ساخت run.sh برای اجرای برنامه اصلی
create_runner() {
    cat << EOF > "$PROGRAM_DIR/run.sh"
#!/bin/bash
cd "$PROGRAM_DIR"
echo "\$(date) - Running Cloudflare-Utils $VERSION_TAG" >> log_file.log
python3 rotate_from_config.py >> log_file.log 2>&1
EOF

    chmod +x "$PROGRAM_DIR/run.sh"
}

# Function to set up the configuration file
setup_config_file() {
    echo -e "\e[1;34mSetting up config file...\e[0m"
    CONFIG_FILE_PATH="$PROGRAM_DIR/configs.json"
    if [ ! -f "$CONFIG_FILE_PATH" ]; then
        echo '{"accounts": []}' > "$CONFIG_FILE_PATH"
        echo -e "\e[1;32mCreated empty config file: $CONFIG_FILE_PATH\e[0m"
    else
        echo -e "\e[1;33mConfig file already exists: $CONFIG_FILE_PATH\e[0m"
    fi

    # Change the owner of the config file to the user who invoked sudo.
    # This allows cli.py to edit the file without requiring sudo itself.
    if [ -n "$SUDO_USER" ]; then
        chown "$SUDO_USER:$SUDO_USER" "$CONFIG_FILE_PATH"
        echo -e "\e[1;32mSet owner of $CONFIG_FILE_PATH to $SUDO_USER\e[0m"
    else
        # If SUDO_USER is not set, cli.py might need to be run with sudo,
        # or file permissions adjusted manually.
        echo -e "\e[1;33mWarning: SUDO_USER not set. Config file permissions might need manual adjustment for cli.py without sudo.\e[0m"
        # As a fallback, chmod 666 could be used, but it's not secure.
        # chmod 666 "$CONFIG_FILE_PATH"
    fi
}

# Function to set up cron jobs
setup_cron() {
    echo -e "\e[1;34mSetting up cron...\e[0m"
    CRON_JOB_RUNNER="/bin/bash $PROGRAM_DIR/run.sh"
    # Remove existing cron jobs for this runner to avoid duplicates
    (crontab -l 2>/dev/null | grep -v -F "$CRON_JOB_RUNNER" || true) | crontab -
    
    # Add new cron jobs
    (crontab -l 2>/dev/null; echo "*/1 * * * * $CRON_JOB_RUNNER") | crontab -
    (crontab -l 2>/dev/null; echo "@reboot $CRON_JOB_RUNNER") | crontab -
    echo -e "\e[1;32mCron job set to run every 5 minutes and on reboot.\e[0m"
}

# منوی اصلی
main_menu() {
    PS3="Please choose: "
    options=("Install $PROGRAM_NAME (branch '$BRANCH')" "Remove $PROGRAM_NAME" "Exit")
    select opt in "${options[@]}"; do
        case $opt in
            "Install $PROGRAM_NAME (branch '$BRANCH')")
                install_packages
                clone_repository
                create_runner
                setup_config_file # Call the new function
                setup_cron

                # Create global command
                CLI_PATH="$PROGRAM_DIR/cli.py"
                GLOBAL_CMD_PATH="/usr/local/bin/cfutils"
                echo -e "\e[1;34mCreating global command '$GLOBAL_CMD_PATH'...\e[0m"
                if [ -f "$CLI_PATH" ]; then
                    ln -sf "$CLI_PATH" "$GLOBAL_CMD_PATH"
                    chmod +x "$CLI_PATH" # Ensure the script itself is executable
                    chmod +x "$GLOBAL_CMD_PATH" # Ensure the symlink is executable
                    echo -e "\e[1;32m✅ Global command 'cfutils' created. You can now use 'cfutils' from anywhere.\e[0m"
                else
                    echo -e "\e[1;31m❌ Error: $CLI_PATH not found. Cannot create global command.\e[0m"
                fi

                echo -e "\e[1;32m✅ Installed version: $VERSION_TAG\e[0m"
                echo -e "\e[1;32m📌 You can also use \`python3 $PROGRAM_DIR/cli.py\` to manage settings.\e[0m"
                break
                ;;
            "Remove $PROGRAM_NAME")
                echo -e "\e[1;34mRemoving $PROGRAM_NAME...\e[0m"
                sudo rm -rf "$PROGRAM_DIR"
                crontab -l | grep -v "$PROGRAM_DIR/run.sh" | crontab -
                
                # Remove global command
                GLOBAL_CMD_PATH="/usr/local/bin/cfutils"
                if [ -L "$GLOBAL_CMD_PATH" ]; then # Check if it's a symlink
                    echo -e "\e[1;34mRemoving global command '$GLOBAL_CMD_PATH'...\e[0m"
                    sudo rm -f "$GLOBAL_CMD_PATH"
                    echo -e "\e[1;32m✅ Global command 'cfutils' removed.\e[0m"
                fi

                echo -e "\e[1;31mRemoved $PROGRAM_NAME and cron jobs.\e[0m"
                break
                ;;
            "Exit")
                break
                ;;
            *) echo "Invalid option $REPLY";;
        esac
    done
}

main_menu