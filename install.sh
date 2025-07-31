#!/bin/bash
set -e

PROGRAM_NAME="Cloudflare-Utils"
DEFAULT_BRANCH="main"
BRANCH="${1:-$DEFAULT_BRANCH}"
PROGRAM_DIR="/opt/$PROGRAM_NAME"
VERSION_TAG=""

install_dependencies() {
    echo -e "\e[1;34mUpdating system and installing dependencies...\e[0m"
    sudo apt-get update
    sudo apt-get install -y git python3-pip python3-venv

    # Handle conflicting apt package for typing-extensions
    if dpkg -s python3-typing-extensions &>/dev/null; then
        echo -e "\e[1;33mDetected conflicting package 'python3-typing-extensions' installed by apt.\e[0m"
        read -rp "Remove it to prevent pip conflicts? [y/N]: " ans
        if [[ "$ans" =~ ^[Yy]$ ]]; then
            sudo apt-get remove -y python3-typing-extensions
        else
            echo -e "\e[1;31mCannot continue without removing 'python3-typing-extensions'. Aborting.\e[0m"
            exit 1
        fi
    fi
}

clone_or_update_repo() {
    if [ -d "$PROGRAM_DIR/.git" ]; then
        echo -e "\e[1;34mRepository found. Fetching latest from branch '$BRANCH'...\e[0m"
        cd "$PROGRAM_DIR"
        git fetch origin
        git checkout "$BRANCH"
        git pull origin "$BRANCH"
        cd - >/dev/null
    else
        echo -e "\e[1;34mCloning repository branch '$BRANCH'...\e[0m"
        git clone --branch "$BRANCH" https://github.com/Issei-177013/Cloudflare-Utils.git "$PROGRAM_DIR"
    fi
    cd "$PROGRAM_DIR"
    VERSION_TAG=$(git describe --tags --abbrev=0 2>/dev/null || git rev-parse --short HEAD)
    cd - >/dev/null
}

setup_python_env() {
    echo -e "\e[1;34mSetting up Python virtual environment...\e[0m"
    # Create venv if not exists
    if [ ! -d "$PROGRAM_DIR/venv" ]; then
        python3 -m venv "$PROGRAM_DIR/venv"
    fi

    # Upgrade pip and install requirements in venv
    source "$PROGRAM_DIR/venv/bin/activate"
    pip install --upgrade pip setuptools wheel
    pip install --break-system-packages -r "$PROGRAM_DIR/requirements.txt"
    deactivate
}

create_runner_script() {
    cat > "$PROGRAM_DIR/run.sh" << EOF
#!/bin/bash
cd "$PROGRAM_DIR"
source "$PROGRAM_DIR/venv/bin/activate"
echo "\$(date) - Running Cloudflare-Utils $VERSION_TAG" >> log_file.log
python3 -m src.ip_rotator >> log_file.log 2>&1
EOF
    chmod +x "$PROGRAM_DIR/run.sh"
}

setup_config() {
    echo -e "\e[1;34mSetting up config file...\e[0m"
    local config_path="$PROGRAM_DIR/src/configs.json"
    if [ ! -f "$config_path" ]; then
        echo '{"accounts": []}' > "$config_path"
        echo -e "\e[1;32mCreated empty config file at $config_path\e[0m"
    else
        echo -e "\e[1;33mConfig file already exists at $config_path\e[0m"
    fi

    if [ -n "$SUDO_USER" ]; then
        chown "$SUDO_USER:$SUDO_USER" "$config_path"
        echo -e "\e[1;32mSet ownership of config file to $SUDO_USER\e[0m"
    else
        echo -e "\e[1;33mWarning: SUDO_USER not set. Manual permission adjustment may be needed.\e[0m"
    fi
}

setup_cron_jobs() {
    echo -e "\e[1;34mConfiguring cron jobs...\e[0m"
    local cron_cmd="/bin/bash $PROGRAM_DIR/run.sh"
    # Remove old entries for this command to prevent duplicates
    (crontab -l 2>/dev/null | grep -v -F "$cron_cmd" || true) | crontab -

    # Add cron jobs for every minute and reboot
    (crontab -l 2>/dev/null; echo "*/1 * * * * $cron_cmd") | crontab -
    (crontab -l 2>/dev/null; echo "@reboot $cron_cmd") | crontab -

    echo -e "\e[1;32mCron job set to run every minute and on reboot.\e[0m"
}

create_global_command() {
    local cli_script="$PROGRAM_DIR/cf-utils.py"
    local global_cmd="/usr/local/bin/cfu"

    echo -e "\e[1;34mCreating global command '$global_cmd'...\e[0m"
    if [ -f "$cli_script" ]; then
        ln -sf "$cli_script" "$global_cmd"
        chmod +x "$cli_script" "$global_cmd"
        echo -e "\e[1;32m✅ Global command 'cfu' created.\e[0m"
    else
        echo -e "\e[1;31m❌ Cannot find $cli_script, skipping global command creation.\e[0m"
    fi
}

remove_program() {
    echo -e "\e[1;34mRemoving $PROGRAM_NAME...\e[0m"
    sudo rm -rf "$PROGRAM_DIR"
    (crontab -l 2>/dev/null | grep -v "$PROGRAM_DIR/run.sh" || true) | crontab -
    local global_cmd="/usr/local/bin/cfu"
    if [ -L "$global_cmd" ]; then
        sudo rm -f "$global_cmd"
        echo -e "\e[1;32mRemoved global command 'cfu'.\e[0m"
    fi
    echo -e "\e[1;31m$PROGRAM_NAME and cron jobs removed.\e[0m"
}

main_menu() {
    PS3="Choose an option: "
    options=(
        "Install $PROGRAM_NAME (branch '$BRANCH')"
        "Remove $PROGRAM_NAME"
        "Exit"
    )
    select opt in "${options[@]}"; do
        case "$opt" in
            "Install $PROGRAM_NAME (branch '$BRANCH')")
                install_dependencies
                clone_or_update_repo
                setup_python_env
                create_runner_script
                setup_config
                setup_cron_jobs
                create_global_command
                echo -e "\e[1;32m✅ Installed version: $VERSION_TAG\e[0m"
                echo -e "\e[1;33mUse 'cfu' to run the CLI or 'bash $PROGRAM_DIR/run.sh' for the runner.\e[0m"
                break
                ;;
            "Remove $PROGRAM_NAME")
                remove_program
                break
                ;;
            "Exit")
                break
                ;;
            *)
                echo "Invalid option. Try again."
                ;;
        esac
    done
}

main_menu
