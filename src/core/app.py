"""
Application Facade.

This module provides a single entry point for all application logic.
It simplifies the interface for consumers like the CLI and the Bot,
and orchestrates the underlying core modules.
"""
from . import accounts
from .exceptions import CoreError

class Application:
    """
    The main application facade.
    """

    def get_accounts(self):
        """
        Retrieves a list of all configured accounts.

        Returns:
            A tuple (success, data_or_error_message).
            If success is True, data_or_error_message is a list of accounts.
            If success is False, data_or_error_message is an error string.
        """
        try:
            account_list = accounts.get_accounts()
            return True, account_list
        except CoreError as e:
            return False, str(e)

    def add_account(self, name, token):
        """
        Adds a new Cloudflare account.

        Args:
            name (str): The name for the new account.
            token (str): The Cloudflare API token.

        Returns:
            A tuple (success, data_or_error_message).
        """
        try:
            new_account = accounts.add_account(name, token)
            return True, new_account
        except CoreError as e:
            return False, str(e)

    def edit_account(self, old_name, new_name, new_token):
        """
        Edits an existing Cloudflare account.

        Args:
            old_name (str): The current name of the account.
            new_name (str): The new name for the account.
            new_token (str): The new API token.

        Returns:
            A tuple (success, data_or_error_message).
        """
        try:
            result = accounts.edit_account(old_name, new_name, new_token)
            return True, result
        except CoreError as e:
            return False, str(e)

    def delete_account(self, name):
        """
        Deletes a Cloudflare account.

        Args:
            name (str): The name of the account to delete.

        Returns:
            A tuple (success, data_or_error_message).
        """
        try:
            result = accounts.delete_account(name)
            return True, result
        except CoreError as e:
            return False, str(e)