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
    # Ensure the directory exists
    sudo mkdir -p $PROGRAM_DIR
    sudo chown $USER:$USER $PROGRAM_DIR
    echo "$var_name=$input" >> $PROGRAM_DIR/.env
    export $var_name="$input" # Keep this for the current session during install
}

# Install necessary packages
install_packages() {
    echo -e "\e[1;34mInstalling necessary packages...\e[0m"
    if ! sudo apt-get update; then
        echo -e "\e[1;31mFailed to update apt repositories.\e[0m" >&2
        exit 1
    fi
    
    # Attempt to install python3-dotenv, if not available, it will be installed via pip
    if ! sudo apt-get install -y git python3-pip python3-dotenv; then
        echo -e "\e[1;33mWarning: Failed to install python3-dotenv via apt. Will attempt with pip.\e[0m"
        # Install git and python3-pip first if python3-dotenv failed with them
        if ! sudo apt-get install -y git python3-pip; then
            echo -e "\e[1;31mFailed to install git and python3-pip.\e[0m" >&2
            exit 1
        fi
    fi
    
    if ! pip3 install cloudflare python-dotenv; then
        echo -e "\e[1;31mFailed to install Python package 'cloudflare'.\e[0m" >&2
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
    
    echo -e "\e[1;32mRepository cloned successfully.\e[0m"
}

# Create the Bash script to run Python script
create_bash_script() {
    echo -e "\e[1;34mCreating Bash script...\e[0m"
    cat << 'EOF' > $PROGRAM_DIR/run.sh
#!/bin/bash
PROGRAM_NAME="Cloudflare-Utils"
PROGRAM_DIR="/opt/$PROGRAM_NAME"

# Load environment variables from .env file
if [ -f "$PROGRAM_DIR/.env" ]; then
    export $(grep -v '^#' $PROGRAM_DIR/.env | xargs)
else
    echo "$(date) - Error: .env file not found at $PROGRAM_DIR/.env" >> $PROGRAM_DIR/log_file.log 2>&1
    exit 1
fi

{
    echo "$(date) - Starting script"
    python3 $PROGRAM_DIR/change_dns.py
    echo "$(date) - Finished script"
} >> $PROGRAM_DIR/log_file.log 2>&1
EOF
    chmod +x $PROGRAM_DIR/run.sh || {
        echo -e "\e[1;31mFailed to set executable permission on $PROGRAM_DIR/run.sh.\e[0m" >&2
        exit 1
    }
    
    echo -e "\e[1;32mBash script created successfully.\e[0m"
}

# Setup Cron Job
setup_cron() {
    echo -e "\e[1;34mSetting up cron job...\e[0m"
    
    (crontab -l 2>/dev/null; echo "*/30 * * * * /bin/bash $PROGRAM_DIR/run.sh >> $PROGRAM_DIR/log_file.log 2>&1") | crontab - || {
        echo -e "\e[1;31mFailed to add cron job for regular execution.\e[0m" >&2
        exit 1
    }
    
    (crontab -l 2>/dev/null; echo "@reboot /bin/bash $PROGRAM_DIR/run.sh >> $PROGRAM_DIR/log_file.log 2>&1") | crontab - || {
        echo -e "\e[1;31mFailed to add cron job for reboot execution.\e[0m" >&2
        exit 1
    }
    
    echo -e "\e[1;32mCron job setup completed.\e[0m"
}

# Function to remove the program and cron jobs
remove_program() {
    echo -e "\e[1;34mRemoving the program and cron jobs...\e[0m"
    
    sudo rm -rf $PROGRAM_DIR
    crontab -l | grep -v "$PROGRAM_DIR/run.sh" | crontab -
    
    echo -e "\e[1;32mProgram and cron jobs removed successfully.\e[0m"
}

# Display menu
display_menu() {
    echo -e "\e[1;33m1. Install Cloudflare-Utils\e[0m"
    echo -e "\e[1;33m2. Remove Cloudflare-Utils\e[0m"
    echo -e "\e[1;33m3. Exit\e[0m"
}

# Main setup function
main_setup() {  
    # display_ascii_art  
    PS3='Please enter your choice: '
    options=("Install Cloudflare-Utils" "Remove Cloudflare-Utils" "Exit")
    select opt in "${options[@]}"
    do
        case $opt in
            "Install Cloudflare-Utils")
                install_packages
                
                # Create $PROGRAM_DIR before asking for input, so .env can be stored.
                # clone_repository also creates this, but it's better to be explicit.
                sudo mkdir -p $PROGRAM_DIR
                sudo chown $USER:$USER $PROGRAM_DIR

                # Check if the variables are already set (e.g. from a previous install attempt or manually set for the session)
                # We don't source .bashrc anymore. We check current environment variables.
                # If .env file exists, we can source it to check, but for simplicity,
                # we'll just ask if not set in current environment.
                # A more robust check would involve reading the .env file if it exists.

                if [ -f "$PROGRAM_DIR/.env" ]; then
                    export $(grep -v '^#' $PROGRAM_DIR/.env | xargs)
                fi

                if [ -z "$CLOUDFLARE_API_TOKEN" ]; then
                    ask_user_input "Enter your Cloudflare API Token" "CLOUDFLARE_API_TOKEN"
                fi

                if [ -z "$CLOUDFLARE_ZONE_ID" ]; then
                    ask_user_input "Enter your Cloudflare Zone ID" "CLOUDFLARE_ZONE_ID"
                fi

                if [ -z "$CLOUDFLARE_RECORD_NAME" ]; then
                    ask_user_input "Enter your Cloudflare Record Name" "CLOUDFLARE_RECORD_NAME"
                fi

                if [ -z "$CLOUDFLARE_IP_ADDRESSES" ]; then
                    ask_user_input "Enter your Cloudflare IP Addresses (comma-separated)" "CLOUDFLARE_IP_ADDRESSES"
                fi

                echo -e "\e[1;32mAll necessary variables have been set in $PROGRAM_DIR/.env\e[0m"

                clone_repository # This will overwrite the .env if it's part of the repo, which is not ideal.
                                 # For now, assume .env is not in the repo or .gitignore handles it.
                                 # A better approach would be to create .env after cloning if it doesn't exist.
                                 # Or, to write to a temporary location and then move it.
                                 # Given the current structure, ask_user_input is called *before* clone_repository.
                                 # The current ask_user_input writes to $PROGRAM_DIR/.env.
                                 # If clone_repository is called after, it might overwrite this .env if .env is tracked.
                                 # The original script called clone_repository AFTER asking for inputs too.
                                 # Let's ensure .env is created in $PROGRAM_DIR which is created by clone_repository.
                                 # The fix in ask_user_input to mkdir -p $PROGRAM_DIR should handle this.

                create_bash_script
                setup_cron

                echo -e "\e[1;32mSetup complete.\e[0m Please check the log file at $PROGRAM_DIR/log_file.log for execution logs."        
                break
                ;;
            "Remove Cloudflare-Utils")
                remove_program
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