#!/bin/bash
PROGRAM_NAME="Cloudflare-Utils"
PROGRAM_DIR="/opt/$PROGRAM_NAME"

# Function to ask for user input securely
ask_user_input() {
    local prompt=$1
    local var_name=$2
    read -p "$prompt: " input
    echo "export $var_name=\"$input\"" >> ~/.bashrc
    export $var_name="$input"
}

# Install necessary packages
install_packages() {
    echo "Installing necessary packages..."
    sudo apt-get update
    sudo apt-get install -y git python3-pip
    pip3 install cloudflare
}

# Clone GitHub repository
clone_repository() {
    echo "Cloning GitHub repository..."
    sudo mkdir -p $PROGRAM_DIR
    sudo chown $USER:$USER $PROGRAM_DIR
    git clone https://github.com/Issei-177013/Cloudflare-Utils.git $PROGRAM_DIR
}

# Create the Bash script to run Python script
create_bash_script() {
    echo "Creating Bash script..."
    cat << 'EOF' > $PROGRAM_DIR/run.sh
#!/bin/bash
PROGRAM_NAME="Cloudflare-Utils"
PROGRAM_DIR="/opt/$PROGRAM_NAME"
source ~/.bashrc
python3 $PROGRAM_DIR/change_dns.py
EOF
    chmod +x $PROGRAM_DIR/run.sh
}

# Setup Cron Job
setup_cron() {
    echo "Setting up cron job..."
    (crontab -l 2>/dev/null; echo "*/30 * * * * $PROGRAM_DIR/run.sh >> $PROGRAM_DIR/log_file.log 2>&1") | crontab -
    (crontab -l 2>/dev/null; echo "@reboot $PROGRAM_DIR/run.sh >> $PROGRAM_DIR/log_file.log 2>&1") | crontab -
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
    python3 $PROGRAM_DIR/change_dns.py

    echo "Setup complete. Please check the log file at $PROGRAM_DIR/log_file.log for execution logs."
}

main_setup
