#!/bin/bash
# Copyright 2024 [Issei-177013]
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
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
  echo "$(date '+%Y-%m-%d %H:%M:%S') - $message" | tee -a "$LOG_FILE"
}

# Function to log errors and exit
log_error() {
  local error_message=$1
  echo -e "${RED}ERROR: $error_message${RESET}" | tee -a "$LOG_FILE"
  echo -e "${RED}ERROR: $error_message${RESET}"
  exit 1
}

# Ensure the log file's directory exists
mkdir -p "$SCRIPT_DIR" || log_error "Failed to create directory $SCRIPT_DIR"

# Ensure the log file exists and is writable
touch "$LOG_FILE" || log_error "Cannot create or write to log file $LOG_FILE"

# Function to remove the program and cron jobs
remove_program() {
  log_message "Removing the program and cron jobs..."
  echo -e "${BLUE}Removing the program and cron jobs...${RESET}"

  sudo rm -rf "$PROGRAM_DIR" || log_error "Failed to remove $PROGRAM_DIR"
  log_message "Program removed successfully."
  echo -e "${GREEN}Program removed successfully.${RESET}"
}

# Function to remove environment variables
remove_env_vars() {
  local vars=("CLOUDFLARE_API_TOKEN" "CLOUDFLARE_ZONE_ID" "CLOUDFLARE_RECORD_NAME" "CLOUDFLARE_IP_ADDRESSES")
  local bashrc_file="$HOME/.bashrc"

  # Create a temporary file
  local temp_file
  temp_file=$(mktemp)

  # Copy the contents of the bashrc file to the temporary file, excluding lines with specified variables
  grep -v -E "$(IFS="|"; echo "${vars[*]}")" "$bashrc_file" > "$temp_file"

  # Replace the original bashrc file with the temporary file
  mv "$temp_file" "$bashrc_file" || log_error "Failed to update $bashrc_file"
  log_message "The specified variables have been removed from the ~/.bashrc file."
  echo -e "${GREEN}The specified variables have been removed from the ~/.bashrc file.${RESET}"
}

# Function to remove cron jobs
remove_cronjobs() {
  local cronjob_pattern='/opt/Cloudflare-Utils/dns_ip_rotator/run.sh'
  
  # Remove cron jobs related to the program
  crontab -l | grep -v "$cronjob_pattern" | crontab - || log_error "Failed to remove cron jobs"
  log_message "Cron jobs removed successfully."
  echo -e "${GREEN}Cron jobs removed successfully.${RESET}"
}

# Main function to run the uninstall steps
uninstall() {
  log_message "Starting the uninstallation process..."

  remove_program
  remove_env_vars
  remove_cronjobs

  log_message "Uninstallation process complete."
  echo -e "${GREEN}Uninstallation process complete.${RESET} Please check the log file at $LOG_FILE for details."
}
