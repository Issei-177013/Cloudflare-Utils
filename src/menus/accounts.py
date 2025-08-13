"""
Account Management Menu.

This module provides the user interface and logic for managing Cloudflare
accounts within the application. It allows users to add, edit, list, and
delete accounts from the configuration.
"""
from ..config import load_config, validate_and_save_config, find_account
from ..cloudflare_api import CloudflareAPI
from ..dns_manager import edit_account_in_config, delete_account_from_config
from ..input_helper import get_validated_input
from ..logger import logger
from ..display import display_as_table, display_token_guidance
from ..error_handler import MissingPermissionError
from cloudflare import APIError
from .utils import clear_screen, select_from_list, confirm_action

def add_account():
    """
    Guides the user through adding a new Cloudflare account.

    This function prompts the user for an account name and an API token.
    It validates the token by making a test API call and ensures the
    account name is unique before saving it to the configuration.
    """
    data = load_config()
    name = get_validated_input("Account name: ", lambda s: s.strip(), "Account name cannot be empty.")

    if find_account(data, name):
        logger.warning("Account already exists")
        print("❌ Account already exists")
        return

    display_token_guidance()

    while True:
        token = get_validated_input("\nEnter your Cloudflare API Token: ", lambda s: s.strip(), "API Token cannot be empty.")
        try:
            print("🔐 Verifying token...")
            cf_api = CloudflareAPI(token)
            cf_api.verify_token()
            print("✅ Token is valid")
            break
        except MissingPermissionError as e:
            logger.error(f"Token validation failed due to missing permissions: {e}")
            print(f"❌ {e}")
            print("Please create a new token with the required permissions listed above.")
            if not confirm_action("Try again with a new token?"):
                logger.warning("User aborted account creation.")
                return
        except APIError as e:
            logger.error(f"Cloudflare API Error on token verification: {e}")
            print(f"❌ Invalid Token. Cloudflare API Error: {e}")
            print("This could be due to an incorrect token, or you might be using a Global API Key which is not recommended.")
            if not confirm_action("Try again?"):
                logger.warning("User aborted account creation.")
                return

    data["accounts"].append({"name": name, "api_token": token, "zones": []})
    if validate_and_save_config(data):
        logger.info(f"Account '{name}' added.")
        print("✅ Account added")

def edit_account():
    """
    Allows the user to edit the name or API token of an existing account.

    The user selects an account from a list, then is prompted to enter a
    new name and/or a new token.
    """
    data = load_config()
    if not data["accounts"]:
        logger.warning("No accounts available.")
        print("❌ No accounts available.")
        return

    acc = select_from_list(data["accounts"], "Select an account to edit:")
    if not acc:
        return

    print(f"\n--- Editing Account: {acc['name']} ---")
    new_name = get_validated_input(f"Enter new name (or press Enter to keep '{acc['name']}'): ", lambda s: s.strip(), allow_empty=True)
    new_token = get_validated_input("Enter new API token (or press Enter to keep current): ", lambda s: s.strip(), allow_empty=True)

    if new_name or new_token:
        edit_account_in_config(acc['name'], new_name, new_token)
    else:
        print("No changes made.")

def delete_account():
    """
    Allows the user to delete an existing account from the configuration.

    The user selects an account from a list and must confirm the deletion
    before the account is removed.
    """
    data = load_config()
    if not data["accounts"]:
        logger.warning("No accounts available.")
        print("❌ No accounts available.")
        return

    acc = select_from_list(data["accounts"], "Select an account to delete:")
    if not acc:
        return

    if confirm_action(f"Are you sure you want to delete the account '{acc['name']}'?"):
        delete_account_from_config(acc['name'])
        logger.info(f"Account '{acc['name']}' deleted.")
    else:
        logger.info("Deletion cancelled.")

def list_accounts():
    """
    Lists all configured accounts in a table format.

    For each account, it displays the name and the number of zones accessible
    with its API token. It handles API errors gracefully if zones cannot be
    fetched for a particular account.
    """
    data = load_config()
    if not data["accounts"]:
        print("No accounts configured.")
        return

    accounts_data = []
    for acc in data["accounts"]:
        try:
            cf_api = CloudflareAPI(acc["api_token"])
            zones = list(cf_api.list_zones())
            zone_count = len(zones)
        except APIError as e:
            logger.error(f"Failed to fetch zones for account {acc['name']}: {e}")
            zone_count = "Error"
        
        accounts_data.append({"Name": acc["name"], "Zones": zone_count})

    print("\n--- Configured Accounts ---")
    display_as_table(accounts_data, headers={"Name": "Name", "Zones": "Zones"})


def account_management_menu():
    """
    Displays and handles the Account Management submenu.

    This function presents the user with options to add, edit, or delete
    Cloudflare accounts. It loops until the user chooses to return to the

    main menu.
    """
    clear_screen()
    while True:
        print("\n--- 👤 Cloudflare Account Management ---")
        list_accounts()
        print("\n1. 👤 Add a New Cloudflare Account")
        print("2. ✏️ Edit an Existing Cloudflare Account")
        print("3. 🗑️ Delete a Cloudflare Account")
        print("0. ⬅️ Return to Main Menu")
        print("---------------------------")

        choice = input("👉 Enter your choice: ").strip()

        if choice == "1":
            add_account()
        elif choice == "2":
            edit_account()
        elif choice == "3":
            delete_account()
        elif choice == "0":
            break
        else:
            logger.warning(f"Invalid choice: {choice}")
            print("❌ Invalid choice. Please select a valid option.")