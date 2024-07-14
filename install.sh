#!/bin/bash

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

source ~/.bashrc

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

                # Check if the variables are already set in ~/.bashrc
                source ~/.bashrc

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

                # Source the ~/.bashrc to ensure variables are available in the current session
                source ~/.bashrc

                echo -e "\e[1;32mAll necessary variables have been set.\e[0m"

                # Reload ~/.bashrc to load the new environment variables
                source ~/.bashrc

                clone_repository
                create_bash_script
                setup_cron

                echo -e "\e[1;32mSetup complete.\e[0m Please check the log file at $PROGRAM_DIR/log_file.log for execution logs."
                
                echo -e "\e[1;34mRunning the program...\e[0m"
                bash $PROGRAM_DIR/run.sh
                echo -e "\e[1;32mCompletion.\e[0m"
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
