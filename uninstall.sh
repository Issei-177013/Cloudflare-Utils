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
LOG_FILE="$PROGRAM_DIR/log.log"

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
mkdir -p "$PROGRAM_DIR" || log_error "Failed to create directory $PROGRAM_DIR"

# Ensure the log file exists and is writable
touch "$LOG_FILE" || log_error "Cannot create or write to log file $LOG_FILE"

# Ensure ~/.bashrc exists
if [ ! -f ~/.bashrc ]; then
  log_error "~/.bashrc does not exist. Please create it before running this script."
fi

# Function to remove the program and cron jobs
remove_program() {
    echo -e "${BLUE}Removing the program and cron jobs...${RESET}"
    log_message "Removing the program and cron jobs..."
    
    sudo rm -rf "$PROGRAM_DIR" || log_error "Failed to remove $PROGRAM_DIR"
    
    echo -e "${GREEN}Program removed successfully.${RESET}"
}

remove_env_vars() {
    # List of variables you want to remove
    vars=("CLOUDFLARE_API_TOKEN" "CLOUDFLARE_ZONE_ID" "CLOUDFLARE_RECORD_NAME" "CLOUDFLARE_IP_ADDRESSES")

    # Path to the bashrc file
    bashrc_file="$HOME/.bashrc"

    # Create a temporary file
    temp_file=$(mktemp)

    # Copy the contents of the bashrc file to the temporary file,
    # excluding lines that contain the specified variables
    grep -v -E "$(IFS="|"; echo "${vars[*]}")" "$bashrc_file" > "$temp_file"

    # Replace the original bashrc file with the temporary file
    mv "$temp_file" "$bashrc_file" || log_error "Failed to update ~/.bashrc file"

    echo -e "${GREEN}The specified variables have been removed from the ~/.bashrc file.${RESET}"
    log_message "The specified variables have been removed from the ~/.bashrc file."
}

remove_cronjobs() {
    crontab -l | grep -v '/opt/Cloudflare-Utils/dns/rotator/run.sh' | crontab - || log_error "Failed to remove cronjobs"
    echo -e "${GREEN}Cronjobs removed successfully.${RESET}"
    log_message "Cronjobs removed successfully."
}

remove_cronjobs
remove_env_vars
remove_program

echo -e "${GREEN}Cleanup complete.${RESET}"

cd || echo -e "Failed to change directory to home"
