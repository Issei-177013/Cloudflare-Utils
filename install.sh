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

# Function to ask for user input and write to .env file
ask_user_input_to_env() {
    local prompt="$1"
    local var_name="$2"
    local env_file_path="$3"
    local input_value=""
    
    read -p "$(echo -e "\e[1;32m$prompt: \e[0m")" input_value
    
    # Remove existing variable definition if any, then append
    # Use a temporary file for sed in-place editing robustness
    tmp_env_file="${env_file_path}.tmp"
    grep -v "^${var_name}=" "$env_file_path" > "$tmp_env_file" 2>/dev/null || true # Allow file not existing initially
    echo "${var_name}=\"${input_value}\"" >> "$tmp_env_file"
    mv "$tmp_env_file" "$env_file_path"
    
    # Export for current session if needed by subsequent script steps (though python script will read from .env)
    export "$var_name"="$input_value"
}

# Install necessary packages
install_packages() {
    echo -e "\e[1;34mInstalling necessary packages...\e[0m"
    if ! sudo apt-get update; then
        echo -e "\e[1;31mFailed to update apt repositories.\e[0m" >&2
        exit 1
    fi
    
    # Install python3-venv for creating virtual environments
    if ! sudo apt-get install -y git python3-pip python3-venv; then
        echo -e "\e[1;31mFailed to install required packages.\e[0m" >&2
        exit 1
    fi
    
    echo -e "\e[1;32mSystem packages installed successfully.\e[0m"
}

# Clone GitHub repository and setup virtual environment
clone_repository_and_setup_venv() {
    echo -e "\e[1;34mCloning GitHub repository and setting up virtual environment...\e[0m"
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

    echo -e "\e[1;34mCreating Python virtual environment...\e[0m"
    python3 -m venv $PROGRAM_DIR/.venv || {
        echo -e "\e[1;31mFailed to create virtual environment.\e[0m" >&2
        exit 1
    }

    echo -e "\e[1;34mInstalling Python dependencies into virtual environment...\e[0m"
    # Activate venv and install packages
    source $PROGRAM_DIR/.venv/bin/activate || {
        echo -e "\e[1;31mFailed to activate virtual environment.\e[0m" >&2
        exit 1
    }
    
    # Install the package itself from the cloned repo
    echo -e "\e[1;34mInstalling Cloudflare-Utils package from $PROGRAM_DIR...\e[0m"
    # Store current directory
    ORIGINAL_DIR=$(pwd)
    cd "$PROGRAM_DIR" || { 
        echo -e "\e[1;31mFailed to change directory to $PROGRAM_DIR.\e[0m"; 
        deactivate; 
        exit 1; 
    }
    
    if ! pip3 install .; then
        echo -e "\e[1;31mFailed to install Cloudflare-Utils package using 'pip3 install .'.\e[0m" >&2
        # cd back to original directory before exiting
        cd "$ORIGINAL_DIR"
        deactivate
        exit 1
    fi
    
    # cd back to original directory
    cd "$ORIGINAL_DIR"
    
    # Dependencies like cloudflare and python-dotenv are now specified in pyproject.toml
    # and should be installed automatically when the package is installed.
    # No longer need: pip3 install cloudflare python-dotenv

    # Deactivate venv after installation
    deactivate
    echo -e "\e[1;32mCloudflare-Utils package and its dependencies installed successfully in virtual environment.\e[0m"
}

# Create the Bash script to run Python script
create_bash_script() {
    echo -e "\e[1;34mCreating Bash script...\e[0m"
    cat << EOF > $PROGRAM_DIR/run.sh
#!/bin/bash
# Copyright $(date +%Y) Issei-177013
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
PROGRAM_DIR="/opt/\$PROGRAM_NAME" # Escaped $PROGRAM_NAME to be literal in heredoc
ENV_FILE="\$PROGRAM_DIR/.env"

# Activate virtual environment
source "\$PROGRAM_DIR/.venv/bin/activate"

# The python script change_dns.py will load variables from .env using python-dotenv
# So, explicit sourcing of .env in run.sh is not strictly necessary for the python script itself,
# but can be useful if other bash commands in this script needed them.
# For now, we'll rely on python-dotenv.

{
    echo "\$(date) - Starting script execution via cloudflare-utils command"
    # Execute the installed CLI command
    # Arguments for the CLI can be passed here if needed, or rely on .env file
    cloudflare-utils
    echo "\$(date) - Finished script execution via cloudflare-utils command"
} >> "\$PROGRAM_DIR/log_file.log" 2>&1

# Deactivate virtual environment
deactivate
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

# Setup Systemd Timer
setup_systemd() {
    echo -e "\e[1;34mSetting up systemd timer...\e[0m"

    # Create temporary copies of unit files to be moved with sudo
    # This assumes cloudflare-utils.service and cloudflare-utils.timer are in the same directory as install.sh
    # If they are part of the git repo, their path needs to be $PROGRAM_DIR/cloudflare-utils.service etc.
    # For now, assuming they are created by the agent in the current directory where install.sh is run from.
    
    # Correctly reference unit files from within the cloned repository ($PROGRAM_DIR)
    SERVICE_FILE_SRC="$PROGRAM_DIR/cloudflare-utils.service"
    TIMER_FILE_SRC="$PROGRAM_DIR/cloudflare-utils.timer"
    
    # Check if source unit files exist (they should be cloned as part of the repo)
    if [ ! -f "$SERVICE_FILE_SRC" ] || [ ! -f "$TIMER_FILE_SRC" ]; then
        echo -e "\e[1;31mError: Systemd unit files not found in $PROGRAM_DIR.\e[0m"
        echo -e "\e[1;31mMake sure cloudflare-utils.service and cloudflare-utils.timer are part of the repository.\e[0m"
        return 1 # Indicate failure
    fi

    # Copy unit files to systemd directory
    sudo cp "$SERVICE_FILE_SRC" /etc/systemd/system/cloudflare-utils.service
    sudo cp "$TIMER_FILE_SRC" /etc/systemd/system/cloudflare-utils.timer

    # Set correct permissions for unit files
    sudo chmod 644 /etc/systemd/system/cloudflare-utils.service
    sudo chmod 644 /etc/systemd/system/cloudflare-utils.timer

    # Reload systemd daemon, enable and start the timer
    echo -e "\e[1;34mReloading systemd daemon and enabling timer...\e[0m"
    sudo systemctl daemon-reload || { echo -e "\e[1;31mFailed to reload systemd daemon.\e[0m"; return 1; }
    sudo systemctl enable cloudflare-utils.timer || { echo -e "\e[1;31mFailed to enable systemd timer.\e[0m"; return 1; }
    sudo systemctl start cloudflare-utils.timer || { echo -e "\e[1;31mFailed to start systemd timer.\e[0m"; return 1; }

    echo -e "\e[1;32mSystemd timer setup completed.\e[0m"
    echo -e "\e[1;34mActive systemd timers for Cloudflare-Utils:\e[0m"
    systemctl list-timers | grep cloudflare-utils.timer || echo -e "\e[1;33mNo active systemd timer found for Cloudflare-Utils.\e[0m"
    return 0 # Indicate success
}


# Function to remove the program and cron jobs/systemd units
remove_program() {
    echo -e "\e[1;34mRemoving the program...\e[0m"
    
    # Remove systemd units if they exist
    if [ -f "/etc/systemd/system/cloudflare-utils.timer" ]; then
        echo -e "\e[1;34mStopping and disabling systemd timer...\e[0m"
        sudo systemctl stop cloudflare-utils.timer
        sudo systemctl disable cloudflare-utils.timer
        sudo rm -f /etc/systemd/system/cloudflare-utils.timer
        sudo rm -f /etc/systemd/system/cloudflare-utils.service
        sudo systemctl daemon-reload
        echo -e "\e[1;32mSystemd units removed.\e[0m"
    fi

    # Remove cron jobs
    if crontab -l 2>/dev/null | grep -q "$PROGRAM_DIR/run.sh"; then
        echo -e "\e[1;34mRemoving cron jobs...\e[0m"
        crontab -l | grep -v "$PROGRAM_DIR/run.sh" | crontab -
        echo -e "\e[1;32mCron jobs removed.\e[0m"
    fi
    
    # Remove program directory
    sudo rm -rf $PROGRAM_DIR
    
    echo -e "\e[1;32mProgram removed successfully.\e[0m"
}

# Display menu
display_menu() {
    echo -e "\e[1;33m1. Install Cloudflare-Utils\e[0m"
    echo -e "\e[1;33m2. Remove Cloudflare-Utils\e[0m"
    echo -e "\e[1;33m3. Exit\e[0m"
}

# Function to write key-value pair to .env file
write_to_env_file() {
    local key="$1"
    local value="$2"
    local env_file_path="$3"
    
    # Remove existing variable definition if any, then append
    tmp_env_file="${env_file_path}.tmp"
    grep -v "^${key}=" "$env_file_path" > "$tmp_env_file" 2>/dev/null || true
    echo "${key}=\"${value}\"" >> "$tmp_env_file"
    mv "$tmp_env_file" "$env_file_path"
}

# Main setup function
main_setup() {
    # Non-interactive mode variables
    NON_INTERACTIVE=false
    CF_API_TOKEN=""
    CF_ZONE_ID=""
    CF_RECORD_NAME=""
    CF_IP_ADDRESSES=""
    ACTION="menu" # Default action

    # Parse command line arguments
    while [[ "$#" -gt 0 ]]; do
        case $1 in
            --api-token) CF_API_TOKEN="$2"; shift ;;
            --zone-id) CF_ZONE_ID="$2"; shift ;;
            --record-name) CF_RECORD_NAME="$2"; shift ;;
            --ip-addresses) CF_IP_ADDRESSES="$2"; shift ;;
            --action) ACTION="$2"; shift ;; # New: allow specifying install/remove directly
            --non-interactive) NON_INTERACTIVE=true ;;
            *) echo "Unknown parameter passed: $1"; exit 1 ;;
        esac
        shift
    done

    if [ "$NON_INTERACTIVE" = true ]; then
        if [ "$ACTION" = "install" ]; then
            # Check if already installed in non-interactive mode
            if [ -d "$PROGRAM_DIR" ]; then
                echo -e "\e[1;33mWarning: Cloudflare-Utils appears to be already installed at $PROGRAM_DIR.\e[0m"
                echo -e "\e[1;33mNon-interactive mode will proceed with reinstallation/update using provided parameters.\e[0m"
                # Optionally, could add a --force flag or similar to control this behavior
            fi

            if [ -z "$CF_API_TOKEN" ] || [ -z "$CF_ZONE_ID" ] || [ -z "$CF_RECORD_NAME" ] || [ -z "$CF_IP_ADDRESSES" ]; then
                echo -e "\e[1;31mError: For non-interactive installation, all parameters (--api-token, --zone-id, --record-name, --ip-addresses) must be provided.\e[0m"
                exit 1
            fi
            
            install_packages
            
            ENV_FILE_PATH="$PROGRAM_DIR/.env"
            sudo mkdir -p $PROGRAM_DIR
            sudo chown $USER:$USER $PROGRAM_DIR
            touch $ENV_FILE_PATH
            chown $USER:$USER $ENV_FILE_PATH

            write_to_env_file "CLOUDFLARE_API_TOKEN" "$CF_API_TOKEN" "$ENV_FILE_PATH"
            write_to_env_file "CLOUDFLARE_ZONE_ID" "$CF_ZONE_ID" "$ENV_FILE_PATH"
            write_to_env_file "CLOUDFLARE_RECORD_NAME" "$CF_RECORD_NAME" "$ENV_FILE_PATH"
            write_to_env_file "CLOUDFLARE_IP_ADDRESSES" "$CF_IP_ADDRESSES" "$ENV_FILE_PATH"
            
            echo -e "\e[1;32mConfiguration saved to $ENV_FILE_PATH via non-interactive mode.\e[0m"

            clone_repository_and_setup_venv # This clones the repo including systemd files if they are added
            create_bash_script
            
            # Non-interactive mode defaults to cron unless specified otherwise (e.g. via a new --scheduler arg)
            # For now, keeping it simple and defaulting to cron for non-interactive.
            # A future improvement could be adding --scheduler systemd|cron to non-interactive mode.
            echo -e "\e[1;34mSetting up scheduler (defaulting to cron for non-interactive)...\e[0m"
            setup_cron 
            echo -e "\e[1;32mNon-interactive setup complete with cron scheduler.\e[0m Please check the log file at $PROGRAM_DIR/log_file.log."
            echo -e "\e[1;34mActive cron jobs for Cloudflare-Utils:\e[0m"
            (crontab -l 2>/dev/null | grep "$PROGRAM_DIR/run.sh") || echo -e "\e[1;33mNo active cron jobs found for Cloudflare-Utils.\e[0m"

        elif [ "$ACTION" = "remove" ]; then
            remove_program # remove_program now handles both cron and systemd
        else
            echo -e "\e[1;31mError: Invalid action '$ACTION' for non-interactive mode. Use 'install' or 'remove'.\e[0m"
            exit 1
        fi
    else
        # Interactive mode (original menu)
        # display_ascii_art # Uncomment if you want ASCII art in interactive mode
        PS3='Please enter your choice: '
        options=("Install Cloudflare-Utils" "Remove Cloudflare-Utils" "Exit")
        select opt in "${options[@]}"
        do
            case $opt in
                "Install Cloudflare-Utils")
                    # Check if already installed in interactive mode
                    if [ -d "$PROGRAM_DIR" ]; then
                        echo -e "\e[1;33mWarning: Cloudflare-Utils appears to be already installed at $PROGRAM_DIR.\e[0m"
                        read -p "Do you want to proceed with reinstallation? This will overwrite existing configurations if new values are provided. (y/N): " choice
                        case "$choice" in 
                          y|Y ) echo "Proceeding with reinstallation...";;
                          * ) echo "Reinstallation aborted."; exit 0;;
                        esac
                    fi

                    install_packages
                    
                    ENV_FILE_PATH="$PROGRAM_DIR/.env"
                    sudo mkdir -p $PROGRAM_DIR
                    sudo chown $USER:$USER $PROGRAM_DIR
                    touch $ENV_FILE_PATH
                    chown $USER:$USER $ENV_FILE_PATH

                    if [ -f "$ENV_FILE_PATH" ]; then
                        export $(grep -v '^#' "$ENV_FILE_PATH" | xargs)
                    fi

                    if [ -z "$CLOUDFLARE_API_TOKEN" ]; then
                        ask_user_input_to_env "Enter your Cloudflare API Token" "CLOUDFLARE_API_TOKEN" "$ENV_FILE_PATH"
                    fi

                    if [ -z "$CLOUDFLARE_ZONE_ID" ]; then
                        ask_user_input_to_env "Enter your Cloudflare Zone ID" "CLOUDFLARE_ZONE_ID" "$ENV_FILE_PATH"
                    fi

                    if [ -z "$CLOUDFLARE_RECORD_NAME" ]; then
                        ask_user_input_to_env "Enter your Cloudflare Record Name(s) (comma-separated)" "CLOUDFLARE_RECORD_NAME" "$ENV_FILE_PATH"
                    fi

                    if [ -z "$CLOUDFLARE_IP_ADDRESSES" ]; then
                        ask_user_input_to_env "Enter your Cloudflare IP Addresses (comma-separated)" "CLOUDFLARE_IP_ADDRESSES" "$ENV_FILE_PATH"
                    fi
                    
                    echo -e "\e[1;32mConfiguration saved to $ENV_FILE_PATH.\e[0m"

                    clone_repository_and_setup_venv # This clones the repo including systemd files
                    create_bash_script

                    # Ask user for scheduler preference
                    echo -e "\e[1;33mChoose a scheduler for periodic execution:\e[0m"
                    echo "1. Cron (traditional, simple)"
                    echo "2. Systemd Timer (more robust, better logging integration with systemd)"
                    read -p "Enter your choice (1 or 2, default 1): " scheduler_choice

                    if [ "$scheduler_choice" = "2" ]; then
                        if setup_systemd; then
                            echo -e "\e[1;32mSystemd setup chosen and completed.\e[0m"
                        else
                            echo -e "\e[1;31mSystemd setup failed. Falling back to Cron.\e[0m"
                            setup_cron
                            echo -e "\e[1;34mActive cron jobs for Cloudflare-Utils:\e[0m"
                            (crontab -l 2>/dev/null | grep "$PROGRAM_DIR/run.sh") || echo -e "\e[1;33mNo active cron jobs found for Cloudflare-Utils.\e[0m"
                        fi
                    else
                        echo -e "\e[1;34mCron setup chosen.\e[0m"
                        setup_cron
                        echo -e "\e[1;34mActive cron jobs for Cloudflare-Utils:\e[0m"
                        (crontab -l 2>/dev/null | grep "$PROGRAM_DIR/run.sh") || echo -e "\e[1;33mNo active cron jobs found for Cloudflare-Utils.\e[0m"
                    fi

                    echo -e "\e[1;32mSetup complete.\e[0m Please check the log file at $PROGRAM_DIR/log_file.log for execution logs."
                    break
                    ;;
                "Remove Cloudflare-Utils") # remove_program now handles both
                    remove_program
                    break
                    ;;
                "Exit")
                    break
                    ;;
                *) echo -e "\e[1;31mInvalid option $REPLY\e[0m";;
            esac
        done
    fi
}

main_setup "$@"
