"""
Service Management for the Telegram Bot.

This module provides a ServiceManager class to handle the bot's lifecycle,
supporting both systemd and a fallback background process management.
"""
import os
import subprocess
import shutil
import time
import signal
from ..core.logger import logger

SERVICE_NAME = "cloudflare-utils-bot"
SERVICE_FILE_NAME = f"{SERVICE_NAME}.service"
SYSTEMD_PATH = "/etc/systemd/system/"
PID_DIR = "/var/run/cf-utils"
PID_FILE_PATH = os.path.join(PID_DIR, f"{SERVICE_NAME}.pid")
BOT_MODULE_PATH = "src.bot.main"
# The venv path is relative to the project root (/opt/Cloudflare-Utils/)
VENV_PYTHON_EXEC = "/opt/Cloudflare-Utils/venv/bin/python"

class ServiceManager:
    """
    Manages the lifecycle of the Telegram bot service.
    """
    def __init__(self):
        self._systemd_available = shutil.which("systemctl") is not None
        logger.info(f"Systemd available: {self._systemd_available}")

    @property
    def systemd_available(self):
        return self._systemd_available

    def get_status(self):
        """Gets the status of the bot service."""
        if self.systemd_available:
            return self._get_systemd_status()
        else:
            return self._get_fallback_status()

    # --- Systemd Methods ---

    def _run_systemctl_action(self, action, service_name=SERVICE_NAME):
        """Helper to run a systemctl action that should return a zero exit code on success."""
        try:
            cmd = ["systemctl", action, service_name]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info(f"Successfully ran systemctl command: {' '.join(cmd)}")
            return True, result.stdout.strip()
        except FileNotFoundError:
            logger.error("systemctl command not found.")
            return False, "systemctl command not found."
        except subprocess.CalledProcessError as e:
            error_message = e.stderr.strip()
            logger.error(f"Error running systemctl command: {' '.join(e.cmd)}. Error: {error_message}")
            return False, error_message

    def _get_systemd_status(self):
        """Returns the status of the systemd service."""
        try:
            # is-active
            result_active = subprocess.run(["systemctl", "is-active", SERVICE_NAME], capture_output=True, text=True)
            status_str = result_active.stdout.strip()

            # is-enabled
            result_enabled = subprocess.run(["systemctl", "is-enabled", SERVICE_NAME], capture_output=True, text=True)
            enabled_str = result_enabled.stdout.strip()
            
            return f"{status_str} ({enabled_str})"
        except FileNotFoundError:
            return "unknown (systemctl not found)"

    def install_service(self):
        """Installs and enables the systemd service."""
        source_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'bot', SERVICE_FILE_NAME))
        dest_path = os.path.join(SYSTEMD_PATH, SERVICE_FILE_NAME)
        
        if not os.path.exists(source_path):
            return False, f"Service file not found at {source_path}"
        
        try:
            shutil.copy(source_path, dest_path)
            logger.info(f"Copied service file from {source_path} to {dest_path}")
            self._run_systemctl_action("daemon-reload")
            self.enable_service()
            return True, f"Service '{SERVICE_NAME}' installed successfully."
        except Exception as e:
            logger.error(f"Failed to install service: {e}")
            return False, f"Failed to install service: {e}"

    def uninstall_service(self):
        """Stops, disables, and removes the systemd service."""
        self.stop_service()
        self.disable_service()
        dest_path = os.path.join(SYSTEMD_PATH, SERVICE_FILE_NAME)
        if os.path.exists(dest_path):
            try:
                os.remove(dest_path)
                self._run_systemctl_action("daemon-reload")
                logger.info(f"Removed service file: {dest_path}")
                return True, "Service uninstalled successfully."
            except Exception as e:
                logger.error(f"Failed to remove service file: {e}")
                return False, f"Failed to remove service file: {e}"
        return True, "Service was not installed."

    def start_service(self):
        """Starts the bot service."""
        if self.systemd_available:
            return self._run_systemctl_action("start")
        else:
            return self._start_fallback()

    def stop_service(self):
        """Stops the bot service."""
        if self.systemd_available:
            return self._run_systemctl_action("stop")
        else:
            return self._stop_fallback()

    def restart_service(self):
        """Restarts the bot service."""
        if self.systemd_available:
            return self._run_systemctl_action("restart")
        else:
            self.stop_service()
            time.sleep(1)
            return self.start_service()

    def enable_service(self):
        """Enables the systemd service to start on boot."""
        if self.systemd_available:
            return self._run_systemctl_action("enable")
        return False, "Not applicable without systemd."

    def disable_service(self):
        """Disables the systemd service from starting on boot."""
        if self.systemd_available:
            return self._run_systemctl_action("disable")
        return False, "Not applicable without systemd."

    # --- Fallback Methods ---

    def _get_pid(self):
        """Gets the PID from the PID file."""
        if os.path.exists(PID_FILE_PATH):
            try:
                with open(PID_FILE_PATH, 'r') as f:
                    return int(f.read().strip())
            except (IOError, ValueError):
                return None
        return None

    def _is_process_running(self, pid):
        """Checks if a process with the given PID is running."""
        if pid is None:
            return False
        try:
            os.kill(pid, 0)
        except OSError:
            return False
        else:
            return True

    def _get_fallback_status(self):
        """Returns the status of the fallback service."""
        pid = self._get_pid()
        if self._is_process_running(pid):
            return f"running (pid: {pid})"
        else:
            return "stopped"

    def _start_fallback(self):
        """Starts the bot as a background process."""
        if self._is_process_running(self._get_pid()):
            return False, "Service is already running."

        if not os.path.exists(PID_DIR):
            os.makedirs(PID_DIR, exist_ok=True)
        
        if os.path.exists(VENV_PYTHON_EXEC):
            python_executable = VENV_PYTHON_EXEC
        else:
            python_executable = shutil.which("python3") or shutil.which("python")

        if not python_executable:
            return False, "Could not find a python executable."

        command = [python_executable, "-m", BOT_MODULE_PATH]
        
        try:
            # Using start_new_session=True to detach the process from the current terminal
            process = subprocess.Popen(command, start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            with open(PID_FILE_PATH, 'w') as f:
                f.write(str(process.pid))
            logger.info(f"Started fallback service with PID: {process.pid}")
            return True, f"Service started with PID {process.pid}."
        except Exception as e:
            logger.error(f"Failed to start fallback service: {e}")
            return False, f"Failed to start fallback service: {e}"

    def _stop_fallback(self):
        """Stops the background process."""
        pid = self._get_pid()
        if not self._is_process_running(pid):
            return True, "Service is not running."
        
        try:
            os.kill(pid, signal.SIGTERM)
            if os.path.exists(PID_FILE_PATH):
                os.remove(PID_FILE_PATH)
            logger.info(f"Stopped fallback service with PID: {pid}")
            return True, "Service stopped."
        except Exception as e:
            logger.error(f"Failed to stop fallback service: {e}")
            return False, f"Failed to stop fallback service: {e}"

# Singleton instance
service_manager = ServiceManager()