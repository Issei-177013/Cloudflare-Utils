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

Issei_ID="@Isseidesu"

# Define colors
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
RESET='\033[0m'

# Function to log messages with timestamps
# log_message() {
#   local message=$1
#   echo -e "$(date '+%Y-%m-%d %H:%M:%S') - $message" >> "$LOG_FILE"
# }

# Function to display error messages and exit
function display_error_and_exit() {
  echo -e "${RED}Error: $1${RESET}"
  echo -e "${YELLOW}${Issei_ID}${RESET}"
  exit 1
}

# Function to log errors and exit
# log_error() {
#   local error_message=$1
#   echo -e "${RED}ERROR: $error_message${RESET}" >> "$LOG_FILE"
#   exit 1
# }

# Ensure the log file's directory exists
# mkdir -p "$PROGRAM_DIR" || log_error "Failed to create directory $PROGRAM_DIR"

# Ensure the log file exists and is writable
# touch "$LOG_FILE" || log_error "Cannot create or write to log file $LOG_FILE"

# Ensure ~/.bashrc exists
if [ ! -f ~/.bashrc ]; then
  display_error_and_exit "~/.bashrc does not exist. Please create it before running this script."
fi

# Function to ask for user input securely
ask_user_input() {
    local prompt=$1
    local var_name=$2
    read -p "$(echo -e "${GREEN}$prompt: ${RESET}")" input
    echo "export $var_name=\"$input\"" >> ~/.bashrc
    export $var_name="$input"
}

# Function to install Git if not already installed
install_git_if_needed() {
  if ! command -v git &>/dev/null; then
    echo -e "${BLUE}Git is not installed. Installing Git...${RESET}"

    # Install Git based on the operating system (Linux)
    if [ -f /etc/os-release ]; then
      source /etc/os-release
      if [ "$ID" == "ubuntu" ] || [ "$ID" == "debian" ]; then
        sudo apt update
        sudo apt install -y git
      elif [ "$ID" == "centos" ] || [ "$ID" == "rhel" ]; then
        sudo yum install -y git
      fi
    elif [ "$(uname -s)" == "Darwin" ]; then # macOS
      if ! command -v brew &>/dev/null; then
        echo -e "${RED}Homebrew is not installed. Installing Homebrew...${RESET}"
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
      fi
      brew install git
    else
      echo -e "${RED}Unsupported operating system. Please install Git manually and try again.${RESET}"
      exit 1
    fi

    if ! command -v git &>/dev/null; then
      echo -e "${RED}Failed to install Git. Please install Git manually and try again.${RESET}"
      exit 1
    fi

    echo -e "${GREEN}Git has been installed successfully.${RESET}"
  fi
}

# Function to install Python 3 and pip if they are not already installed
install_python3_and_pip_if_needed() {
  if ! command -v python3 &>/dev/null || ! command -v pip3 &>/dev/null; then
    echo -e "${BLUE}Python 3 and pip are required. Installing Python 3 and pip...${RESET}"

    # Install Python 3 and pip based on the operating system (Linux)
    if [ -f /etc/os-release ]; then
      source /etc/os-release
      if [ "$ID" == "ubuntu" ] || [ "$ID" == "debian" ]; then
        sudo apt update
        sudo apt install -y python3 python3-pip
      elif [ "$ID" == "centos" ] || [ "$ID" == "rhel" ]; then
        sudo yum install -y python3 python3-pip
      fi
    elif [ "$(uname -s)" == "Darwin" ]; then # macOS
      if ! command -v brew &>/dev/null; then
        echo -e "${RED}Homebrew is not installed. Installing Homebrew...${RESET}"
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
      fi
      brew install python@3
    else
      echo -e "${RED}Unsupported operating system. Please install Python 3 and pip manually and try again.${RESET}"
      exit 1
    fi

    if ! command -v python3 &>/dev/null || ! command -v pip3 &>/dev/null; then
      echo -e "${RED}Failed to install Python 3 and pip. Please install Python 3 and pip manually and try again.${RESET}"
      exit 1
    fi

    echo -e "${GREEN}Python 3 and pip have been installed successfully.${RESET}"
  fi
}

# Function to install necessary packages
install_requirements() {
    echo -e "${BLUE}Checking and installing necessary packages...${RESET}"

    # Read each line from requirements.txt
    while IFS= read -r package || [ -n "$package" ]; do
        # Extract package name without version (in case version is specified)
        package_name=$(echo $package | cut -d'=' -f1)
        
        # Check if the package is installed
        if ! pip3 show "$package_name" &>/dev/null; then
            echo -e "${BLUE}Installing Python package '$package_name'...${RESET}"
            if ! pip3 install "$package"; then
                echo -e "${RED}Failed to install Python package '$package_name'.${RESET}"
                exit 1
            fi
        else
            echo -e "${GREEN}Python package '$package_name' is already installed.${RESET}"
        fi
    done < requirements.txt

    echo -e "${GREEN}All requirements are installed.${RESET}"
}

# Final check to ensure all requirements are installed
requirements_check() {
    # Read each line from requirements.txt and check if it's installed
    while IFS= read -r package || [ -n "$package" ]; do
        package_name=$(echo $package | cut -d'=' -f1)

        if ! pip3 show "$package_name" &>/dev/null; then
            echo -e "${RED}Package '$package_name' is not installed properly.${RESET}"
            exit 1
        fi
    done < requirements.txt
}

echo -e "${BLUE}Step 0: Checking requirements...${RESET}"
install_git_if_needed
install_python3_and_pip_if_needed

# Check if Git is installed
if ! command -v git &>/dev/null; then
  echo -e "${RED}Git is not installed. Please install Git and try again.${RESET}"
  exit 1
fi

# Check if Python 3 and pip are installed
if ! command -v python3 &>/dev/null || ! command -v pip3 &>/dev/null; then
  echo -e "${RED}Python 3 and pip are required. Please install them and try again.${RESET}"
  exit 1
fi

echo -e "${BLUE}Step 1: Cloning the repository and changing directory...${RESET}"

repository_url="https://github.com/Issei-177013/Cloudflare-Utils.git"
install_dir="/opt/Cloudflare-Utils"

branch="main"

if [ "$0" == "--dev" ]; then
    branch="dev"
fi

echo "${GREEN}Selected branch: $branch ${RESET}"

if [ -d "$install_dir" ]; then
    echo "Directory $install_dir exists."
else
    git clone -b "$branch" "$repository_url" "$install_dir" || display_error_and_exit "${RED}Failed to clone the repository.${RESET}"
fi

cd "$install_dir" || display_error_and_exit "Failed to change directory."

echo -e "${BLUE}Step 2: Installing requirements...${RESET}"
install_requirements
requirements_check

echo -e "${BLUE}Step 3: Preparing ...${RESET}"
logs_dir="$install_dir/Logs"

create_directory_if_not_exists() {
  if [ ! -d "$1" ]; then
    echo "${BLUE}Creating directory $1 ${RESET}"
    mkdir -p "$1"
  fi
}

create_directory_if_not_exists "$logs_dir"

# chmod +x "$install_dir/restart.sh"
# chmod +x "$install_dir/update.sh"

# echo -e "${BLUE}Step 4: Running config.py to generate config.json...${RESET}"
# python3 config.py || display_error_and_exit "${RED}Failed to run config.py.${RESET}"

# echo -e "${BLUE}Step 5: Running Script${RESET}"
# nohup python3 ****** >>$install_dir/***** 2>&1 &

# echo -e "${BLUE}Step 6: Adding cron jobs...${RESET}"

# add_cron_job_if_not_exists() {
#   local cron_job="$1"
#   local current_crontab
#
#   # Normalize the cron job formatting (remove extra spaces)
#   cron_job=$(echo "$cron_job" | sed -e 's/^[ \t]*//' -e 's/[ \t]*$//')
#
#   # Check if the cron job already exists in the current user's crontab
#   current_crontab=$(crontab -l 2>/dev/null || true)
#
#   if [[ -z "$current_crontab" ]]; then
#     # No existing crontab, so add the new cron job
#     (echo "$cron_job") | crontab -
#   elif ! (echo "$current_crontab" | grep -Fq "$cron_job"); then
#     # Cron job doesn't exist, so append it to the crontab
#     (echo "$current_crontab"; echo "$cron_job") | crontab -
#   fi
# }

echo -e "${YELLOW}Waiting for a few seconds...${RESET}"
echo -e "${GREEN}Install successfully${RESET}"
sleep 7

# if pgrep -f "python3 ***.py" >/dev/null; then
#   echo -e "${GREEN}The *** has been started successfully.${RESET}"
# else
#   display_error_and_exit "Failed to start the ***. Please check for errors and try again."
# fi

# Main setup function
# main_setup() {
#     echo -e "${BLUE}Cloudflare-Utils Setup${RESET}"
#     PS3='Please enter your choice: '
#     options=("Install Cloudflare-Utils" "Remove Cloudflare-Utils" "Exit")
#     select opt in "${options[@]}"
#     do
#         case $opt in
#             "Install Cloudflare-Utils")
#                 clone_repository
#                 install_packages
#
#                 # Check if the variables are already set in ~/.bashrc
#                 source ~/.bashrc
#
#                 if [ -z "$CLOUDFLARE_API_TOKEN" ]; then
#                     ask_user_input "Enter your Cloudflare API Token" "CLOUDFLARE_API_TOKEN"
#                 fi
#
#                 if [ -z "$CLOUDFLARE_ZONE_ID" ]; then
#                     ask_user_input "Enter your Cloudflare Zone ID" "CLOUDFLARE_ZONE_ID"
#                 fi
#
#                 # Source the ~/.bashrc to ensure variables are available in the current session
#                 source ~/.bashrc
#
#                 echo -e "${GREEN}All necessary variables have been set.${RESET}"
#                 log_message "All necessary variables have been set."
#
#                 # Reload ~/.bashrc to load the new environment variables
#                 source ~/.bashrc
#
#                 bash "$PROGRAM_DIR/menu.sh"
#                 break
#                 ;;
#             "Remove Cloudflare-Utils")
#                 bash "$PROGRAM_DIR/uninstall.sh"
#                 break
#                 ;;
#             "Exit")
#                 break
#                 ;;
#             *) echo -e "${RED}Invalid option $REPLY${RESET}";;
#         esac
#     done
# }
