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
    echo -e "\e[1;34mFetching available versions...\e[0m" >&2
    if ! git -C "$PROGRAM_DIR" fetch --all --tags --prune; then
        echo -e "\e[1;31mError: Failed to fetch updates from the repository.\e[0m" >&2
        echo -e "\e[1;33mPlease check your internet connection and repository access.\e[0m" >&2
        # Return a special value or exit to indicate failure to get_versions caller
        # For now, let's echo an empty string which will cancel the update in the caller
        echo "" 
        return 1 # Indicate error
    fi

    current_branch=$(get_current_branch)
    if [ -z "$current_branch" ]; then
        echo -e "\e[1;31mError: Could not determine the current branch in $PROGRAM_DIR.\e[0m" >&2
        echo ""
        return 1 # Indicate error
    fi
    echo -e "\e[1;33mCurrent branch: $current_branch\e[0m" >&2

    versions=()
    local list_title=""

    if [[ "$current_branch" == "dev" ]];then
        list_title="Showing last 10 dev versions (tags containing 'dev'):"
        mapfile -t versions < <(
            git -C "$PROGRAM_DIR" tag --sort=-v:refname | grep 'dev' | head -n 10
        )
    else
        list_title="Showing last 10 release versions (tags not containing 'dev'):"
        mapfile -t versions < <(
            git -C "$PROGRAM_DIR" tag --sort=-v:refname | grep -v 'dev' | head -n 10
        )
    fi
    
    echo -e "\e[1;34m$list_title\e[0m" >&2

    if [ ${#versions[@]} -eq 0 ]; then
        echo -e "\e[1;33m⚠ No matching tagged versions found for this branch criteria.\e[0m" >&2
        echo -e "\e[1;34mFalling back to showing latest 5 commits on branch '$current_branch':\e[0m" >&2
        mapfile -t versions < <(
            git -C "$PROGRAM_DIR" log "$current_branch" --pretty=format:"%h (%s, %ar)" --abbrev-commit --max-count=5
        )
        if [ ${#versions[@]} -eq 0 ]; then
            echo -e "\e[1;31mError: Could not list any versions or commits from the repository.\e[0m" >&2
            echo ""
            return 1 # Indicate error
        fi
    fi

    for i in "${!versions[@]}"; do
        echo "$((i+1))) ${versions[$i]}" >&2 # Print list to stderr
    done

    echo "$(( ${#versions[@]} + 1 ))) Enter version manually" >&2
    echo "0) Cancel update" >&2

    local user_choice
    while true; do
        # The prompt from read -p already goes to stderr by default if stdin is a tty
        read -r -p "Select version to update to: " user_choice
        if [[ "$user_choice" -eq 0 ]]; then
            echo -e "\e[1;31mUpdate cancelled.\e[0m"
            exit 0
        elif [[ "$user_choice" -gt 0 && "$user_choice" -le ${#versions[@]} ]]; then
            selected_version="${versions[$((user_choice-1))]}"
            # Clean ANSI codes first
            selected_version=$(echo "$selected_version" | sed 's/\x1B\[[0-9;]*[a-zA-Z]//g')
            echo -e "\e[1;32mSelected: $selected_version\e[0m" >&2 # Redirect to stderr
            break
        elif [[ "$user_choice" -eq $(( ${#versions[@]} + 1 )) ]]; then
            read -r -p "Enter version (tag, commit hash, or branch name): " selected_version
            # Clean ANSI codes first
            selected_version=$(echo "$selected_version" | sed 's/\x1B\[[0-9;]*[a-zA-Z]//g')
            if [[ -z "$selected_version" ]]; then
                echo -e "\e[1;31mVersion cannot be empty.\e[0m" >&2 # Redirect to stderr
            else
                echo -e "\e[1;32mSelected manually: $selected_version\e[0m" >&2 # Redirect to stderr
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
    local git_dir_arg="-C $PROGRAM_DIR"
    # Attempt to get a tag
    VERSION_TAG=$(git $git_dir_arg describe --tags --abbrev=0 2>/dev/null)

    if [ -z "$VERSION_TAG" ]; then
        # If no tag, check if we are on a branch
        current_ref=$(git $git_dir_arg symbolic-ref -q HEAD)
        if [ -n "$current_ref" ]; then
            # Use branch name, e.g., refs/heads/dev -> dev
            VERSION_TAG=$(git $git_dir_arg rev-parse --abbrev-ref HEAD)
        else
            # Detached HEAD, use short commit hash
            VERSION_TAG=$(git $git_dir_arg rev-parse --short HEAD)
        fi
    fi

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