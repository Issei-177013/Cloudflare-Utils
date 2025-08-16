#!/bin/bash
# Installer for Cloudflare-Utils and Monitoring Agent
# This script must be run as root.

set -e

# --- Colors and Logging ---
C_RESET='\e[0m'
C_RED='\e[1;31m'
C_GREEN='\e[1;32m'
C_YELLOW='\e[1;33m'
C_BLUE='\e[1;34m'
C_CYAN='\e[1;36m'
C_MAGENTA='\e[1;35m'

log_info() { echo -e "${C_BLUE}INFO: ${1}${C_RESET}"; }
log_success() { echo -e "${C_GREEN}✅ SUCCESS: ${1}${C_RESET}"; }
log_warning() { echo -e "${C_YELLOW}⚠️ WARNING: ${1}${C_RESET}"; }
log_error() { echo -e "${C_RED}❌ ERROR: ${1}${C_RESET}"; }
die() { log_error "$1"; exit 1; }

# --- Configuration ---
CONTROLLER_PROGRAM_NAME="Cloudflare-Utils"
AGENT_PROGRAM_NAME="Cloudflare-Utils-Agent"
DEFAULT_BRANCH="main"
# Allow branch to be specified as an argument, e.g., ./install.sh dev
BRANCH="${1:-$DEFAULT_BRANCH}"
CONTROLLER_DIR="/opt/$CONTROLLER_PROGRAM_NAME"
AGENT_DIR="/opt/$AGENT_PROGRAM_NAME"
REPO_URL="https://github.com/Issei-177013/Cloudflare-Utils.git"
VERSION_TAG=""

# --- Helper Functions ---
ensure_root() {
    if [ "$EUID" -ne 0 ]; then
        die "This script must be run as root. Please use 'sudo'."
    fi
}

check_command() {
    command -v "$1" >/dev/null 2>&1 || die "Command '$1' is required but not found. Please install it."
}

# --- Pre-flight Checks ---
pre_flight_checks() {
    log_info "Running pre-flight checks..."
    ensure_root
    check_command "git"
    check_command "python3"
    check_command "pip3"
    check_command "curl"
    check_command "jq"

    if ! python3 -c "import venv" &>/dev/null; then
        log_warning "The 'python3-venv' package seems to be missing."
        log_info "Attempting to install 'python3-venv'..."
        if apt-get install -y python3-venv; then
            log_success "Successfully installed 'python3-venv'."
        else
            die "Failed to install 'python3-venv'. Please install it manually."
        fi
    fi
    log_success "All required base commands are available."
}

# --- Repository Functions ---
verify_branch_and_agent_dir() {
    log_info "Verifying branch '$BRANCH' and presence of 'src/agent' directory..."

    # Check if branch exists on the remote repository
    if ! git ls-remote --exit-code --heads "$REPO_URL" "$BRANCH" &>/dev/null; then
        die "Branch '$BRANCH' does not exist on the remote repository."
    fi
    log_info "Branch '$BRANCH' found on remote."

    # Use GitHub API to check for the 'src/agent' directory. This is a non-critical check.
    # It provides an early failure warning but falls back to local check if the API fails.
    local github_repo_path
    github_repo_path=$(echo "$REPO_URL" | sed -n 's|https://github.com/||p' | sed 's/\.git$//')
    if [ -n "$github_repo_path" ]; then
        local api_url="https://api.github.com/repos/$github_repo_path/contents/src/agent?ref=$BRANCH"
        local http_status
        http_status=$(curl -s -o /dev/null -w "%{http_code}" -H "Accept: application/vnd.github.v3+json" "$api_url")

        if [ "$http_status" -eq 200 ]; then
            log_success "'src/agent' directory confirmed on branch '$BRANCH'."
        elif [ "$http_status" -eq 404 ]; then
            die "'src/agent' directory not found on branch '$BRANCH'. Cannot proceed with Agent installation."
        else
            log_warning "Could not verify 'src/agent' via GitHub API (HTTP status: $http_status). Will clone and check locally."
        fi
    else
        log_warning "Could not parse GitHub repository path from URL. Skipping remote directory check."
    fi
}

clone_or_update_repo() {
    log_info "Cloning or updating repository from branch '$BRANCH'..."
    if [ -d "$CONTROLLER_DIR/.git" ]; then
        cd "$CONTROLLER_DIR" || die "Could not navigate to '$CONTROLLER_DIR'"
        log_info "Fetching latest changes..."
        git fetch origin --all --prune || die "Failed to fetch from repository."
        log_info "Checking out branch '$BRANCH'..."
        git checkout "$BRANCH" || die "Branch '$BRANCH' does not exist in the remote repository."
        log_info "Pulling latest changes from '$BRANCH'..."
        git pull origin "$BRANCH" || die "Failed to pull from branch '$BRANCH'."
    else
        log_info "Cloning new repository..."
        git clone --branch "$BRANCH" "$REPO_URL" "$CONTROLLER_DIR" || die "Failed to clone repository."
    fi

    cd "$CONTROLLER_DIR" || die "Could not navigate to '$CONTROLLER_DIR' after clone/pull."
    VERSION_TAG=$(git describe --tags --abbrev=0 2>/dev/null || git rev-parse --short HEAD)
    cd - > /dev/null
    log_success "Repository is up to date (Version: $VERSION_TAG)."
}

# --- Controller Functions ---
setup_controller_venv() {
    log_info "Setting up Python virtual environment for the Controller..."
    python3 -m venv "$CONTROLLER_DIR/venv" || die "Failed to create virtual environment."
    
    log_info "Upgrading pip in the new virtual environment..."
    "$CONTROLLER_DIR/venv/bin/pip" install --upgrade pip || log_warning "Failed to upgrade pip, continuing with existing version."

    log_info "Installing Controller dependencies..."
    "$CONTROLLER_DIR/venv/bin/pip" install -r "$CONTROLLER_DIR/requirements.txt" || die "Failed to install dependencies from requirements.txt."
}

setup_controller_cron() {
    log_info "Setting up cron job for IP rotation..."
    local cron_runner_path="$CONTROLLER_DIR/run.sh"
    cat << EOF > "$cron_runner_path"
#!/bin/bash
cd "$CONTROLLER_DIR"
export LOG_TO_FILE=true
"$CONTROLLER_DIR/venv/bin/python3" -m src.ip_rotator >> "$CONTROLLER_DIR/logs/cron.log" 2>&1
EOF
    chmod +x "$cron_runner_path"

    # Remove old cron job entry and add new ones
    (crontab -l 2>/dev/null | grep -v -F "$cron_runner_path") | crontab -
    (crontab -l 2>/dev/null; echo "*/1 * * * * $cron_runner_path") | crontab -
    (crontab -l 2>/dev/null; echo "@reboot $cron_runner_path") | crontab -
    log_success "Cron job set up successfully."
}

setup_log_rotation() {
    log_info "Setting up log rotation for Controller logs..."
    local logrotate_conf="/etc/logrotate.d/cloudflare-utils-controller"
    cat << EOF > "$logrotate_conf"
$CONTROLLER_DIR/logs/cron.log {
    weekly
    missingok
    rotate 4
    compress
    delaycompress
    notifempty
    create 0640 root adm
}
EOF
    log_success "Log rotation configured at $logrotate_conf."
}

install_controller() {
    log_info "--- Starting Cloudflare-Utils Controller Installation ---"
    clone_or_update_repo
    setup_controller_venv

    log_info "Creating required directories and files..."
    mkdir -p "$CONTROLLER_DIR/src" "$CONTROLLER_DIR/logs"
    touch "$CONTROLLER_DIR/logs/cron.log"
    chown -R root:root "$CONTROLLER_DIR" || log_warning "Could not set ownership to root:root. May require manual adjustment."
    
    if [ ! -f "$CONTROLLER_DIR/src/configs.json" ]; then
        echo '{"accounts": [], "agents": []}' > "$CONTROLLER_DIR/src/configs.json"
    fi

    setup_controller_cron
    setup_log_rotation

    log_info "Creating global 'cfu' command..."
    ln -sf "$CONTROLLER_DIR/cf-utils.py" "/usr/local/bin/cfu"
    chmod +x "$CONTROLLER_DIR/cf-utils.py"
    chmod +x "/usr/local/bin/cfu"

    log_success "Cloudflare-Utils Controller installed successfully (Version: $VERSION_TAG)."
    echo -e "${C_CYAN}   Use 'cfu' to manage the controller.${C_RESET}"
}

remove_controller() {
    log_info "--- Starting Cloudflare-Utils Controller Removal ---"
    local answer
    read -rp "$(echo -e "${C_YELLOW}Are you sure you want to remove the Controller? [y/N]: ${C_RESET}")" answer
    if [[ "$answer" != "y" && "$answer" != "Y" ]]; then
        log_info "Removal cancelled."
        return
    fi

    if [ ! -d "$CONTROLLER_DIR" ]; then
        log_warning "Controller directory not found. Nothing to remove."
    else
        log_info "Removing cron job..."
        (crontab -l 2>/dev/null | grep -v "$CONTROLLER_DIR/run.sh" || true) | crontab -
        
        log_info "Removing global command..."
        rm -f "/usr/local/bin/cfu"

        log_info "Removing log rotation config..."
        rm -f "/etc/logrotate.d/cloudflare-utils-controller"

        log_info "Removing directory: $CONTROLLER_DIR..."
        rm -rf "$CONTROLLER_DIR"
        log_success "Controller removed successfully."
    fi
}

# --- Agent Functions ---
install_agent() {
    log_info "--- Starting Monitoring Agent Installation ---"
    check_command "vnstat"
    verify_branch_and_agent_dir

    clone_or_update_repo
    local agent_src_dir="$CONTROLLER_DIR/src/agent"
    if [ ! -d "$agent_src_dir" ]; then
        die "Agent source files not found in '$agent_src_dir' on branch '$BRANCH'."
    fi

    log_info "Setting up Agent directory: $AGENT_DIR"
    mkdir -p "$AGENT_DIR"
    cp -r "$agent_src_dir/." "$AGENT_DIR/" || die "Failed to copy agent files."

    log_info "Setting up Python virtual environment for Agent..."
    python3 -m venv "$AGENT_DIR/venv" || die "Failed to create agent virtual environment."
    
    log_info "Upgrading pip in agent venv..."
    "$AGENT_DIR/venv/bin/pip" install --upgrade pip || log_warning "Failed to upgrade pip."

    log_info "Installing Agent dependencies (flask, psutil)..."
    "$AGENT_DIR/venv/bin/pip" install flask psutil || die "Failed to install agent dependencies."

    echo -e "\n${C_CYAN}--- Agent Configuration ---${C_RESET}"
    local api_key
    api_key=$(head /dev/urandom | tr -dc A-Za-z0-9 | head -c 32)
    
    local whitelist_input
    read -rp "Enter comma-separated IPs to whitelist (e.g., 1.1.1.1,8.8.8.8) [optional]: " whitelist_input
    local whitelist_json="\"127.0.0.1\""
    if [ -n "$whitelist_input" ]; then
        local ips
        IFS=',' read -ra ips <<< "$whitelist_input"
        for ip in "${ips[@]}"; do
            whitelist_json="$whitelist_json, \"$ip\""
        done
    else
        log_warning "Whitelist is empty. The agent will accept connections from any IP."
    fi

    local interfaces=()
    for iface_path in /sys/class/net/*; do
        if [ -d "$iface_path" ]; then
            local iface_name
            iface_name=$(basename "$iface_path")
            if [ "$iface_name" != "lo" ]; then
                interfaces+=("$iface_name")
            fi
        fi
    done
    local iface
    PS3="$(echo -e "${C_YELLOW}Please select the network interface to monitor: ${C_RESET}")"
    select iface in "${interfaces[@]}"; do
        if [[ -n "$iface" ]]; then
            break
        else
            log_warning "Invalid selection. Please try again."
        fi
    done
    log_info "Selected interface: $iface"
    log_info "Validating interface '$iface' with vnstat..."
    if ! vnstat --json d 1 -i "$iface" | jq -e '.interfaces[0].traffic.day[0]' > /dev/null 2>&1; then
        log_warning "vnstat does not appear to have any data for '$iface'."
        local answer
        read -rp "$(echo -e "${C_YELLOW}Continue anyway? [y/N]: ${C_RESET}")" answer
        if [[ "$answer" != "y" && "$answer" != "Y" ]]; then
            die "Installation cancelled by user."
        fi
    else
        log_success "vnstat validation passed for interface '$iface'."
    fi

    log_info "Creating config file: '$AGENT_DIR/config.json'"
    cat << EOF > "$AGENT_DIR/config.json"
{
  "api_key": "$api_key",
  "whitelist": [$whitelist_json],
  "vnstat_interface": "$iface"
}
EOF
    chmod 600 "$AGENT_DIR/config.json"
    chown root:root "$AGENT_DIR/config.json"

    log_info "Setting up systemd service..."
    sed "s|__PYTHON_EXEC_PATH__|$AGENT_DIR/venv/bin/python3|g" "$AGENT_DIR/cloudflare-utils-agent.service" > "/etc/systemd/system/cloudflare-utils-agent.service"
    
    log_info "Reloading systemd, enabling and starting the agent..."
    systemctl daemon-reload
    systemctl enable cloudflare-utils-agent.service || die "Failed to enable agent service."
    systemctl restart cloudflare-utils-agent.service || die "Failed to restart agent service."

    if ! systemctl is-active --quiet cloudflare-utils-agent.service; then
        log_error "Agent service failed to start. Please check the logs for errors:"
        log_error "journalctl -u cloudflare-utils-agent.service"
        die "Installation failed."
    fi

    log_success "Monitoring Agent installed and started successfully."
    echo -e "${C_GREEN}Your API Key is: ${C_YELLOW}$api_key${C_RESET}"
    echo -e "${C_CYAN}To check agent status, run: systemctl status cloudflare-utils-agent.service${C_RESET}"
}

remove_agent() {
    log_info "--- Starting Monitoring Agent Removal ---"
    local answer
    read -rp "$(echo -e "${C_YELLOW}Are you sure you want to remove the Agent? [y/N]: ${C_RESET}")" answer
    if [[ "$answer" != "y" && "$answer" != "Y" ]]; then
        log_info "Removal cancelled."
        return
    fi
    
    if [ -f "/etc/systemd/system/cloudflare-utils-agent.service" ]; then
        log_info "Stopping and disabling systemd service..."
        systemctl stop cloudflare-utils-agent.service
        if systemctl is-active --quiet cloudflare-utils-agent.service; then
            die "Failed to stop the agent service. Please stop it manually and run the removal again."
        fi
        log_success "Agent service stopped."
        systemctl disable cloudflare-utils-agent.service
        
        log_info "Removing service file..."
        rm -f "/etc/systemd/system/cloudflare-utils-agent.service"
        systemctl daemon-reload
    else
        log_warning "Agent service file not found. Skipping service removal."
    fi

    if [ ! -d "$AGENT_DIR" ]; then
        log_warning "Agent directory not found. Nothing to remove."
    else
        log_info "Removing directory: $AGENT_DIR..."
        rm -rf "$AGENT_DIR"
        log_success "Agent removed successfully."
    fi
}

# --- Verification & Rollback Functions ---
rollback_controller() {
    log_warning "--- Rolling back Controller installation ---"
    if [ ! -d "$CONTROLLER_DIR" ]; then
        log_info "Controller directory not found. Nothing to roll back."
    else
        log_info "Removing cron job..."
        (crontab -l 2>/dev/null | grep -v "$CONTROLLER_DIR/run.sh" || true) | crontab -
        
        log_info "Removing global command..."
        rm -f "/usr/local/bin/cfu"

        log_info "Removing log rotation config..."
        rm -f "/etc/logrotate.d/cloudflare-utils-controller"

        log_info "Removing directory: $CONTROLLER_DIR..."
        rm -rf "$CONTROLLER_DIR"
        log_success "Controller rollback complete."
    fi
}

rollback_agent() {
    log_warning "--- Rolling back Agent installation ---"
    if [ -f "/etc/systemd/system/cloudflare-utils-agent.service" ]; then
        log_info "Stopping and disabling systemd service..."
        systemctl stop cloudflare-utils-agent.service
        systemctl disable cloudflare-utils-agent.service
        
        log_info "Removing service file..."
        rm -f "/etc/systemd/system/cloudflare-utils-agent.service"
        systemctl daemon-reload
    fi

    if [ -d "$AGENT_DIR" ]; then
        log_info "Removing directory: $AGENT_DIR..."
        rm -rf "$AGENT_DIR"
        log_success "Agent rollback complete."
    fi
}

verify_controller_installation() {
    log_info "--- Verifying Controller Installation ---"
    local all_checks_passed=true
    local checklist=""

    # Check 1: Directory
    if [ -d "$CONTROLLER_DIR" ]; then
        checklist+="${C_GREEN}[✓]${C_RESET} Controller directory exists at '$CONTROLLER_DIR'.\n"
    else
        checklist+="${C_RED}[✗]${C_RESET} Controller directory not found at '$CONTROLLER_DIR'.\n"
        all_checks_passed=false
    fi

    # Check 2: Venv
    if [ -d "$CONTROLLER_DIR/venv" ]; then
        checklist+="${C_GREEN}[✓]${C_RESET} Python virtual environment exists.\n"
    else
        checklist+="${C_RED}[✗]${C_RESET} Python virtual environment not found.\n"
        all_checks_passed=false
    fi
    
    # Check 3: Dependencies
    if [ -f "$CONTROLLER_DIR/venv/bin/pip" ] && "$CONTROLLER_DIR/venv/bin/pip" freeze | grep -qi "requests"; then
        checklist+="${C_GREEN}[✓]${C_RESET} Python dependencies are installed.\n"
    else
        checklist+="${C_RED}[✗]${C_RESET} Python dependencies are not installed correctly.\n"
        all_checks_passed=false
    fi

    # Check 4: Cron job
    if crontab -l 2>/dev/null | grep -q "$CONTROLLER_DIR/run.sh"; then
        checklist+="${C_GREEN}[✓]${C_RESET} Cron job is configured.\n"
    else
        checklist+="${C_RED}[✗]${C_RESET} Cron job is not configured.\n"
        all_checks_passed=false
    fi

    # Check 5: Global command
    if [ -L "/usr/local/bin/cfu" ] && [ -x "/usr/local/bin/cfu" ]; then
        checklist+="${C_GREEN}[✓]${C_RESET} Global command 'cfu' is set up correctly.\n"
    else
        checklist+="${C_RED}[✗]${C_RESET} Global command 'cfu' not found or not executable.\n"
        all_checks_passed=false
    fi

    echo -e "\n$checklist"

    if [ "$all_checks_passed" = true ]; then
        log_success "Installation verified successfully. All components are working correctly."
    else
        log_error "Controller installation verification failed."
        local answer
        read -rp "$(echo -e "${C_YELLOW}An error occurred during verification. Do you want to roll back the installation? [Y/n]: ${C_RESET}")" answer
        if [[ "$answer" != "n" && "$answer" != "N" ]]; then
            rollback_controller
        fi
        die "Aborting due to verification failure."
    fi
}

verify_agent_installation() {
    log_info "--- Verifying Agent Installation ---"
    local all_checks_passed=true
    local checklist=""
    local config_file="$AGENT_DIR/config.json"

    # Check 1: Directory
    if [ -d "$AGENT_DIR" ]; then
        checklist+="${C_GREEN}[✓]${C_RESET} Agent directory exists at '$AGENT_DIR'.\n"
    else
        checklist+="${C_RED}[✗]${C_RESET} Agent directory not found at '$AGENT_DIR'.\n"
        all_checks_passed=false
    fi

    # Check 2: Venv
    if [ -d "$AGENT_DIR/venv" ]; then
        checklist+="${C_GREEN}[✓]${C_RESET} Agent Python virtual environment exists.\n"
    else
        checklist+="${C_RED}[✗]${C_RESET} Agent Python virtual environment not found.\n"
        all_checks_passed=false
    fi

    # Check 3: Dependencies
    if [ -f "$AGENT_DIR/venv/bin/pip" ] && "$AGENT_DIR/venv/bin/pip" freeze | grep -qi "flask"; then
        checklist+="${C_GREEN}[✓]${C_RESET} Agent Python dependencies are installed.\n"
    else
        checklist+="${C_RED}[✗]${C_RESET} Agent Python dependencies are not installed correctly.\n"
        all_checks_passed=false
    fi

    # Check 4: Config file and its security
    if [ -f "$config_file" ]; then
        checklist+="${C_GREEN}[✓]${C_RESET} Agent config file exists at '$config_file'.\n"
        local perms; perms=$(stat -c "%a" "$config_file")
        if [ "$perms" = "600" ]; then
            checklist+="${C_GREEN}[✓]${C_RESET} Config file permissions are correct (600).\n"
        else
            checklist+="${C_RED}[✗]${C_RESET} Config file permissions are incorrect (should be 600, are $perms).\n"
            all_checks_passed=false
        fi
        local owner; owner=$(stat -c "%U:%G" "$config_file")
        if [ "$owner" = "root:root" ]; then
            checklist+="${C_GREEN}[✓]${C_RESET} Config file ownership is correct (root:root).\n"
        else
            checklist+="${C_RED}[✗]${C_RESET} Config file ownership is incorrect (should be root:root, is $owner).\n"
            all_checks_passed=false
        fi
        if jq -e '.api_key | test(".+")' "$config_file" > /dev/null; then
            checklist+="${C_GREEN}[✓]${C_RESET} API key is present in config file.\n"
        else
            checklist+="${C_RED}[✗]${C_RESET} API key is missing or empty in config file.\n"
            all_checks_passed=false
        fi
    else
        checklist+="${C_RED}[✗]${C_RESET} Agent config file not found.\n"
        all_checks_passed=false
    fi
    
    # Check 5: Systemd service
    if [ -f "/etc/systemd/system/cloudflare-utils-agent.service" ]; then
        checklist+="${C_GREEN}[✓]${C_RESET} Systemd service file exists.\n"
        if systemctl is-enabled --quiet cloudflare-utils-agent.service; then
            checklist+="${C_GREEN}[✓]${C_RESET} Agent service is enabled.\n"
        else
            checklist+="${C_RED}[✗]${C_RESET} Agent service is not enabled.\n"
            all_checks_passed=false
        fi
        if systemctl is-active --quiet cloudflare-utils-agent.service; then
            checklist+="${C_GREEN}[✓]${C_RESET} Agent service is active and running.\n"
        else
            checklist+="${C_RED}[✗]${C_RESET} Agent service is not running.\n"
            all_checks_passed=false
        fi
    else
        checklist+="${C_RED}[✗]${C_RESET} Systemd service file not found.\n"
        all_checks_passed=false
    fi

    echo -e "\n$checklist"

    if [ "$all_checks_passed" = true ]; then
        log_success "Installation verified successfully. All components are working correctly."
    else
        log_error "Agent installation verification failed."
        local answer
        read -rp "$(echo -e "${C_YELLOW}An error occurred during verification. Do you want to roll back the installation? [Y/n]: ${C_RESET}")" answer
        if [[ "$answer" != "n" && "$answer" != "N" ]]; then
            rollback_agent
        fi
        die "Aborting due to verification failure."
    fi
}

# --- Main Menu ---
main_menu() {
    clear
    echo -e "${C_MAGENTA}--- Cloudflare-Utils & Monitoring Agent Installer ---${C_RESET}"
    if [ -n "$VERSION_TAG" ]; then
        echo -e "${C_CYAN}Version: $VERSION_TAG${C_RESET}"
    fi
    PS3="$(echo -e "${C_YELLOW}\nPlease choose an option: ${C_RESET}")"
    options=(
        "Install/Update Controller"
        "Install/Update Agent"
        "Remove Controller"
        "Remove Agent"
        "Exit"
    )
    select opt in "${options[@]}"; do
        case $opt in
            "Install/Update Controller")
                install_controller
                verify_controller_installation
                break
                ;;
            "Install/Update Agent")
                install_agent
                verify_agent_installation
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
            *) log_warning "Invalid option '$REPLY'";;
        esac
    done
}

# --- Main Execution ---
pre_flight_checks
clone_or_update_repo # Clone once at the start to get version tag for the menu
main_menu