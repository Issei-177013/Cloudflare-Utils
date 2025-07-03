import typer
from rich.console import Console
from rich.table import Table
import os
import subprocess
import sys

# Attempt to import InquirerPy, provide guidance if not found
try:
    from InquirerPy import prompt as i_prompt
    from InquirerPy.validator import PathValidator
    INQUIRERPY_AVAILABLE = True
except ImportError:
    INQUIRERPY_AVAILABLE = False

app = typer.Typer(
    name="cfu-manager",
    help="Cloudflare Utils Manager: Install, configure, and manage Cloudflare-Utils instances.",
    add_completion=False
)
console = Console()

# --- Configuration & Constants ---
BASE_INSTALL_DIR = "/opt"
APP_NAME_BASE = "Cloudflare-Utils"
CFU_MAIN_REPO_URL = "https://github.com/Issei-177013/Cloudflare-Utils.git"
INSTALL_SCRIPT_NAME = "install.sh" # The script within the Cloudflare-Utils repo

# --- Helper Functions ---
def get_instance_dir(branch_name: str = None) -> str:
    """Determines the directory for a given branch/instance."""
    if not branch_name or branch_name.lower() == "main":
        return f"{BASE_INSTALL_DIR}/{APP_NAME_BASE}"
    
    sanitized_branch_name = "".join(c if c.isalnum() or c in ['_','-'] else '_' for c in branch_name)
    return f"{BASE_INSTALL_DIR}/{APP_NAME_BASE}-{sanitized_branch_name}"

def get_instance_name(branch_name: str = None) -> str:
    if not branch_name or branch_name.lower() == "main":
        return APP_NAME_BASE
    sanitized_branch_name = "".join(c if c.isalnum() or c in ['_','-'] else '_' for c in branch_name)
    return f"{APP_NAME_BASE}-{sanitized_branch_name}"

def is_instance_installed(branch_name: str = None) -> bool:
    """Checks if a specific instance is installed by looking for its directory and run.sh script."""
    instance_dir = get_instance_dir(branch_name)
    # A more reliable check could be the presence of '.venv/bin/activate' or 'run.sh'
    return os.path.isdir(instance_dir) and os.path.isfile(os.path.join(instance_dir, "run.sh"))

def _run_command(command: list[str], error_message: str, success_message: str = None):
    """Helper to run subprocess commands."""
    try:
        # Use Popen to stream output in real-time if needed, or run for simpler cases
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()

        if process.returncode == 0:
            if success_message:
                console.print(f"[green]SUCCESS:[/] {success_message}")
            if stdout:
                console.print(f"[dim]{stdout}[/dim]")
            return True
        else:
            console.print(f"[bold red]ERROR:[/] {error_message}")
            console.print(f"[red]Return Code: {process.returncode}[/red]")
            if stdout:
                console.print(f"[bold]Stdout:[/]\n{stdout}")
            if stderr:
                console.print(f"[bold red]Stderr:[/]\n{stderr}")
            return False
    except FileNotFoundError:
        console.print(f"[bold red]ERROR:[/] Command not found: {command[0]}. Is it in PATH or installed?")
        return False
    except Exception as e:
        console.print(f"[bold red]ERROR:[/] An unexpected error occurred: {e}")
        return False

def _get_install_script_path() -> str | None:
    """
    Attempts to locate the install.sh script.
    This is tricky as cfu-manager itself is installed from the repo.
    Strategy:
    1. If cfu-manager is running from a venv inside a cloned repo (dev setup), find it relative to this script.
    2. If cfu-manager is installed globally, it might need to download install.sh from the repo.
    """
    # Strategy 1: Check if running from a local dev setup
    # __file__ points to src/cloudflare_utils_manager/main.py
    # project_root would be two levels up from __file__'s directory
    try:
        current_script_path = os.path.abspath(__file__)
        manager_dir = os.path.dirname(current_script_path) # .../cloudflare_utils_manager
        src_dir = os.path.dirname(manager_dir) # .../src
        project_root = os.path.dirname(src_dir) # project root

        # Check if install.sh exists at project_root/install.sh
        potential_path = os.path.join(project_root, INSTALL_SCRIPT_NAME)
        if os.path.isfile(potential_path):
            console.print(f"[debug]Found '{INSTALL_SCRIPT_NAME}' at: {potential_path}[/debug]", style="dim")
            return potential_path
    except Exception:
        pass # Could not determine path this way

    # Strategy 2: Fallback - could involve downloading, or assuming install.sh is bundled/accessible.
    # For now, if not found locally, we might have to ask the user or fail.
    # This is a key part that makes `cfu-manager` able to install new instances.
    # The original install.sh (one-liner) installs cfu-manager.
    # For cfu-manager to install *another* instance, it needs access to that instance's install.sh.
    # Best approach: cfu-manager should clone the target branch to a temp dir, then run its install.sh.
    console.print(f"[yellow]Warning: Could not locate '{INSTALL_SCRIPT_NAME}' relative to cfu-manager script.[/yellow]")
    console.print(f"[yellow]Will attempt to use 'git archive' or direct download for installations.[/yellow]")
    return None # Indicates that install.sh needs to be fetched

# --- Typer Commands ---

@app.command()
def install(
    branch: str = typer.Option("main", help="Branch to install from GitHub (e.g., main, dev).", prompt="Enter branch to install (default: main)"),
    api_token: str = typer.Option(None, help="Cloudflare API Token (interactive if not set)."),
    zone_id: str = typer.Option(None, help="Cloudflare Zone ID (interactive if not set)."),
    record_names: str = typer.Option(None, help="Cloudflare Record Name(s), comma-separated (interactive if not set)."),
    ip_addresses: str = typer.Option(None, help="Cloudflare IP Addresses, comma-separated (interactive if not set)."),
    non_interactive: bool = typer.Option(False, "--non-interactive", help="Run in non-interactive mode (requires all params)."),
    scheduler: str = typer.Option("interactive", help="Scheduler type: cron, systemd, or interactive.", case_sensitive=False)
):
    """
    Install a new instance of Cloudflare-Utils or reinstall/update an existing one.
    This command will download the specified branch's install.sh and execute it.
    """
    instance_name = get_instance_name(branch)
    instance_dir = get_instance_dir(branch)
    console.print(f"Initiating installation for [bold cyan]{instance_name}[/] (branch: [green]{branch}[/]).")
    console.print(f"Target directory: [magenta]{instance_dir}[/]")

    if non_interactive and not all([api_token, zone_id, record_names, ip_addresses]):
        console.print("[bold red]ERROR:[/] For non-interactive installation, all Cloudflare parameters must be provided (--api-token, --zone-id, --record-names, --ip-addresses).")
        raise typer.Exit(code=1)

    if scheduler.lower() not in ["cron", "systemd", "interactive"]:
        console.print(f"[bold red]ERROR:[/] Invalid scheduler type '{scheduler}'. Must be 'cron', 'systemd', or 'interactive'.")
        raise typer.Exit(code=1)
    
    temp_install_script_path = os.path.join(f"/tmp/{INSTALL_SCRIPT_NAME}")

    console.print(f"Attempting to download '{INSTALL_SCRIPT_NAME}' for branch '{branch}'...")
    # Use curl to download the specific branch's install.sh
    # curl -fsSL -o /tmp/install.sh https://raw.githubusercontent.com/Issei-177013/Cloudflare-Utils/<branch>/install.sh
    download_url = f"https://raw.githubusercontent.com/Issei-177013/Cloudflare-Utils/{branch}/{INSTALL_SCRIPT_NAME}"
    curl_cmd = ["curl", "-fsSL", "-o", temp_install_script_path, download_url]
    
    process = subprocess.run(curl_cmd)
    if process.returncode != 0:
        console.print(f"[bold red]ERROR:[/] Failed to download '{INSTALL_SCRIPT_NAME}' from branch '{branch}'. Please check branch name and network.")
        if os.path.exists(temp_install_script_path):
            os.remove(temp_install_script_path)
        raise typer.Exit(code=1)
    
    console.print(f"Successfully downloaded '{INSTALL_SCRIPT_NAME}' to '{temp_install_script_path}'.")
    os.chmod(temp_install_script_path, 0o755) # Make it executable

    # Construct the command to run the downloaded install.sh
    # sudo bash /tmp/install.sh --action install --branch <branch> [--non-interactive --api-token ... --scheduler cron/systemd]
    command = ["sudo", "bash", temp_install_script_path, "--action", "install"]
    if branch.lower() != "main": # install.sh defaults to main if --branch not given
        command.extend(["--branch", branch])

    if non_interactive:
        command.append("--non-interactive")
        command.extend(["--api-token", api_token, "--zone-id", zone_id, "--record-name", record_names, "--ip-addresses", ip_addresses])
        if scheduler.lower() != "interactive": # install.sh handles interactive scheduler choice by default
             # Current install.sh non-interactive defaults to cron. If we want to specify, it needs an arg.
             # For now, assume install.sh will be updated to accept --scheduler in non-interactive mode
             # Or, we just let it default to cron for non-interactive via manager.
             # Let's assume current install.sh defaults to cron for non-interactive, and interactive if not.
             if scheduler.lower() == "systemd":
                 console.print("[yellow]Note: Non-interactive systemd choice via manager depends on install.sh supporting a --scheduler flag. Defaulting to install.sh behavior.[/yellow]")
                 # command.extend(["--scheduler", "systemd"]) # If install.sh supports this
    elif scheduler.lower() != "interactive":
        console.print(f"[yellow]Scheduler '{scheduler}' selected, but will be chosen interactively by install.sh unless in --non-interactive mode.[/yellow]")


    console.print(f"\n[bold]Executing downloaded '{INSTALL_SCRIPT_NAME}' for branch '{branch}':[/]")
    console.print(f"[dim]$ {' '.join(command)}[/dim]\n")
    console.print(f"You may be prompted for your sudo password and configuration details if running interactively.")

    try:
        # Run the script; it will handle its own output.
        subprocess.run(command, check=True)
        console.print(f"\n[green]SUCCESS:[/] Installation/Update for branch '{branch}' initiated by '{INSTALL_SCRIPT_NAME}'.")
        console.print("Please check its output for details.")
    except subprocess.CalledProcessError as e:
        console.print(f"[bold red]ERROR:[/] '{INSTALL_SCRIPT_NAME}' failed for branch '{branch}'.")
        console.print(f"[red]Return Code: {e.returncode}[/red]")
    except FileNotFoundError: # Should not happen if download succeeded
        console.print(f"[bold red]ERROR:[/] Temporary install script '{temp_install_script_path}' not found.")
    finally:
        if os.path.exists(temp_install_script_path):
            os.remove(temp_install_script_path)


@app.command()
def uninstall(
    branch: str = typer.Option(..., help="Branch to uninstall.", prompt="Enter branch to uninstall (e.g., main, dev)")
):
    """Uninstall an instance of Cloudflare-Utils by executing its install.sh --action remove."""
    instance_name = get_instance_name(branch)
    instance_dir = get_instance_dir(branch)

    if not is_instance_installed(branch): # Basic check, install.sh will do a more thorough one
        console.print(f"[yellow]Warning:[/] Instance [bold cyan]{instance_name}[/] at [magenta]{instance_dir}[/] does not seem to be fully installed or was already removed.")
        # Ask if user wants to proceed anyway, install.sh might clean up remnants
        if not typer.confirm(f"Do you want to attempt to run uninstall for '{instance_name}' anyway?", default=False):
            raise typer.Exit()

    console.print(f"Initiating uninstallation for [bold cyan]{instance_name}[/] (branch: [green]{branch}[/]).")

    temp_install_script_path = os.path.join(f"/tmp/{INSTALL_SCRIPT_NAME}")
    
    # Determine which install.sh to use for uninstall.
    # Ideally, use the install.sh from the branch itself if available, or fallback to main's.
    # For simplicity, we'll download the specified branch's install.sh to run its own uninstall logic.
    # This ensures branch-specific uninstall steps (if any) are respected.
    console.print(f"Attempting to download '{INSTALL_SCRIPT_NAME}' for branch '{branch}' to perform uninstallation...")
    download_url = f"https://raw.githubusercontent.com/Issei-177013/Cloudflare-Utils/{branch}/{INSTALL_SCRIPT_NAME}"
    curl_cmd = ["curl", "-fsSL", "-o", temp_install_script_path, download_url]
    
    process = subprocess.run(curl_cmd)
    if process.returncode != 0:
        # Fallback to main branch's install.sh if specified branch's doesn't exist (e.g. remote branch deleted)
        console.print(f"[yellow]Warning:[/] Failed to download '{INSTALL_SCRIPT_NAME}' from branch '{branch}'. Trying 'main' branch's script.")
        download_url = f"https://raw.githubusercontent.com/Issei-177013/Cloudflare-Utils/main/{INSTALL_SCRIPT_NAME}"
        curl_cmd = ["curl", "-fsSL", "-o", temp_install_script_path, download_url]
        process = subprocess.run(curl_cmd)
        if process.returncode != 0:
            console.print(f"[bold red]ERROR:[/] Failed to download '{INSTALL_SCRIPT_NAME}' from 'main' branch either. Cannot proceed with uninstall.")
            if os.path.exists(temp_install_script_path):
                os.remove(temp_install_script_path)
            raise typer.Exit(code=1)

    console.print(f"Successfully downloaded '{INSTALL_SCRIPT_NAME}' to '{temp_install_script_path}'.")
    os.chmod(temp_install_script_path, 0o755)

    command = ["sudo", "bash", temp_install_script_path, "--action", "remove"]
    if branch.lower() != "main":
         command.extend(["--branch", branch])
    # Non-interactive for remove is implicit in install.sh if --action remove is given.

    console.print(f"\n[bold]Executing downloaded '{INSTALL_SCRIPT_NAME}' for uninstall of branch '{branch}':[/]")
    console.print(f"[dim]$ {' '.join(command)}[/dim]\n")
    console.print(f"You may be prompted for your sudo password.")

    try:
        subprocess.run(command, check=True)
        console.print(f"\n[green]SUCCESS:[/] Uninstallation for branch '{branch}' initiated by '{INSTALL_SCRIPT_NAME}'.")
    except subprocess.CalledProcessError as e:
        console.print(f"[bold red]ERROR:[/] '{INSTALL_SCRIPT_NAME}' failed during uninstall for branch '{branch}'.")
        console.print(f"[red]Return Code: {e.returncode}[/red]")
    except FileNotFoundError:
        console.print(f"[bold red]ERROR:[/] Temporary install script '{temp_install_script_path}' not found.")
    finally:
        if os.path.exists(temp_install_script_path):
            os.remove(temp_install_script_path)


@app.command(name="list")
def list_installed():
    """List all detected Cloudflare-Utils instances."""
    console.print(f"Scanning for installed instances in [magenta]{BASE_INSTALL_DIR}[/]...")
    table = Table(title="Installed Cloudflare-Utils Instances", show_lines=True)
    table.add_column("Instance Name", style="cyan", overflow="fold")
    table.add_column("Branch Name", style="green", overflow="fold")
    table.add_column("Path", style="magenta", overflow="fold")
    table.add_column("Status", style="yellow")
    table.add_column("Python Version", style="blue")
    table.add_column("CFU Version", style="blue")

    found_instances_count = 0
    try:
        if not os.path.isdir(BASE_INSTALL_DIR):
            console.print(f"[yellow]Base installation directory {BASE_INSTALL_DIR} not found.[/yellow]")
            return

        for item in os.listdir(BASE_INSTALL_DIR):
            item_path = os.path.join(BASE_INSTALL_DIR, item)
            if os.path.isdir(item_path) and item.startswith(APP_NAME_BASE):
                instance_name = item
                branch_name = "main" # Default if not suffixed
                if item == APP_NAME_BASE:
                    pass # It's the main default instance
                elif item.startswith(APP_NAME_BASE + "-"):
                    branch_name = item[len(APP_NAME_BASE)+1:]
                
                status = []
                py_version = "N/A"
                cfu_version = "N/A"

                if not os.path.isfile(os.path.join(item_path, "run.sh")):
                    status.append("[red]run.sh missing[/red]")
                if not os.path.isdir(os.path.join(item_path, ".venv")):
                    status.append("[red].venv missing[/red]")
                else:
                    status.append("[green]OK[/green]")
                    # Try to get Python version from venv
                    py_exe = os.path.join(item_path, ".venv/bin/python")
                    if os.path.isfile(py_exe):
                        try:
                            result = subprocess.run([py_exe, "--version"], capture_output=True, text=True, check=False)
                            py_version = result.stdout.strip() or result.stderr.strip()
                             # Try to get cloudflare-utils version
                            result_cfu = subprocess.run([os.path.join(item_path,".venv/bin/pip"), "show", "cloudflare-utils"], capture_output=True, text=True, check=False)
                            if result_cfu.returncode == 0:
                                for line in result_cfu.stdout.splitlines():
                                    if line.startswith("Version:"):
                                        cfu_version = line.split(":")[1].strip()
                                        break
                        except Exception:
                            py_version = "[red]Error[/red]"
                            cfu_version = "[red]Error[/red]"


                if not status: status.append("[yellow]Unknown[/yellow]")
                
                table.add_row(instance_name, branch_name, item_path, ", ".join(status), py_version, cfu_version)
                found_instances_count +=1
            
        if not found_instances_count:
            console.print("No Cloudflare-Utils instances found.")
        else:
            console.print(table)

    except Exception as e:
        console.print(f"[bold red]Error scanning for instances: {e}[/bold red]")

# --- Menu System ---
def _ensure_inquirerpy():
    if not INQUIRERPY_AVAILABLE:
        console.print("[bold yellow]Interactive menu requires 'InquirerPy'.[/bold yellow]")
        console.print("Please install it: pip install inquirerpy")
        console.print("Or install cfu-manager with all extras: pip install cloudflare-utils[manager] (if 'manager' extra is defined in pyproject.toml)")
        raise typer.Exit(code=1)

@app.command(name="menu")
def main_menu():
    """Open an interactive menu to manage Cloudflare-Utils."""
    _ensure_inquirerpy()
    console.print("\n[bold blue]Welcome to the Cloudflare-Utils Interactive Manager![/bold blue]\n")

    while True:
        questions = [
            {
                "type": "list",
                "message": "What would you like to do?",
                "choices": [
                    "Install New Instance / Reinstall Existing",
                    "Uninstall Instance",
                    "List Installed Instances",
                    "Update Instance",
                    "Rollback Instance (simple)",
                    # "Manage Configuration (TODO)",
                    # "Run Instance Manually (TODO)",
                    # "View Logs (TODO)",
                    # "Manage Scheduler (TODO)",
                    "Exit"
                ],
                "default": "List Installed Instances",
                "name": "main_action",
                "cycle": False,
            }
        ]
        try:
            answers = i_prompt(questions=questions, vi_mode=True)
            if not answers: # User might have Ctrl+C'd
                console.print("[yellow]Operation cancelled.[/yellow]")
                break
            action = answers.get("main_action")
        except KeyboardInterrupt:
            console.print("[yellow]\nOperation cancelled by user.[/yellow]")
            break

        if action == "Install New Instance / Reinstall Existing":
            try:
                branch = i_prompt([{"type": "input", "message": "Enter branch name to install/reinstall:", "default": "main", "name":"branch"}])["branch"]
                
                is_non_interactive = not i_prompt([{"type":"confirm", "message":"Configure interactively via install.sh prompts?", "default":True, "name":"interactive_install"}])["interactive_install"]
                api_token, zone_id, record_names, ip_addresses, scheduler_choice = None, None, None, None, "interactive"

                if is_non_interactive:
                    params = i_prompt([
                        {"type":"input", "message":"Cloudflare API Token:", "name":"api"},
                        {"type":"input", "message":"Cloudflare Zone ID:", "name":"zone"},
                        {"type":"input", "message":"Record Names (comma-separated):", "name":"records"},
                        {"type":"input", "message":"IP Addresses (comma-separated):", "name":"ips"},
                        {"type":"list", "message":"Scheduler (install.sh default is cron for non-interactive):", "choices":["cron", "systemd"], "default":"cron", "name":"sched"}
                    ])
                    api_token, zone_id, record_names, ip_addresses, scheduler_choice = params["api"], params["zone"], params["records"], params["ips"], params["sched"]
                
                install(branch, api_token, zone_id, record_names, ip_addresses, is_non_interactive, scheduler_choice)
            except (KeyboardInterrupt, Exception) as e:
                console.print(f"[yellow]Installation cancelled or failed: {e}[/yellow]")

        elif action == "Uninstall Instance":
            try:
                # TODO: Could list available branches first
                branch = i_prompt([{"type": "input", "message": "Enter branch name to uninstall:", "name":"branch"}])["branch"]
                if branch and typer.confirm(f"Are you sure you want to uninstall instance for branch '{branch}'?", default=False):
                    uninstall(branch)
            except (KeyboardInterrupt, Exception) as e:
                console.print(f"[yellow]Uninstallation cancelled or failed: {e}[/yellow]")
        
        elif action == "List Installed Instances":
            list_installed()

        elif action == "Update Instance":
            try:
                # TODO: Could list available branches first for selection
                branch_to_update = i_prompt([{"type": "input", "message": "Enter branch name to update:", "name":"branch"}])["branch"]
                if branch_to_update:
                    if not is_instance_installed(branch_to_update): # Prompt before calling if not installed
                        console.print(f"[yellow]Instance for branch '{branch_to_update}' does not seem to be installed. Cannot update.[/yellow]")
                    else:
                        update(branch=branch_to_update, restart_scheduler=True) 
            except (KeyboardInterrupt, typer.Exit):
                console.print("[yellow]Update cancelled.[/yellow]")
            except Exception as e:
                console.print(f"[bold red]An error occurred during update: {e}[/bold red]")


        elif action == "Rollback Instance (simple)":
            try:
                # TODO: Could list available branches first for selection
                branch_to_rollback = i_prompt([{"type": "input", "message": "Enter branch name to roll back:", "name":"branch"}])["branch"]
                if branch_to_rollback:
                    if not is_instance_installed(branch_to_rollback):
                         console.print(f"[yellow]Instance for branch '{branch_to_rollback}' does not seem to be installed. Cannot roll back.[/yellow]")
                    else:
                        steps_to_rollback_q = i_prompt([{"type": "input", "message": "How many commits to go back (e.g., 1 for last commit)?", "default":"1", "validate": lambda text: text.isdigit() and int(text) > 0, "name":"steps"}])
                        if steps_to_rollback_q: # Check if user provided input (didn't Ctrl+C)
                            steps_to_rollback = steps_to_rollback_q["steps"]
                            rollback(branch=branch_to_rollback, steps=int(steps_to_rollback), restart_scheduler=True)
            except (KeyboardInterrupt, typer.Exit):
                console.print("[yellow]Rollback cancelled.[/yellow]")
            except Exception as e:
                console.print(f"[bold red]An error occurred during rollback: {e}[/bold red]")

        elif action == "Exit":
            console.print("Exiting cfu-manager.")
            break
        else:
            console.print(f"Action '{action}' selected. Implementation pending for: {action}")
        
        if action != "Exit":
            try:
                if not i_prompt([{"type":"confirm", "message":"\nReturn to main menu?", "default":True, "name":"rtm"}])["rtm"]:
                    break
            except (KeyboardInterrupt, typer.Exit): # Handle Ctrl+C on the confirm prompt
                console.print("[yellow]\nExiting cfu-manager.[/yellow]")
                break
            except Exception: # Catch other potential errors from i_prompt if it was force closed
                console.print("[yellow]\nExiting cfu-manager.[/yellow]")
                break


@app.command()
def update(
    branch: str = typer.Option(..., help="Branch instance to update.", prompt="Enter branch to update (e.g., main, dev)"),
    restart_scheduler: bool = typer.Option(True, help="Automatically restart the scheduler (if active) after update.")
):
    """
    Update an existing Cloudflare-Utils instance to the latest version from its branch.
    This involves git pull and reinstalling the package in its virtual environment.
    """
    instance_name = get_instance_name(branch)
    instance_dir = get_instance_dir(branch)

    console.print(f"Initiating update for [bold cyan]{instance_name}[/] (branch: [green]{branch}[/]) at [magenta]{instance_dir}[/magenta].")

    if not is_instance_installed(branch):
        console.print(f"[bold red]ERROR:[/] Instance [bold cyan]{instance_name}[/] does not appear to be installed at [magenta]{instance_dir}[/magenta].")
        console.print(f"Please install it first using 'cfu-manager install --branch {branch}'.")
        raise typer.Exit(code=1)

    # 1. Git Pull
    console.print(f"Attempting 'git pull' in [magenta]{instance_dir}[/]...")
    
    # Determine owner of instance_dir for running git commands correctly
    try:
        dir_stat = os.stat(instance_dir)
        dir_owner_uid = dir_stat.st_uid
        dir_owner_name = pwd.getpwuid(dir_owner_uid).pw_name
    except Exception as e:
        console.print(f"[yellow]Warning: Could not determine owner of {instance_dir}. Will attempt git pull as current user. Error: {e}[/yellow]")
        dir_owner_name = os.getlogin() # Fallback to current user

    git_pull_cmd_prefix = []
    if os.geteuid() == 0 and dir_owner_name != "root": # If manager is run as root, but dir is user-owned
        git_pull_cmd_prefix = ["sudo", "-u", dir_owner_name]
    
    git_pull_cmd = git_pull_cmd_prefix + ["git", "-C", instance_dir, "pull"]
    
    pull_process = subprocess.Popen(git_pull_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=instance_dir)
    pull_stdout, pull_stderr = pull_process.communicate()

    if pull_process.returncode == 0:
        console.print(f"[green]SUCCESS:[/] 'git pull' completed for [bold cyan]{instance_name}[/].")
        if pull_stdout: console.print(f"[dim]{pull_stdout}[/dim]")
    else:
        console.print(f"[bold red]ERROR:[/] 'git pull' failed for [bold cyan]{instance_name}[/].")
        if pull_stdout: console.print(f"[bold]Stdout:[/]\n{pull_stdout}")
        if pull_stderr: console.print(f"[bold red]Stderr:[/]\n{pull_stderr}")
        raise typer.Exit(code=1)

    # 2. Pip Install in venv
    console.print(f"Reinstalling package in virtual environment for [bold cyan]{instance_name}[/]...")
    venv_python_exe = os.path.join(instance_dir, ".venv/bin/python")
    
    pip_install_cmd_prefix = []
    if os.geteuid() == 0 and dir_owner_name != "root":
         pip_install_cmd_prefix = ["sudo", "-u", dir_owner_name]

    pip_install_cmd = pip_install_cmd_prefix + [
        venv_python_exe,
        "-m", "pip", "install", "--no-cache-dir", "--ignore-installed", "."
    ]
    
    install_process = subprocess.Popen(pip_install_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=instance_dir)
    install_stdout, install_stderr = install_process.communicate()

    if install_process.returncode == 0:
        console.print(f"[green]SUCCESS:[/] Package reinstalled successfully for [bold cyan]{instance_name}[/].")
        if install_stdout: console.print(f"[dim]{install_stdout}[/dim]")
    else:
        console.print(f"[bold red]ERROR:[/] Package reinstallation failed for [bold cyan]{instance_name}[/].")
        if install_stdout: console.print(f"[bold]Stdout:[/]\n{install_stdout}")
        if install_stderr: console.print(f"[bold red]Stderr:[/]\n{install_stderr}")
    
    if restart_scheduler:
        console.print(f"Attempting to restart scheduler for [bold cyan]{instance_name}[/] (if active)...")
        console.print("[yellow]Scheduler restart functionality is TODO. Please manually restart if needed.[/yellow]")

    console.print(f"\nUpdate process for [bold cyan]{instance_name}[/] finished.")


@app.command()
def rollback(
    branch: str = typer.Option(..., help="Branch instance to roll back.", prompt="Enter branch to roll back (e.g., main, dev)"),
    steps: int = typer.Option(1, "--steps", min=1, help="Number of commits to go back (HEAD~<steps>)."),
    restart_scheduler: bool = typer.Option(True, help="Automatically restart the scheduler (if active) after rollback.")
):
    """
    Roll back an instance to a previous commit (simple version: HEAD~<steps>).
    This involves git reset --hard HEAD~<steps> and reinstalling the package.
    WARNING: This is a hard reset and will discard uncommitted local changes.
    """
    instance_name = get_instance_name(branch)
    instance_dir = get_instance_dir(branch)

    console.print(f"Initiating rollback for [bold cyan]{instance_name}[/] (branch: [green]{branch}[/]) at [magenta]{instance_dir}[/magenta].")
    console.print(f"[bold yellow]WARNING:[/] This will perform 'git reset --hard HEAD~{steps}' in {instance_dir}.")
    console.print("[bold yellow]This will discard any uncommitted local changes in that directory.[/bold yellow]")
    
    if not INQUIRERPY_AVAILABLE : # Fallback if InquirerPy is not available for confirm
        if input("Are you sure you want to proceed? (yes/no): ").lower() != "yes":
            console.print("Rollback aborted by user.")
            raise typer.Exit()
    elif not i_prompt([{"type":"confirm", "message":"Are you sure you want to proceed with this rollback?", "default":False, "name":"rb_confirm"}])["rb_confirm"]:
        console.print("Rollback aborted by user.")
        raise typer.Exit()


    if not is_instance_installed(branch):
        console.print(f"[bold red]ERROR:[/] Instance [bold cyan]{instance_name}[/] does not appear to be installed at [magenta]{instance_dir}[/magenta].")
        raise typer.Exit(code=1)

    try:
        dir_stat = os.stat(instance_dir)
        dir_owner_uid = dir_stat.st_uid
        dir_owner_name = pwd.getpwuid(dir_owner_uid).pw_name
    except Exception as e:
        console.print(f"[yellow]Warning: Could not determine owner of {instance_dir}. Will attempt git reset as current user. Error: {e}[/yellow]")
        dir_owner_name = os.getlogin()

    git_cmd_prefix = []
    if os.geteuid() == 0 and dir_owner_name != "root":
        git_cmd_prefix = ["sudo", "-u", dir_owner_name]

    # 1. Git Reset
    console.print(f"Attempting 'git reset --hard HEAD~{steps}' in [magenta]{instance_dir}[/]...")
    git_reset_cmd = git_cmd_prefix + ["git", "-C", instance_dir, "reset", "--hard", f"HEAD~{steps}"]
    
    reset_process = subprocess.Popen(git_reset_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=instance_dir)
    reset_stdout, reset_stderr = reset_process.communicate()

    if reset_process.returncode == 0:
        console.print(f"[green]SUCCESS:[/] 'git reset --hard HEAD~{steps}' completed for [bold cyan]{instance_name}[/].")
        if reset_stdout: console.print(f"[dim]{reset_stdout}[/dim]")
    else:
        console.print(f"[bold red]ERROR:[/] 'git reset' failed for [bold cyan]{instance_name}[/].")
        if reset_stdout: console.print(f"[bold]Stdout:[/]\n{reset_stdout}")
        if reset_stderr: console.print(f"[bold red]Stderr:[/]\n{reset_stderr}")
        raise typer.Exit(code=1)
    
    # Fetch latest tags after reset, in case the reset went too far back from a tag.
    # This helps if we want to checkout a specific tag later.
    git_fetch_tags_cmd = git_cmd_prefix + ["git", "-C", instance_dir, "fetch", "--tags", "origin"]
    subprocess.run(git_fetch_tags_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=instance_dir)


    # 2. Pip Install in venv
    console.print(f"Reinstalling package in virtual environment for [bold cyan]{instance_name}[/] after rollback...")
    venv_python_exe = os.path.join(instance_dir, ".venv/bin/python")
    
    pip_install_cmd_prefix = []
    if os.geteuid() == 0 and dir_owner_name != "root":
         pip_install_cmd_prefix = ["sudo", "-u", dir_owner_name]

    pip_install_cmd = pip_install_cmd_prefix + [
        venv_python_exe,
        "-m", "pip", "install", "--no-cache-dir", "--ignore-installed", "--force-reinstall", "."
    ]
    install_process = subprocess.Popen(pip_install_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=instance_dir)
    install_stdout, install_stderr = install_process.communicate()
    
    if install_process.returncode == 0:
        console.print(f"[green]SUCCESS:[/] Package reinstalled successfully for [bold cyan]{instance_name}[/].")
        if install_stdout: console.print(f"[dim]{install_stdout}[/dim]")
    else:
        console.print(f"[bold red]ERROR:[/] Package reinstallation failed for [bold cyan]{instance_name}[/].")
        if install_stdout: console.print(f"[bold]Stdout:[/]\n{install_stdout}")
        if install_stderr: console.print(f"[bold red]Stderr:[/]\n{install_stderr}")

    if restart_scheduler:
        console.print(f"Attempting to restart scheduler for [bold cyan]{instance_name}[/] (if active)...")
        console.print("[yellow]Scheduler restart functionality is TODO. Please manually restart if needed.[/yellow]")

    console.print(f"\nRollback process for [bold cyan]{instance_name}[/] finished.")


if __name__ == "__main__":
    # This is primarily for development. When installed, `cfu-manager` command (from pyproject.toml) is used.
    # To make `python src/cloudflare_utils_manager/main.py` work easily from project root during dev:
    # Add project root to sys.path so it can find `cloudflare_utils_manager` module if not installed in editable mode.
    if not os.path.dirname(os.path.dirname(os.path.abspath(__file__))) in sys.path:
         sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    app()
