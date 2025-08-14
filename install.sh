#!/bin/bash
set -e

# --- Configuration ---
CONTROLLER_PROGRAM_NAME="Cloudflare-Utils"
AGENT_PROGRAM_NAME="cloudflare-agent"
DEFAULT_BRANCH="main"
# Allow branch to be specified as an argument, e.g., ./install.sh dev
BRANCH="${1:-$DEFAULT_BRANCH}"
CONTROLLER_DIR="/opt/$CONTROLLER_PROGRAM_NAME"
AGENT_DIR="/opt/$AGENT_PROGRAM_NAME"
VERSION_TAG=""

# --- Helper Functions ---
install_base_dependencies() {
    echo -e "\e[1;34mInstalling base dependencies (git, python3-pip, python3-venv)...\e[0m"
    sudo apt-get update
    sudo apt-get install -y git python3-pip python3-venv
}

clone_repository() {
    echo -e "\e[1;34mCloning repository from branch '$BRANCH' into $CONTROLLER_DIR...\e[0m"
    if [ -d "$CONTROLLER_DIR/.git" ]; then
        cd "$CONTROLLER_DIR"
        git fetch origin --all
        git checkout "$BRANCH"
        git pull origin "$BRANCH"
    else
        git clone --branch "$BRANCH" https://github.com/Issei-177013/Cloudflare-Utils.git "$CONTROLLER_DIR"
    fi

    cd "$CONTROLLER_DIR"
    VERSION_TAG=$(git describe --tags --abbrev=0 2>/dev/null || git rev-parse --short HEAD)
    cd - > /dev/null
    echo -e "\e[1;32m✅ Repository cloned/updated successfully.\e[0m"
}

# --- Controller Functions ---
install_controller() {
    echo -e "\n\e[1;36m--- Installing Cloudflare-Utils Controller ---\e[0m"
    install_base_dependencies
    clone_repository

    echo -e "\e[1;34mSetting up Python virtual environment...\e[0m"
    python3 -m venv "$CONTROLLER_DIR/venv"

    echo -e "\e[1;34mInstalling Controller Python dependencies into virtual environment...\e[0m"
    "$CONTROLLER_DIR/venv/bin/pip" install -r "$CONTROLLER_DIR/requirements.txt"
    
    echo -e "\e[1;34mSetting up runner script, config file, and cron job...\e[0m"
    # Create runner for cron job
    cat << EOF > "$CONTROLLER_DIR/run.sh"
#!/bin/bash
cd "$CONTROLLER_DIR"
export LOG_TO_FILE=true
"$CONTROLLER_DIR/venv/bin/python3" -m src.ip_rotator
EOF
    chmod +x "$CONTROLLER_DIR/run.sh"

    # Create config file if it doesn't exist
    mkdir -p "$CONTROLLER_DIR/src"
    if [ ! -f "$CONTROLLER_DIR/src/configs.json" ]; then
        echo '{"accounts": [], "agents": []}' > "$CONTROLLER_DIR/src/configs.json"
    fi
    mkdir -p "$CONTROLLER_DIR/logs"

    # Setup cron job
    CRON_JOB_RUNNER="/bin/bash $CONTROLLER_DIR/run.sh"
    (crontab -l 2>/dev/null | grep -v -F "$CRON_JOB_RUNNER" || true) | crontab -
    (crontab -l 2>/dev/null; echo "*/1 * * * * $CRON_JOB_RUNNER") | crontab -
    (crontab -l 2>/dev/null; echo "@reboot $CRON_JOB_RUNNER") | crontab -

    # Create global command
    ln -sf "$CONTROLLER_DIR/cf-utils.py" "/usr/local/bin/cfu"
    chmod +x "$CONTROLLER_DIR/cf-utils.py"
    chmod +x "/usr/local/bin/cfu"

    echo -e "\e[1;32m✅ Cloudflare-Utils Controller installed successfully (Version: $VERSION_TAG).\e[0m"
    echo -e "\e[1;32m   Use 'cfu' to manage the controller.\e[0m"
}

remove_controller() {
    echo -e "\n\e[1;31m--- Removing Cloudflare-Utils Controller ---\e[0m"
    read -rp "Are you sure you want to remove the Controller? [y/N]: " answer
    if [[ "$answer" != "y" && "$answer" != "Y" ]]; then
        echo "Removal cancelled."
        return
    fi

    if [ ! -d "$CONTROLLER_DIR" ]; then
        echo -e "\e[1;33mController directory not found. Nothing to remove.\e[0m"
    else
        echo "Removing cron job..."
        (crontab -l 2>/dev/null | grep -v "$CONTROLLER_DIR/run.sh" || true) | crontab -
        
        echo "Removing global command..."
        rm -f "/usr/local/bin/cfu"

        echo "Removing directory..."
        rm -rf "$CONTROLLER_DIR"
        echo -e "\e[1;32m✅ Controller removed successfully.\e[0m"
    fi
}

# --- Agent Functions ---
install_agent() {
    echo -e "\n\e[1;36m--- Installing Monitoring Agent ---\e[0m"
    install_base_dependencies

    echo -e "\e[1;34mInstalling Agent system dependencies (vnstat)...\e[0m"
    sudo apt-get install -y vnstat

    echo -e "\e[1;34mInstalling Agent Python dependencies (flask, psutil)...\e[0m"
    pip3 install --break-system-packages flask psutil

    clone_repository
    AGENT_SRC_DIR="$CONTROLLER_DIR/src/agent"

    if [ ! -d "$AGENT_SRC_DIR" ]; then
        echo -e "\e[1;31mError: Agent source files not found in '$AGENT_SRC_DIR'. Aborting.\e[0m"
        exit 1
    fi

    echo -e "\e[1;34mSetting up Agent directory: $AGENT_DIR\e[0m"
    mkdir -p "$AGENT_DIR"
    cp -r "$AGENT_SRC_DIR"/* "$AGENT_DIR/"

    echo -e "\n\e[1;34m--- Agent Configuration ---\e[0m"
    read -rp "Enter a secure API Key for the agent (leave blank to generate one): " api_key
    if [ -z "$api_key" ]; then
        api_key=$(head /dev/urandom | tr -dc A-Za-z0-9 | head -c 32)
        echo "Generated API Key: $api_key"
    fi

    read -rp "Enter the controller's IP address to whitelist: " whitelist_ip
    while [ -z "$whitelist_ip" ]; do
        read -rp "Whitelist IP cannot be empty. Please enter the controller's IP: " whitelist_ip
    done

    # --- FIXED network interface detection ---
    interfaces_list=()
    for iface in /sys/class/net/*; do
        iface_name=$(basename "$iface")
        [ "$iface_name" != "lo" ] && interfaces_list+=("$iface_name")
    done
    interfaces_str="${interfaces_list[*]}"
    # ------------------------------------------

    read -rp "Enter the network interface to monitor (detected: $interfaces_str): " vnstat_interface
    if [ -z "$vnstat_interface" ]; then
        vnstat_interface=$(echo "$interfaces_str" | awk '{print $1}')
        echo "No interface specified, using default: $vnstat_interface"
    fi

    echo -e "\e[1;34mCreating config file: $AGENT_DIR/config.json\e[0m"
    cat << EOF > "$AGENT_DIR/config.json"
{
  "api_key": "$api_key",
  "whitelist": ["$whitelist_ip", "127.0.0.1"],
  "vnstat_interface": "$vnstat_interface"
}
EOF

    echo -e "\e[1;34mSetting up systemd service...\e[0m"
    cp "$AGENT_DIR/cloudflare-agent.service" "/etc/systemd/system/"
    systemctl daemon-reload
    systemctl enable cloudflare-agent.service
    systemctl restart cloudflare-agent.service

    echo -e "\e[1;32m✅ Monitoring Agent installed and started successfully.\e[0m"
    echo -e "\e[1;33mTo check agent status, run: systemctl status cloudflare-agent\e[0m"
}

remove_agent() {
    echo -e "\n\e[1;31m--- Removing Monitoring Agent ---\e[0m"
    read -rp "Are you sure you want to remove the Agent? [y/N]: " answer
    if [[ "$answer" != "y" && "$answer" != "Y" ]]; then
        echo "Removal cancelled."
        return
    fi
    
    if [ -f "/etc/systemd/system/cloudflare-agent.service" ]; then
        echo "Stopping and disabling systemd service..."
        systemctl stop cloudflare-agent.service || true
        systemctl disable cloudflare-agent.service || true
        
        echo "Removing service file..."
        rm -f "/etc/systemd/system/cloudflare-agent.service"
        systemctl daemon-reload
    else
        echo -e "\e[1;33mAgent service file not found. Skipping service removal.\e[0m"
    fi

    if [ ! -d "$AGENT_DIR" ]; then
        echo -e "\e[1;33mAgent directory not found. Nothing to remove.\e[0m"
    else
        echo "Removing directory..."
        rm -rf "$AGENT_DIR"
        echo -e "\e[1;32m✅ Agent removed successfully.\e[0m"
    fi
}

# --- Main Menu ---
main_menu() {
    clear
    echo -e "\e[1;35m--- Cloudflare-Utils & Monitoring Agent Installer ---\e[0m"
    PS3="\nPlease choose an option: "
    options=(
        "Install/Update Controller (Cloudflare-Utils)"
        "Install/Update Agent (on remote server)"
        "Remove Controller"
        "Remove Agent"
        "Exit"
    )
    select opt in "${options[@]}"; do
        case $opt in
            "Install/Update Controller (Cloudflare-Utils)")
                install_controller
                break
                ;;
            "Install/Update Agent (on remote server)")
                install_agent
                break
                ;;
            "Remove Controller")
                remove_controller
                break
                ;;
            "Remove Agent")
                remove_agent
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