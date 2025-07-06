#!/bin/bash
set -e

PROGRAM_NAME="Cloudflare-Utils"
DEFAULT_BRANCH="dev"
BRANCH="${1:-$DEFAULT_BRANCH}"
PROGRAM_DIR="/opt/$PROGRAM_NAME"
VERSION_TAG=""

# نصب وابستگی‌ها
install_packages() {
    echo -e "\e[1;34mInstalling dependencies...\e[0m"
    sudo apt-get update
    sudo apt-get install -y git python3-pip
    pip3 install cloudflare python-dotenv
}

# کلون کردن سورس
clone_repository() {
    echo -e "\e[1;34mCloning from branch '$BRANCH'...\e[0m"
    if [ -d "$PROGRAM_DIR/.git" ]; then
        cd "$PROGRAM_DIR"
        git fetch origin
        git checkout "$BRANCH"
        git pull origin "$BRANCH"
    else
        git clone --branch "$BRANCH" https://github.com/Issei-177013/Cloudflare-Utils.git "$PROGRAM_DIR"
    fi

    cd "$PROGRAM_DIR"
    VERSION_TAG=$(git describe --tags --abbrev=0 2>/dev/null || git rev-parse --short HEAD)
    cd - > /dev/null
}

# ساخت run.sh برای اجرای برنامه اصلی
create_runner() {
    cat << EOF > "$PROGRAM_DIR/run.sh"
#!/bin/bash
cd "$PROGRAM_DIR"
echo "\$(date) - Running Cloudflare-Utils $VERSION_TAG" >> log_file.log
python3 rotate_from_config.py >> log_file.log 2>&1
EOF

    chmod +x "$PROGRAM_DIR/run.sh"
}

# تنظیم کرون
setup_cron() {
    echo -e "\e[1;34mSetting up cron...\e[0m"
    (crontab -l 2>/dev/null; echo "*/30 * * * * /bin/bash $PROGRAM_DIR/run.sh") | crontab -
    (crontab -l 2>/dev/null; echo "@reboot /bin/bash $PROGRAM_DIR/run.sh") | crontab -
}

# منوی اصلی
main_menu() {
    PS3="Please choose: "
    options=("Install $PROGRAM_NAME (branch '$BRANCH')" "Remove $PROGRAM_NAME" "Exit")
    select opt in "${options[@]}"; do
        case $opt in
            "Install $PROGRAM_NAME (branch '$BRANCH')")
                install_packages
                clone_repository
                create_runner
                setup_cron
                echo -e "\e[1;32m✅ Installed version: $VERSION_TAG\e[0m"
                echo -e "\e[1;32m📌 Use \`python3 $PROGRAM_DIR/cli.py\` to add accounts and records.\e[0m"
                break
                ;;
            "Remove $PROGRAM_NAME")
                sudo rm -rf "$PROGRAM_DIR"
                crontab -l | grep -v "$PROGRAM_DIR/run.sh" | crontab -
                echo -e "\e[1;31mRemoved $PROGRAM_NAME and cron jobs.\e[0m"
                break
                ;;
            "Exit")
                break
                ;;
            *) echo "Invalid option $REPLY";;
        esac
    done
}

main_menu
