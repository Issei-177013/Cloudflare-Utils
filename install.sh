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
  echo -e "$(date '+%Y-%m-%d %H:%M:%S') - $message" | tee -a "$LOG_FILE"
}

# Function to log errors and exit
log_error() {
  local error_message=$1
  echo -e "${RED}ERROR: $error_message${RESET}" | tee -a "$LOG_FILE"
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

# Install necessary packages
install_packages() {
    echo -e "${BLUE}Installing necessary packages...${RESET}"
    log_message "Installing necessary packages..."
    
    if ! sudo apt-get update; then
        log_error "Failed to update apt repositories."
    fi
    
    if ! sudo apt-get install -y git python3-pip; then
        log_error "Failed to install required packages."
    fi
    
    if ! pip3 install cloudflare; then
        log_error "Failed to install Python package 'cloudflare'."
    fi

    if ! pip3 install tabulate; then
        log_error "Failed to install Python package 'tabulate'."
    fi
    
    echo -e "${GREEN}Packages installed successfully.${RESET}"
    log_message "Packages installed successfully."
}

# # Clone GitHub repository
# clone_repository() {
#     echo -e "${BLUE}Cloning GitHub repository...${RESET}"
#     log_message "Cloning GitHub repository..."
    
#     sudo mkdir -p "$PROGRAM_DIR"
#     sudo chown $USER:$USER "$PROGRAM_DIR" || log_error "Failed to create directory $PROGRAM_DIR."

#     if ! git clone https://github.com/Issei-177013/Cloudflare-Utils.git "$PROGRAM_DIR"; then
#         log_error "Failed to clone repository."
#     fi

#     cd "$PROGRAM_DIR" || log_error "Failed to change directory to $PROGRAM_DIR."

#     if ! git checkout alpha; then
#         log_error "Failed to checkout branch 'alpha'."
#     fi
    
#     echo -e "${GREEN}Repository cloned and switched to branch 'alpha' successfully.${RESET}"
#     log_message "Repository cloned and switched to branch 'alpha' successfully."
# }

# Main setup function
main_setup() {
    echo -e "${BLUE}Cloudflare-Utils Setup${RESET}"
    PS3='Please enter your choice: '
    options=("Install Cloudflare-Utils" "Remove Cloudflare-Utils" "Exit")
    select opt in "${options[@]}"
    do
        case $opt in
            "Install Cloudflare-Utils")
                install_packages

                # Check if the variables are already set in ~/.bashrc
                source ~/.bashrc

                if [ -z "$CLOUDFLARE_API_TOKEN" ]; then
                    ask_user_input "Enter your Cloudflare API Token" "CLOUDFLARE_API_TOKEN"
                fi

                if [ -z "$CLOUDFLARE_ZONE_ID" ]; then
                    ask_user_input "Enter your Cloudflare Zone ID" "CLOUDFLARE_ZONE_ID"
                fi

                # Source the ~/.bashrc to ensure variables are available in the current session
                source ~/.bashrc

                echo -e "${GREEN}All necessary variables have been set.${RESET}"
                log_message "All necessary variables have been set."

                # Reload ~/.bashrc to load the new environment variables
                source ~/.bashrc

                # clone_repository
                bash "$PROGRAM_DIR/menu.sh"
                break
                ;;
            "Remove Cloudflare-Utils")
                bash "$PROGRAM_DIR/uninstall.sh"
                break
                ;;
            "Exit")
                break
                ;;
            *) echo -e "${RED}Invalid option $REPLY${RESET}";;
        esac
    done
}

main_setup
