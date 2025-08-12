from cloudflare import Cloudflare, APIError
from .config import REQUIRED_PERMISSIONS
from .error_handler import MissingPermissionError

class CloudflareAPI:
    def __init__(self, api_token):
        self.cf = Cloudflare(api_token=api_token)

    def list_dns_records(self, zone_id):
        """
        Returns a list of DNS records for the given zone.
        """
        try:
            return self.cf.dns.records.list(zone_id=zone_id)
        except APIError as e:
            raise e

    def list_zones(self):
        try:
            return self.cf.zones.list()
        except APIError as e:
            raise RuntimeError(f"Error listing zones: {e}")

    def get_account_id(self):
        try:
            accounts_iterator = self.cf.accounts.list()
            first_account = next(iter(accounts_iterator), None)
            if first_account:
                return first_account.id
            else:
                raise RuntimeError("❌ No Cloudflare accounts found.")
        except APIError as e:
            raise RuntimeError(f"Cloudflare API error when fetching account ID: {e}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error fetching account ID: {e}")

    def add_zone(self, domain_name, zone_type="full"):
        try:
            # Build raw request because cloudflare-python can't handle token-only account_id
            url = "https://api.cloudflare.com/client/v4/zones"
            headers = {
                "Authorization": f"Bearer {self.cf.api_token}",
                "Content-Type": "application/json"
            }
            payload = {
                "name": domain_name,
                "type": zone_type
            }

            import requests
            response = requests.post(url, headers=headers, json=payload)
            data = response.json()

            if not response.ok or not data.get("success", False):
                errors = data.get("errors", [])
                # Check for specific permission errors
                for error in errors:
                    if "Requires permission" in error.get("message", ""):
                        # Extract the permission string
                        permission_needed = error["message"].split('"')[1]
                        raise MissingPermissionError(f"'{permission_needed}'")
                raise RuntimeError(f"Failed to add zone: {errors}")

            # Return parsed zone info as a simple object
            return data["result"]

        except MissingPermissionError:
            # Re-raise to be caught by the calling function
            raise
        except Exception as e:
            raise RuntimeError(f"❌ Failed to add zone '{domain_name}': {e}")

    def get_zone_details(self, zone_id):
        try:
            return self.cf.zones.get(zone_id=zone_id)
        except APIError as e:
            raise RuntimeError(f"Error getting zone details: {e}")

    def delete_zone(self, zone_id):
        try:
            return self.cf.zones.delete(zone_id=zone_id)
        except APIError as e:
            raise RuntimeError(f"Error deleting zone: {e}")

    def verify_token(self):
        """
        Verifies the API token by attempting to list zones.
        If the token is invalid or misses permissions, an APIError or MissingPermissionError is raised.
        """
        try:
            # Check Zone Read permission
            self.cf.zones.list()
            # Check DNS Read permission (as a proxy for DNS Edit)
            # We assume if they can read, they might have edit. A full check is complex.
            # A sample zone_id is needed. We can't get one without Zone:Read.
            # This is a limitation. We'll rely on the user providing a token with the right perms.
        except APIError as e:
            if e.code == 9109:
                # Likely insufficient permissions
                # We map the attempted action to a user-friendly permission name
                permission_name = "Unknown"
                if "zones" in e.request.url:
                    permission_name = REQUIRED_PERMISSIONS['validation_map'].get('Zone:Read', 'Zone.Zone')
                
                raise MissingPermissionError(
                    f"Token is missing required permission: '{permission_name}'. "
                    "Please ensure your token has Zone:Read and DNS:Read/Edit permissions."
                )
            else:
                # Re-raise other API errors
                raise e
        except Exception as e:
            # Wrap other exceptions
            raise APIError(f"An unexpected error occurred during token verification: {e}")

    def update_dns_record(self, zone_id, dns_record_id, name, type, content, proxied=False):
        """
        Updates the content of a specific DNS record.
        """
        try:
            self.cf.dns.records.update(
                zone_id=zone_id,
                dns_record_id=dns_record_id,
                name=name,
                type=type,
                content=content,
                proxied=proxied
            )
        except APIError as e:
            raise e