import requests
from typing import List
from cloudflare import Cloudflare, APIError
from .permissions_registry import FEATURE_PERMISSIONS
from .logger import logger

class CloudflareAPI:
    def __init__(self, api_token):
        self.cf = Cloudflare(api_token=api_token)
        self.token_permissions: List[str] = []
        try:
            self.token_permissions = self.get_token_permissions()
        except APIError as e:
            # This can happen if the token doesn't have "API Tokens Read"
            # We'll handle this gracefully. The token_permissions list will be empty.
            logger.warning(f"Could not fetch token permissions: {e}. This may be expected if the token lacks 'API Tokens Read' permission.")


    def get_token_permissions(self) -> List[str]:
        """
        Fetches the names of all permission groups granted to this token.
        Requires the 'API Tokens Read' permission.
        """
        try:
            # This endpoint is not directly available in the cloudflare-python library,
            # so we make a direct request.
            response = self.cf.get("user/tokens/permission_groups")
            
            # The response is a list of objects, each with a 'name' field.
            # e.g., [{'id': '...', 'name': 'Zone.DNS'}, ...]
            return [perm['name'] for perm in response]
        except APIError as e:
            # Re-raise with a more specific message
            raise APIError(f"Failed to get token permissions. Ensure the token has 'API Tokens Read' permission. Details: {e}")


    def has_permission(self, feature: str) -> bool:
        """Checks if the token has all required permissions for a given feature."""
        required = FEATURE_PERMISSIONS.get(feature, [])
        if not required:
            return True # No specific permissions required for this feature.
        
        # Check if all required permissions are present in the token's permissions.
        return all(r in self.token_permissions for r in required)

    def get_usable_features(self) -> List[str]:
        """Returns a list of features that are usable with the current token's permissions."""
        usable = []
        for feature, required_perms in FEATURE_PERMISSIONS.items():
            if all(r in self.token_permissions for r in required_perms):
                usable.append(feature)
        return usable

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
                raise RuntimeError(f"Failed to add zone: {errors}")

            # Return parsed zone info as a simple object
            return data["result"]

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

    def verify_token(self) -> bool:
        """
        Verifies the API token by checking its status and ensuring it has at least one
        permission required by this application.
        """
        try:
            # The get_token_permissions call in __init__ already attempted to verify the token.
            # If that call failed (e.g., due to 'API Tokens Read' being absent),
            # self.token_permissions will be empty.
            
            # A token is considered valid for this app if it could be read AND has permissions for at least one feature.
            if not self.token_permissions:
                # If we couldn't get permissions, we try a fallback: listing zones.
                # This helps with tokens that don't have 'API Tokens Read' but might have 'Zone.Zone' etc.
                logger.warning("Token permissions could not be read. Falling back to listing zones for verification.")
                self.cf.zones.list()
                return True # If list_zones() succeeds, token is valid but has limited (unknown) scope.

            # If we *could* get permissions, check if any of them are useful.
            if not self.get_usable_features():
                 raise APIError("Token is valid but has no permissions for any of the tool's features.", request=None, body=None)

            return True

        except APIError as e:
            # Re-raise to be caught by the UI
            raise e

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