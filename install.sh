#!/bin/bash
# Cloudflare-Utils Installer / Updater (Debian/Ubuntu + systemd)
# Must be run as root.

set -Eeuo pipefail
trap 'log_error "Installer aborted at line $LINENO"; exit 1' ERR

# --- Logging Setup ---
LOG_DIR="/var/log/cloudflare-utils"
mkdir -p "$LOG_DIR"
INSTALL_LOG_FILE="$LOG_DIR/installer.log"
exec > >(tee -a "$INSTALL_LOG_FILE") 2>&1
echo "--- Starting Cloudflare-Utils Installer Log $(date) ---"

# --- Colors & Logging ---
C_RESET='\e[0m'
C_RED='\e[1;31m'
C_GREEN='\e[1;32m'
C_YELLOW='\e[1;33m'
C_BLUE='\e[1;34m'
C_CYAN='\e[1;36m'
C_MAGENTA='\e[1;35m'

log_info()    { echo -e "${C_BLUE}INFO:${C_RESET} $*"; }
log_success() { echo -e "${C_GREEN}✅ SUCCESS:${C_RESET} $*"; }
log_warning() { echo -e "${C_YELLOW}⚠️ WARNING:${C_RESET} $*"; }
log_error()   { echo -e "${C_RED}❌ ERROR:${C_RESET} $*"; }
die()         { log_error "$*"; exit 1; }

# --- Configuration & Defaults ---
CFUTILS_PROGRAM_NAME="Cloudflare-Utils"
AGENT_PROGRAM_NAME="Cloudflare-Utils-Agent"
CFUTILS_DIR="/opt/$CFUTILS_PROGRAM_NAME"
AGENT_DIR="/opt/$AGENT_PROGRAM_NAME"
REPO_URL="https://github.com/Issei-177013/Cloudflare-Utils.git"
VERSION_TAG=""

INTERACTIVE_MODE=true
BRANCH="main"
LOCAL_DEV_PATH=""
UNINSTALL_MODE=false
AGENT_MODE=false
IP_WHITELIST=""
IFACE=""

# --- Helper Functions ---
ensure_root() {
  if [[ $EUID -ne 0 ]]; then
    die "This script must be run as root. Please use 'sudo'."
  fi
}

check_command() {
  local cmd="$1" pkg="${2:-$1}"
  if command -v "$cmd" >/dev/null 2>&1; then return 0; fi
  log_warning "Command '$cmd' is required but not found."
  log_info "Attempting to install '$pkg' via apt-get…"
  apt-get update -y >/dev/null 2>&1 || true
  if apt-get install -y "$pkg"; then
    log_success "Installed '$pkg'."
  else
    die "Failed to install '$pkg'. Please install it manually."
  fi
  command -v "$cmd" >/dev/null 2>&1 || die "Command '$cmd' still not available. Check PATH or install it manually."
}

usage() {
  cat <<EOF
Usage: $0 [options]
Run without options for interactive mode.

Options:
  -b <branch>              Install/update from a specific Git branch (default: main).
  --local                  Update from the local repository (directory of this script).
  -u                       Uninstall the application.
  --agent                  Install/Update/Uninstall the monitoring agent (instead of main utility).
  --ip-whitelist <ips>     Comma-separated IPs to whitelist for the agent (non-interactive).
  --iface <interface>      Network interface for the agent to monitor (non-interactive).
  -h, --help               Show this help and exit.

Examples:
  Interactive install/update:
    sudo $0

  Non-interactive install/update from branch:
    sudo $0 -b main

  Non-interactive from local path:
    sudo $0 --local

  Uninstall Cloudflare-Utils:
    sudo $0 -u

  Install Agent (non-interactive):
    sudo $0 --agent --iface eth0 --ip-whitelist "1.1.1.1,8.8.8.8"
EOF
  exit 0
}

# Bot restart hook after update
restart_bot_if_enabled() {
  log_info "Checking if Telegram bot needs restart after update…"
  local config_file="$CFUTILS_DIR/configs/configs.json"
  local python_exec="$CFUTILS_DIR/venv/bin/python3"
  local cfu_script="$CFUTILS_DIR/cf-utils.py"

  if [[ -f "$config_file" && -f "$python_exec" && -f "$cfu_script" ]]; then
    if jq -e '.bot.enabled == true' "$config_file" >/dev/null 2>&1; then
      log_info "Telegram bot is enabled → issuing restart command…"
      if "$python_exec" "$cfu_script" --restart-bot; then
        log_success "Bot restart command issued successfully."
        log_info "If the bot doesn’t respond in Telegram, open: cfu → Settings → Telegram Bot → Manage Service → Restart."
      else
        log_warning "Bot restart command failed. You may need to restart it manually from CLI menu."
      fi
    else
      log_info "Telegram bot is not enabled → skipping restart."
    fi
  else
    log_info "Bot config or runtime not found → skipping restart check."
    log_info "Tip: Initialize the bot from: cfu → Settings → Telegram Bot (interactive setup)."
  fi
}

# --- Pre-flight Checks ---
pre_flight_checks() {
  log_info "Running pre-flight checks…"
  ensure_root
  check_command "git" "git"
  check_command "python3" "python3"
  check_command "pip3" "python3-pip"
  check_command "curl" "curl"
  check_command "jq" "jq"
  check_command "openssl" "openssl"
  check_command "vnstat" "vnstat"
  check_command "crontab" "cron"
  check_command "systemctl" "systemd"

  if ! python3 -c "import venv" &>/dev/null; then
    log_warning "'python3-venv' not installed."
    log_info "Attempting to install 'python3-venv'…"
    apt-get install -y python3-venv || die "Failed to install python3-venv."
  fi
  log_success "All required base commands are available."
  if [ -t 1 ]; then clear; fi
}

# --- Repo helpers ---
verify_branch_exists() {
  log_info "Verifying branch '$BRANCH' exists on remote…"
  git ls-remote --exit-code --heads "$REPO_URL" "$BRANCH" >/dev/null 2>&1 || die "Branch '$BRANCH' does not exist on remote."
  log_success "Branch '$BRANCH' found on remote."
}

setup_repo_files() {
  if [[ -n "$LOCAL_DEV_PATH" ]]; then
    log_info "Setting up from local path: $LOCAL_DEV_PATH"
    [[ -d "$LOCAL_DEV_PATH" ]] || die "Local path not found: $LOCAL_DEV_PATH"
    rm -rf "$CFUTILS_DIR"
    mkdir -p "$CFUTILS_DIR"
    cp -a "$LOCAL_DEV_PATH/." "$CFUTILS_DIR/" || die "Failed to copy from local path."
    VERSION_TAG="local"
    log_success "Repository files copied from local path."
  else
    verify_branch_exists
    log_info "Cloning repository from branch '$BRANCH'…"
    rm -rf "$CFUTILS_DIR"
    git clone --branch "$BRANCH" "$REPO_URL" "$CFUTILS_DIR" || die "Failed to clone repository."
    pushd "$CFUTILS_DIR" >/dev/null
    VERSION_TAG=$(git describe --tags --abbrev=0 2>/dev/null || git rev-parse --short HEAD)
    popd >/dev/null
    log_success "Repository is ready (Version: $VERSION_TAG)."
  fi
}

# --- Python env ---
setup_cfutils_venv() {
  log_info "Setting up Python virtual environment…"
  python3 -m venv "$CFUTILS_DIR/venv" || die "Failed to create virtual environment."
  log_info "Upgrading pip…"
  "$CFUTILS_DIR/venv/bin/pip" install --upgrade pip || log_warning "Failed to upgrade pip (continuing)."
  if [[ -f "$CFUTILS_DIR/requirements.txt" ]]; then
    log_info "Installing dependencies from requirements.txt…"
    "$CFUTILS_DIR/venv/bin/pip" install -r "$CFUTILS_DIR/requirements.txt" || die "Failed to install dependencies."
  else
    log_warning "requirements.txt not found → skipping dependency installation."
  fi
}

# --- Cron & Logrotate ---
setup_cfutils_cron() {
  log_info "Setting up cron job for IP rotation…"
  local cron_runner="$CFUTILS_DIR/run.sh"
  cat > "$cron_runner" <<EOF
#!/bin/bash
cd "$CFUTILS_DIR"
export LOG_TO_FILE=true
"$CFUTILS_DIR/venv/bin/python3" -m src.ip_rotator >> "$CFUTILS_DIR/logs/cron.log" 2>&1
EOF
  chmod +x "$cron_runner"
  # Atomic crontab update
  if ! (crontab -l 2>/dev/null | grep -v -F "$cron_runner"; echo "*/1 * * * * $cron_runner"; echo "@reboot $cron_runner") | crontab -; then
    die "Failed to set up cron job. Ensure 'cron' service is running."
  fi
  log_success "Cron job set up."
}

setup_log_rotation() {
  log_info "Setting up log rotation…"
  local cfg="/etc/logrotate.d/cloudflare-utils"
  cat > "$cfg" <<EOF
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
  log_success "Log rotation configured at $cfg."
}

# --- Verification (SC2015-safe) ---
run_verification_checks_cfutils() {
  log_info "--- Verifying Cloudflare-Utils Installation ---"
  local ok=true
  local checklist=""

  if [[ -d "$CFUTILS_DIR" ]]; then
    checklist+="${C_GREEN}[✓]${C_RESET} Dir: $CFUTILS_DIR exists.\n"
  else
    checklist+="${C_RED}[✗]${C_RESET} Dir missing: $CFUTILS_DIR\n"
    ok=false
  fi

  if [[ -d "$CFUTILS_DIR/venv" ]]; then
    checklist+="${C_GREEN}[✓]${C_RESET} Python venv exists.\n"
  else
    checklist+="${C_RED}[✗]${C_RESET} Python venv missing.\n"
    ok=false
  fi

  if [[ -f "$CFUTILS_DIR/venv/bin/pip" ]] && "$CFUTILS_DIR/venv/bin/pip" freeze | grep -qi "requests"; then
    checklist+="${C_GREEN}[✓]${C_RESET} Python deps installed.\n"
  else
    checklist+="${C_RED}[✗]${C_RESET} Python deps not detected.\n"
    ok=false
  fi

  if systemctl is-active --quiet cron || systemctl is-active --quiet crond; then
    checklist+="${C_GREEN}[✓]${C_RESET} Cron service running.\n"
  else
    checklist+="${C_RED}[✗]${C_RESET} Cron service not running.\n"
    ok=false
  fi

  if crontab -l 2>/dev/null | grep -q "$CFUTILS_DIR/run.sh"; then
    checklist+="${C_GREEN}[✓]${C_RESET} Cron job configured.\n"
  else
    checklist+="${C_RED}[✗]${C_RESET} Cron job missing.\n"
    ok=false
  fi

  if [[ -L "/usr/local/bin/cfu" && -x "/usr/local/bin/cfu" ]]; then
    checklist+="${C_GREEN}[✓]${C_RESET} Global command 'cfu' is ready.\n"
  else
    checklist+="${C_RED}[✗]${C_RESET} Global command 'cfu' missing or not executable.\n"
    ok=false
  fi

  echo -e "\n$checklist"

  if [[ "$ok" == true ]]; then
    return 0
  else
    return 1
  fi
}

verify_cfutils_installation() {
  if run_verification_checks_cfutils; then
    log_success "Installation verified successfully."
    print_next_steps_cfutils
  else
    log_error "Installation verification failed."
    read -rp "$(echo -e "${C_YELLOW}Do you want to roll back the installation? [Y/n]: ${C_RESET}")" ans
    if [[ "$ans" != "n" && "$ans" != "N" ]]; then
      rollback_cfutils
    fi
    die "Aborting due to verification failure."
  fi
}

print_next_steps_cfutils() {
  echo -e "${C_CYAN}
Next steps:
  • Run '${C_YELLOW}cfu${C_CYAN}' to open the CLI.
  • To set up the Telegram bot: ${C_YELLOW}cfu → Settings → Telegram Bot${C_CYAN} (interactive).
  • Logs:
      - Installer: ${C_YELLOW}$INSTALL_LOG_FILE${C_CYAN}
      - Cron (IP rotation): ${C_YELLOW}$CFUTILS_DIR/logs/cron.log${C_CYAN}
  • If you updated and bot is enabled but not responding:
      - ${C_YELLOW}cfu → Settings → Telegram Bot → Manage Service → Restart${C_CYAN}
${C_RESET}"
}

# --- Install / Update / Remove Cloudflare-Utils ---
install_cfutils() {
  log_info "--- Starting Cloudflare-Utils Installation ---"
  setup_repo_files
  setup_cfutils_venv

  log_info "Creating required directories and files…"
  mkdir -p "$CFUTILS_DIR/configs" "$CFUTILS_DIR/logs"
  touch "$CFUTILS_DIR/logs/cron.log"

  if [[ ! -f "$CFUTILS_DIR/configs/configs.json" ]]; then
    cat > "$CFUTILS_DIR/configs/configs.json" <<'EOF'
{
  "accounts": [],
  "agents": [],
  "bot": {
    "enabled": false,
    "token": "",
    "allowed_user_ids": []
  }
}
EOF
    log_info "Created default configs.json (includes bot skeleton)."
  fi

  setup_cfutils_cron
  setup_log_rotation

  log_info "Linking global 'cfu' command…"
  ln -sf "$CFUTILS_DIR/cf-utils.py" "/usr/local/bin/cfu"
  chmod +x "$CFUTILS_DIR/cf-utils.py" "/usr/local/bin/cfu"

  log_success "Cloudflare-Utils installed (Version: $VERSION_TAG)."
  verify_cfutils_installation
}

update_cfutils_from_local() {
  log_info "--- Updating Cloudflare-Utils from local path ---"
  [[ -d "$LOCAL_DEV_PATH" ]] || die "Local path not found: $LOCAL_DEV_PATH"

  log_info "Backing up configuration…"
  mkdir -p /tmp/cfutils_backup
  [[ -f "$CFUTILS_DIR/configs/configs.json" ]] && cp "$CFUTILS_DIR/configs/configs.json" /tmp/cfutils_backup/configs.json
  [[ -f "$CFUTILS_DIR/configs/rotation_status.json" ]] && cp "$CFUTILS_DIR/configs/rotation_status.json" /tmp/cfutils_backup/rotation_status.json

  log_info "Copying application files…"
  cp -a "$LOCAL_DEV_PATH/." "$CFUTILS_DIR/" || die "Failed to copy from local path."

  log_info "Restoring configuration…"
  [[ -f /tmp/cfutils_backup/configs.json ]] && mv /tmp/cfutils_backup/configs.json "$CFUTILS_DIR/configs/configs.json"
  [[ -f /tmp/cfutils_backup/rotation_status.json ]] && mv /tmp/cfutils_backup/rotation_status.json "$CFUTILS_DIR/configs/rotation_status.json"
  rm -rf /tmp/cfutils_backup

  setup_cfutils_venv

  log_info "Relinking global command…"
  ln -sf "$CFUTILS_DIR/cf-utils.py" "/usr/local/bin/cfu"
  chmod +x "$CFUTILS_DIR/cf-utils.py"

  log_info "Verifying update…"
  if ! run_verification_checks_cfutils; then
    die "Update from local path failed during verification."
  fi

  VERSION_TAG="local"
  log_success "Cloudflare-Utils updated from local path."
  restart_bot_if_enabled
  print_next_steps_cfutils
}

update_cfutils() {
  log_info "--- Starting Cloudflare-Utils Update ---"
  if [[ -n "$LOCAL_DEV_PATH" ]]; then
    update_cfutils_from_local
    return
  fi

  verify_branch_exists
  pushd "$CFUTILS_DIR" >/dev/null || die "Cannot cd to $CFUTILS_DIR"

  local old_commit; old_commit=$(git rev-parse HEAD)
  log_info "Current commit: $old_commit"

  log_info "Backing up configuration…"
  mkdir -p /tmp/cfutils_backup
  [[ -f "$CFUTILS_DIR/configs/configs.json" ]] && cp "$CFUTILS_DIR/configs/configs.json" /tmp/cfutils_backup/configs.json
  [[ -f "$CFUTILS_DIR/configs/rotation_status.json" ]] && cp "$CFUTILS_DIR/configs/rotation_status.json" /tmp/cfutils_backup/rotation_status.json

  log_info "Fetching and resetting to branch '$BRANCH'…"
  git stash || true
  if ! (git fetch --all --prune && git checkout "$BRANCH" && git reset --hard "origin/$BRANCH"); then
    log_error "Failed to update repository."
    [[ -f /tmp/cfutils_backup/configs.json ]] && mv /tmp/cfutils_backup/configs.json "$CFUTILS_DIR/configs/configs.json"
    [[ -f /tmp/cfutils_backup/rotation_status.json ]] && mv /tmp/cfutils_backup/rotation_status.json "$CFUTILS_DIR/configs/rotation_status.json"
    rm -rf /tmp/cfutils_backup
    die "Update failed. Your configuration was restored."
  fi
  git clean -fd
  popd >/dev/null

  log_info "Restoring configuration…"
  [[ -f /tmp/cfutils_backup/configs.json ]] && mv /tmp/cfutils_backup/configs.json "$CFUTILS_DIR/configs/configs.json"
  [[ -f /tmp/cfutils_backup/rotation_status.json ]] && mv /tmp/cfutils_backup/rotation_status.json "$CFUTILS_DIR/configs/rotation_status.json"
  rm -rf /tmp/cfutils_backup

  setup_cfutils_venv

  log_info "Relinking global 'cfu' command…"
  rm -f "/usr/local/bin/cfu"
  ln -sf "$CFUTILS_DIR/cf-utils.py" "/usr/local/bin/cfu"
  chmod +x "$CFUTILS_DIR/cf-utils.py"

  if ! run_verification_checks_cfutils; then
    log_error "Update verification failed → rolling back."
    pushd "$CFUTILS_DIR" >/dev/null || die "Cannot cd to $CFUTILS_DIR"
    git reset --hard "$old_commit" || log_warning "Failed to reset git to previous commit."
    git clean -fd
    popd >/dev/null
    setup_cfutils_venv
    ln -sf "$CFUTILS_DIR/cf-utils.py" "/usr/local/bin/cfu"
    chmod +x "$CFUTILS_DIR/cf-utils.py"
    die "Update rolled back to previous version."
  fi

  VERSION_TAG=$(cd "$CFUTILS_DIR" && (git describe --tags --abbrev=0 2>/dev/null || git rev-parse --short HEAD))
  log_success "Cloudflare-Utils updated (Version: $VERSION_TAG)."
  restart_bot_if_enabled
  print_next_steps_cfutils
}

remove_cfutils() {
  log_info "--- Removing Cloudflare-Utils ---"
  if [[ -d "$CFUTILS_DIR" ]]; then
    log_info "Removing cron job…"
    (crontab -l 2>/dev/null | grep -v "$CFUTILS_DIR/run.sh" || true) | crontab -
    log_info "Removing logrotate config…"
    rm -f "/etc/logrotate.d/cloudflare-utils"
    log_info "Removing global command…"
    rm -f "/usr/local/bin/cfu"
    log_info "Removing directory: $CFUTILS_DIR"
    rm -rf "$CFUTILS_DIR"
    log_success "Cloudflare-Utils removed."
  else
    log_warning "Cloudflare-Utils directory not found. Skipping."
  fi
  log_info "Keeping installer logs for audit."
}

rollback_cfutils() {
  log_warning "--- Rolling back Cloudflare-Utils installation ---"
  if [[ -d "$CFUTILS_DIR" ]]; then
    (crontab -l 2>/dev/null | grep -v "$CFUTILS_DIR/run.sh" || true) | crontab -
    rm -f "/usr/local/bin/cfu"
    rm -f "/etc/logrotate.d/cloudflare-utils"
    rm -rf "$CFUTILS_DIR"
    log_success "Rollback complete."
  else
    log_info "Nothing to roll back."
  fi
}

# --- Agent (SC2015-safe) ---
setup_agent_venv() {
  log_info "Setting up Agent virtual environment…"
  python3 -m venv "$AGENT_DIR/venv" || die "Failed to create agent venv."
  "$AGENT_DIR/venv/bin/pip" install --upgrade pip || log_warning "Failed to upgrade pip."
  if [[ -f "$AGENT_DIR/requirements.txt" ]]; then
    "$AGENT_DIR/venv/bin/pip" install -r "$AGENT_DIR/requirements.txt" || die "Failed to install agent deps."
  else
    die "Agent requirements.txt not found."
  fi
  log_success "Agent venv ready."
}

run_verification_checks_agent() {
  log_info "--- Verifying Agent Installation ---"
  local ok=true
  local checklist=""
  local cfg="$AGENT_DIR/config.json"

  if [[ -d "$AGENT_DIR" ]]; then
    checklist+="${C_GREEN}[✓]${C_RESET} Dir: $AGENT_DIR exists.\n"
  else
    checklist+="${C_RED}[✗]${C_RESET} Dir missing.\n"
    ok=false
  fi

  if [[ -d "$AGENT_DIR/venv" ]]; then
    checklist+="${C_GREEN}[✓]${C_RESET} Python venv exists.\n"
  else
    checklist+="${C_RED}[✗]${C_RESET} Python venv missing.\n"
    ok=false
  fi

  if [[ -f "$AGENT_DIR/venv/bin/pip" ]] && "$AGENT_DIR/venv/bin/pip" freeze | grep -qi "flask"; then
    checklist+="${C_GREEN}[✓]${C_RESET} Python deps installed.\n"
  else
    checklist+="${C_RED}[✗]${C_RESET} Python deps missing.\n"
    ok=false
  fi

  if [[ -f "$cfg" ]]; then
    checklist+="${C_GREEN}[✓]${C_RESET} Config exists.\n"
    local perms owner
    perms=$(stat -c "%a" "$cfg")
    owner=$(stat -c "%U:%G" "$cfg")

    if [[ "$perms" == "600" ]]; then
      checklist+="${C_GREEN}[✓]${C_RESET} Config perms 600.\n"
    else
      checklist+="${C_RED}[✗]${C_RESET} Config perms should be 600 (are $perms).\n"
      ok=false
    fi

    if [[ "$owner" == "root:root" ]]; then
      checklist+="${C_GREEN}[✓]${C_RESET} Config owner root:root.\n"
    else
      checklist+="${C_RED}[✗]${C_RESET} Config owner should be root:root (is $owner).\n"
      ok=false
    fi

    if jq -e '.api_key | test(".+")' "$cfg" >/dev/null; then
      checklist+="${C_GREEN}[✓]${C_RESET} API key present.\n"
    else
      checklist+="${C_RED}[✗]${C_RESET} API key missing.\n"
      ok=false
    fi
  else
    checklist+="${C_RED}[✗]${C_RESET} Config file missing.\n"
    ok=false
  fi

  if [[ -f "/etc/systemd/system/cloudflare-utils-agent.service" ]]; then
    checklist+="${C_GREEN}[✓]${C_RESET} systemd service exists.\n"

    if systemctl is-enabled --quiet cloudflare-utils-agent.service; then
      checklist+="${C_GREEN}[✓]${C_RESET} Service enabled.\n"
    else
      checklist+="${C_RED}[✗]${C_RESET} Service not enabled.\n"
      ok=false
    fi

    if systemctl is-active --quiet cloudflare-utils-agent.service; then
      checklist+="${C_GREEN}[✓]${C_RESET} Service active.\n"
    else
      checklist+="${C_RED}[✗]${C_RESET} Service not running.\n"
      ok=false
    fi
  else
    checklist+="${C_RED}[✗]${C_RESET} systemd service file missing.\n"
    ok=false
  fi

  echo -e "\n$checklist"

  if [[ "$ok" == true ]]; then
    return 0
  else
    return 1
  fi
}

verify_agent_installation() {
  if run_verification_checks_agent; then
    log_success "Agent installation verified."
    echo -e "${C_CYAN}
Agent tips:
  • Status: ${C_YELLOW}systemctl status cloudflare-utils-agent.service${C_CYAN}
  • Logs:   ${C_YELLOW}$AGENT_DIR/logs/startup.log${C_CYAN}
${C_RESET}"
  else
    log_error "Agent verification failed."
    read -rp "$(echo -e "${C_YELLOW}Rollback Agent installation? [Y/n]: ${C_RESET}")" ans
    if [[ "$ans" != "n" && "$ans" != "N" ]]; then
      rollback_agent
    fi
    die "Aborting due to agent verification failure."
  fi
}

install_agent() {
  local p_iface="$1" p_whitelist_csv="$2"
  log_info "--- Installing Monitoring Agent ---"

  verify_branch_and_agent_dir
  mkdir -p "$AGENT_DIR"
  download_agent_files
  setup_agent_venv

  echo -e "\n${C_CYAN}--- Agent Configuration ---${C_RESET}"
  local api_key; api_key=$(openssl rand -base64 32)

  local whitelist_json=""
  if [[ -n "$p_whitelist_csv" ]]; then
    local processed_ips=() ips
    IFS=',' read -ra ips <<< "$p_whitelist_csv"
    for ip in "${ips[@]}"; do
      ip="${ip// /}"
      if [[ -n "$ip" ]]; then
        processed_ips+=("\"$ip\"")
      fi
    done
    whitelist_json=$(IFS=,; echo "${processed_ips[*]}")
  else
    log_warning "Whitelist is empty → agent accepts connections from any IP."
  fi

  log_info "Validating interface '$p_iface' with vnstat…"
  if ! vnstat --json d 1 -i "$p_iface" | jq -e '.interfaces[0].traffic.day[0]' >/dev/null 2>&1; then
    log_warning "vnstat has no data for '$p_iface'. You can continue, but verify later via systemctl status."
  else
    log_success "vnstat validation passed for '$p_iface'."
  fi

  log_info "Creating Agent log directory…"
  mkdir -p "$AGENT_DIR/logs"
  touch "$AGENT_DIR/logs/startup.log"

  log_info "Writing config: $AGENT_DIR/config.json"
  cat > "$AGENT_DIR/config.json" <<EOF
{
  "api_key": "$api_key",
  "whitelist": [$whitelist_json],
  "vnstat_interface": "$p_iface"
}
EOF
  chmod 600 "$AGENT_DIR/config.json"
  chown root:root "$AGENT_DIR/config.json"

  log_info "Setting up systemd service…"
  sed "s|__PYTHON_EXEC_PATH__|$AGENT_DIR/venv/bin/python3|g" "$AGENT_DIR/cloudflare-utils-agent.service" > "/etc/systemd/system/cloudflare-utils-agent.service"

  log_info "Linking global 'cfu-agent' command…"
  ln -sf "$AGENT_DIR/cfu-agent.py" "/usr/local/bin/cfu-agent"
  chmod +x "$AGENT_DIR/cfu-agent.py" "/usr/local/bin/cfu-agent"

  log_info "Reloading systemd, enabling and starting the agent…"
  systemctl daemon-reload
  systemctl enable --now cloudflare-utils-agent.service || die "Failed to enable/start agent service."

  if ! systemctl is-active --quiet cloudflare-utils-agent.service; then
    log_error "Agent service failed to start."
    journalctl -u cloudflare-utils-agent.service --no-pager > "$AGENT_DIR/logs/startup.log"
    log_error "Logs saved to $AGENT_DIR/logs/startup.log"
    die "Installation failed."
  fi

  log_success "Monitoring Agent installed and running."
  echo -e "${C_GREEN}--- Agent API Key ---${C_RESET}
Your API Key: ${C_YELLOW}$api_key${C_RESET}
Stored at: ${C_CYAN}$AGENT_DIR/config.json${C_RESET}
Add this agent to Cloudflare-Utils via 'cfu' command.
Example:
  ${C_YELLOW}cfu add-agent --name my-server --ip <server-ip> --key '$api_key'${C_RESET}"
  verify_agent_installation
}

update_agent() {
  log_info "--- Updating Monitoring Agent ---"
  systemctl stop cloudflare-utils-agent.service || true

  log_info "Creating full backup of agent directory…"
  rm -rf /tmp/agent_full_backup
  cp -a "$AGENT_DIR" "/tmp/agent_full_backup" || die "Failed to backup agent."

  log_info "Backing up agent config…"
  mkdir -p /tmp/agent_backup
  [[ -f "$AGENT_DIR/config.json" ]] && cp "$AGENT_DIR/config.json" "/tmp/agent_backup/config.json"

  verify_branch_and_agent_dir
  download_agent_files
  setup_agent_venv

  log_info "Relinking 'cfu-agent' command…"
  rm -f "/usr/local/bin/cfu-agent"
  ln -sf "$AGENT_DIR/cfu-agent.py" "/usr/local/bin/cfu-agent"
  chmod +x "$AGENT_DIR/cfu-agent.py" "/usr/local/bin/cfu-agent"

  log_info "Reloading systemd and restarting agent…"
  sed "s|__PYTHON_EXEC_PATH__|$AGENT_DIR/venv/bin/python3|g" "$AGENT_DIR/cloudflare-utils-agent.service" > "/etc/systemd/system/cloudflare-utils-agent.service"
  systemctl daemon-reload
  systemctl restart cloudflare-utils-agent.service

  log_info "Verifying update…"
  if ! run_verification_checks_agent; then
    log_error "Agent update verification failed → rolling back."
    systemctl stop cloudflare-utils-agent.service || true
    rm -rf "$AGENT_DIR"
    mv "/tmp/agent_full_backup" "$AGENT_DIR"
    if [[ -f "$AGENT_DIR/cloudflare-utils-agent.service" ]]; then
      sed "s|__PYTHON_EXEC_PATH__|$AGENT_DIR/venv/bin/python3|g" "$AGENT_DIR/cloudflare-utils-agent.service" > "/etc/systemd/system/cloudflare-utils-agent.service"
      systemctl daemon-reload
    fi
    systemctl start cloudflare-utils-agent.service || true
    die "Agent update rolled back to previous version."
  fi

  rm -rf /tmp/agent_full_backup /tmp/agent_backup
  log_success "Monitoring Agent updated successfully."
}

remove_agent() {
  log_info "--- Removing Monitoring Agent ---"
  rm -f "/usr/local/bin/cfu-agent"
  if [[ -f "/etc/systemd/system/cloudflare-utils-agent.service" ]]; then
    log_info "Stopping and disabling service…"
    systemctl stop cloudflare-utils-agent.service || true
    systemctl disable cloudflare-utils-agent.service || true
    rm -f "/etc/systemd/system/cloudflare-utils-agent.service"
    systemctl daemon-reload
  else
    log_warning "Agent service file not found. Skipping."
  fi
  if [[ -d "$AGENT_DIR" ]]; then
    log_info "Removing directory: $AGENT_DIR"
    rm -rf "$AGENT_DIR"
    log_success "Agent removed."
  else
    log_warning "Agent directory not found. Skipping."
  fi
}

# --- Agent repo helpers (unchanged logic) ---
verify_branch_and_agent_dir() {
  if [[ -n "$LOCAL_DEV_PATH" ]]; then
    log_info "Verifying 'src/agent' in local path…"
    [[ -d "$LOCAL_DEV_PATH/src/agent" ]] || die "'src/agent' not found in '$LOCAL_DEV_PATH'."
    log_success "'src/agent' found in local path."
    return
  fi
  log_info "Verifying branch '$BRANCH' and presence of 'src/agent' on remote…"
  verify_branch_exists
  local github_repo_path api_url http_status
  github_repo_path=$(echo "$REPO_URL" | sed -n 's|https://github.com/||p' | sed 's/\.git$//')
  api_url="https://api.github.com/repos/$github_repo_path/contents/src/agent?ref=$BRANCH"
  http_status=$(curl -s -o /dev/null -w "%{http_code}" -H "Accept: application/vnd.github.v3+json" "$api_url")
  if [[ "$http_status" -eq 200 ]]; then
    log_success "'src/agent' directory confirmed on branch '$BRANCH'."
  elif [[ "$http_status" -eq 404 ]]; then
    die "'src/agent' directory not found on branch '$BRANCH'."
  else
    die "Could not verify 'src/agent' via GitHub API (HTTP $http_status)."
  fi
}

download_agent_files() {
  if [[ -n "$LOCAL_DEV_PATH" ]]; then
    log_info "Copying agent files from local path…"
    cp -a "$LOCAL_DEV_PATH/src/agent/." "$AGENT_DIR/" || die "Failed to copy agent files."
    log_success "Agent files copied from local path."
    return
  fi
  log_info "Downloading agent files from GitHub…"
  local github_repo_path api_url files_json
  github_repo_path=$(echo "$REPO_URL" | sed -n 's|https://github.com/||p' | sed 's/\.git$//')
  api_url="https://api.github.com/repos/$github_repo_path/contents/src/agent?ref=$BRANCH"
  files_json=$(curl -s -H "Accept: application/vnd.github.v3+json" "$api_url")
  echo "$files_json" | jq -e '.[0].name' >/dev/null 2>&1 || die "Failed to list agent dir via GitHub API."
  echo "$files_json" | jq -r '.[].name' | while read -r filename; do
    local url="https://raw.githubusercontent.com/$github_repo_path/$BRANCH/src/agent/$filename"
    log_info "Downloading '$filename'…"
    curl -s -L "$url" -o "$AGENT_DIR/$filename" || die "Failed to download '$filename'."
  done
  log_success "Agent files downloaded."
}

# --- Modes ---
run_non_interactive_mode() {
  log_info "Running in non-interactive mode…"
  if $AGENT_MODE; then
    if $UNINSTALL_MODE; then
      remove_agent
    else
      if [[ -d "$AGENT_DIR" ]]; then
        update_agent
      else
        install_agent "$IFACE" "$IP_WHITELIST"
      fi
    fi
  else
    if $UNINSTALL_MODE; then
      remove_cfutils
    else
      if [[ -d "$CFUTILS_DIR" ]]; then
        update_cfutils
      else
        install_cfutils
      fi
    fi
  fi
}

run_interactive_mode() {
  BRANCH="main"; LOCAL_DEV_PATH=""
  if [ -t 1 ]; then clear; fi
  echo -e "${C_MAGENTA}--- Cloudflare-Utils Installer ---${C_RESET}"
  log_info "Interactive mode uses default 'main' branch. For custom branch/local: use non-interactive flags."

  PS3="$(echo -e "${C_YELLOW}\nPlease choose an option: ${C_RESET}")"
  select opt in \
    "Install/Update Cloudflare-Utils" \
    "Install/Update Agent" \
    "Uninstall Cloudflare-Utils" \
    "Uninstall Agent" \
    "Exit"
  do
    case "$opt" in
      "Install/Update Cloudflare-Utils")
        if [[ -d "$CFUTILS_DIR" ]]; then update_cfutils; else install_cfutils; fi
        break;;
      "Install/Update Agent")
        if [[ -d "$AGENT_DIR" ]]; then
          update_agent
        else
          # Interactive agent prompts
          local whitelist_input
          read -rp "Enter comma-separated IPs to whitelist (e.g., 1.1.1.1,8.8.8.8) [optional]: " whitelist_input
          local interfaces=() iface
          for p in /sys/class/net/*; do
            [[ -d "$p" ]] || continue
            local name; name=$(basename "$p")
            [[ "$name" == "lo" ]] && continue
            interfaces+=("$name")
          done
          [[ ${#interfaces[@]} -gt 0 ]] || die "No network interfaces found (excluding 'lo')."
          PS3="$(echo -e "${C_YELLOW}Select the network interface to monitor: ${C_RESET}")"
          select iface in "${interfaces[@]}"; do
            [[ -n "$iface" ]] && break || log_warning "Invalid selection."
          done
          if ! vnstat --json d 1 -i "$iface" | jq -e '.interfaces[0].traffic.day[0]' >/dev/null 2>&1; then
            log_warning "vnstat has no data for '$iface'."
            read -rp "$(echo -e "${C_YELLOW}Continue anyway? [y/N]: ${C_RESET}")" a
            if [[ "$a" != "y" && "$a" != "Y" ]]; then
              die "Installation cancelled by user."
            fi
          fi
          install_agent "$iface" "$whitelist_input"
        fi
        break;;
      "Uninstall Cloudflare-Utils")
        read -rp "$(echo -e "${C_YELLOW}Are you sure you want to remove Cloudflare-Utils? [y/N]: ${C_RESET}")" a
        if [[ "$a" == "y" || "$a" == "Y" ]]; then
          remove_cfutils
        else
          log_info "Removal cancelled."
        fi
        break;;
      "Uninstall Agent")
        read -rp "$(echo -e "${C_YELLOW}Are you sure you want to remove the Agent? [y/N]: ${C_RESET}")" a
        if [[ "$a" == "y" || "$a" == "Y" ]]; then
          remove_agent
        else
          log_info "Removal cancelled."
        fi
        break;;
      "Exit") break;;
      *) log_warning "Invalid option '$REPLY'";;
    esac
  done
}

# --- Argument Parser ---
parse_args() {
  if [[ $# -gt 0 ]]; then INTERACTIVE_MODE=false; fi
  while [[ $# -gt 0 ]]; do
    case "$1" in
      -b) BRANCH="${2:?'-b' requires a value}"; shift 2;;
      --local) LOCAL_DEV_PATH=$(cd "$(dirname "$0")" && pwd); shift;;
      -u) UNINSTALL_MODE=true; shift;;
      --agent) AGENT_MODE=true; shift;;
      --ip-whitelist) IP_WHITELIST="${2:?--ip-whitelist requires value}"; shift 2;;
      --iface) IFACE="${2:?--iface requires value}"; shift 2;;
      -h|--help) usage;;
      *) log_error "Unknown option: $1"; usage;;
    esac
  done

  if ! $INTERACTIVE_MODE; then
    if [[ -n "$LOCAL_DEV_PATH" && "$BRANCH" != "main" ]]; then
      log_warning "Both --local and -b provided. Using local path."
    fi
    if $AGENT_MODE && ! $UNINSTALL_MODE && [[ -z "$IFACE" ]]; then
      die "Agent install in non-interactive mode requires --iface."
    fi
  fi
}

# --- Main ---
pre_flight_checks
parse_args "$@"

if $INTERACTIVE_MODE; then
  run_interactive_mode
else
  run_non_interactive_mode
fi