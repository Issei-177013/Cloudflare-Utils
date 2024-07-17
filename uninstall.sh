#!/bin/bash
# Copyright 2024 [Issei-177013]
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

PROGRAM_NAME="Cloudflare-Utils"
PROGRAM_DIR="/opt/$PROGRAM_NAME"

# Define colors
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
RESET='\033[0m'

# Function to remove the program and cron jobs
remove_program() {
    echo -e "\e[1;34mRemoving the program and cron jobs...\e[0m"
    
    sudo rm -rf $PROGRAM_DIR
    
    echo -e "\e[1;32mProgram removed successfully.\e[0m"
}


remove_env_vars(){
# List of variables you want to remove
vars=("CLOUDFLARE_API_TOKEN" "CLOUDFLARE_ZONE_ID" "CLOUDFLARE_RECORD_NAME" "CLOUDFLARE_IP_ADDRESSES")

# Path to the bashrc file
bashrc_file="$HOME/.bashrc"

# Create a temporary file
temp_file=$(mktemp)

# Copy the contents of the bashrc file to the temporary file,
# excluding lines that contain the specified variables
grep -v -E "$(IFS="|"; echo "${vars[*]}")" "$bashrc_file" > "$temp_file"

# Replace the original bashrc file with the temporary file
mv "$temp_file" "$bashrc_file"

echo "The specified variables have been removed from the ~/.bashrc file."
}

remove_cronjobs(){
    crontab -l | grep -v '/opt/Cloudflare-Utils/dns/rotator/run.sh' | crontab -
    echo -e "\e[1;32mCronjobs removed successfully.\e[0m"

}


remove_cronjobs
remove_env_vars
remove_program