"""
Core Account Management Logic.

This module provides the business logic for managing Cloudflare accounts.
It handles the interaction with the configuration file and the Cloudflare API
for account-related operations, without any presentation-layer code.
"""
from .config import config_manager
from .cloudflare_api import CloudflareAPI
from .exceptions import ConfigError, APIError, AuthenticationError
from cloudflare import APIError as CloudflareAPIError


def add_account(name, token):
    """
    Adds a new Cloudflare account to the configuration after verifying the token.

    Args:
        name (str): The name for the new account.
        token (str): The Cloudflare API token.

    Returns:
        dict: The newly added account data.

    Raises:
        ConfigError: If an account with the same name already exists or config save fails.
        AuthenticationError: If the token is missing required permissions.
        APIError: If the token is invalid or another API error occurs.
    """
    if config_manager.find_account(name):
        raise ConfigError(f"Account with name '{name}' already exists.")

    try:
        cf_api = CloudflareAPI(token)
        cf_api.verify_token()
    except AuthenticationError as e:
        raise AuthenticationError(str(e), original_exception=e)
    except CloudflareAPIError as e:
        raise APIError(f"Cloudflare API Error: {e}", original_exception=e)

    config_data = config_manager.get_config()
    new_account = {"name": name, "api_token": token, "zones": []}
    config_data["accounts"].append(new_account)
    
    config_manager.save_config()
    
    return new_account

def edit_account(account_name, new_name=None, new_token=None):
    """
    Edits the details of a Cloudflare account in the configuration.

    Args:
        account_name (str): The current name of the account to edit.
        new_name (str, optional): The new name for the account. Defaults to None.
        new_token (str, optional): The new API token. Defaults to None.

    Returns:
        bool: True if the account was edited and saved successfully.
    
    Raises:
        ConfigError: If the account to edit is not found.
    """
    acc = config_manager.find_account(account_name)
    if not acc:
        raise ConfigError(f"Account '{account_name}' not found.")

    if new_name:
        acc['name'] = new_name
    if new_token:
        acc['api_token'] = new_token

    config_manager.save_config()
    return True

def delete_account(account_name):
    """
    Deletes a Cloudflare account from the configuration.

    Args:
        account_name (str): The name of the account to delete.

    Returns:
        bool: True if the account was deleted and saved successfully.

    Raises:
        ConfigError: If the account to delete is not found.
    """
    config_data = config_manager.get_config()
    acc = config_manager.find_account(account_name)
    if not acc:
        raise ConfigError(f"Account '{account_name}' not found.")

    config_data['accounts'].remove(acc)
    config_manager.save_config()
    return True

def get_accounts():
    """
    Retrieves the list of all configured accounts.

    Returns:
        list: A list of account dictionaries.
    """
    return config_manager.get_config().get("accounts", [])