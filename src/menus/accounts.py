"""
Account Management Menu.

This module provides the user interface for managing Cloudflare
accounts within the application. It allows users to add, edit, list, and
delete accounts from the configuration.
"""
from ..core.app import Application
from ..core.cloudflare_api import CloudflareAPI
from ..core.exceptions import APIError, AuthenticationError
from ..core.logger import logger

app = Application()
from ..display import (
    display_as_table,
    print_fast,
    print_slow,
    display_token_guidance,
    COLOR_TITLE,
    COLOR_SUCCESS,
    COLOR_ERROR,
    COLOR_WARNING,
    COLOR_SEPARATOR,
    OPTION_SEPARATOR,
    RESET_COLOR,
)
from .utils import clear_screen, select_from_list, confirm_action, get_validated_input

def add_account_menu():
    """
    Guides the user through adding a new Cloudflare account.
    """
    name = get_validated_input("Account name: ", lambda s: s.strip(), "Account name cannot be empty.")

    display_token_guidance()

    while True:
        token = get_validated_input("\nEnter your Cloudflare API Token: ", lambda s: s.strip(), "API Token cannot be empty.")
        print_fast("🔐 Verifying token and adding account...")
        success, result = app.add_account(name, token)

        if success:
            logger.info(f"Account '{name}' added.")
            print_fast(f"{COLOR_SUCCESS}✅ Account '{name}' added successfully!{RESET_COLOR}")
            break
        
        logger.error(f"Failed to add account: {result}")
        print_fast(f"{COLOR_ERROR}❌ {result}{RESET_COLOR}")
        
        # If it's an authentication error, ask to try again
        if "permission" in str(result).lower() or "token" in str(result).lower():
             if not confirm_action("Try again with a new token?"):
                logger.warning("User aborted account creation.")
                break
        else:
            # For other errors like 'account already exists', just break
            break


def edit_account_menu():
    """
    Allows the user to edit the name or API token of an existing account.
    """
    success, accounts = app.get_accounts()
    if not success:
        print_fast(f"{COLOR_ERROR}❌ Error: {accounts}{RESET_COLOR}")
        return

    if not accounts:
        logger.warning("No accounts available.")
        print_fast(f"{COLOR_WARNING}⚠️ No accounts available.{RESET_COLOR}")
        return

    acc = select_from_list(accounts, "Select an account to edit:")
    if not acc:
        return

    print_fast(f"\n--- Editing Account: {acc['name']} ---")
    new_name = get_validated_input(f"Enter new name (or press Enter to keep '{acc['name']}'): ", lambda s: s.strip(), allow_empty=True)
    new_token = get_validated_input("Enter new API token (or press Enter to keep current): ", lambda s: s.strip(), allow_empty=True)

    if new_name or new_token:
        success, result = app.edit_account(acc['name'], new_name or None, new_token or None)
        if success:
            logger.info(f"Account '{acc['name']}' updated.")
            print_fast(f"{COLOR_SUCCESS}✅ Account updated successfully!{RESET_COLOR}")
        else:
            logger.error(f"Error editing account: {result}")
            print_fast(f"{COLOR_ERROR}❌ {result}{RESET_COLOR}")
    else:
        print_fast("No changes made.")


def delete_account_menu():
    """
    Allows the user to delete an existing account from the configuration.
    """
    success, accounts = app.get_accounts()
    if not success:
        print_fast(f"{COLOR_ERROR}❌ Error: {accounts}{RESET_COLOR}")
        return
        
    if not accounts:
        logger.warning("No accounts available.")
        print_fast(f"{COLOR_WARNING}⚠️ No accounts available.{RESET_COLOR}")
        return

    acc = select_from_list(accounts, "Select an account to delete:")
    if not acc:
        return

    if confirm_action(f"Are you sure you want to delete the account '{acc['name']}'?"):
        success, result = app.delete_account(acc['name'])
        if success:
            logger.info(f"Account '{acc['name']}' deleted.")
            print_fast(f"{COLOR_SUCCESS}✅ Account '{acc['name']}' deleted successfully.{RESET_COLOR}")
        else:
            logger.error(f"Error deleting account: {result}")
            print_fast(f"{COLOR_ERROR}❌ {result}{RESET_COLOR}")
    else:
        logger.info("Deletion cancelled by user.")
        print_fast("Deletion cancelled.")


def list_accounts_menu():
    """
    Lists all configured accounts in a table format.
    """
    success, accounts = app.get_accounts()
    if not success:
        print_fast(f"{COLOR_ERROR}❌ Error: {accounts}{RESET_COLOR}")
        return

    if not accounts:
        print_fast("No accounts configured.")
        return

    accounts_data = []
    print_fast("\nFetching zone information for accounts...")
    for acc in accounts:
        try:
            # This logic remains in the UI as it's for display purposes
            cf_api = CloudflareAPI(acc["api_token"])
            zone_count = len(list(cf_api.list_zones()))
        except APIError as e:
            logger.error(f"Failed to fetch zones for account {acc['name']}: {e}")
            zone_count = "Error"
        
        accounts_data.append({"Name": acc["name"], "Zones": zone_count})

    print_fast("\n--- Configured Accounts ---")
    display_as_table(accounts_data, headers={"Name": "Name", "Zones": "Zones"})


def account_management_menu():
    """
    Displays and handles the Account Management submenu.
    """
    while True:
        clear_screen()
        print_fast(f"\n{COLOR_TITLE}--- 👤 Cloudflare Account Management ---{RESET_COLOR}")
        list_accounts_menu()
        print_slow("\n1. 👤 Add a New Cloudflare Account")
        print_slow("2. ✏️ Edit an Existing Cloudflare Account")
        print_slow("3. 🗑️ Delete a Cloudflare Account")
        print_slow("0. ⬅️ Return to Main Menu")
        print_fast(f"{COLOR_SEPARATOR}{OPTION_SEPARATOR}{RESET_COLOR}")

        choice = input("👉 Enter your choice: ").strip()

        if choice == "1":
            add_account_menu()
        elif choice == "2":
            edit_account_menu()
        elif choice == "3":
            delete_account_menu()
        elif choice == "0":
            break
        else:
            logger.warning(f"Invalid choice: {choice}")
            print_fast(f"{COLOR_ERROR}❌ Invalid choice. Please select a valid option.{RESET_COLOR}")
        
        if choice in ["1", "2", "3"]:
            input("\nPress Enter to continue...")