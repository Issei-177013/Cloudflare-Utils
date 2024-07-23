#!/bin/bash
# Copyright 2024 [Issei-177013]
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Define program and directory variables
PROGRAM_NAME="Cloudflare-Utils"
PROGRAM_DIR="/opt/$PROGRAM_NAME"
SCRIPT_DIR="$PROGRAM_DIR/dns_ip_rotator"
LOG_FILE="$SCRIPT_DIR/log.log"

# Define colors
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
RESET='\033[0m'

# Function to log messages with timestamps
log_message() {
  local message=$1
  echo -e "$(date '+%Y-%m-%d %H:%M:%S') - $message" >> "$LOG_FILE"
}

# Function to log errors and exit
log_error() {
  local error_message=$1
  echo -e "${RED}ERROR: $error_message${RESET}" >> "$LOG_FILE"
  exit 1
}

# Ensure the log file's directory exists
mkdir -p "$SCRIPT_DIR" || log_error "Failed to create directory $SCRIPT_DIR"

# Ensure the log file exists and is writable
touch "$LOG_FILE" || log_error "Cannot create or write to log file $LOG_FILE"

# Ensure ~/.bashrc exists
if [ ! -f ~/.bashrc ]; then
  log_error "~/.bashrc does not exist. Please create it before running this script."
fi

# Function to run a Python script with error handling and logging
run_show_dns_record() {
  local python_script="$SCRIPT_DIR/utils/run_show_dns_record.py"

  if [ ! -f "$python_script" ]; then
    log_error "Python script $python_script not found."
  fi

  log_message "Starting Python script: $python_script"

  python3 "$python_script" >> "$LOG_FILE" 2>&1

  if [ $? -ne 0 ]; then
    log_error "Python script $python_script failed. Check the log file for details."
  else
    log_message "Python script $python_script executed successfully."
  fi
}

# Function to ask for user input securely
ask_user_input() {
  local prompt=$1
  local var_name=$2
  read -p "$(echo -e "${GREEN}${prompt}: ${RESET}")" input
  # Remove existing definition
  sed -i "/export $var_name=/d" ~/.bashrc
  # Add new definition
  echo "export $var_name=\"$input\"" >> ~/.bashrc
  export $var_name="$input"
}

# Function to set up variables
set_variable() {
  log_message "Starting variable setup..."
  echo -e "${BLUE}Starting variable setup...${RESET}"

  run_show_dns_record
  source ~/.bashrc

  if [ -z "$CLOUDFLARE_RECORD_NAME" ]; then
    ask_user_input "Enter name of your record to be rotated" "CLOUDFLARE_RECORD_NAME"
  fi

  if [ -z "$CLOUDFLARE_IP_ADDRESSES" ]; then
    ask_user_input "Give me your list of IPs to start rotating (comma-separated)" "CLOUDFLARE_IP_ADDRESSES"
  fi

  source ~/.bashrc

  log_message "All variables have been set."
  echo -e "${GREEN}All variables have been set.${RESET}"
}

# Function to prompt user for input and update the variable
update_variable() {
  local var_name="$1"
  local prompt_message="$2"
  local current_value="${!var_name}"

  run_show_dns_record
  echo "$var_name is currently set to '$current_value'."
  read -p "$(echo -e "${GREEN}Enter new value for $var_name: ${RESET}")" new_value
  export $var_name="$new_value"

  sed -i "/export $var_name=/d" ~/.bashrc || log_error "Failed to remove old definition for $var_name"
  echo "export $var_name=\"$new_value\"" >> ~/.bashrc || log_error "Failed to add new definition for $var_name"
  source ~/.bashrc || log_error "Failed to source ~/.bashrc"

  log_message "$var_name has been updated to '$new_value'."
  echo -e "${GREEN}$var_name has been updated to '$new_value'.${RESET}"
}

# Function to prompt user for cron schedule
get_cron_schedule() {
  local default_schedule="*/30 * * * *"
  read -p "Enter cron schedule (default: $default_schedule): " schedule
  if [ -z "$schedule" ]; then
    schedule="$default_schedule"
  fi
  echo "$schedule"
}

# Function to set up the cron job
set_cronjob() {
  log_message "Setting up cron job..."
  echo -e "${BLUE}Setting up cron job...${RESET}"

  local cron_schedule
  cron_schedule=$(get_cron_schedule)

  (crontab -l 2>/dev/null; echo "$cron_schedule /bin/bash $SCRIPT_DIR/run.sh >> $SCRIPT_DIR/log.log 2>&1") | crontab - || log_error "Failed to add cron job for regular execution"
  (crontab -l 2>/dev/null; echo "@reboot /bin/bash $SCRIPT_DIR/run.sh >> $SCRIPT_DIR/log.log 2>&1") | crontab - || log_error "Failed to add cron job for reboot execution"

  log_message "Cron job setup completed."
  echo -e "${GREEN}Cron job setup completed.${RESET}"
}

# Function to display the menu
cfg_menu() {
  echo -e "${YELLOW}1. Update CLOUDFLARE_RECORD_NAME${RESET}"
  echo -e "${YELLOW}2. Update CLOUDFLARE_IP_ADDRESSES${RESET}"
  echo -e "${YELLOW}3. Setup Cron Job${RESET}"
  echo -e "${YELLOW}4. Exit${RESET}"
  read -p "Choose an option: " choice
  case $choice in
    1) update_variable "CLOUDFLARE_RECORD_NAME" "Enter name of your record to be rotated";;
    2) update_variable "CLOUDFLARE_IP_ADDRESSES" "Give me your list of IPs to start rotating (comma-separated)";;
    3) set_cronjob;;
    4) exit 0;;
    *) echo -e "${RED}Invalid option, please try again.${RESET}"; display_menu;;
  esac
}

# Main script logic

if [[ "$1" == "menu" ]]; then
  log_message "__cfg.sh__"
  # Loop to display the menu until the user chooses to exit
  while true; do
    display_menu
  done
elif [[ "$1" == "set_variable" ]]; then
  set_variable
elif [[ "$1" == "update_variable" ]]; then
  update_variable "$2" "$3"
elif [[ "$1" == "set_cronjob" ]]; then
  set_cronjob
else
  echo -e "${RED}Invalid argument. Usage: $0 {menu|set_variable|update_variable [var_name prompt_message]|set_cronjob}${RESET}"
  exit 1
fi
