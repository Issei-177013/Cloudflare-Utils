#!/bin/bash
# Installer for Cloudflare-Utils and Monitoring Agent
# This script must be run as root.

set -e
trap 'log_error "Installer aborted unexpectedly at line $LINENO"' ERR

# --- Logging Setup ---
LOG_DIR="/var/log/cloudflare-utils"
mkdir -p "$LOG_DIR"
INSTALL_LOG_FILE="$LOG_DIR/installer.log"
exec > >(tee "$INSTALL_LOG_FILE") 2>&1
echo "--- Starting Cloudflare-Utils Installer Log $(date) ---"

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

# --- Configuration & Argument Defaults ---
CFUTILS_PROGRAM_NAME="Cloudflare-Utils"
AGENT_PROGRAM_NAME="Cloudflare-Utils-Agent"
CFUTILS_DIR="/opt/$CFUTILS_PROGRAM_NAME"
AGENT_DIR="/opt/$AGENT_PROGRAM_NAME"
REPO_URL="https://github.com/Issei-177013/Cloudflare-Utils.git"
VERSION_TAG=""

# Flags & Defaults
INTERACTIVE_MODE=true
BRANCH="main"
LOCAL_DEV_PATH=""
UNINSTALL_MODE=false
AGENT_MODE=false
IP_WHITELIST=""
IFACE=""

# --- Helper Functions ---
usage() {
    echo "Usage: $0 [options]"
    echo "  Run without options for interactive mode."
    echo ""
    echo "Options:"
    echo "  -b <branch>              Specify the branch to install from (default: main)."
    echo "  -p <path>                Use a local development path."
    echo "  -u                       Uninstall the application."
    echo "  --agent                  Install or uninstall the agent instead of the main utility."
    echo "  --ip-whitelist <ips>     Comma-separated IPs to whitelist for the agent."
    echo "  --iface <interface>      Network interface for the agent to monitor."
    echo "  -h, --help               Display this help and exit."
    exit 0
}

ensure_root() {
    if [ "$EUID" -ne 0 ]; then
        die "This script must be run as root. Please use 'sudo'."
    fi
}

check_command() {
    local command="$1"
    local package_name="$2"

    if which "$command" >/dev/null 2>&1; then
        return 0
    fi

    log_warning "Command '$command' is required but not found."

    if [ -z "$package_name" ]; then
        package_name="$command"
    fi

    log_info "Attempting to install '$package_name'..."
    if apt-get install -y "$package_name"; then
        log_success "Successfully installed '$package_name'."
    else
        die "Failed to install '$package_name'. Please install it manually."
    fi

    if ! which "$command" >/dev/null 2>&1; then
        die "Command '$command' could not be found even after installation. Please check your PATH or install it manually."
    fi
}

# --- Pre-flight Checks ---
pre_flight_checks() {
    log_info "Running pre-flight checks..."
    ensure_root
    check_command "git" "git"
    check_command "python3" "python3"
    check_command "pip3" "python3-pip"
    check_command "curl" "curl"
    check_command "jq" "jq"
    check_command "openssl" "openssl"
    check_command "vnstat" "vnstat"
    check_command "crontab" "cron"

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
    if [ -t 1 ]; then clear; fi
}

# --- Repository Functions ---
verify_branch_exists() {
    log_info "Verifying branch '$BRANCH' exists on remote..."
    if ! git ls-remote --exit-code --heads "$REPO_URL" "$BRANCH" &>/dev/null; then
        die "Branch '$BRANCH' does not exist on the remote repository."
    fi
    log_success "Branch '$BRANCH' found on remote."
}

verify_branch_and_agent_dir() {
    if [ -n "$LOCAL_DEV_PATH" ]; then
        log_info "Verifying 'src/agent' directory in local path..."
        if [ ! -d "$LOCAL_DEV_PATH/src/agent" ]; then
            die "Agent source directory 'src/agent' not found in '$LOCAL_DEV_PATH'."
        fi
        log_success "'src/agent' directory found in local path."
        return
    fi

    log_info "Verifying branch '$BRANCH' and presence of 'src/agent' directory..."

    verify_branch_exists

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
            die "Could not verify 'src/agent' via GitHub API (HTTP status: $http_status). Agent installation cannot proceed."
        fi
    else
        die "Could not parse GitHub repository path from URL. Skipping remote directory check."
    fi
}

download_agent_files() {
    if [ -n "$LOCAL_DEV_PATH" ]; then
        log_info "Copying agent files from '$LOCAL_DEV_PATH/src/agent'..."
        cp -a "$LOCAL_DEV_PATH/src/agent/." "$AGENT_DIR/" || die "Failed to copy agent files from local path."
        log_success "Agent files copied successfully from local path."
        return
    fi

    log_info "Downloading agent files from branch '$BRANCH'..."
    local github_repo_path
    github_repo_path=$(echo "$REPO_URL" | sed -n 's|https://github.com/||p' | sed 's/\.git$//')
    local api_url="https://api.github.com/repos/$github_repo_path/contents/src/agent?ref=$BRANCH"

    # Fetch file list from GitHub API
    local files_json
    files_json=$(curl -s -H "Accept: application/vnd.github.v3+json" "$api_url")
    if ! echo "$files_json" | jq -e '.[0].name' > /dev/null 2>&1; then
        die "Failed to retrieve file list from GitHub API or directory is empty."
    fi

    # Download each file
    echo "$files_json" | jq -r '.[] | .name' | while read -r filename; do
        local download_url="https://raw.githubusercontent.com/$github_repo_path/$BRANCH/src/agent/$filename"
        log_info "Downloading '$filename'..."
        if ! curl -s -L "$download_url" -o "$AGENT_DIR/$filename"; then
            die "Failed to download '$filename'."
        fi
    done
    log_success "All agent files downloaded successfully."
}

setup_repo_files() {
    if [ -n "$LOCAL_DEV_PATH" ]; then
        log_info "Setting up from local path: $LOCAL_DEV_PATH..."
        if [ ! -d "$LOCAL_DEV_PATH" ]; then
            die "Local development path not found: $LOCAL_DEV_PATH"
        fi
        rm -rf "$CFUTILS_DIR"
        mkdir -p "$CFUTILS_DIR"
        cp -a "$LOCAL_DEV_PATH/." "$CFUTILS_DIR/" || die "Failed to copy from local path."
        VERSION_TAG="local"
        log_success "Repository files copied from local path."
    else
        verify_branch_exists
        log_info "Cloning new repository from branch '$BRANCH'..."
        rm -rf "$CFUTILS_DIR" # Ensure directory is empty before cloning
        git clone --branch "$BRANCH" "$REPO_URL" "$CFUTILS_DIR" || die "Failed to clone repository."

        cd "$CFUTILS_DIR" || die "Could not navigate to '$CFUTILS_DIR' after clone."
        VERSION_TAG=$(git describe --tags --abbrev=0 2>/dev/null || git rev-parse --short HEAD)
        cd - > /dev/null
        log_success "Repository is ready (Version: $VERSION_TAG)."
    fi
}

# TODO: Add generic functions for use by both the agent and main script. (download, backup, rollback, setup venv)

# --- Cloudflare-Utils Functions ---
update_cfutils_from_local() {
    log_info "--- Starting Cloudflare-Utils Update from Local Path ---"

    if [ ! -d "$LOCAL_DEV_PATH" ]; then
        die "Local development path not found: $LOCAL_DEV_PATH"
    fi

    log_info "Backing up configuration files..."
    mkdir -p /tmp/cfutils_backup
    if [ -f "$CFUTILS_DIR/src/configs.json" ]; then
        cp "$CFUTILS_DIR/src/configs.json" "/tmp/cfutils_backup/configs.json"
        log_info "Backed up configs.json."
    fi
    if [ -f "$CFUTILS_DIR/src/rotation_status.json" ]; then
        cp "$CFUTILS_DIR/src/rotation_status.json" "/tmp/cfutils_backup/rotation_status.json"
        log_info "Backed up rotation_status.json."
    fi

    log_info "Copying application files from '$LOCAL_DEV_PATH'..."
    cp -a "$LOCAL_DEV_PATH/." "$CFUTILS_DIR/" || die "Failed to copy from local path."

    log_info "Restoring configuration files..."
    if [ -f "/tmp/cfutils_backup/configs.json" ]; then
        mv "/tmp/cfutils_backup/configs.json" "$CFUTILS_DIR/src/configs.json"
        log_info "Restored configs.json."
    fi
    if [ -f "/tmp/cfutils_backup/rotation_status.json" ]; then
        mv "/tmp/cfutils_backup/rotation_status.json" "$CFUTILS_DIR/src/rotation_status.json"
        log_info "Restored rotation_status.json."
    fi
    rm -rf /tmp/cfutils_backup

    log_info "Updating Python dependencies..."
    setup_cfutils_venv

    log_info "Re-linking global command..."
    ln -sf "$CFUTILS_DIR/cf-utils.py" "/usr/local/bin/cfu"
    chmod +x "$CFUTILS_DIR/cf-utils.py"

    log_info "Verifying update..."
    if ! run_verification_checks_cfutils; then
        log_error "Update verification failed. The installation might be in an inconsistent state."
        die "Update from local path failed during verification."
    fi

    VERSION_TAG="local"
    log_success "Cloudflare-Utils updated successfully from local path (Version: $VERSION_TAG)."
}

update_cfutils() {
    log_info "--- Starting Cloudflare-Utils Update ---"

    if [ -n "$LOCAL_DEV_PATH" ]; then
        log_info "Updating from local path..."
        update_cfutils_from_local
        log_success "Update from local path completed."
        return
    fi

    verify_branch_exists

    cd "$CFUTILS_DIR" || die "Could not navigate to '$CFUTILS_DIR'"
    local old_commit_hash
    old_commit_hash=$(git rev-parse HEAD)
    log_info "Current version commit: $old_commit_hash"

    log_info "Backing up configuration files..."
    mkdir -p /tmp/cfutils_backup
    if [ -f "$CFUTILS_DIR/src/configs.json" ]; then
        cp "$CFUTILS_DIR/src/configs.json" "/tmp/cfutils_backup/configs.json"
        log_info "Backed up configs.json."
    fi
    if [ -f "$CFUTILS_DIR/src/rotation_status.json" ]; then
        cp "$CFUTILS_DIR/src/rotation_status.json" "/tmp/cfutils_backup/rotation_status.json"
        log_info "Backed up rotation_status.json."
    fi

    log_info "Updating repository from branch '$BRANCH'..."
    git stash
    if ! (git fetch --all --prune && git checkout "$BRANCH" && git reset --hard "origin/$BRANCH"); then
        log_error "Failed to update the repository. Please check for errors."
        log_info "Restoring configuration files from backup..."
        if [ -f "/tmp/cfutils_backup/configs.json" ]; then
            mv "/tmp/cfutils_backup/configs.json" "$CFUTILS_DIR/src/configs.json"
        fi
        if [ -f "/tmp/cfutils_backup/rotation_status.json" ]; then
            mv "/tmp/cfutils_backup/rotation_status.json" "$CFUTILS_DIR/src/rotation_status.json"
        fi
        rm -rf /tmp/cfutils_backup
        die "Update failed. Your configuration has been restored."
    fi
    git clean -fd

    log_info "Restoring configuration files..."
    if [ -f "/tmp/cfutils_backup/configs.json" ]; then
        mv "/tmp/cfutils_backup/configs.json" "$CFUTILS_DIR/src/configs.json"
        log_info "Restored configs.json."
    fi
    if [ -f "/tmp/cfutils_backup/rotation_status.json" ]; then
        mv "/tmp/cfutils_backup/rotation_status.json" "$CFUTILS_DIR/src/rotation_status.json"
        log_info "Restored rotation_status.json."
    fi
    rm -rf /tmp/cfutils_backup

    log_info "Updating Python dependencies..."
    setup_cfutils_venv

    log_info "Deleting old entrypoint..."
    rm -f "/usr/local/bin/cfu"
    log_info "Re-linking global command..."
    ln -sf "$CFUTILS_DIR/cf-utils.py" "/usr/local/bin/cfu"
    chmod +x "$CFUTILS_DIR/cf-utils.py"

    log_info "Verifying update..."
    if ! run_verification_checks_cfutils; then
        log_error "Update verification failed. Rolling back to the previous version."
        
        log_info "Restoring previous version ($old_commit_hash)..."
        git reset --hard "$old_commit_hash" || log_warning "Failed to reset git repo. It may be in an inconsistent state."
        git clean -fd

        log_info "Restoring previous Python dependencies..."
        setup_cfutils_venv

        log_info "Re-linking global command..."
        ln -sf "$CFUTILS_DIR/cf-utils.py" "/usr/local/bin/cfu"
        chmod +x "$CFUTILS_DIR/cf-utils.py"

        die "Update rolled back. Your previous version has been restored."
    fi

    cd - > /dev/null
    VERSION_TAG=$(cd "$CFUTILS_DIR" && (git describe --tags --abbrev=0 2>/dev/null || git rev-parse --short HEAD))
    log_success "Cloudflare-Utils updated successfully (Version: $VERSION_TAG)."
}

setup_cfutils_venv() {
    log_info "Setting up Python virtual environment for the Cloudflare-Utils..."
    python3 -m venv "$CFUTILS_DIR/venv" || die "Failed to create virtual environment."
    
    log_info "Upgrading pip in the new virtual environment..."
    "$CFUTILS_DIR/venv/bin/pip" install --upgrade pip || log_warning "Failed to upgrade pip, continuing with existing version."

    if [ -f "$CFUTILS_DIR/requirements.txt" ]; then
        log_info "Installing Cloudflare-Utils dependencies..."
        "$CFUTILS_DIR/venv/bin/pip" install -r "$CFUTILS_DIR/requirements.txt" || die "Failed to install dependencies from requirements.txt."
    else
        log_warning "requirements.txt not found, skipping dependency installation."
    fi
}

setup_cfutils_cron() {
    log_info "Setting up cron job for IP rotation..."
    local cron_runner_path="$CFUTILS_DIR/run.sh"
    cat << EOF > "$cron_runner_path"
#!/bin/bash
cd "$CFUTILS_DIR"
export LOG_TO_FILE=true
"$CFUTILS_DIR/venv/bin/python3" -m src.ip_rotator >> "$CFUTILS_DIR/logs/cron.log" 2>&1
EOF
    chmod +x "$cron_runner_path"

    # Atomically update crontab
    if ! (crontab -l 2>/dev/null | grep -v -F "$cron_runner_path"; \
     echo "*/1 * * * * $cron_runner_path"; \
     echo "@reboot $cron_runner_path") | crontab -; then
        die "Failed to set up cron job. Please check if 'cron' service is running."
    fi
    log_success "Cron job set up successfully."
}

setup_log_rotation() {
    log_info "Setting up log rotation for Cloudflare-Utils logs..."
    local logrotate_conf="/etc/logrotate.d/cloudflare-utils"
    cat << EOF > "$logrotate_conf"
$CFUTILS_DIR/logs/cron.log {
    daily
    size 10M
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 0640 root adm
}
EOF
    log_success "Log rotation configured at $logrotate_conf."
}

install_cfutils() {
    log_info "--- Starting Cloudflare-Utils Installation ---"
    setup_repo_files
    setup_cfutils_venv

    log_info "Creating required directories and files..."
    mkdir -p "$CFUTILS_DIR/src" "$CFUTILS_DIR/logs"
    touch "$CFUTILS_DIR/logs/cron.log"
    chown -R root:root "$CFUTILS_DIR" || log_warning "Could not set ownership to root:root. May require manual adjustment."
    
    if [ ! -f "$CFUTILS_DIR/src/configs.json" ]; then
        echo '{"accounts": [], "agents": []}' > "$CFUTILS_DIR/src/configs.json"
    fi

    setup_cfutils_cron
    setup_log_rotation

    log_info "Creating global 'cfu' command..."
    ln -sf "$CFUTILS_DIR/cf-utils.py" "/usr/local/bin/cfu"
    chmod +x "$CFUTILS_DIR/cf-utils.py"
    chmod +x "/usr/local/bin/cfu"

    log_success "Cloudflare-Utils installed successfully (Version: $VERSION_TAG)."
    echo -e "${C_CYAN}   Use 'cfu' to manage the Cloudflare-Utils.${C_RESET}"
}

remove_cfutils() {
    log_info "--- Starting Cloudflare-Utils Removal ---"
    if [ ! -d "$CFUTILS_DIR" ]; then
        log_warning "Cloudflare-Utils directory not found. Nothing to remove."
    else
        log_info "Removing cron job..."
        (crontab -l 2>/dev/null | grep -v "$CFUTILS_DIR/run.sh" || true) | crontab -
        
        log_info "Removing global command..."
        rm -f "/usr/local/bin/cfu"

        log_info "Removing log rotation config..."
        rm -f "/etc/logrotate.d/cloudflare-utils"

        log_info "Removing directory: $CFUTILS_DIR..."
        rm -rf "$CFUTILS_DIR"
        log_success "Cloudflare-Utils removed successfully."

        log_info "Removing installer log file..."
        rm -f "$INSTALL_LOG_FILE"
        rmdir --ignore-fail-on-non-empty "$LOG_DIR" || true
    fi
}

# --- Agent Functions ---
setup_agent_venv() {
    log_info "Setting up Python virtual environment for Agent..."
    python3 -m venv "$AGENT_DIR/venv" || die "Failed to create agent virtual environment."
    
    log_info "Upgrading pip in agent venv..."
    "$AGENT_DIR/venv/bin/pip" install --upgrade pip || log_warning "Failed to upgrade pip."

    if [ -f "$AGENT_DIR/requirements.txt" ]; then
        log_info "Installing/Updating Agent dependencies from requirements.txt..."
        "$AGENT_DIR/venv/bin/pip" install -r "$AGENT_DIR/requirements.txt" || die "Failed to install agent dependencies."
    else
        die "Agent requirements.txt not found. Cannot proceed."
    fi
    log_success "Agent virtual environment is up to date."
}

update_agent() {
    log_info "--- Starting Monitoring Agent Update ---"
    log_info "Stopping agent service to begin update..."
    systemctl stop cloudflare-utils-agent.service

    log_info "Creating a full backup of the agent directory..."
    rm -rf /tmp/agent_full_backup
    cp -a "$AGENT_DIR" "/tmp/agent_full_backup" || die "Failed to create agent backup."

    log_info "Backing up agent configuration separately..."
    mkdir -p /tmp/agent_backup
    if [ -f "$AGENT_DIR/config.json" ]; then
        cp "$AGENT_DIR/config.json" "/tmp/agent_backup/config.json"
        log_info "Backed up config.json."
    fi

    verify_branch_and_agent_dir
    log_info "Downloading updated agent files..."
    download_agent_files

    log_info "Restoring agent configuration..."
    if [ -f "/tmp/agent_backup/config.json" ]; then
        mv "/tmp/agent_backup/config.json" "$AGENT_DIR/config.json"
        log_info "Restored config.json."
    fi
    rm -rf /tmp/agent_backup

    log_info "Updating Python dependencies for Agent..."
    setup_agent_venv

    log_info "Deleting old entrypoint..."
    rm -f "/usr/local/bin/cfu-agent"
    log_info "Re-linking global 'cfu-agent' command..."
    ln -sf "$AGENT_DIR/cfu-agent.py" "/usr/local/bin/cfu-agent"
    chmod +x "$AGENT_DIR/cfu-agent.py"
    chmod +x "/usr/local/bin/cfu-agent"

    log_info "Reloading systemd and restarting the agent..."
    sed "s|__PYTHON_EXEC_PATH__|$AGENT_DIR/venv/bin/python3|g" "$AGENT_DIR/cloudflare-utils-agent.service" > "/etc/systemd/system/cloudflare-utils-agent.service"
    systemctl daemon-reload
    systemctl restart cloudflare-utils-agent.service

    log_info "Verifying update..."
    if ! run_verification_checks_agent; then
        log_error "Agent update verification failed. Rolling back to the previous version."
        systemctl stop cloudflare-utils-agent.service
        rm -rf "$AGENT_DIR"
        mv "/tmp/agent_full_backup" "$AGENT_DIR"
        
        log_info "Restoring previous systemd service file and restarting..."
        if [ -f "$AGENT_DIR/cloudflare-utils-agent.service" ]; then
            sed "s|__PYTHON_EXEC_PATH__|$AGENT_DIR/venv/bin/python3|g" "$AGENT_DIR/cloudflare-utils-agent.service" > "/etc/systemd/system/cloudflare-utils-agent.service"
            systemctl daemon-reload
        fi
        systemctl start cloudflare-utils-agent.service
        die "Agent update rolled back. Your previous version has been restored."
    fi

    rm -rf /tmp/agent_full_backup
    log_success "Monitoring Agent updated successfully."
}

install_agent() {
    local p_iface="$1"
    local p_whitelist_csv="$2"

    log_info "--- Starting Monitoring Agent Installation ---"
    verify_branch_and_agent_dir

    log_info "Setting up Agent directory: $AGENT_DIR"
    mkdir -p "$AGENT_DIR"
    
    download_agent_files
    setup_agent_venv

    echo -e "\n${C_CYAN}--- Agent Configuration ---${C_RESET}"
    local api_key
    api_key=$(openssl rand -base64 32)
    
    # Process whitelist from parameter
    local whitelist_json=""
    if [ -n "$p_whitelist_csv" ]; then
        local processed_ips=()
        local ips
        IFS=',' read -ra ips <<< "$p_whitelist_csv"
        for ip in "${ips[@]}"; do
            ip=$(echo "$ip" | sed 's/ //g') # Trim whitespace
            if [ -n "$ip" ]; then
                processed_ips+=("\"$ip\"")
            fi
        done
        whitelist_json=$(IFS=,; echo "${processed_ips[*]}")
    else
        log_warning "Whitelist is empty. The agent will accept connections from any IP."
    fi

    # Use interface from parameter
    log_info "Validating interface '$p_iface' with vnstat..."
    if ! vnstat --json d 1 -i "$p_iface" | jq -e '.interfaces[0].traffic.day[0]' > /dev/null 2>&1; then
        log_warning "vnstat does not appear to have any data for '$p_iface'."
        # In non-interactive mode, we proceed. In interactive mode, the prompt is handled by the caller.
    else
        log_success "vnstat validation passed for interface '$p_iface'."
    fi

    log_info "Creating Agent log directory..."
    mkdir -p "$AGENT_DIR/logs"
    touch "$AGENT_DIR/logs/startup.log"

    log_info "Creating config file: '$AGENT_DIR/config.json'"
    cat << EOF > "$AGENT_DIR/config.json"
{
  "api_key": "$api_key",
  "whitelist": [$whitelist_json],
  "vnstat_interface": "$p_iface"
}
EOF
    chmod 600 "$AGENT_DIR/config.json"
    chown root:root "$AGENT_DIR/config.json"

    log_info "Setting up systemd service..."
    sed "s|__PYTHON_EXEC_PATH__|$AGENT_DIR/venv/bin/python3|g" "$AGENT_DIR/cloudflare-utils-agent.service" > "/etc/systemd/system/cloudflare-utils-agent.service"
    
    log_info "Creating global 'cfu-agent' command..."
    ln -sf "$AGENT_DIR/cfu-agent.py" "/usr/local/bin/cfu-agent"
    chmod +x "$AGENT_DIR/cfu-agent.py"
    chmod +x "/usr/local/bin/cfu-agent"

    log_info "Reloading systemd, enabling and starting the agent..."
    systemctl daemon-reload
    systemctl enable --now cloudflare-utils-agent.service || die "Failed to enable and start agent service."

    if ! systemctl is-active --quiet cloudflare-utils-agent.service; then
        log_error "Agent service failed to start. Please check the logs for errors."
        local log_file="$AGENT_DIR/logs/startup.log"
        journalctl -u cloudflare-utils-agent.service --no-pager > "$log_file"
        log_error "Logs saved to $log_file"
        log_error "You can also run: journalctl -u cloudflare-utils-agent.service"
        die "Installation failed."
    fi

    log_success "Monitoring Agent installed and started successfully."
    echo -e "${C_GREEN}--- Agent API Key ---${C_RESET}"
    echo -e "Your API Key is: ${C_YELLOW}$api_key${C_RESET}"
    echo -e "This key is stored in ${C_CYAN}$AGENT_DIR/config.json${C_RESET}"
    echo -e "You will need to add this agent and its key to the Cloudflare-Utils configuration using the 'cfu' command."
    echo -e "Example: ${C_YELLOW}cfu add-agent --name my-server --ip <server-ip> --key 'YOUR_API_KEY'${C_RESET}"
    echo -e "\nTo check agent status, run: ${C_CYAN}systemctl status cloudflare-utils-agent.service${C_RESET}"
    echo -e "Agent logs are available at: ${C_CYAN}$AGENT_DIR/logs/startup.log${C_RESET}"
}

remove_agent() {
    log_info "--- Starting Monitoring Agent Removal ---"
    log_info "Removing global 'cfu-agent' command..."
    rm -f "/usr/local/bin/cfu-agent"

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
    
    log_info "Removing installer log file..."
    rm -f "$INSTALL_LOG_FILE"
    rmdir --ignore-fail-on-non-empty "$LOG_DIR" || true
}

# --- Verification & Rollback Functions ---
run_verification_checks_cfutils() {
    log_info "--- Verifying Cloudflare-Utils Installation ---"
    local all_checks_passed=true
    local checklist=""

    # Check 1: Directory
    if [ -d "$CFUTILS_DIR" ]; then
        checklist+="${C_GREEN}[✓]${C_RESET} Cloudflare-Utils directory exists at '$CFUTILS_DIR'.\n"
    else
        checklist+="${C_RED}[✗]${C_RESET} Cloudflare-Utils directory not found at '$CFUTILS_DIR'.\n"
        all_checks_passed=false
    fi

    # Check 2: Venv
    if [ -d "$CFUTILS_DIR/venv" ]; then
        checklist+="${C_GREEN}[✓]${C_RESET} Python virtual environment exists.\n"
    else
        checklist+="${C_RED}[✗]${C_RESET} Python virtual environment not found.\n"
        all_checks_passed=false
    fi

    # Check 3: Dependencies
    if [ -f "$CFUTILS_DIR/venv/bin/pip" ] && "$CFUTILS_DIR/venv/bin/pip" freeze | grep -qi "requests"; then
        checklist+="${C_GREEN}[✓]${C_RESET} Python dependencies are installed.\n"
    else
        checklist+="${C_RED}[✗]${C_RESET} Python dependencies are not installed correctly.\n"
        all_checks_passed=false
    fi

    # Check 4: Cron service
    if systemctl is-active --quiet cron || systemctl is-active --quiet crond; then
        checklist+="${C_GREEN}[✓]${C_RESET} Cron service is running.\n"
    else
        checklist+="${C_RED}[✗]${C_RESET} Cron service is not running.\n"
        all_checks_passed=false
    fi

    # Check 5: Cron job
    if crontab -l 2>/dev/null | grep -q "$CFUTILS_DIR/run.sh"; then
        checklist+="${C_GREEN}[✓]${C_RESET} Cron job is configured.\n"
    else
        checklist+="${C_RED}[✗]${C_RESET} Cron job is not configured.\n"
        all_checks_passed=false
    fi

    # Check 6: Global command
    if [ -L "/usr/local/bin/cfu" ] && [ -x "/usr/local/bin/cfu" ]; then
        checklist+="${C_GREEN}[✓]${C_RESET} Global command 'cfu' is set up correctly.\n"
    else
        checklist+="${C_RED}[✗]${C_RESET} Global command 'cfu' not found or not executable.\n"
        all_checks_passed=false
    fi

    echo -e "\n$checklist"

    if [ "$all_checks_passed" = true ]; then
        return 0 # Success
    else
        return 1 # Failure
    fi
}

rollback_cfutils() {
    log_warning "--- Rolling back Cfutils installation ---"
    if [ ! -d "$CFUTILS_DIR" ]; then
        log_info "Cfutils directory not found. Nothing to roll back."
    else
        log_info "Removing cron job..."
        (crontab -l 2>/dev/null | grep -v "$CFUTILS_DIR/run.sh" || true) | crontab -
        
        log_info "Removing global command..."
        rm -f "/usr/local/bin/cfu"

        log_info "Removing log rotation config..."
        rm -f "/etc/logrotate.d/cloudflare-utils"

        log_info "Removing directory: $CFUTILS_DIR..."
        rm -rf "$CFUTILS_DIR"
        log_success "Cloudflare-Utils rollback complete."
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

verify_cfutils_installation() {
    if ! run_verification_checks_cfutils; then
        log_error "Cloudflare-Utils installation verification failed."
        local answer
        read -rp "$(echo -e "${C_YELLOW}An error occurred during verification. Do you want to roll back the installation? [Y/n]: ${C_RESET}")" answer
        if [[ "$answer" != "n" && "$answer" != "N" ]]; then
            rollback_cfutils
        fi
        die "Aborting due to verification failure."
    else
        log_success "Installation verified successfully. All components are working correctly."
    fi
}

run_verification_checks_agent() {
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
        return 0 # Success
    else
        return 1 # Failure
    fi
}

verify_agent_installation() {
    if ! run_verification_checks_agent; then
        log_error "Agent installation verification failed."
        local answer
        read -rp "$(echo -e "${C_YELLOW}An error occurred during verification. Do you want to roll back the installation? [Y/n]: ${C_RESET}")" answer
        if [[ "$answer" != "n" && "$answer" != "N" ]]; then
            rollback_agent
        fi
        die "Aborting due to verification failure."
    else
        log_success "Installation verified successfully. All components are working correctly."
    fi
}

# --- Main Execution Logic ---
run_non_interactive_mode() {
    log_info "Running in non-interactive mode..."

    if $AGENT_MODE; then
        if $UNINSTALL_MODE; then
            log_info "Action: Uninstall Agent"
            remove_agent
        else
            log_info "Action: Install/Update Agent"
            if [ -d "$AGENT_DIR" ]; then
                update_agent
            else
                install_agent "$IFACE" "$IP_WHITELIST"
            fi
        fi
    else
        if $UNINSTALL_MODE; then
            log_info "Action: Uninstall Cloudflare-Utils"
            remove_cfutils
        else
            log_info "Action: Install/Update Cloudflare-Utils"
            if [ -d "$CFUTILS_DIR" ]; then
                update_cfutils
            else
                install_cfutils
            fi
        fi
    fi
}

run_interactive_mode() {
    # Enforce default branch and path for interactive mode, as they are non-interactive flags
    BRANCH="main"
    LOCAL_DEV_PATH=""

    if [ -t 1 ]; then clear; fi
    echo -e "${C_MAGENTA}--- Cloudflare-Utils Installer ---${C_RESET}"
    log_info "Branch selection and local install are only supported in non-interactive mode (using -b or -p flags)."
    log_info "This interactive installer will use the default 'main' branch."
    
    PS3="$(echo -e "${C_YELLOW}\nPlease choose an option: ${C_RESET}")"
    options=(
        "Install/Update Cloudflare-Utils"
        "Install/Update Agent"
        "Uninstall Cloudflare-Utils"
        "Uninstall Agent"
        "Exit"
    )
    select opt in "${options[@]}"; do
        case $opt in
            "Install/Update Cloudflare-Utils")
                if [ -d "$CFUTILS_DIR" ]; then update_cfutils; else install_cfutils; fi
                break
                ;;
            "Install/Update Agent")
                if [ -d "$AGENT_DIR" ]; then
                    update_agent
                else
                    # --- Interactive Agent Setup ---
                    local whitelist_input
                    read -rp "Enter comma-separated IPs to whitelist (e.g., 1.1.1.1,8.8.8.8) [optional, press Enter to skip]: " whitelist_input

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
                    
                    if [ ${#interfaces[@]} -eq 0 ]; then
                        die "No network interfaces found (excluding 'lo')."
                    fi
                    
                    local iface
                    PS3="$(echo -e "${C_YELLOW}Please select the network interface to monitor: ${C_RESET}")"
                    select iface in "${interfaces[@]}"; do
                        if [[ -n "$iface" ]]; then break; else log_warning "Invalid selection."; fi
                    done
                    
                    if ! vnstat --json d 1 -i "$iface" | jq -e '.interfaces[0].traffic.day[0]' > /dev/null 2>&1; then
                        log_warning "vnstat does not appear to have any data for '$iface'."
                        local answer
                        read -rp "$(echo -e "${C_YELLOW}Continue anyway? [y/N]: ${C_RESET}")" answer
                        if [[ "$answer" != "y" && "$answer" != "Y" ]]; then
                            die "Installation cancelled by user."
                        fi
                    fi
                    # --- End of Interactive Agent Setup ---
                    install_agent "$iface" "$whitelist_input"
                fi
                break
                ;;
            "Uninstall Cloudflare-Utils")
                local answer
                read -rp "$(echo -e "${C_YELLOW}Are you sure you want to remove Cloudflare-Utils? [y/N]: ${C_RESET}")" answer
                if [[ "$answer" == "y" || "$answer" == "Y" ]]; then
                    remove_cfutils
                else
                    log_info "Removal cancelled."
                fi
                break
                ;;
            "Uninstall Agent")
                local answer
                read -rp "$(echo -e "${C_YELLOW}Are you sure you want to remove the Agent? [y/N]: ${C_RESET}")" answer
                if [[ "$answer" == "y" || "$answer" == "Y" ]]; then
                    remove_agent
                else
                    log_info "Removal cancelled."
                fi
                break
                ;;
            "Exit")
                break
                ;;
            *) log_warning "Invalid option '$REPLY'";;
        esac
    done
}

# --- Argument Parser ---
parse_args() {
    if [ "$#" -gt 0 ]; then
        INTERACTIVE_MODE=false
    fi

    while [ "$#" -gt 0 ]; do
        case "$1" in
            -b)
                if [ -z "$2" ]; then die "'-b' requires an argument."; fi
                BRANCH="$2"
                shift 2
                ;;
            -p)
                if [ -z "$2" ]; then die "'-p' requires an argument."; fi
                LOCAL_DEV_PATH="$2"
                shift 2
                ;;
            -u)
                UNINSTALL_MODE=true
                shift
                ;;
            --agent)
                AGENT_MODE=true
                shift
                ;;
            --ip-whitelist)
                if [ -z "$2" ]; then die "'--ip-whitelist' requires an argument."; fi
                IP_WHITELIST="$2"
                shift 2
                ;;
            --iface)
                if [ -z "$2" ]; then die "'--iface' requires an argument."; fi
                IFACE="$2"
                shift 2
                ;;
            -h|--help)
                usage
                ;;
            *)
                log_error "Unknown option: $1"
                usage
                ;;
        esac
    done

    # Validation for non-interactive mode
    if ! $INTERACTIVE_MODE; then
        if [ -n "$LOCAL_DEV_PATH" ] && [ "$BRANCH" != "main" ]; then
            log_warning "Both -p (local path) and -b (branch) were specified. Using local path."
        fi
        if $AGENT_MODE && ! $UNINSTALL_MODE; then
            if [ -z "$IFACE" ]; then
                die "Agent installation in non-interactive mode requires the --iface flag."
            fi
        fi
    fi
}

# --- Main Execution ---
pre_flight_checks
parse_args "$@"

if $INTERACTIVE_MODE; then
    run_interactive_mode
else
    run_non_interactive_mode
fi