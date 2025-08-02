#!/bin/bash
set -e

PROGRAM_NAME="Cloudflare-Utils"
DEFAULT_BRANCH="main"
BRANCH="${1:-$DEFAULT_BRANCH}"
PROGRAM_DIR="/opt/$PROGRAM_NAME"
VERSION_TAG=""

install_packages() {
    echo -e "\e[1;34mInstalling dependencies...\e[0m"
    sudo apt-get update
    sudo apt-get install -y git python3-pip

    # Check if typing-extensions is installed by apt
    if dpkg -s python3-typing-extensions &> /dev/null; then
        echo -e "\e[1;33mDetected 'python3-typing-extensions' package installed by apt, which may conflict with pip.\e[0m"
        read -rp "Do you want to remove 'python3-typing-extensions' to avoid conflicts? [y/N]: " answer
        case "$answer" in
            [Yy]* )
                echo -e "\e[1;34mRemoving 'python3-typing-extensions'...\e[0m"
                sudo apt-get remove -y python3-typing-extensions || {
                    echo -e "\e[1;31mFailed to remove 'python3-typing-extensions'. Aborting installation.\e[0m"
                    exit 1
                }
                ;;
            * )
                echo -e "\e[1;31mCannot proceed without removing 'python3-typing-extensions'. Aborting.\e[0m"
                exit 1
                ;;
        esac
    fi

    pip3 install --break-system-packages cloudflare python-dotenv coloredlogs tabulate
}


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

create_runner() {
    cat << EOF > "$PROGRAM_DIR/run.sh"
#!/bin/bash
cd "$PROGRAM_DIR"
export LOG_TO_FILE=true
python3 -m src.ip_rotator
EOF

    chmod +x "$PROGRAM_DIR/run.sh"
}

# Function to set up the configuration file
setup_config_file() {
    echo -e "\e[1;34mSetting up config file and logs directory...\e[0m"
    CONFIG_FILE_PATH="$PROGRAM_DIR/src/configs.json"
    LOGS_DIR_PATH="$PROGRAM_DIR/logs"

    # Create config file if it doesn't exist
    if [ ! -f "$CONFIG_FILE_PATH" ]; then
        echo '{"accounts": []}' > "$CONFIG_FILE_PATH"
        echo -e "\e[1;32mCreated empty config file: $CONFIG_FILE_PATH\e[0m"
    else
        echo -e "\e[1;33mConfig file already exists, no changes made.\e[0m"
    fi

    # Create logs directory if it doesn't exist
    mkdir -p "$LOGS_DIR_PATH"
    echo -e "\e[1;32mEnsured logs directory exists: $LOGS_DIR_PATH\e[0m"
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
    echo -e "\e[1;32mCron job set to run every 1 minute and on reboot.\e[0m"
}

# Main menu
main_menu() {
    PS3="Please choose: "
    options=("Install $PROGRAM_NAME (branch '$BRANCH')" "Remove $PROGRAM_NAME" "Exit")
    select opt in "${options[@]}"; do
        case $opt in
            "Install $PROGRAM_NAME (branch '$BRANCH')")
                install_packages
                clone_repository

                echo -e "\e[1;34mRemoving old log file...\e[0m"
                rm -f "$PROGRAM_DIR/log_file.log"

                create_runner
                setup_config_file # Call the new function
                setup_cron

                # Create global command
                CLI_PATH="$PROGRAM_DIR/cf-utils.py"
                GLOBAL_CMD_PATH="/usr/local/bin/cfu"
                echo -e "\e[1;34mCreating global command '$GLOBAL_CMD_PATH'...\e[0m"
                if [ -f "$CLI_PATH" ]; then
                    ln -sf "$CLI_PATH" "$GLOBAL_CMD_PATH"
                    chmod +x "$CLI_PATH" # Ensure the script itself is executable
                    chmod +x "$GLOBAL_CMD_PATH" # Ensure the symlink is executable
                    echo -e "\e[1;32m✅ Global command 'cfu' created. You can now use 'cfu' from anywhere.\e[0m"
                else
                    echo -e "\e[1;31m❌ Error: $CLI_PATH not found. Cannot create global command.\e[0m"
                fi

                echo -e "\e[1;32m✅ Installed version: $VERSION_TAG\e[0m"
                echo -e "\e[1;32m📌 You can also use \`python3 $PROGRAM_DIR/cf-utils.py\` to manage settings.\e[0m"
                break
                ;;
            "Remove $PROGRAM_NAME")
                echo -e "\e[1;34mRemoving $PROGRAM_NAME...\e[0m"
                sudo rm -rf "$PROGRAM_DIR"
                crontab -l | grep -v "$PROGRAM_DIR/run.sh" | crontab -
                
                # Remove global command
                GLOBAL_CMD_PATH="/usr/local/bin/cfu"
                if [ -L "$GLOBAL_CMD_PATH" ]; then # Check if it's a symlink
                    echo -e "\e[1;34mRemoving global command '$GLOBAL_CMD_PATH'...\e[0m"
                    sudo rm -f "$GLOBAL_CMD_PATH"
                    echo -e "\e[1;32m✅ Global command 'cfu' removed.\e[0m"
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