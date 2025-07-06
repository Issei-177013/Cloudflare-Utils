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
VERSION="v1.0.0"
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

# Clone GitHub repository or update if it already exists
clone_repository() {
    echo -e "\e[1;34mSetting up repository in $PROGRAM_DIR...\e[0m"

    # Ensure the program directory exists and has correct permissions
    # This needs to be done before git operations, especially for the initial clone
    if [ ! -d "$PROGRAM_DIR" ]; then
        sudo mkdir -p $PROGRAM_DIR || {
            echo -e "\e[1;31mFailed to create directory $PROGRAM_DIR.\e[0m" >&2
            exit 1
        }
        sudo chown $USER:$USER $PROGRAM_DIR || {
            echo -e "\e[1;31mFailed to set ownership for $PROGRAM_DIR.\e[0m" >&2
            # Attempt to continue if chown fails, git might still work if user has rights
        }
    fi

    if [ -d "$PROGRAM_DIR/.git" ]; then
        echo -e "\e[1;34mRepository already exists. Updating from remote...\e[0m"
        # Temporarily change ownership to current user for git pull if needed, then revert
        # This is complex if root owns some files. Assuming user owns $PROGRAM_DIR for simplicity here.
        # A better model might involve running git operations as the user, not sudo, if $PROGRAM_DIR is user-owned.
        # For now, let's assume the user who runs install.sh owns $PROGRAM_DIR or has write permissions.
        # The sudo chown $USER:$USER $PROGRAM_DIR above should handle this for the current user.
        
        # Ensure the current user can write to the directory for git pull
        sudo chown -R $USER:$USER $PROGRAM_DIR 2>/dev/null # Best effort, might fail on some files if not owned by user initially

        cd $PROGRAM_DIR || {
            echo -e "\e[1;31mFailed to change directory to $PROGRAM_DIR.\e[0m" >&2
            exit 1
        }
        if ! git pull; then
            echo -e "\e[1;31mFailed to update repository. Please check for errors or try manually.\e[0m" >&2
            # Optionally, exit here or allow script to continue with potentially outdated code
            # exit 1 
        else
            echo -e "\e[1;32mRepository updated successfully.\e[0m"
        fi
        cd - > /dev/null # Go back to previous directory
    else
        echo -e "\e[1;34mCloning GitHub repository...\e[0m"
        # Need to ensure $PROGRAM_DIR is writable by current user for git clone,
        # or clone into a temp dir and then sudo mv.
        # The initial sudo mkdir -p and sudo chown $USER:$USER should make it writable.
        if ! git clone https://github.com/Issei-177013/Cloudflare-Utils.git $PROGRAM_DIR; then
            echo -e "\e[1;31mFailed to clone repository.\e[0m" >&2
            exit 1
        fi
        # After cloning, ensure the user owns the files if that's the desired state
        sudo chown -R $USER:$USER $PROGRAM_DIR 2>/dev/null # Best effort
        echo -e "\e[1;32mRepository cloned successfully.\e[0m"
    fi
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
                
                # First, setup or update the repository.
                # clone_repository will also handle creation of $PROGRAM_DIR and basic ownership.
                clone_repository

                # Now that the repository is in place, ask for credentials.
                # ask_user_input will store them in $PROGRAM_DIR/.env
                # The $PROGRAM_DIR is guaranteed to exist by clone_repository.
                # Ensure $USER owns $PROGRAM_DIR for writing .env, clone_repository attempts this.
                # We might need an explicit chown here again if clone_repository's attempt wasn't enough or for clarity.
                sudo chown $USER:$USER $PROGRAM_DIR # Ensure user owns the directory for .env writing

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

                # clone_repository has already been called.
                # The .env file is now safe as it's created after repository setup.

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