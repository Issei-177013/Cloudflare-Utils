#!/opt/Cloudflare-Utils-Agent/venv/bin/python3
import argparse
import json
import os
import subprocess
import sys
import requests
import re
from datetime import datetime
from security import generate_api_key

# Define paths
AGENT_DIR = "/opt/Cloudflare-Utils-Agent"
AGENT_CONFIG_PATH = os.path.join(AGENT_DIR, "config.json")
AGENT_SERVICE_NAME = "cloudflare-utils-agent.service"
AGENT_VERSION_PATH = os.path.join(AGENT_DIR, "version.py")
AUDIT_LOG_PATH = "/var/log/cfu-agent-audit.log"


# --- Helper Functions ---

def _log_audit_event(message):
    """Logs a security-sensitive event to the audit log."""
    try:
        # Ensure the log directory exists (though /var/log should always exist)
        os.makedirs(os.path.dirname(AUDIT_LOG_PATH), exist_ok=True)
        
        # Get current timestamp and username
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        username = os.getenv('SUDO_USER') or os.getenv('USER') or 'unknown'

        log_entry = f"{timestamp} - User:{username} - Event: {message}\n"
        
        with open(AUDIT_LOG_PATH, 'a') as f:
            f.write(log_entry)
        
        # Set secure permissions for the audit log
        os.chmod(AUDIT_LOG_PATH, 0o640)

    except (IOError, PermissionError) as e:
        print(f"\nWarning: Could not write to audit log at {AUDIT_LOG_PATH}.")
        print(f"  Reason: {e}")
        print("  Please ensure you have the necessary permissions.")
        print("  You may need to create the file manually (`sudo touch /var/log/cfu-agent-audit.log`)")
        print("  and grant write permissions to the appropriate user/group.")


def _is_service_active():
    """Checks if the agent service is active."""
    try:
        result = subprocess.run(['systemctl', 'is-active', AGENT_SERVICE_NAME], capture_output=True, text=True)
        return result.stdout.strip() == 'active'
    except FileNotFoundError:
        print("Error: systemctl not found. Are you on a systemd-based Linux distribution?")
        return False

def _read_agent_config():
    """Reads the agent's configuration file."""
    if not os.path.exists(AGENT_CONFIG_PATH):
        print(f"Error: Agent configuration file not found at {AGENT_CONFIG_PATH}")
        return None
    try:
        with open(AGENT_CONFIG_PATH, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error reading agent configuration: {e}")
        return None

def _write_agent_config(config):
    """Writes to the agent's configuration file."""
    try:
        with open(AGENT_CONFIG_PATH, 'w') as f:
            json.dump(config, f, indent=2)
        # Set permissions to 600 for security
        os.chmod(AGENT_CONFIG_PATH, 0o600)
        return True
    except IOError as e:
        print(f"Error writing agent configuration: {e}")
        return False

def _restart_agent_service():
    """Restarts the agent service."""
    print("Restarting agent service to apply changes...")
    try:
        subprocess.run(['sudo', 'systemctl', 'restart', AGENT_SERVICE_NAME], check=True)
        print("Agent service restarted successfully.")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Error restarting agent service: {e}")
        print("Please restart the service manually: sudo systemctl restart " + AGENT_SERVICE_NAME)

# --- Command Functions ---

def handle_token_display(args):
    """Displays the current API key."""
    config = _read_agent_config()
    if not config or 'api_key' not in config or not config['api_key']:
        print("No API key is set.")
        return

    key = config['api_key']

    if args.full:
        if not args.force:
            print("Warning: Displaying the full API token is a security risk.")
            if input("Are you sure you want to continue? (y/N): ").lower() != 'y':
                print("Aborted.")
                return
        
        print(f"Full API Key: {key}")
        _log_audit_event("Displayed full API token.")
    else:
        masked_key = key[:4] + '*' * (len(key) - 8) + key[-4:] if len(key) > 8 else key[:2] + '*' * (len(key) - 4) + key[-2:]
        print(f"Current API Key (masked): {masked_key}")


def handle_token_change(args):
    """Revokes the old token and generates a new one."""
    if not args.force:
        print("Warning: This will revoke the current token and generate a new one.")
        print("The agent service will be restarted, and any application using the old token will lose access.")
        if input("Are you sure you want to continue? (y/N): ").lower() != 'y':
            print("Aborted.")
            return

    config = _read_agent_config()
    if config is None:
        return

    # Generate a new token
    new_token = generate_api_key()
    config['api_key'] = new_token
    config['token_last_changed'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    if 'token_created_at' not in config:
        config['token_created_at'] = config['token_last_changed']

    if _write_agent_config(config):
        print("New API token generated and saved.")
        _log_audit_event("Changed API token.")
        _restart_agent_service()
        
        print("\n--- NEW API TOKEN ---")
        print("Please copy this token and store it securely. It will not be shown again.")
        print(f"Token: {new_token}")
        print("---------------------\n")
    else:
        print("Failed to save the new token to the configuration file.")


def handle_service_start(args):
    """Starts the agent service."""
    try:
        subprocess.run(['sudo', 'systemctl', 'start', AGENT_SERVICE_NAME], check=True)
        print("Agent service started.")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Error starting agent service: {e}")

def handle_service_stop(args):
    """Stops the agent service."""
    try:
        subprocess.run(['sudo', 'systemctl', 'stop', AGENT_SERVICE_NAME], check=True)
        print("Agent service stopped.")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Error stopping agent service: {e}")

def handle_service_restart(args):
    """Restarts the agent service."""
    _restart_agent_service()

def handle_service_status(args):
    """Shows the agent service status."""
    try:
        subprocess.run(['sudo', 'systemctl', 'status', AGENT_SERVICE_NAME])
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Error getting agent service status: {e}")

def handle_logs(args):
    """Views recent agent logs."""
    try:
        cmd = ['sudo', 'journalctl', '-u', AGENT_SERVICE_NAME]
        if args.follow:
            cmd.append('-f')
        if args.lines:
            cmd.extend(['-n', str(args.lines)])
        subprocess.run(cmd)
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Error viewing logs: {e}")

def handle_version(args):
    """Shows the agent version."""
    if not os.path.exists(AGENT_VERSION_PATH):
        print(f"Error: Version file not found at {AGENT_VERSION_PATH}")
        return

    try:
        with open(AGENT_VERSION_PATH, 'r') as f:
            version_content = f.read()
        
        version_match = re.search(r"__version__\s*=\s*['\"]([^'\"]*)['\"]", version_content)
        if version_match:
            print(f"Cloudflare-Utils-Agent Version: {version_match.group(1)}")
        else:
            print("Could not determine agent version.")
    except IOError as e:
        print(f"Error reading version file: {e}")


def handle_stats(args):
    """Displays agent traffic/usage statistics."""
    if not _is_service_active():
        print("Agent service is not running. Please start it first.")
        return

    config = _read_agent_config()
    if not config or 'api_key' not in config:
        print("API key not found in agent configuration. Cannot fetch stats.")
        return

    api_key = config['api_key']
    port = config.get('port', 15728)
    url = f"http://127.0.0.1:{port}/usage"
    
    try:
        response = requests.get(url, headers={'X-API-Key': api_key}, timeout=5)
        response.raise_for_status()
        stats = response.json()

        def format_bytes(byte_count):
            if byte_count is None:
                return "N/A"
            power = 1024
            n = 0
            power_labels = {0: '', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
            while byte_count >= power and n < len(power_labels) -1 :
                byte_count /= power
                n += 1
            return f"{byte_count:.2f} {power_labels[n]}B"

        print("--- Agent Traffic Statistics ---")
        print(f"Interface: {stats.get('interface', 'N/A')}")
        
        today = stats.get('today', {})
        print("\nToday:")
        print(f"  Received:  {format_bytes(today.get('rx_bytes'))}")
        print(f"  Sent:      {format_bytes(today.get('tx_bytes'))}")
        print(f"  Total:     {format_bytes(today.get('total_bytes'))}")

        this_month = stats.get('this_month', {})
        print("\nThis Month:")
        print(f"  Received:  {format_bytes(this_month.get('rx_bytes'))}")
        print(f"  Sent:      {format_bytes(this_month.get('tx_bytes'))}")
        print(f"  Total:     {format_bytes(this_month.get('total_bytes'))}")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching stats from agent: {e}")


def handle_stats_reset(args):
    """Resets agent traffic/usage statistics."""
    config = _read_agent_config()
    if not config or 'vnstat_interface' not in config:
        print("vnstat interface not found in agent configuration. Cannot reset stats.")
        return

    interface = config['vnstat_interface']
    
    if not args.force:
        print(f"Warning: This will permanently delete the statistics for interface '{interface}'.")
        if input("Are you sure you want to continue? (y/N): ").lower() != 'y':
            print("Aborted.")
            return

    try:
        print(f"Resetting statistics for interface '{interface}'...")
        subprocess.run(['sudo', 'vnstat', '--delete', '--force', '-i', interface], check=True)
        print("Statistics reset successfully.")
        _restart_agent_service() # Restart to ensure vnstat re-initializes the interface
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Error resetting statistics: {e}")


def handle_config_display(args):
    """Displays the current configuration file."""
    config = _read_agent_config()
    if config:
        # Mask the API key for safety
        if 'api_key' in config:
            key = config['api_key']
            config['api_key'] = key[:4] + '*' * (len(key) - 8) + key[-4:] if len(key) > 8 else key[:2] + '*' * (len(key) - 4) + key[-2:]
        
        print(json.dumps(config, indent=2))

class HelpOnFailArgumentParser(argparse.ArgumentParser):
    """Custom ArgumentParser that prints help on error."""
    def error(self, message):
        sys.stderr.write(f'error: {message}\n')
        self.print_help()
        sys.exit(2)

def main():
    """Main function for the agent CLI."""
    parser = HelpOnFailArgumentParser(
        description="A CLI for managing the Cloudflare-Utils-Agent.",
        prog="cfu-agent"
    )
    # Token management
    # We are using a new variable for subparsers to use the custom class
    subparsers = parser.add_subparsers(dest='command', parser_class=HelpOnFailArgumentParser)

    parser_token = subparsers.add_parser('token',
                                         help='Manage agent API token',
                                         description='Manage the agent API token. Use "display" to see the current token or "change" to generate a new one.',
                                         epilog="""
Examples:
  cfu-agent token display
  cfu-agent token display --full
  cfu-agent token change --force
""")
    token_subparsers = parser_token.add_subparsers(dest='action', help='Action to perform', required=True)
    
    # cfu-agent token display
    parser_token_display = token_subparsers.add_parser('display', help='Display the current token (masked by default)',
                                                       description='Displays the current token. Shows a masked version by default for security.',
                                                       epilog="""
Example:
  cfu-agent token display
  cfu-agent token display --full
  cfu-agent token display --full --force
""")
    parser_token_display.add_argument('--full', action='store_true', help='Display the full, unmasked token with a confirmation warning.')
    parser_token_display.add_argument('--force', action='store_true', help='Skip the confirmation warning when displaying the full token.')
    parser_token_display.set_defaults(func=handle_token_display)

    # cfu-agent token change
    parser_token_change = token_subparsers.add_parser('change', help='Change token (revoke old, create new, show full)',
                                                      description='Revokes the current token, generates a new one, saves it, and restarts the agent.',
                                                      epilog="""
Example:
  cfu-agent token change
  cfu-agent token change --force
""")
    parser_token_change.add_argument('--force', action='store_true', help='Skip the confirmation prompt before changing the token.')
    parser_token_change.set_defaults(func=handle_token_change)


    # Service control
    parser_service = subparsers.add_parser('service', help='Control the agent service')
    service_subparsers = parser_service.add_subparsers(dest='action', help='Action to perform', required=True)
    parser_service_start = service_subparsers.add_parser('start', help='Start the agent service')
    parser_service_start.set_defaults(func=handle_service_start)
    parser_service_stop = service_subparsers.add_parser('stop', help='Stop the agent service')
    parser_service_stop.set_defaults(func=handle_service_stop)
    parser_service_restart = service_subparsers.add_parser('restart', help='Restart the agent service')
    parser_service_restart.set_defaults(func=handle_service_restart)
    parser_service_status = service_subparsers.add_parser('status', help='Show agent service status')
    parser_service_status.set_defaults(func=handle_service_status)

    # Logs
    parser_logs = subparsers.add_parser('logs', help='View agent logs')
    parser_logs.add_argument('-f', '--follow', action='store_true', help='Follow log output')
    parser_logs.add_argument('-n', '--lines', type=int, help='Number of lines to show')
    parser_logs.set_defaults(func=handle_logs)

    # Version
    parser_version = subparsers.add_parser('version', help='Show agent version')
    parser_version.set_defaults(func=handle_version)

    # Statistics
    parser_stats = subparsers.add_parser('stats', help='Display agent traffic/usage statistics')
    stats_subparsers = parser_stats.add_subparsers(dest='action', parser_class=HelpOnFailArgumentParser)
    parser_stats_reset = stats_subparsers.add_parser('reset', help='Reset statistics')
    parser_stats_reset.add_argument('--force', action='store_true', help='Reset without prompting for confirmation')
    parser_stats_reset.set_defaults(func=handle_stats_reset)
    parser_stats.set_defaults(func=handle_stats)


    # Configuration
    parser_config = subparsers.add_parser('config', help='Manage agent configuration')
    config_subparsers = parser_config.add_subparsers(dest='action', required=True, parser_class=HelpOnFailArgumentParser)
    parser_config_display = config_subparsers.add_parser('show', help='Display the current configuration file')
    parser_config_display.set_defaults(func=handle_config_display)

    # Help command
    parser_help = subparsers.add_parser('help', help='Show help for a specific command')
    parser_help.add_argument('help_command', nargs='?', help='The command to get help for')
    parser_help.set_defaults(func=lambda args: parser.parse_args([args.help_command, '--help'] if args.help_command else ['--help']))


    # If no command is provided, print help and exit.
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
        
    args = parser.parse_args()

    if hasattr(args, 'func'):
        args.func(args)

if __name__ == '__main__':
    main()