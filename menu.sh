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

PROGRAM_NAME="Cloudflare-Utils"
PROGRAM_DIR="/opt/$PROGRAM_NAME"

# Define colors
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
RESET='\033[0m'

# Function to ask for user input securely
ask_user_input() {
    local prompt=$1
    local var_name=$2
    read -p "$(echo -e "\e[1;32m$prompt: \e[0m")" input
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
      echo "DNS utils"
      bash "$PROGRAM_DIR/dns/dns_menu.sh"
      ;;
    2)
      clear
      echo "Option 2: noting"
      read -n 1 -s -r -p "Press any key to continue..."
      ;;
    3)
      clear
      echo "Option 3: noting"
      read -n 1 -s -r -p "Press any key to continue..."
      ;;
    4)
      clear
      echo "Option 3: Uninstall Cloudflare-Utils"
      bash "$PROGRAM_DIR/uninstall.sh"
      read -n 1 -s -r -p "Press any key to continue..."
      ;;
    0)
      echo "Exiting..."
      break
      ;;
    *)
      echo "Invalid option. Please select a valid option."
      read -n 1 -s -r -p "Press any key to continue..."
      ;;
  esac
done