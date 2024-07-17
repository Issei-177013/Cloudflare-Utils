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

# Function to display the menu
show_menu() {
    clear  # Clear the terminal screen
    echo -e "${BLUE}Select an option:${RESET}"
    echo -e "${YELLOW}1)${RESET} ${GREEN}Show all DNS Records${RESET}"
    echo -e "${YELLOW}2)${RESET} ${GREEN}IP rotator${RESET}"
    echo -e "${YELLOW}3)${RESET} ${GREEN}Settings${RESET}"
    echo -e "${YELLOW}0)${RESET} ${GREEN}Back${RESET}"
}

# Main loop to display menu and handle user input
while true; do
    show_menu  # Display the menu

    # Prompt for user input
    read -rp "Enter your choice: " choice

    case $choice in
        1)
            clear
            echo "Show all DNS Records"
            python3 "$(pwd)/show_dns.py"
            read -n 1 -s -r -p "Press any key to continue..."
            ;;
        2)
            clear
            echo "IP rotator"
            bash "$(pwd)/rotator/dns_rotator.sh"
            ;;
        3)
            clear
            echo "Settings"
            read -n 1 -s -r -p "Press any key to continue..."
            ;;
        0)
            echo "Back to main menu..."
            bash "$PROGRAM_DIR/menu.sh"
            break
            ;;
        *)
            echo "Invalid option. Please select a valid option."
            read -n 1 -s -r -p "Press any key to continue..."
            ;;
    esac
done
