#!/bin/bash

PROGRAM_NAME="Cloudflare-Utils"
PROGRAM_DIR="/opt/$PROGRAM_NAME"

# Colors for the menu
RED=$(tput setaf 1)
GREEN=$(tput setaf 2)
YELLOW=$(tput setaf 3)
BLUE=$(tput setaf 4)
RESET=$(tput sgr0)

# Navigate to the project directory
cd "$PROGRAM_DIR" || { echo "${RED}Failed to navigate to $PROGRAM_DIR${RESET}"; exit 1; }

# Enable error handling
set -e

# Function to update to the latest version of a branch
update_branch() {
  branch=$1
  echo "${GREEN}Updating to latest version of branch: $branch${RESET}"
  git fetch origin $branch
  git checkout $branch
  git pull origin $branch
}

# Function to update to the latest tagged version
update_tag() {
  tag_prefix=$1
  echo "${GREEN}Updating to latest tag with prefix: $tag_prefix${RESET}"
  latest_tag=$(git tag -l "$tag_prefix*" | sort -V | tail -n 1)
  if [ -z "$latest_tag" ]; then
    echo "${RED}No tag found with prefix $tag_prefix${RESET}"
  else
    git checkout tags/$latest_tag
  fi
}

# Display the menu
show_menu() {
  echo "${BLUE}Select an update option:${RESET}"
  echo "${YELLOW}1)${RESET} ${GREEN}latest release version (main)${RESET}"
  echo "${YELLOW}2)${RESET} ${GREEN}latest beta version (beta)${RESET}"
  echo "${YELLOW}3)${RESET} ${GREEN}latest alpha version (alpha)${RESET}"
  echo "${YELLOW}4)${RESET} ${GREEN}latest dev version (dev)${RESET}"
  echo "${YELLOW}0)${RESET} ${GREEN}Back${RESET}"
}

# Handle user input
handle_choice() {
  case "$1" in
    1)
      update_branch "main"
      ;;
    2)
      update_branch "beta"
      ;;
    3)
      update_branch "alpha"
      ;;
    4)
      update_branch "dev"
      ;;
    0)
      echo "${BLUE}Returning to previous menu...${RESET}"
      exit 0
      ;;
    *)
      echo "${RED}Invalid choice! Please enter a number between 0 and 4.${RESET}"
      ;;
  esac
}

# Main script execution
while true; do
  show_menu
  read -p "${YELLOW}Enter your choice [0-4]: ${RESET}" choice
  handle_choice "$choice"
done
