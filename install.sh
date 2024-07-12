#!/bin/bash

# Function to ask for user input securely
ask_user_input() {
    local prompt=$1
    local var_name=$2
    read -p "$prompt: " input
    echo "export $var_name=$input" >> ~/.bashrc
    export $var_name=$input
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
    sudo mkdir -p /opt/update_dns
    sudo chown $USER:$USER /opt/update_dns
    git clone https://github.com/username/repository.git /opt/update_dns
}

# Create the Bash script to run Python script
create_bash_script() {
    echo "Creating Bash script..."
    cat << 'EOF' > /opt/update_dns/run.sh
#!/bin/bash
source ~/.bashrc
python3 /opt/update_dns/change_dns.py
EOF
    chmod +x /opt/update_dns/run.sh
}

# Setup Cron Job
setup_cron() {
    echo "Setting up cron job..."
    (crontab -l 2>/dev/null; echo "*/30 * * * * /opt/update_dns/run.sh >> /opt/update_dns/log_file.log 2>&1") | crontab -
}

# Main setup function
main_setup() {
    install_packages

    # Ask for user inputs
    ask_user_input "Enter your Cloudflare API token" "CLOUDFLARE_API_TOKEN"
    ask_user_input "Enter your Cloudflare Zone ID" "CLOUDFLARE_ZONE_ID"

    # Reload ~/.bashrc to load the new environment variables
    source ~/.bashrc

    clone_repository
    create_bash_script
    setup_cron

    echo "Setup complete. Please check the log file at /opt/update_dns/log_file.log for execution logs."
}

main_setup
