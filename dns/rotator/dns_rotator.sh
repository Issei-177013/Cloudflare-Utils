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
SCRIPT_DIR="$PROGRAM_DIR/dns/rotator"

# Define colors
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
RESET='\033[0m'

# Function to ask for user input securely
ask_user_input() {
    local prompt=$1
    local var_name=$2
    read -p "$(echo -e "${GREEN}${prompt}: ${RESET}")" input
    echo "export $var_name=\"$input\"" >> ~/.bashrc
    export $var_name="$input"
}

# Create the Bash script to run Python script
create_dns_rotator_run_script() {
    echo -e "\e[1;34mCreating Bash script...\e[0m"
    cat << 'EOF' > $SCRIPT_DIR/run.sh
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

source ~/.bashrc

{
    echo "$(date) - Starting script"
    python3 $SCRIPT_DIR/dns_rotator.py
    echo "$(date) - Finished script"
} >> $PROGRAM_DIR/log_file.log 2>&1
EOF
    chmod +x $PROGRAM_DIR/run.sh || {
        echo -e "\e[1;31mFailed to set executable permission on $PROGRAM_DIR/run.sh.\e[0m" >&2
        exit 1
    }
    
    echo -e "\e[1;32mBash script created successfully.\e[0m"
}

setup_dns_rotator(){
  python3 "$(pwd)/show_dns.py"

  # Check if the variables are already set in ~/.bashrc
  source ~/.bashrc

  if [ -z "$CLOUDFLARE_RECORD_NAME" ]; then
    ask_user_input "Enter IP of your record to be rotate" "CLOUDFLARE_RECORD_NAME"
  fi

  if [ -z "$CLOUDFLARE_IP_ADDRESSES" ]; then
    ask_user_input "Give me your list of IPs to start rotating (comma-separated)" "CLOUDFLARE_IP_ADDRESSES"
  fi

  # Source the ~/.bashrc to ensure variables are available in the current session
  source ~/.bashrc

  echo -e "${GREEN}All necessary variables have been set.${RESET}"

  echo -e "${BLUE}Setting up cron job...${RESET}"

  (crontab -l 2>/dev/null; echo "*/30 * * * * /bin/bash $SCRIPT_DIR/run.sh >> $SCRIPT_DIR/log_file.log 2>&1") | crontab - || {
    echo -e "${RED}Failed to add cron job for regular execution.${RESET}" >&2
    exit 1
  }

  (crontab -l 2>/dev/null; echo "@reboot /bin/bash $SCRIPT_DIR/run.sh >> $SCRIPT_DIR/log_file.log 2>&1") | crontab - || {
    echo -e "${RED}Failed to add cron job for reboot execution.${RESET}" >&2
    exit 1
  }

  echo -e "${GREEN}Cron job setup completed.${RESET}"

  echo -e "${GREEN}DNS rotator setup complete.${RESET} Please check the log file at $PROGRAM_DIR/log_file.log for execution logs."

}

# Function to display the menu
show_menu() {
    clear  # Clear the terminal screen
    echo -e "${BLUE}Select an option:${RESET}"
    echo -e "${YELLOW}1)${RESET} ${GREEN}Setup DNS rotator${RESET}"
    echo -e "${YELLOW}2)${RESET} ${GREEN}Change record${RESET}"
    echo -e "${YELLOW}3)${RESET} ${GREEN}Set cronjob time${RESET}"
    echo -e "${YELLOW}4)${RESET} ${GREEN}Stop Service${RESET}"
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
            echo "Start Setup DNS rotator..."
            setup_dns_rotator
            read -n 1 -s -r -p "Press any key to continue..."
            ;;
        2)
            clear
            echo "Change domain to rotate"
            read -n 1 -s -r -p "Press any key to continue..."
            ;;
        3)
            clear
            echo "Seting cronjob time"
            ;;
        4)
            clear
            echo "Stoping DNS rotator service"
            read -n 1 -s -r -p "Press any key to continue..."
            ;;
        0)
            echo "back"
            bash "$(pwd)/dns_menu.sh"
            break
            ;;
        *)
            echo "Invalid option. Please select a valid option."
            read -n 1 -s -r -p "Press any key to continue..."
            ;;
    esac
done