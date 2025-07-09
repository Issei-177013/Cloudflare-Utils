#!/bin/bash
set -e

PROGRAM_NAME="Cloudflare-Utils"
PROGRAM_DIR="/opt/$PROGRAM_NAME"
CONFIG_FILE_PATH="$PROGRAM_DIR/configs.json"

# Function to get the current Git branch
get_current_branch() {
    git -C "$PROGRAM_DIR" rev-parse --abbrev-ref HEAD
}

# Function to list available versions
get_versions() {
    echo -e "\e[1;34mFetching available versions...\e[0m"
    git -C "$PROGRAM_DIR" fetch --all --tags --prune

    current_branch=$(get_current_branch)
    echo -e "\e[1;33mCurrent branch: $current_branch\e[0m"

    versions=()
    if [[ "$current_branch" == "dev" ]]; then
        echo -e "\e[1;34mLast 5 dev versions (tags/commits on dev branch):\e[0m"
        mapfile -t versions < <( (git -C "$PROGRAM_DIR" tag --sort=-v:refname | grep 'dev' | head -n 5; \
                                git -C "$PROGRAM_DIR" log dev --pretty=format:"%h (%s, %ar)" --abbrev-commit --max-count=5) | \
                                awk '!seen[$0]++' | head -n 5)
    else
        echo -e "\e[1;34mLast 5 release versions (tags not containing 'dev'):\e[0m"
        mapfile -t versions < <(git -C "$PROGRAM_DIR" tag --sort=-v:refname | grep -v 'dev' | head -n 5)
    fi

    if [ ${#versions[@]} -eq 0 ]; then
        echo -e "\e[1;31mNo versions found to list. You can try entering one manually.\e[0m"
    else
        for i in "${!versions[@]}"; do
            echo "$((i+1))) ${versions[$i]}"
        done
    fi

    echo "$(( ${#versions[@]} + 1 ))) Enter version manually"
    echo "0) Cancel update"

    user_choice=""
    while true; do
        read -r -p "Select version to update to: " user_choice
        if [[ "$user_choice" -eq 0 ]]; then
            echo -e "\e[1;31mUpdate cancelled.\e[0m"
            exit 0
        elif [[ "$user_choice" -gt 0 && "$user_choice" -le ${#versions[@]} ]]; then
            selected_version="${versions[$((user_choice-1))]}"
            # Extract version string and remove ANSI color codes (safety)
            selected_version=$(echo "$selected_version" | awk '{print $1}' | sed 's/\x1B\[[0-9;]*[a-zA-Z]//g')
            echo -e "\e[1;32mSelected: $selected_version\e[0m"
            break
        elif [[ "$user_choice" -eq $(( ${#versions[@]} + 1 )) ]]; then
            read -r -p "Enter version (tag, commit hash, or branch name): " selected_version
            if [[ -z "$selected_version" ]]; then
                echo -e "\e[1;31mVersion cannot be empty.\e[0m"
            else
                # Sanitize input from ANSI if pasted
                selected_version=$(echo "$selected_version" | sed 's/\x1B\[[0-9;]*[a-zA-Z]//g')
                echo -e "\e[1;32mSelected manually: $selected_version\e[0m"
                break
            fi
        else
            echo -e "\e[1;31mInvalid choice. Please try again.\e[0m"
        fi
    done
    echo "$selected_version"
}

# Function to re-create the runner script
create_runner() {
    VERSION_TAG=$(git -C "$PROGRAM_DIR" describe --tags --abbrev=0 2>/dev/null || git -C "$PROGRAM_DIR" rev-parse --short HEAD)
    echo -e "\e[1;34mUpdating runner script for version $VERSION_TAG...\e[0m"
    cat << EOF > "$PROGRAM_DIR/run.sh"
#!/bin/bash
cd "$PROGRAM_DIR"
echo "\$(date) - Running Cloudflare-Utils $VERSION_TAG" >> log_file.log
python3 config_manager.py >> log_file.log 2>&1
EOF
    chmod +x "$PROGRAM_DIR/run.sh"
}

# Function to update to the selected version
update_to_version() {
    local version_to_update_to="$1"
    echo -e "\e[1;34mAttempting to update to version: $version_to_update_to\e[0m"

    cd "$PROGRAM_DIR"

    if ! git diff --quiet || ! git diff --cached --quiet; then
        echo -e "\e[1;33mStashing local changes...\e[0m"
        git stash push -m "Update_script_stash_$(date +%s)"
        stashed=true
    else
        stashed=false
    fi

    current_checkout=$(git rev-parse --abbrev-ref HEAD)

    if git checkout "$version_to_update_to"; then
        echo -e "\e[1;32mSuccessfully checked out version: $version_to_update_to\e[0m"

        if git show-ref --verify --quiet "refs/heads/$version_to_update_to" || git show-ref --verify --quiet "refs/remotes/origin/$version_to_update_to"; then
            echo -e "\e[1;34mPulling latest changes for branch $version_to_update_to...\e[0m"
            git pull origin "$version_to_update_to" --ff-only
        fi

        create_runner

        CLI_PATH="$PROGRAM_DIR/cli.py"
        GLOBAL_CMD_PATH="/usr/local/bin/cfutils"
        if [ -f "$CLI_PATH" ]; then
            echo -e "\e[1;34mUpdating global command '$GLOBAL_CMD_PATH'...\e[0m"
            sudo ln -sf "$CLI_PATH" "$GLOBAL_CMD_PATH"
            sudo chmod +x "$CLI_PATH"
            sudo chmod +x "$GLOBAL_CMD_PATH"
            echo -e "\e[1;32m✅ Global command 'cfutils' updated.\e[0m"
        else
            echo -e "\e[1;31m❌ Error: $CLI_PATH not found. Cannot update global command.\e[0m"
        fi

        if [ "$stashed" = true ]; then
            echo -e "\e[1;33mAttempting to reapply stashed changes...\e[0m"
            if git stash pop; then
                echo -e "\e[1;32m✅ Stashed changes reapplied successfully.\e[0m"
            else
                echo -e "\e[1;31m❌ Failed to reapply stashed changes. Please resolve conflicts manually.\e[0m"
                echo -e "\e[1;33mRun \`git stash list\` to see remaining stash.\e[0m"
            fi
        fi

        NEW_VERSION_TAG=$(git describe --tags --abbrev=0 2>/dev/null || git rev-parse --short HEAD)
        echo -e "\e[1;32m✅ Update complete. Current version: $NEW_VERSION_TAG\e[0m"
        echo -e "\e[1;33mNote: If dependencies changed, re-run install.sh to reinstall them.\e[0m"
    else
        echo -e "\e[1;31m❌ Failed to checkout version: $version_to_update_to\e[0m"
        echo -e "\e[1;33mRestoring previous state...\e[0m"
        git checkout "$current_checkout"
        if [ "$stashed" = true ]; then
            echo -e "\e[1;33mAttempting to reapply stashed changes to original state...\e[0m"
            git stash pop || echo -e "\e[1;31mCould not reapply stash. Check 'git stash list'.\e[0m"
        fi
        exit 1
    fi
    cd - > /dev/null
}

# Main
main() {
    if [ ! -d "$PROGRAM_DIR/.git" ]; then
        echo -e "\e[1;31mError: $PROGRAM_NAME is not installed or not a Git repo at $PROGRAM_DIR.\e[0m"
        echo -e "\e[1;33mPlease install it first using install.sh.\e[0m"
        exit 1
    fi

    if [ "$EUID" -ne 0 ]; then
        echo -e "\e[1;33mThis script needs sudo. Trying to re-run...\e[0m"
        sudo "$0" "$@"
        exit $?
    fi

    echo -e "\e[1;32mStarting $PROGRAM_NAME Updater...\e[0m"
    ORIG_DIR=$(pwd)

    selected_version_string=$(get_versions)
    if [[ -n "$selected_version_string" ]]; then
        update_to_version "$selected_version_string"
    fi

    cd "$ORIG_DIR"
    echo -e "\e[1;32mUpdate process finished.\e[0m"
}

main "$@"