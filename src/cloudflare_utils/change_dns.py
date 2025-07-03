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

import os
import argparse
import logging
from cloudflare import Cloudflare, APIError
from dotenv import load_dotenv
from tabulate import tabulate

# --- Determine Base Directory ---
# This logic tries to determine the actual installation directory.
# If CFU_INSTALL_DIR is set (e.g., by run.sh), use that.
# Otherwise, fall back to a default. This helps with locating .env and log files
# correctly, especially for branched installs.
# run.sh should export CFU_INSTALL_DIR="$SCRIPT_DIR"
APP_INSTALL_DIR = os.getenv("CFU_INSTALL_DIR", "/opt/Cloudflare-Utils") # Default if not set by run.sh

# --- Constants based on determined install directory ---
LOG_FILE_PATH = os.path.join(APP_INSTALL_DIR, "log_file.log")
DEFAULT_ENV_FILE_PATH = os.path.join(APP_INSTALL_DIR, ".env")

# --- Global Cloudflare client ---
cf_client = None # Will be initialized by initialize_cloudflare_client

# --- Logging Configuration ---
def setup_logging(log_level_str="INFO"):
    # Ensure log directory exists using the determined LOG_FILE_PATH
    # This path is now dynamic based on APP_INSTALL_DIR
    os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)
    
    numeric_level = getattr(logging, log_level_str.upper(), None)
    if not isinstance(numeric_level, int):
        # Using print here as logging might not be fully set up if this is the first message.
        print(f"Warning: Invalid log level: {log_level_str}. Defaulting to INFO.")
        numeric_level = logging.INFO

    # Remove any existing handlers before adding new ones to prevent duplicate logs
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
        
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(levelname)s - %(module)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE_PATH),
            logging.StreamHandler()
        ]
    )
# --- End Logging Configuration ---

def load_configuration(args, effective_env_file_path_to_load):
    """Loads configuration from the effective .env file path and then overrides with CLI arguments if provided."""
    
    # Load from the specified .env file.
    # `override=True` means variables in .env will overwrite existing OS environment variables for the scope of this script.
    if os.path.exists(effective_env_file_path_to_load):
        load_dotenv(dotenv_path=effective_env_file_path_to_load, override=True) 
        logging.info(f".env file loaded from {effective_env_file_path_to_load} (values will override OS env vars for this session)")
    else:
        logging.info(f".env file not found at {effective_env_file_path_to_load}. Relying on OS environment variables or CLI arguments.")

    # Priority:
    # 1. CLI arguments (if provided by user, not None)
    # 2. OS environment variables (which now include .env values if `override=True` was used for `load_dotenv`)
    
    config = {}
    config["api_token"] = args.api_token if args.api_token is not None else os.getenv('CLOUDFLARE_API_TOKEN')
    config["zone_id"] = args.zone_id if args.zone_id is not None else os.getenv('CLOUDFLARE_ZONE_ID')
    config["record_names_str"] = args.record_names if args.record_names is not None else os.getenv('CLOUDFLARE_RECORD_NAME')
    config["ip_addresses_str"] = args.ip_addresses if args.ip_addresses is not None else os.getenv('CLOUDFLARE_IP_ADDRESSES')
    
    return config

def initialize_cloudflare_client(api_token_val):
    global cf_client 
    if not api_token_val:
        logging.error("Cloudflare API Token is missing.")
        return False
    try:
        cf_client = Cloudflare(api_token=api_token_val)
        logging.info("Cloudflare client initialized successfully.")
        return True
    except Exception as e:
        logging.error(f"Failed to initialize Cloudflare client: {e}")
        return False

def fetch_dns_records(target_zone_id, record_types=['A', 'AAAA']):
    all_records = []
    if not cf_client:
        logging.error("Cloudflare client not initialized for fetching records.")
        return None
    try:
        for record_type in record_types:
            # Updated to use 'type' as a direct keyword argument instead of 'params'
            response = cf_client.dns.records.list(zone_id=target_zone_id, type=record_type)
            all_records.extend([record.model_dump() for record in response])
        return all_records
    except APIError as e:
        logging.error(f"Cloudflare API Error while fetching records: {e.status_code} - {e.body}")
        return None
    except Exception as e:
        logging.error(f"An unexpected error occurred while fetching records: {e}")
        return None

def display_dns_records_table(dns_records):
    """Displays DNS records in a formatted table."""
    if not dns_records:
        logging.info("No DNS records to display.")
        return

    headers = ["Type", "Name", "Content (IP)", "TTL", "Proxied"]
    table_data = []
    for record in dns_records:
        table_data.append([
            record.get('type', 'N/A'),
            record.get('name', 'N/A'),
            record.get('content', 'N/A'),
            record.get('ttl', 'N/A'),
            record.get('proxied', 'N/A')
        ])
    
    # Using print directly for table output, as logging might format it undesirably.
    print("\nDNS Records:")
    print(tabulate(table_data, headers=headers, tablefmt="grid"))
    print("\n")

def update_dns_record(target_zone_id, record_id, record_name, record_type, new_content):
    if not cf_client:
        logging.error("Cloudflare client not initialized for updating record.")
        return False
        
    is_ipv6 = ':' in new_content
    if record_type == 'A' and is_ipv6:
        logging.warning(f"Skipping update for A record {record_name} ({record_id}): {new_content} is IPv6 but expected IPv4.")
        return False
    if record_type == 'AAAA' and not is_ipv6:
        logging.warning(f"Skipping update for AAAA record {record_name} ({record_id}): {new_content} is IPv4 but expected IPv6.")
        return False

    try:
        payload = {'type': record_type, 'name': record_name, 'content': new_content}
        cf_client.dns.records.update(dns_record_id=record_id, zone_id=target_zone_id, data=payload)
        logging.info(f"Successfully updated {record_type} record: {record_name} ({record_id}) to {new_content}")
        return True
    except APIError as e:
        logging.error(f"Cloudflare API Error while updating {record_type} record {record_name} ({record_id}): {e.status_code} - {e.body}")
        return False
    except Exception as e:
        logging.error(f"An unexpected error occurred while updating record {record_name}: {e}")
        return False

def get_next_ip(current_ip, record_type, available_ips):
    potential_ips = [ip for ip in available_ips if (':' in ip if record_type == 'AAAA' else ':' not in ip)]
    if not potential_ips:
        return current_ip
    try:
        current_index = potential_ips.index(current_ip)
    except ValueError:
        current_index = -1
    next_index = (current_index + 1) % len(potential_ips)
    return potential_ips[next_index]

def core_dns_update_logic(config_dict):
    if not initialize_cloudflare_client(config_dict.get("api_token")):
        return

    zone_id_val = config_dict.get("zone_id")
    record_names_str_val = config_dict.get("record_names_str")
    ip_addresses_str_val = config_dict.get("ip_addresses_str")

    if not zone_id_val or not record_names_str_val or not ip_addresses_str_val:
        logging.error("Missing one or more required configurations: Zone ID, Record Name(s), or IP Addresses.")
        return

    target_record_names = [name.strip() for name in record_names_str_val.split(',') if name.strip()]
    ip_addresses_list = [ip.strip() for ip in ip_addresses_str_val.split(',') if ip.strip()]

    # This is a placeholder for how interactive mode might be passed.
    # It assumes 'interactive' is a boolean attribute in config_dict, set by main_cli based on args.
    is_interactive_mode = config_dict.get("interactive", False)

    logging.info(f"Fetching A and AAAA records for zone ID: {zone_id_val}...")
    # In interactive mode, we might want to fetch all records initially, not just A/AAAA,
    # or allow type filtering later. For now, sticking to A/AAAA as per current fetch_dns_records.
    dns_records = fetch_dns_records(zone_id_val)

    if dns_records is None:
        logging.error("Could not fetch DNS records. Exiting.")
        return
    
    if is_interactive_mode:
        if not dns_records:
            logging.info("No A or AAAA records found in the zone to display.")
        else:
            display_dns_records_table(dns_records)
        logging.info("Interactive mode: Displayed records. Further interaction not yet implemented.")
        return # Exit after displaying in this initial interactive step

    # Non-interactive mode continues below (original logic)
    if not target_record_names:
        logging.error("Parsed Record Name(s) list is empty. This is required for non-interactive mode.")
        return
    if not ip_addresses_list:
        logging.error("Parsed IP Addresses list is empty. This is required for non-interactive mode.")
        return
        
    if not dns_records: # Check again in case interactive mode was false and no records found
        logging.info("No A or AAAA records found in the zone.")
        return

    logging.info(f"Found {len(dns_records)} A/AAAA records. Processing records matching: {', '.join(target_record_names)}")

    updated_count = 0
    processed_count = 0
    for record in dns_records:
        if record['name'] in target_record_names:
            processed_count += 1
            current_content = record['content']
            record_id = record['id']
            record_type = record['type']
            full_record_name = record['name']

            logging.info(f"Processing record: {full_record_name} (Type: {record_type}, Current IP: {current_content})")
            next_ip_to_use = get_next_ip(current_content, record_type, ip_addresses_list)

            if next_ip_to_use != current_content:
                logging.info(f"Attempting to update {record_type} record {full_record_name} from {current_content} to {next_ip_to_use}...")
                if update_dns_record(zone_id_val, record_id, full_record_name, record_type, next_ip_to_use):
                    updated_count += 1
            else:
                logging.info(f"No IP change needed for {record_type} record {full_record_name}. Current IP: {current_content}.")
    
    if processed_count == 0:
        logging.info(f"No DNS records found matching the target name(s): {', '.join(target_record_names)}")
    elif updated_count > 0:
        logging.info(f"Successfully updated {updated_count} DNS record(s).")
    else:
        logging.info("No DNS records were updated (no changes needed or no matching records found).")
    
    logging.info("Cloudflare DNS update script finished.")

def main_cli():
    # APP_INSTALL_DIR and DEFAULT_ENV_FILE_PATH are determined at module start.
    
    parser = argparse.ArgumentParser(description="Cloudflare DNS Update Utility.")
    parser.add_argument('--api-token', type=str, default=None, 
                        help='Cloudflare API Token (overrides .env and OS env variables).')
    parser.add_argument('--zone-id', type=str, default=None, 
                        help='Cloudflare Zone ID (overrides .env and OS env variables).')
    parser.add_argument('--record-names', type=str, default=None, 
                        help='Comma-separated DNS record names (overrides .env and OS env variables). Required for non-interactive mode.')
    parser.add_argument('--ip-addresses', type=str, default=None, 
                        help='Comma-separated IP addresses to rotate (overrides .env and OS env variables). Required for non-interactive mode.')
    parser.add_argument('--env-file', type=str, default=DEFAULT_ENV_FILE_PATH, 
                        help=f'Path to .env file. (Default: {DEFAULT_ENV_FILE_PATH}, which is derived from actual install location if CFU_INSTALL_DIR env var is set by run.sh, else /opt/Cloudflare-Utils/.env).')
    parser.add_argument('--log-level', type=str, default="INFO", 
                        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], 
                        help='Set the logging level (default: INFO).')
    parser.add_argument('--interactive', action='store_true', 
                        help='Enable interactive mode for record selection and operations.')
    parser.add_argument('--version', action='version', version='%(prog)s 0.1.0') # Version will be updated by packaging later

    args = parser.parse_args()

    # Setup logging using the LOG_FILE_PATH (now determined dynamically based on APP_INSTALL_DIR)
    setup_logging(args.log_level)
    
    # Determine the .env file path to use.
    # args.env_file holds the value from CLI if provided, else its default (DEFAULT_ENV_FILE_PATH).
    effective_env_path_for_loading = args.env_file 
    
    # Log which .env file path is being attempted for loading
    logging.info(f"Attempting to load .env file from: {effective_env_path_for_loading}")

    logging.info("Cloudflare DNS update CLI started.")
    
    final_config = load_configuration(args, effective_env_path_for_loading)
    # Add the interactive flag to the config to be passed to core_dns_update_logic
    final_config["interactive"] = args.interactive
    
    # Validate required arguments for non-interactive mode
    if not args.interactive:
        if not final_config.get("record_names_str"):
            logging.error("Error: --record-names (or CLOUDFLARE_RECORD_NAME in .env) is required in non-interactive mode.")
            parser.print_help()
            return 
        if not final_config.get("ip_addresses_str"):
            logging.error("Error: --ip-addresses (or CLOUDFLARE_IP_ADDRESSES in .env) is required in non-interactive mode.")
            parser.print_help()
            return

    core_dns_update_logic(final_config)

if __name__ == "__main__":
    main_cli()