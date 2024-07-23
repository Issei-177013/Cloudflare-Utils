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
DNS_DIR="$PROGRAM_DIR/dns_ip_rotator"

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

  # Check if the Python script file exists
  if [ ! -f "$python_script" ]; then
    log_error "Python script $python_script not found."
  fi

  # Log the start of the Python script execution
  log_message "Starting Python script: $python_script"

  # Execute the Python script and redirect both stdout and stderr to the log file
  python3 "$python_script" >> "$LOG_FILE" 2>&1

  # Check the exit status of the Python script
  if [ $? -ne 0 ]; then
    log_error "Python script $python_script failed. Check the log file for details."
  else
    log_message "Python script $python_script executed successfully."
  fi
}

# Function to display the menu
show_menu() {
    clear  # Clear the terminal screen
    echo -e "${BLUE}Select an option:${RESET}"
    echo -e "${YELLOW}1)${RESET} ${GREEN}Setup DNS IP rotator${RESET}"
    echo -e "${YELLOW}2)${RESET} ${GREEN}Change Config${RESET}"
    echo -e "${YELLOW}3)${RESET} ${GREEN}Stop and Uninstall Script${RESET}"
    echo -e "${YELLOW}0)${RESET} ${GREEN}Back${RESET}"
}

# Function to call the setup_dns_ip_rotator function from setup.sh
setup_dns_ip_rotator() {
    if ! source "$SCRIPT_DIR/setup.sh"; then
        log_error "Failed to source setup.sh"
    fi
    setup_dns_ip_rotator  # Call the setup_dns_ip_rotator function defined in setup.sh
}

# Function to change the DNS record by calling cfg.sh
change_config() {
    if ! source "$SCRIPT_DIR/cfg.sh"; then
        log_error "Failed to source cfg.sh"
    fi
    cfg_menu  # Call the cfg_menu function defined in cfg.sh
}

# Function to stop the DNS rotator service by calling uninstall.sh
uninstall() {
    if ! source "$SCRIPT_DIR/uninstall.sh"; then
        log_error "Failed to source uninstall.sh"
    fi
    uninstall  # Call the stop_service function defined in uninstall.sh
}

# Main loop to display menu and handle user input
while true; do
    run_show_dns_record
    show_menu  # Display the menu

    # Prompt for user input
    read -rp "Enter your choice: " choice

    case $choice in
        1)
            clear
            echo -e "${GREEN}Setup DNS IP rotator${RESET}"
            setup_dns_ip_rotator
            read -n 1 -s -r -p "Press any key to continue..."
            ;;
        2)
            clear
            echo -e "${GREEN}change config${RESET}"
            change_config
            ;;
        3)
            clear
            echo -e "${GREEN}Stop and Uninstall Script${RESET}"
            uninstall
            read -n 1 -s -r -p "Press any key to continue..."
            ;;
        0)
            clear
            echo -e "${YELLOW}Returning to main menu...${RESET}"
            bash "$DNS_DIR/dns_menu.sh"
            break
            ;;
        *)
            echo -e "${RED}Invalid option. Please select a valid option.${RESET}"
            ;;
    esac
done
