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

# Log the start of the script
log_message "Starting script"

# Execute the Python script and log its output
{
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Running Python script"
    python3 "$SCRIPT_DIR/dns_rotator.py"
    if [ $? -eq 0 ]; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') - Python script completed successfully"
        log_message "Python script completed successfully"
    else
        echo "$(date '+%Y-%m-%d %H:%M:%S') - Python script failed with exit code $?"
        log_error "Python script failed with exit code $?"
    fi
} >> "$LOG_FILE" 2>&1

# Log the end of the script
log_message "Finished script"
