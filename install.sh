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

# Function to display ASCII art
display_ascii_art() {
    curl -sSL https://raw.githubusercontent.com/Issei-177013/Cloudflare-Utils/main/asset/Issei.txt
}

# Function to ask for user input securely
ask_user_input() {
    local prompt=$1
    local var_name=$2
    read -p "$(echo -e "\e[1;32m$prompt: \e[0m")" input
    echo "export $var_name=\"$input\"" >> ~/.bashrc
    export $var_name="$input"
}

# Install necessary packages
install_packages() {
    echo -e "\e[1;34mInstalling necessary packages...\e[0m"
    if ! sudo apt-get update; then
        echo -e "\e[1;31mFailed to update apt repositories.\e[0m" >&2
        exit 1
    fi
    
    if ! sudo apt-get install -y git python3-pip; then
        echo -e "\e[1;31mFailed to install required packages.\e[0m" >&2
        exit 1
    fi
    
    if ! pip3 install cloudflare; then
        echo -e "\e[1;31mFailed to install Python package 'cloudflare'.\e[0m" >&2
        exit 1
    fi

    if ! pip3 install tabulate; then
        echo -e "\e[1;31mFailed to install Python package 'tabulate'.\e[0m" >&2
        exit 1
    fi
    
    echo -e "\e[1;32mPackages installed successfully.\e[0m"
}

# Clone GitHub repository
clone_repository() {
    echo -e "\e[1;34mCloning GitHub repository...\e[0m"
    sudo mkdir -p $PROGRAM_DIR
    sudo chown $USER:$USER $PROGRAM_DIR || {
        echo -e "\e[1;31mFailed to create directory $PROGRAM_DIR.\e[0m" >&2
        exit 1
    }

    if ! git clone https://github.com/Issei-177013/Cloudflare-Utils.git $PROGRAM_DIR; then
        echo -e "\e[1;31mFailed to clone repository.\e[0m" >&2
        exit 1
    fi

    cd $PROGRAM_DIR || {
        echo -e "\e[1;31mFailed to change directory to $PROGRAM_DIR.\e[0m" >&2
        exit 1
    }

    if ! git checkout alpha; then
        echo -e "\e[1;31mFailed to checkout branch 'alpha'.\e[0m" >&2
        exit 1
    fi
    
    echo -e "\e[1;32mRepository cloned and switched to branch 'alpha' successfully.\e[0m"
}

# Main setup function
main_setup() {  
    display_ascii_art  
    echo " "
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

                echo -e "\e[1;32mAll necessary variables have been set.\e[0m"

                # Reload ~/.bashrc to load the new environment variables
                source ~/.bashrc

                clone_repository
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
            *) echo -e "\e[1;31mInvalid option $REPLY\e[0m";;
        esac
    done
}

main_setup
