#!/bin/bash

PROGRAM_NAME="Cloudflare-Utils"
PROGRAM_DIR="/opt/$PROGRAM_NAME"

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
python3 $PROGRAM_DIR/change_dns.py
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
    (crontab -l 2>/dev/null; echo "*/30 * * * * $PROGRAM_DIR/run.sh >> $PROGRAM_DIR/log_file.log 2>&1") | crontab - || {
        echo -e "\e[1;31mFailed to add cron job for regular execution.\e[0m" >&2
        exit 1
    }
    
    (crontab -l 2>/dev/null; echo "@reboot $PROGRAM_DIR/run.sh >> $PROGRAM_DIR/log_file.log 2>&1") | crontab - || {
        echo -e "\e[1;31mFailed to add cron job for reboot execution.\e[0m" >&2
        exit 1
    }
    
    echo -e "\e[1;32mCron job setup completed.\e[0m"
}

# Remove the program and clean up
remove_program() {
    echo -e "\e[1;34mRemoving program and cleaning up...\e[0m"
    
    # Remove the cron jobs
    crontab -l | grep -v "$PROGRAM_DIR/run.sh" | crontab - || {
        echo -e "\e[1;31mFailed to remove cron jobs.\e[0m" >&2
        exit 1
    }
    
    # Remove the program directory
    sudo rm -rf $PROGRAM_DIR || {
        echo -e "\e[1;31mFailed to remove program directory $PROGRAM_DIR.\e[0m" >&2
        exit 1
    }
    
    echo -e "\e[1;32mProgram removed and cleanup completed.\e[0m"
}

# Main setup function
main_setup() {
    install_packages

    # Ask for user inputs
    ask_user_input "Enter your Cloudflare API token" "CLOUDFLARE_API_TOKEN"
    ask_user_input "Enter your Cloudflare Zone ID" "CLOUDFLARE_ZONE_ID"
    ask_user_input "Enter your Cloudflare Record Name" "CLOUDFLARE_RECORD_NAME"
    ask_user_input "Enter your servers IP Addresses (comma separated)" "CLOUDFLARE_IP_ADDRESSES"

    # Reload ~/.bashrc to load the new environment variables
    source ~/.bashrc

    clone_repository
    create_bash_script
    setup_cron

    echo -e "\e[1;32mSetup complete.\e[0m Please check the log file at $PROGRAM_DIR/log_file.log for execution logs."
    
    echo -e "\e[1;34mRunning the program...\e[0m"
    bash $PROGRAM_DIR/run.sh
    echo -e "\e[1;32mCompletion.\e[0m"
}

# Display menu options
show_menu() {
    echo -e "\e[1;34mSelect an option:\e[0m"
    echo "1) Install and setup"
    echo "2) Remove program and cleanup"
    echo "3) Exit"
    read -p "Enter your choice [1-3]: " choice
    
    case $choice in
        1)
            main_setup
            ;;
        2)
            remove_program
            ;;
        3)
            echo -e "\e[1;34mExiting...\e[0m"
            exit 0
            ;;
        *)
            echo -e "\e[1;31mInvalid choice, please try again.\e[0m"
            show_menu
            ;;
    esac
}

show_menu
