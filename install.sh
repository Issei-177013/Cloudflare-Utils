#!/bin/bash
set -e

PROGRAM_NAME="Cloudflare-Utils"
DEFAULT_BRANCH="dev"
BRANCH="${1:-$DEFAULT_BRANCH}"
PROGRAM_DIR="/opt/$PROGRAM_NAME"
VERSION_TAG=""

# Install required system and Python packages
install_packages() {
    echo -e "\e[1;34mInstalling dependencies...\e[0m"
    sudo apt-get update
    sudo apt-get install -y git python3-pip

    # Determine Python minor version
    PY_MINOR=$(python3 -c "import sys; print(sys.version_info.minor)")
    if [[ "$PY_MINOR" -ge 11 ]]; then
        pip3 install --break-system-packages cloudflare python-dotenv
    else
        pip3 install cloudflare python-dotenv
    fi
}

# Clone or update the repository from the specified branch
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

# Create the runner script for cron usage
create_runner() {
    cat << EOF > "$PROGRAM_DIR/run.sh"
#!/bin/bash
cd "$PROGRAM_DIR"
echo "\$(date) - Running Cloudflare-Utils $VERSION_TAG" >> log_file.log
python3 config_manager.py >> log_file.log 2>&1
EOF

    chmod +x "$PROGRAM_DIR/run.sh"
}

# Create the initial configuration file if not exists
setup_config_file() {
    echo -e "\e[1;34mSetting up config file...\e[0m"
    CONFIG_FILE_PATH="$PROGRAM_DIR/configs.json"
    if [ ! -f "$CONFIG_FILE_PATH" ]; then
        echo '{"accounts": []}' > "$CONFIG_FILE_PATH"
        echo -e "\e[1;32mCreated empty config file: $CONFIG_FILE_PATH\e[0m"
    else
        echo -e "\e[1;33mConfig file already exists: $CONFIG_FILE_PATH\e[0m"
    fi

    # Set file ownership to the original user who ran sudo
    if [ -n "$SUDO_USER" ]; then
        chown "$SUDO_USER:$SUDO_USER" "$CONFIG_FILE_PATH"
        echo -e "\e[1;32mSet owner of $CONFIG_FILE_PATH to $SUDO_USER\e[0m"
    else
        echo -e "\e[1;33mWarning: SUDO_USER not set. File permissions may need manual adjustment.\e[0m"
    fi
}

# Configure cron jobs to run the tool periodically
setup_cron() {
    echo -e "\e[1;34mSetting up cron...\e[0m"
    CRON_JOB_RUNNER="/bin/bash $PROGRAM_DIR/run.sh"
    
    # Remove existing entries
    (crontab -l 2>/dev/null | grep -v -F "$CRON_JOB_RUNNER" || true) | crontab -
    
    # Add new entries
    (crontab -l 2>/dev/null; echo "*/1 * * * * $CRON_JOB_RUNNER") | crontab -
    (crontab -l 2>/dev/null; echo "@reboot $CRON_JOB_RUNNER") | crontab -
    
    echo -e "\e[1;32mCron job set to run every 1 minute and on system reboot.\e[0m"
}

# Main interactive menu
main_menu() {
    PS3="Please choose: "
    options=("Install $PROGRAM_NAME (branch '$BRANCH')" "Remove $PROGRAM_NAME" "Exit")
    select opt in "${options[@]}"; do
        case $opt in
            "Install $PROGRAM_NAME (branch '$BRANCH')")
                install_packages
                clone_repository
                create_runner
                setup_config_file
                setup_cron

                # Create global command alias
                CLI_PATH="$PROGRAM_DIR/cli.py"
                GLOBAL_CMD_PATH="/usr/local/bin/cfutils"
                echo -e "\e[1;34mCreating global command '$GLOBAL_CMD_PATH'...\e[0m"
                if [ -f "$CLI_PATH" ]; then
                    ln -sf "$CLI_PATH" "$GLOBAL_CMD_PATH"
                    chmod +x "$CLI_PATH"
                    chmod +x "$GLOBAL_CMD_PATH"
                    echo -e "\e[1;32m✅ Global command 'cfutils' created. You can now use 'cfutils' from anywhere.\e[0m"
                else
                    echo -e "\e[1;31m❌ Error: $CLI_PATH not found. Cannot create global command.\e[0m"
                fi

                echo -e "\e[1;32m✅ Installed version: $VERSION_TAG\e[0m"
                echo -e "\e[1;32m📌 You can also run: \`python3 $PROGRAM_DIR/cli.py\`\e[0m"
                break
                ;;
            "Remove $PROGRAM_NAME")
                echo -e "\e[1;34mRemoving $PROGRAM_NAME...\e[0m"
                sudo rm -rf "$PROGRAM_DIR"
                crontab -l | grep -v "$PROGRAM_DIR/run.sh" | crontab -

                GLOBAL_CMD_PATH="/usr/local/bin/cfutils"
                if [ -L "$GLOBAL_CMD_PATH" ]; then
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