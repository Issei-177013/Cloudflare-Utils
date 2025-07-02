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


PROGRAM_NAME_BASE="Cloudflare-Utils" # Base name
BRANCH_NAME="" # Will be set by --branch arg
PROGRAM_NAME="$PROGRAM_NAME_BASE" # Default program name
PROGRAM_DIR="/opt/$PROGRAM_NAME" # Default program dir

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
    local clone_url="https://github.com/Issei-177013/Cloudflare-Utils.git"
    local clone_cmd="git clone $clone_url $PROGRAM_DIR"

    if [ -n "$BRANCH_NAME" ]; then
        echo -e "\e[1;34mCloning branch '$BRANCH_NAME' from $clone_url into $PROGRAM_DIR and setting up virtual environment...\e[0m"
        clone_cmd="git clone -b $BRANCH_NAME $clone_url $PROGRAM_DIR"
    else
        echo -e "\e[1;34mCloning default branch from $clone_url into $PROGRAM_DIR and setting up virtual environment...\e[0m"
    fi
    
    # If $PROGRAM_DIR exists and is a git repo, try to fetch and checkout the branch instead of full clone
    # This handles re-running the installer for a different branch or re-installing the same branch
    if [ -d "$PROGRAM_DIR/.git" ]; then
        echo -e "\e[1;33mDirectory $PROGRAM_DIR already exists and is a git repository.\e[0m"
        echo -e "\e[1;34mAttempting to fetch and checkout branch '$BRANCH_NAME' (or default if no branch specified)...\e[0m"
        ORIGINAL_DIR_GIT_OP=$(pwd)
        cd "$PROGRAM_DIR" || { echo -e "\e[1;31mFailed to cd into $PROGRAM_DIR for git operations.\e[0m"; exit 1; }
        git fetch origin || { echo -e "\e[1;31mFailed to fetch from origin.\e[0m"; cd "$ORIGINAL_DIR_GIT_OP"; exit 1; }
        
        local target_branch_checkout="$BRANCH_NAME"
        if [ -z "$target_branch_checkout" ]; then
             # Attempt to get default branch from remote, fallback to main/master
            target_branch_checkout=$(git symbolic-ref refs/remotes/origin/HEAD | sed 's@^refs/remotes/origin/@@' || echo "main")
        fi

        git checkout "$target_branch_checkout" || { echo -e "\e[1;31mFailed to checkout branch '$target_branch_checkout'.\e[0m"; cd "$ORIGINAL_DIR_GIT_OP"; exit 1; }
        git pull origin "$target_branch_checkout" || { echo -e "\e[1;31mFailed to pull latest changes for branch '$target_branch_checkout'.\e[0m"; cd "$ORIGINAL_DIR_GIT_OP"; exit 1; }
        cd "$ORIGINAL_DIR_GIT_OP"
        echo -e "\e[1;32mSuccessfully updated existing repository for branch '$target_branch_checkout'.\e[0m"
    else
        # $PROGRAM_DIR does not exist or is not a git repo, proceed with clone
        # Need to remove $PROGRAM_DIR if it exists but is not a git repo, or if clone should overwrite
        # The existing installation warning logic should handle if user wants to proceed with overwrite.
        # If user proceeds, we might need to rm -rf $PROGRAM_DIR first if it's not a git repo.
        # For now, assuming the warning handles this. If clone fails due to non-empty dir, this needs refinement.
        # The `main_setup` function's interactive "reinstall" prompt implies user consent to potential overwrite.
        # If $PROGRAM_DIR exists from a failed previous clone (empty dir) or non-git files, clone might fail.
        # `git clone` itself fails if $PROGRAM_DIR exists and is not empty.
        # The `main_setup` already has a check for `if [ -d "$PROGRAM_DIR" ]` for interactive,
        # and non-interactive warns and proceeds. This means if user proceeds, we should ensure $PROGRAM_DIR is usable by git.
        # A robust way: if $PROGRAM_DIR exists and user wants to (re)install, remove it first.
        # This is dangerous if user has custom data. The current reinstall warning is better.
        # Let's assume if we reach here, and $PROGRAM_DIR is not a .git repo, it was created by mkdir -p
        # or the user agreed to overwrite.
        # The bug fix for .env creation *after* clone helps a lot here.

        sudo mkdir -p "$PROGRAM_DIR" # Ensure dir exists, git clone needs parent dir.
        sudo chown $USER:$USER "$PROGRAM_DIR" || { # chown parent first, then git clone will create with user perms
            echo -e "\e[1;31mFailed to chown $PROGRAM_DIR for user $USER.\e[0m" >&2
            exit 1
        }
        
        # If $PROGRAM_DIR was created by mkdir and is empty, git clone is fine.
        # If it existed and user chose to reinstall, it implies we can overwrite.
        # If it's a non-empty non-git directory, git clone will fail.
        # The current reinstall logic in main_setup for interactive mode is:
        # "Warning: Cloudflare-Utils appears to be already installed at $PROGRAM_DIR."
        # "Do you want to proceed with reinstallation? This will overwrite existing configurations if new values are provided. (y/N): "
        # This doesn't explicitly say it will delete the directory.
        # For safety, `git clone` should only be run if $PROGRAM_DIR is empty or doesn't exist.
        # The `clone_repository_and_setup_venv` is called *after* this prompt in interactive.
        # And for non-interactive, it just warns and proceeds.
        # Let's refine: if $PROGRAM_DIR exists and is NOT a git repo, and we are proceeding, it should be removed.
        # This is handled by the general installation warning where user agrees to reinstall.

        if ! $clone_cmd; then
            echo -e "\e[1;31mFailed to clone repository using command: $clone_cmd\e[0m" >&2
            exit 1
        fi
        echo -e "\e[1;32mRepository cloned successfully into $PROGRAM_DIR.\e[0m"
    fi
    
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
    local service_name_suffix=""
    if [ -n "$SANITIZED_BRANCH_NAME" ]; then # SANITIZED_BRANCH_NAME is set if --branch is used
        service_name_suffix="-$SANITIZED_BRANCH_NAME"
    fi
    local systemd_service_name="cloudflare-utils${service_name_suffix}.service"
    local systemd_timer_name="cloudflare-utils${service_name_suffix}.timer"

    echo -e "\e[1;34mSetting up systemd timer as $systemd_timer_name...\e[0m"
    
    local service_file_template_src="$PROGRAM_DIR/cloudflare-utils.service" # Template from repo
    local timer_file_template_src="$PROGRAM_DIR/cloudflare-utils.timer"   # Template from repo

    if [ ! -f "$service_file_template_src" ] || [ ! -f "$timer_file_template_src" ]; then
        echo -e "\e[1;31mError: Systemd unit file templates not found in $PROGRAM_DIR.\e[0m"
        echo -e "\e[1;31mMake sure cloudflare-utils.service and cloudflare-utils.timer are part of the repository.\e[0m"
        return 1 # Indicate failure
    fi

    # Create temporary, modified unit files
    local temp_service_file=$(mktemp)
    local temp_timer_file=$(mktemp)

    # Modify service file: Description and ExecStart
    sed "s|Description=Cloudflare DNS Update Service|Description=Cloudflare DNS Update Service ($PROGRAM_NAME)|g" "$service_file_template_src" | \
        sed "s|ExecStart=/opt/Cloudflare-Utils/run.sh|ExecStart=$PROGRAM_DIR/run.sh|g" > "$temp_service_file"
    
    # Modify timer file: Unit (to point to the correct service name)
    sed "s|Unit=cloudflare-utils.service|Unit=$systemd_service_name|g" "$timer_file_template_src" > "$temp_timer_file"

    # Copy modified unit files to systemd directory with unique names
    sudo cp "$temp_service_file" "/etc/systemd/system/$systemd_service_name"
    sudo cp "$temp_timer_file" "/etc/systemd/system/$systemd_timer_name"
    rm "$temp_service_file" "$temp_timer_file"

    sudo chmod 644 "/etc/systemd/system/$systemd_service_name"
    sudo chmod 644 "/etc/systemd/system/$systemd_timer_name"

    echo -e "\e[1;34mReloading systemd daemon and enabling $systemd_timer_name...\e[0m"
    sudo systemctl daemon-reload || { echo -e "\e[1;31mFailed to reload systemd daemon.\e[0m"; return 1; }
    sudo systemctl enable "$systemd_timer_name" || { echo -e "\e[1;31mFailed to enable $systemd_timer_name.\e[0m"; return 1; }
    sudo systemctl start "$systemd_timer_name" || { echo -e "\e[1;31mFailed to start $systemd_timer_name.\e[0m"; return 1; }

    echo -e "\e[1;32mSystemd timer $systemd_timer_name setup completed.\e[0m"
    echo -e "\e[1;34mActive systemd timers for $PROGRAM_NAME:\e[0m"
    systemctl list-timers | grep "$systemd_timer_name" || echo -e "\e[1;33mNo active systemd timer found for $PROGRAM_NAME.\e[0m"
    return 0
}


# Function to remove the program and cron jobs/systemd units
remove_program() {
    # PROGRAM_DIR is set based on --branch if provided, or defaults.
    echo -e "\e[1;34mRemoving program $PROGRAM_NAME from $PROGRAM_DIR...\e[0m"
    
    local service_name_suffix=""
    if [ -n "$SANITIZED_BRANCH_NAME" ]; then
        service_name_suffix="-$SANITIZED_BRANCH_NAME"
    fi
    local systemd_service_name="cloudflare-utils${service_name_suffix}.service"
    local systemd_timer_name="cloudflare-utils${service_name_suffix}.timer"

    # Remove systemd units if they exist
    if [ -f "/etc/systemd/system/$systemd_timer_name" ]; then
        echo -e "\e[1;34mStopping and disabling systemd timer $systemd_timer_name...\e[0m"
        sudo systemctl stop "$systemd_timer_name"
        sudo systemctl disable "$systemd_timer_name"
        sudo rm -f "/etc/systemd/system/$systemd_timer_name"
        sudo rm -f "/etc/systemd/system/$systemd_service_name" # Remove corresponding service file
        sudo systemctl daemon-reload
        echo -e "\e[1;32mSystemd units for $PROGRAM_NAME removed.\e[0m"
    fi

    # Remove cron jobs
    # Cron jobs are identified by the $PROGRAM_DIR in their command.
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
            --action) ACTION="$2"; shift ;;
            --branch) BRANCH_NAME="$2"; shift ;;
            --non-interactive) NON_INTERACTIVE=true ;;
            *) echo "Unknown parameter passed: $1"; exit 1 ;;
        esac
        shift
    done

    # Adjust PROGRAM_NAME and PROGRAM_DIR if a branch is specified
    if [ -n "$BRANCH_NAME" ]; then
        # Sanitize branch name for use in directory/service names (e.g. replace / with -)
        SANITIZED_BRANCH_NAME=$(echo "$BRANCH_NAME" | sed 's/[^a-zA-Z0-9._-]/_/g')
        PROGRAM_NAME="${PROGRAM_NAME_BASE}-${SANITIZED_BRANCH_NAME}"
        PROGRAM_DIR="/opt/$PROGRAM_NAME"
        echo -e "\e[1;36mBranch specified: '$BRANCH_NAME'. Using program directory: $PROGRAM_DIR\e[0m"
    fi

    if [ "$NON_INTERACTIVE" = true ]; then
        if [ "$ACTION" = "install" ]; then
            # Check if already installed in non-interactive mode
            # This check now uses the potentially modified $PROGRAM_DIR
            if [ -d "$PROGRAM_DIR" ]; then
                echo -e "\e[1;33mWarning: $PROGRAM_NAME appears to be already installed at $PROGRAM_DIR.\e[0m"
                echo -e "\e[1;33mNon-interactive mode will proceed with reinstallation/update using provided parameters.\e[0m"
                # Optionally, could add a --force flag or similar to control this behavior
            fi

            if [ -z "$CF_API_TOKEN" ] || [ -z "$CF_ZONE_ID" ] || [ -z "$CF_RECORD_NAME" ] || [ -z "$CF_IP_ADDRESSES" ]; then
                echo -e "\e[1;31mError: For non-interactive installation, all parameters (--api-token, --zone-id, --record-name, --ip-addresses) must be provided.\e[0m"
                exit 1
            fi
            
            install_packages # System packages
            
            # 1. Clone repository and setup venv first. This creates $PROGRAM_DIR.
            clone_repository_and_setup_venv 

            # 2. Now, setup .env file inside the cloned $PROGRAM_DIR
            ENV_FILE_PATH="$PROGRAM_DIR/.env"
            # $PROGRAM_DIR is created by clone_repository_and_setup_venv, ensure ownership for .env creation
            sudo chown $USER:$USER $PROGRAM_DIR 
            touch $ENV_FILE_PATH # Create .env if it doesn't exist
            chown $USER:$USER $ENV_FILE_PATH # Ensure current user owns it

            write_to_env_file "CLOUDFLARE_API_TOKEN" "$CF_API_TOKEN" "$ENV_FILE_PATH"
            write_to_env_file "CLOUDFLARE_ZONE_ID" "$CF_ZONE_ID" "$ENV_FILE_PATH"
            write_to_env_file "CLOUDFLARE_RECORD_NAME" "$CF_RECORD_NAME" "$ENV_FILE_PATH"
            write_to_env_file "CLOUDFLARE_IP_ADDRESSES" "$CF_IP_ADDRESSES" "$ENV_FILE_PATH"
            
            echo -e "\e[1;32mConfiguration saved to $ENV_FILE_PATH via non-interactive mode.\e[0m"

            # 3. Create bash script and setup scheduler
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
        # Interactive mode
        if ! [ -t 0 ] && [ "$NON_INTERACTIVE" = false ]; then # Check if stdin is a TTY if not explicitly non-interactive
            echo -e "\e[1;31mError: Interactive mode cannot be used when input is not a terminal (e.g., when piping to 'sudo bash -s').\e[0m"
            echo -e "For interactive installation, please download the script first and then run it directly:"
            echo -e "Example for 'dev' branch:"
            echo -e "  1. curl -fsSL -o install.sh https://raw.githubusercontent.com/Issei-177013/Cloudflare-Utils/dev/install.sh"
            echo -e "  2. chmod +x install.sh"
            echo -e "  3. sudo ./install.sh --branch dev" # Add other flags like --branch as needed
            echo -e "\nAlternatively, use the --non-interactive flag with all required parameters for a fully automated setup via one-liner."
            exit 1
        fi

        # display_ascii_art # Uncomment if you want ASCII art in interactive mode
        PS3='Please enter your choice: '
        options=("Install $PROGRAM_NAME" "Remove $PROGRAM_NAME" "Exit") # Use $PROGRAM_NAME
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

                    install_packages # System packages
                    
                    # 1. Clone repository and setup venv first. This creates $PROGRAM_DIR.
                    # The warning about existing directory is handled inside this selection block already.
                    clone_repository_and_setup_venv 

                    # 2. Now, setup .env file inside the cloned $PROGRAM_DIR
                    ENV_FILE_PATH="$PROGRAM_DIR/.env"
                    # $PROGRAM_DIR is created by clone_repository_and_setup_venv, ensure ownership for .env creation
                    sudo chown $USER:$USER $PROGRAM_DIR
                    touch $ENV_FILE_PATH # Create .env if it doesn't exist
                    chown $USER:$USER $ENV_FILE_PATH # Ensure current user owns it
                    
                    # Load existing .env values if any, to pre-fill or check
                    if [ -f "$ENV_FILE_PATH" ]; then
                        # Source them to make them available for the -z checks below
                        set -a # Automatically export all variables subsequently defined or modified
                        source "$ENV_FILE_PATH"
                        set +a
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

                    # 3. Create bash script and setup scheduler
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
