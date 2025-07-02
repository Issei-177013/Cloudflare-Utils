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

# --- Constants ---
# The installation directory, assumed to be /opt/Cloudflare-Utils
# This is where .env and log_file.log are expected to be.
INSTALL_DIR = "/opt/Cloudflare-Utils"
LOG_FILE_PATH = os.path.join(INSTALL_DIR, "log_file.log")
ENV_FILE_PATH = os.path.join(INSTALL_DIR, ".env")

# --- Global Cloudflare client ---
# This will be initialized in main_cli after loading config
cf_client = None

# --- Logging Configuration ---
def setup_logging(log_level_str="INFO"):
    # Ensure log directory exists
    os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)
    
    numeric_level = getattr(logging, log_level_str.upper(), None)
    if not isinstance(numeric_level, int):
        logging.warning(f"Invalid log level: {log_level_str}. Defaulting to INFO.")
        numeric_level = logging.INFO

    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(levelname)s - %(module)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE_PATH),
            logging.StreamHandler() # Also log to console for CLI usage
        ]
    )
# --- End Logging Configuration ---

def load_configuration(args):
    """Loads configuration from .env file and then overrides with CLI arguments if provided."""
    
    # Load from .env file first
    if os.path.exists(ENV_FILE_PATH):
        load_dotenv(ENV_FILE_PATH)
        logging.info(f".env file loaded from {ENV_FILE_PATH}")
    else:
        logging.info(f".env file not found at {ENV_FILE_PATH}. Relying on environment variables or CLI arguments.")

    config = {
        "api_token": os.getenv('CLOUDFLARE_API_TOKEN'),
        "zone_id": os.getenv('CLOUDFLARE_ZONE_ID'),
        "record_names_str": os.getenv('CLOUDFLARE_RECORD_NAME'),
        "ip_addresses_str": os.getenv('CLOUDFLARE_IP_ADDRESSES'),
    }

    # Override with CLI arguments if provided
    if args.api_token:
        config["api_token"] = args.api_token
    if args.zone_id:
        config["zone_id"] = args.zone_id
    if args.record_names:
        config["record_names_str"] = args.record_names
    if args.ip_addresses:
        config["ip_addresses_str"] = args.ip_addresses
    
    return config

def initialize_cloudflare_client(api_token):
    global cf_client
    if not api_token:
        logging.error("Cloudflare API Token is missing.")
        return False
    try:
        cf_client = Cloudflare(api_token=api_token)
        logging.info("Cloudflare client initialized successfully.")
        return True
    except Exception as e:
        logging.error(f"Failed to initialize Cloudflare client: {e}")
        return False

def fetch_dns_records(target_zone_id, record_types=['A', 'AAAA']):
    all_records = []
    if not cf_client:
        logging.error("Cloudflare client not initialized.")
        return None
    try:
        for record_type in record_types:
            response = cf_client.dns.records.list(zone_id=target_zone_id, params={'type': record_type})
            all_records.extend([record.model_dump() for record in response])
        return all_records
    except APIError as e:
        logging.error(f"Cloudflare API Error while fetching records: {e.status_code} - {e.body}")
        return None
    except Exception as e:
        logging.error(f"An unexpected error occurred while fetching records: {e}")
        return None

def update_dns_record(target_zone_id, record_id, record_name, record_type, new_content):
    if not cf_client:
        logging.error("Cloudflare client not initialized.")
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

def core_dns_update_logic(config):
    """
    The main DNS update logic, using the provided config dictionary.
    This function is called by main_cli after parsing args and loading config.
    """
    if not initialize_cloudflare_client(config["api_token"]):
        return

    if not config["zone_id"] or not config["record_names_str"] or not config["ip_addresses_str"]:
        logging.error("Missing one or more required configurations: Zone ID, Record Name(s), or IP Addresses.")
        return

    target_record_names = [name.strip() for name in config["record_names_str"].split(',') if name.strip()]
    ip_addresses_list = [ip.strip() for ip in config["ip_addresses_str"].split(',') if ip.strip()]

    if not target_record_names:
        logging.error("Parsed Record Name(s) list is empty.")
        return
    if not ip_addresses_list:
        logging.error("Parsed IP Addresses list is empty.")
        return

    logging.info(f"Fetching A and AAAA records for zone ID: {config['zone_id']}...")
    dns_records = fetch_dns_records(config['zone_id'])

    if dns_records is None:
        logging.error("Could not fetch DNS records. Exiting.")
        return
    if not dns_records:
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
                if update_dns_record(config['zone_id'], record_id, full_record_name, record_type, next_ip_to_use):
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
    parser = argparse.ArgumentParser(description="Cloudflare DNS Update Utility.")
    parser.add_argument('--api-token', type=str, help='Cloudflare API Token.')
    parser.add_argument('--zone-id', type=str, help='Cloudflare Zone ID.')
    parser.add_argument('--record-names', type=str, help='Comma-separated list of DNS record names (e.g., example.com,sub.example.com).')
    parser.add_argument('--ip-addresses', type=str, help='Comma-separated list of IP addresses to rotate through.')
    parser.add_argument('--env-file', type=str, default=ENV_FILE_PATH, help=f'Path to .env file (default: {ENV_FILE_PATH}).')
    parser.add_argument('--log-level', type=str, default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], help='Set the logging level (default: INFO).')
    # Add a version action
    parser.add_argument('--version', action='version', version='%(prog)s 0.1.0')


    args = parser.parse_args()

    # Setup logging as early as possible, using CLI arg for level
    setup_logging(args.log_level)
    
    # Update ENV_FILE_PATH if user specified a different one
    global ENV_FILE_PATH
    if args.env_file != ENV_FILE_PATH: # Check if user provided a non-default path
        ENV_FILE_PATH = args.env_file
        logging.info(f"Using custom .env file path: {ENV_FILE_PATH}")


    logging.info("Cloudflare DNS update CLI started.")
    
    config = load_configuration(args)
    core_dns_update_logic(config)


if __name__ == "__main__":
    # This allows the script to be run directly for testing,
    # even though the entry point for the package is main_cli.
    main_cli()
