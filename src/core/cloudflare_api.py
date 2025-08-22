"""
Cloudflare API Wrapper.

This module provides a simplified interface for interacting with the Cloudflare API.
It encapsulates the official `cloudflare-python` library, handling common API calls
for managing zones, DNS records, and account information. It also includes custom
error handling to provide more specific feedback, such as for missing API token
permissions.
"""
import requests
from requests.exceptions import RequestException
from cloudflare import Cloudflare
from cloudflare import APIError as CloudflareAPIError
from .config import REQUIRED_PERMISSIONS
from .exceptions import APIError, AuthenticationError
from .logger import logger

class CloudflareAPI:
    """
    A wrapper class for the Cloudflare API.

    This class simplifies interactions with the Cloudflare API by providing
    methods for common operations like managing zones, DNS records, and
    verifying API tokens.

    Attributes:
        cf (Cloudflare): An instance of the official Cloudflare client.
    """

    def __init__(self, api_token):
        """
        Initializes the CloudflareAPI client.

        Args:
            api_token (str): The Cloudflare API token for authentication.
        """
        self.cf = Cloudflare(api_token=api_token)

    def list_zones(self):
        """
        Retrieves a list of all zones accessible by the API token.

        Returns:
            list: A list of zone objects.

        Raises:
            APIError: If there is an API error while listing zones.
        """
        try:
            return self.cf.zones.list()
        except CloudflareAPIError as e:
            logger.error(f"Error listing zones: {e}")
            raise APIError("Error listing zones.", original_exception=e)

    def get_zone_details(self, zone_id):
        """
        Retrieves the details for a specific zone.

        Args:
            zone_id (str): The ID of the zone to retrieve.

        Returns:
            dict: An object containing the details of the zone.

        Raises:
            APIError: If there is an API error.
        """
        try:
            return self.cf.zones.get(zone_id=zone_id)
        except CloudflareAPIError as e:
            logger.error(f"Error getting zone details for zone_id={zone_id}: {e}")
            raise APIError("Error getting zone details.", original_exception=e)

    def add_zone(self, domain_name, zone_type="full"):
        """
        Adds a new zone (domain) to the Cloudflare account.

        Args:
            domain_name (str): The name of the domain to add.
            zone_type (str, optional): The type of zone to create.
                                       Defaults to "full".

        Returns:
            dict: The result from the API call upon successful creation.

        Raises:
            AuthenticationError: If the API token lacks the required permissions.
            APIError: If the zone creation fails for other reasons.
        """
        try:
            url = "https://api.cloudflare.com/client/v4/zones"
            headers = {
                "Authorization": f"Bearer {self.cf.api_token}",
                "Content-Type": "application/json"
            }
            payload = {"name": domain_name, "type": zone_type}

            response = requests.post(url, headers=headers, json=payload)
            data = response.json()

            if not response.ok or not data.get("success", False):
                errors = data.get("errors", [])
                for error in errors:
                    if "Requires permission" in error.get("message", ""):
                        permission_needed = error["message"].split('"')[1]
                        raise AuthenticationError(f"Missing permission: '{permission_needed}'")
                
                logger.error(f"Failed to add zone '{domain_name}'. API response: {errors}")
                raise APIError(f"Failed to add zone: {errors}")

            return data["result"]

        except RequestException as e:
            logger.error(f"Network error while trying to add zone '{domain_name}': {e}")
            raise APIError(f"Failed to add zone '{domain_name}' due to a network error.", original_exception=e)
        except Exception as e:
            logger.error(f"An unexpected error occurred while adding zone '{domain_name}': {e}", exc_info=True)
            raise APIError(f"Failed to add zone '{domain_name}' due to an unexpected error.", original_exception=e)

    def delete_zone(self, zone_id):
        """
        Deletes a specific zone from the Cloudflare account.

        Args:
            zone_id (str): The ID of the zone to delete.

        Returns:
            dict: The result from the API call upon successful deletion.

        Raises:
            APIError: If there is an API error during deletion.
        """
        try:
            return self.cf.zones.delete(zone_id=zone_id)
        except CloudflareAPIError as e:
            logger.error(f"Error deleting zone {zone_id}: {e}")
            raise APIError("Error deleting zone.", original_exception=e)

    def get_account_id(self):
        """
        Retrieves the ID of the first Cloudflare account found.

        Returns:
            str: The ID of the Cloudflare account.

        Raises:
            APIError: If no accounts are found or if there is an API error.
        """
        try:
            accounts_iterator = self.cf.accounts.list()
            first_account = next(iter(accounts_iterator), None)
            if first_account:
                return first_account.id
            else:
                raise APIError("No Cloudflare accounts found.")
        except CloudflareAPIError as e:
            logger.error(f"Cloudflare API error when fetching account ID: {e}")
            raise APIError("Cloudflare API error when fetching account ID.", original_exception=e)
        except Exception as e:
            logger.error(f"Unexpected error fetching account ID: {e}", exc_info=True)
            raise APIError("Unexpected error fetching account ID.", original_exception=e)

    def verify_token(self):
        """
        Verifies that the API token has the necessary permissions.

        This method attempts to list zones, which is a basic read operation.
        If it fails with a specific permission error code (9109), it raises
        an `AuthenticationError`.

        Raises:
            AuthenticationError: If the token is missing required permissions.
            APIError: For other types of API errors during verification.
        """
        try:
            self.cf.zones.list()
        except CloudflareAPIError as e:
            if e.code == 9109:
                permission_name = "Unknown"
                if "zones" in e.request.url:
                    permission_name = REQUIRED_PERMISSIONS['validation_map'].get('Zone:Read', 'Zone.Zone')
                raise AuthenticationError(
                    f"Token is missing required permission: '{permission_name}'. "
                    "Please ensure your token has Zone:Read and DNS:Read/Edit permissions.",
                    original_exception=e
                )
            else:
                logger.error(f"An unexpected API error occurred during token verification: {e}")
                raise APIError("An unexpected API error occurred during token verification.", original_exception=e)
        except Exception as e:
            logger.error(f"An unexpected error occurred during token verification: {e}", exc_info=True)
            raise APIError("An unexpected error occurred during token verification.", original_exception=e)

    def list_dns_records(self, zone_id):
        """
        Retrieves a list of DNS records for a given zone.

        Args:
            zone_id (str): The ID of the zone.

        Returns:
            list: A list of DNS record objects.

        Raises:
            APIError: If the API call fails.
        """
        try:
            return self.cf.dns.records.list(zone_id=zone_id)
        except CloudflareAPIError as e:
            logger.error(f"Error listing DNS records for zone {zone_id}: {e}")
            raise APIError(f"Error listing DNS records for zone {zone_id}.", original_exception=e)

    def create_dns_record(self, zone_id, name, type, content, proxied=False, ttl=None):
        """
        Creates a new DNS record in a specific zone.

        Args:
            zone_id (str): The ID of the zone.
            name (str): The record name (e.g., 'subdomain.example.com').
            type (str): The DNS record type (e.g., 'A', 'AAAA', 'CNAME').
            content (str): The record content (e.g., an IP address).
            proxied (bool, optional): Whether the record is proxied by
                                      Cloudflare. Defaults to False.
            ttl (int, optional): The Time To Live for the record in seconds.
                                 Defaults to None (automatic).

        Returns:
            dict: The newly created DNS record object.

        Raises:
            APIError: If the API call fails.
        """
        try:
            return self.cf.dns.records.create(
                zone_id=zone_id,
                name=name,
                type=type,
                content=content,
                proxied=proxied,
                ttl=ttl
            )
        except CloudflareAPIError as e:
            logger.error(f"Error creating DNS record for zone {zone_id}: {e}")
            raise APIError(f"Error creating DNS record for zone {zone_id}.", original_exception=e)

    def update_dns_record(self, zone_id, dns_record_id, name, type, content, proxied=False, ttl=None):
        """
        Updates an existing DNS record.

        Args:
            zone_id (str): The ID of the zone.
            dns_record_id (str): The ID of the DNS record to update.
            name (str): The record name.
            type (str): The DNS record type.
            content (str): The new record content.
            proxied (bool, optional): Whether the record is proxied.
                                      Defaults to False.
            ttl (int, optional): The new TTL for the record. Defaults to None.

        Returns:
            dict: The updated DNS record object.

        Raises:
            APIError: If the API call fails.
        """
        try:
            return self.cf.dns.records.update(
                zone_id=zone_id,
                dns_record_id=dns_record_id,
                name=name,
                type=type,
                content=content,
                proxied=proxied,
                ttl=ttl
            )
        except CloudflareAPIError as e:
            logger.error(f"Error updating DNS record {dns_record_id} for zone {zone_id}: {e}")
            raise APIError(f"Error updating DNS record {dns_record_id}.", original_exception=e)

    def delete_dns_record(self, zone_id, dns_record_id):
        """
        Deletes a specific DNS record.

        Args:
            zone_id (str): The ID of the zone.
            dns_record_id (str): The ID of the DNS record to delete.

        Returns:
            dict: A confirmation object from the API.

        Raises:
            APIError: If the API call fails.
        """
        try:
            return self.cf.dns.records.delete(
                zone_id=zone_id,
                dns_record_id=dns_record_id
            )
        except CloudflareAPIError as e:
            logger.error(f"Error deleting DNS record {dns_record_id} for zone {zone_id}: {e}")
            raise APIError(f"Error deleting DNS record {dns_record_id}.", original_exception=e)

    def get_zone_setting(self, zone_id, setting_name):
        """
        Fetches a specific setting for a zone.

        Args:
            zone_id (str): The ID of the zone.
            setting_name (str): The name of the setting to retrieve
                                (e.g., 'ssl', 'always_use_https').

        Returns:
            any: The value of the requested setting, or None if not found.

        Raises:
            AuthenticationError: If the token lacks permission to read zone settings.
            APIError: For other API-related errors.
        """
        try:
            setting = self.cf.zones.settings.get(zone_id=zone_id, setting_id=setting_name)
            return setting.value
        except CloudflareAPIError as e:
            if "setting not found" in str(e).lower():
                return None
            logger.error(f"API error getting zone setting '{setting_name}' for zone {zone_id}: {e}")
            if "permission" in str(e).lower():
                 raise AuthenticationError(f"Missing permission: 'Zone Settings:Read'", original_exception=e)
            else:
                 raise APIError(f"API error getting zone setting '{setting_name}'.", original_exception=e)

    def update_zone_setting(self, zone_id, setting_name, new_value):
        """
        Updates a specific setting for a zone.

        Args:
            zone_id (str): The ID of the zone.
            setting_name (str): The name of the setting to update.
            new_value (any): The new value for the setting.

        Raises:
            AuthenticationError: If the token lacks permission to edit zone settings.
            APIError: For other API-related errors.
        """
        try:
            self.cf.zones.settings.update(zone_id=zone_id, setting_id=setting_name, value=new_value)
        except CloudflareAPIError as e:
            logger.error(f"API error updating zone setting '{setting_name}' for zone {zone_id}: {e}")
            if "permission" in str(e).lower():
                raise AuthenticationError(f"Missing permission: 'Zone Settings:Edit'", original_exception=e)
            else:
                raise APIError(f"API error updating zone setting '{setting_name}'.", original_exception=e)

    def get_zone_core_settings(self, zone_id):
        """
        Fetches a dictionary of core settings for a zone.

        This method retrieves a predefined list of important zone settings,
        such as SSL, Always Use HTTPS, and TLS version.

        Args:
            zone_id (str): The ID of the zone.

        Returns:
            dict: A dictionary where keys are setting names and values are
                  the current settings.
        """
        settings_to_fetch = [
            "ssl",
            "always_use_https",
            "automatic_https_rewrites",
            "min_tls_version"
        ]
        core_settings = {}
        for setting_name in settings_to_fetch:
            core_settings[setting_name] = self.get_zone_setting(zone_id, setting_name)
        return core_settings