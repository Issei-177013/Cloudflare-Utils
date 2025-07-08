#!/bin/bash
set -e

PROGRAM_NAME="Cloudflare-Utils"
PROGRAM_DIR="/opt/$PROGRAM_NAME"
CONFIG_FILE_PATH="$PROGRAM_DIR/configs.json" # Added for clarity, though not directly modified by update script

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
        # This will list tags and recent commits on the dev branch.
        # Adjust git log format as needed if specific dev versioning scheme is used.
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
            # Extract version string if it contains more details (e.g., from log)
            selected_version=$(echo "$selected_version" | awk '{print $1}')
            echo -e "\e[1;32mSelected: $selected_version\e[0m"
            break
        elif [[ "$user_choice" -eq $(( ${#versions[@]} + 1 )) ]]; then
            read -r -p "Enter version (tag, commit hash, or branch name): " selected_version
            if [[ -z "$selected_version" ]]; then
                echo -e "\e[1;31mVersion cannot be empty.\e[0m"
                # Loop back to re-select or cancel
            else
                echo -e "\e[1;32mSelected manually: $selected_version\e[0m"
                break
            fi
        else
            echo -e "\e[1;31mInvalid choice. Please try again.\e[0m"
        fi
    done
    # Return the selected version
    echo "$selected_version"
}

# Function to re-create the runner script (copied from install.sh)
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

    # Stash any local changes to avoid conflicts, apply them later if possible
    # Check if there are any changes to stash
    if ! git diff --quiet || ! git diff --cached --quiet; then
        echo -e "\e[1;33mStashing local changes...\e[0m"
        git stash push -m "Update_script_stash_$(date +%s)"
        stashed=true
    else
        stashed=false
    fi

    current_checkout=$(git rev-parse --abbrev-ref HEAD)

    # Perform the checkout
    if git checkout "$version_to_update_to"; then
        echo -e "\e[1;32mSuccessfully checked out version: $version_to_update_to\e[0m"

        # If the target is a branch, pull the latest changes
        # Check if version_to_update_to is a branch
        if git show-ref --verify --quiet "refs/heads/$version_to_update_to" || git show-ref --verify --quiet "refs/remotes/origin/$version_to_update_to"; then
            echo -e "\e[1;34mPulling latest changes for branch $version_to_update_to...\e[0m"
            git pull origin "$version_to_update_to" --ff-only # Use --ff-only to avoid merge commits by the script
        fi

        # Re-create runner script
        create_runner # This will use the new version's code context

        # Update global command (ensure it points to the potentially new cli.py location/version)
        # install.sh uses `ln -sf`, which should be robust.
        # However, we can re-link it to be certain, especially if cli.py path could change (though unlikely in this project structure)
        CLI_PATH="$PROGRAM_DIR/cli.py"
        GLOBAL_CMD_PATH="/usr/local/bin/cfutils"
        if [ -f "$CLI_PATH" ]; then
            echo -e "\e[1;34mUpdating global command '$GLOBAL_CMD_PATH'...\e[0m"
            sudo ln -sf "$CLI_PATH" "$GLOBAL_CMD_PATH"
            sudo chmod +x "$CLI_PATH" # Ensure executable bit is set on new version
            sudo chmod +x "$GLOBAL_CMD_PATH"
            echo -e "\e[1;32m✅ Global command 'cfutils' updated.\e[0m"
        else
            echo -e "\e[1;31m❌ Error: $CLI_PATH not found in the updated version. Cannot update global command.\e[0m"
        fi

        # Attempt to reapply stashed changes
        if [ "$stashed" = true ]; then
            echo -e "\e[1;33mAttempting to reapply stashed changes...\e[0m"
            if git stash pop; then
                echo -e "\e[1;32m✅ Stashed changes reapplied successfully.\e[0m"
            else
                echo -e "\e[1;31m❌ Failed to reapply stashed changes automatically. Please resolve conflicts manually in $PROGRAM_DIR.\e[0m"
                echo -e "\e[1;33mYour changes are still available in 'git stash list'.\e[0m"
            fi
        fi

        NEW_VERSION_TAG=$(git describe --tags --abbrev=0 2>/dev/null || git rev-parse --short HEAD)
        echo -e "\e[1;32m✅ Update complete. Current version: $NEW_VERSION_TAG\e[0m"
        echo -e "\e[1;33mImportant: If this update included changes to dependencies, you might need to reinstall them manually or via install.sh (if it handles Python dependencies).\e[0m"
    else
        echo -e "\e[1;31m❌ Failed to checkout version: $version_to_update_to\e[0m"
        echo -e "\e[1;33mRestoring previous state...\e[0m"
        git checkout "$current_checkout" # Attempt to restore original checkout
        if [ "$stashed" = true ]; then
            echo -e "\e[1;33mAttempting to reapply stashed changes to original state...\e[0m"
            git stash pop || echo -e "\e[1;31mCould not reapply stash to original state. Check 'git stash list'.\e[0m"
        fi
        exit 1
    fi
    cd - > /dev/null
}

# Main script execution
main() {
    if [ ! -d "$PROGRAM_DIR/.git" ]; then
        echo -e "\e[1;31mError: $PROGRAM_NAME installation directory not found or is not a git repository ($PROGRAM_DIR).\e[0m"
        echo -e "\e[1;33mPlease install the program using install.sh first.\e[0m"
        exit 1
    fi

    # Ensure script is run with sudo for commands that need it (like ln -sf to /usr/local/bin)
    if [ "$EUID" -ne 0 ]; then
        echo -e "\e[1;33mThis script needs to run with sudo privileges to update global commands.\e[0m"
        echo -e "\e[1;33mAttempting to re-run with sudo...\e[0m"
        sudo "$0" "$@"
        exit $?
    fi
    
    echo -e "\e[1;32mStarting $PROGRAM_NAME Updater...\e[0m"
    
    # Preserve original directory
    ORIG_DIR=$(pwd)

    # Get selected version from user
    selected_version_string=$(get_versions)

    if [[ -n "$selected_version_string" ]]; then
        update_to_version "$selected_version_string"
    fi

    # Return to original directory
    cd "$ORIG_DIR"
    echo -e "\e[1;32mUpdate process finished.\e[0m"
}

main "$@"