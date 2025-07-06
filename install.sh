#!/bin/bash
PROGRAM_NAME="Cloudflare-Utils"
DEFAULT_BRANCH="main"
BRANCH="${1:-$DEFAULT_BRANCH}"
PROGRAM_DIR="/opt/$PROGRAM_NAME"
VERSION_TAG=""

# Function to display ASCII art
display_ascii_art() {
    curl -sSL https://raw.githubusercontent.com/Issei-177013/Cloudflare-Utils/$BRANCH/asset/Issei.txt
}

# Secure user input
ask_user_input() {
    local prompt=$1
    local var_name=$2
    read -p "$(echo -e "\e[1;32m$prompt: \e[0m")" input
    mkdir -p "$PROGRAM_DIR"
    echo "$var_name=$input" >> "$PROGRAM_DIR/.env"
    export $var_name="$input"
}

# Install required packages
install_packages() {
    echo -e "\e[1;34mInstalling required packages...\e[0m"
    sudo apt-get update
    sudo apt-get install -y git python3-pip python3-dotenv || true
    pip3 install cloudflare python-dotenv
}

# Clone or pull repo from the selected branch
clone_repository() {
    echo -e "\e[1;34mCloning $PROGRAM_NAME from branch '$BRANCH'...\e[0m"
    if [ -d "$PROGRAM_DIR/.git" ]; then
        cd "$PROGRAM_DIR" || exit 1
        git fetch origin
        git checkout "$BRANCH"
        git pull origin "$BRANCH"
    else
        git clone --branch "$BRANCH" https://github.com/Issei-177013/Cloudflare-Utils.git "$PROGRAM_DIR"
    fi

    # Get current commit hash or tag (version)
    cd "$PROGRAM_DIR" || exit 1
    VERSION_TAG=$(git describe --tags --abbrev=0 2>/dev/null || git rev-parse --short HEAD)
    cd - > /dev/null
}

# Create run.sh
create_bash_script() {
    cat << 'EOF' > "$PROGRAM_DIR/run.sh"
#!/bin/bash
PROGRAM_NAME="Cloudflare-Utils"
PROGRAM_DIR="/opt/$PROGRAM_NAME"

if [ -f "$PROGRAM_DIR/.env" ]; then
    export $(grep -v '^#' "$PROGRAM_DIR/.env" | xargs)
else
    echo "$(date) - Error: .env not found" >> "$PROGRAM_DIR/log_file.log"
    exit 1
fi

{
    echo "$(date) - Starting script"
    python3 "$PROGRAM_DIR/change_dns.py"
    echo "$(date) - Finished script"
} >> "$PROGRAM_DIR/log_file.log" 2>&1
EOF

    chmod +x "$PROGRAM_DIR/run.sh"
}

# Setup cron
setup_cron() {
    echo -e "\e[1;34mSetting up cron...\e[0m"
    (crontab -l 2>/dev/null; echo "*/30 * * * * /bin/bash $PROGRAM_DIR/run.sh >> $PROGRAM_DIR/log_file.log 2>&1") | crontab -
    (crontab -l 2>/dev/null; echo "@reboot /bin/bash $PROGRAM_DIR/run.sh >> $PROGRAM_DIR/log_file.log 2>&1") | crontab -
}

# Remove program
remove_program() {
    echo -e "\e[1;34mRemoving $PROGRAM_NAME and cron jobs...\e[0m"
    sudo rm -rf "$PROGRAM_DIR"
    crontab -l | grep -v "$PROGRAM_DIR/run.sh" | crontab -
}

# Main menu
main_setup() {
    PS3='Please enter your choice: '
    options=("Install $PROGRAM_NAME from '$BRANCH'" "Remove $PROGRAM_NAME" "Exit")
    select opt in "${options[@]}"; do
        case $opt in
            "Install $PROGRAM_NAME from '$BRANCH'")
                install_packages
                clone_repository

                # Add version to .env
                echo "INSTALLED_VERSION=$VERSION_TAG" >> "$PROGRAM_DIR/.env"

                # Ask for user inputs
                [ -f "$PROGRAM_DIR/.env" ] && export $(grep -v '^#' "$PROGRAM_DIR/.env" | xargs)
                [ -z "$CLOUDFLARE_API_TOKEN" ] && ask_user_input "Enter your Cloudflare API Token" "CLOUDFLARE_API_TOKEN"
                [ -z "$CLOUDFLARE_ZONE_ID" ] && ask_user_input "Enter your Cloudflare Zone ID" "CLOUDFLARE_ZONE_ID"
                [ -z "$CLOUDFLARE_RECORD_NAME" ] && ask_user_input "Enter your Cloudflare Record Name" "CLOUDFLARE_RECORD_NAME"
                [ -z "$CLOUDFLARE_IP_ADDRESSES" ] && ask_user_input "Enter IP list (comma-separated)" "CLOUDFLARE_IP_ADDRESSES"

                echo -e "\e[1;32mEnvironment variables saved to .env\e[0m"
                create_bash_script
                setup_cron
                echo -e "\e[1;32mInstalled version: $VERSION_TAG\e[0m"
                break
                ;;
            "Remove $PROGRAM_NAME")
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
