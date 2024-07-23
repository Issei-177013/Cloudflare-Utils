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

# Function to ask for user input securely
ask_user_input() {
    local prompt=$1
    local var_name=$2
    read -p "$(echo -e "${GREEN}$prompt: ${RESET}")" input
    echo "export $var_name=\"$input\"" >> ~/.bashrc
    export $var_name="$input"
}

# Function to display the menu
show_menu() {
  clear  # Clear the terminal screen
  echo -e "${BLUE}Select an option:${RESET}"
  echo -e "${YELLOW}1)${RESET} ${GREEN}DNS utils${RESET}"
  echo -e "${YELLOW}2)${RESET} ${GREEN}noting${RESET}"
  echo -e "${YELLOW}3)${RESET} ${GREEN}noting${RESET}"
  echo -e "${YELLOW}4)${RESET} ${GREEN}Uninstall Cloudflare-Utils${RESET}"
  echo -e "${YELLOW}0)${RESET} ${GREEN}Exit${RESET}"
}

# Main loop to display menu and handle user input
while true; do
  show_menu  # Display the menu

  # Prompt for user input
  read -rp "Enter your choice: " choice

  case $choice in
    1)
      clear
      log_message "Selected DNS utils"
      echo -e "${BLUE}DNS IPs rotator${RESET}"
      bash "$PROGRAM_DIR/dns_ip_rotator/menu.sh" || log_error "Failed to execute DNS IPs rotator script."
      read -n 1 -s -r -p "$(echo -e "${YELLOW}Press any key to continue...${RESET}")"
      ;;
    2)
      clear
      log_message "Selected Option 2: noting"
      echo -e "${YELLOW}Option 2: noting${RESET}"
      read -n 1 -s -r -p "$(echo -e "${YELLOW}Press any key to continue...${RESET}")"
      ;;
    3)
      clear
      log_message "Selected Option 3: noting"
      echo -e "${YELLOW}Option 3: noting${RESET}"
      read -n 1 -s -r -p "$(echo -e "${YELLOW}Press any key to continue...${RESET}")"
      ;;
    4)
      clear
      log_message "Selected Uninstall Cloudflare-Utils"
      echo -e "${RED}Uninstall Cloudflare-Utils${RESET}"
      bash "$PROGRAM_DIR/uninstall.sh" || log_error "Failed to execute uninstall script."
      read -n 1 -s -r -p "$(echo -e "${YELLOW}Press any key to continue...${RESET}")"
      ;;
    0)
      log_message "Exiting script"
      echo -e "${GREEN}Exiting...${RESET}"
      break
      ;;
    *)
      log_message "Invalid option selected: $choice"
      echo -e "${RED}Invalid option. Please select a valid option.${RESET}"
      read -n 1 -s -r -p "$(echo -e "${YELLOW}Press any key to continue...${RESET}")"
      ;;
  esac
done
