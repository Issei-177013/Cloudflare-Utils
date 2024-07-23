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

setup_dns_ip_rotator() {
  log_message "Starting DNS IP rotator setup..."

  # Source the utils.sh file to import the set_variable function
  if ! source "$SCRIPT_DIR/cfg.sh"; then
    log_error "Failed to source utils.sh. Ensure the file exists and is accessible."
  fi

  # Call the set_variable function
  if ! set_variable; then
    log_error "Failed to execute set_variable. Check the log for details."
  fi

  # Source the edit_cfg.sh file
  if ! source "$SCRIPT_DIR/cfg.sh"; then
    log_error "Failed to source edit_cfg.sh. Ensure the file exists and is accessible."
  fi

  # Call the set_cronjob function
  if ! set_cronjob; then
    log_error "Failed to execute set_cronjob. Check the log for details."
  fi

  log_message "DNS rotator setup complete. Please check the log file at $LOG_FILE for execution details."
  echo -e "${GREEN}DNS IP rotator setup complete.${RESET} Please check the log file at $LOG_FILE for execution details."
}