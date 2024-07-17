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
    crontab -l | grep -v "$PROGRAM_DIR/run.sh" | crontab -
    
    echo -e "\e[1;32mProgram and cron jobs removed successfully.\e[0m"
}

remove_program