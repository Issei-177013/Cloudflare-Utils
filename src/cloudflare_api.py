from cloudflare import Cloudflare, APIError
from .config import REQUIRED_PERMISSIONS
from .error_handler import MissingPermissionError

class CloudflareAPI:
    def __init__(self, api_token):
        self.cf = Cloudflare(api_token=api_token)

    # ------------------ ZONE ------------------
    def list_zones(self):
        try:
            return self.cf.zones.list()
        except APIError as e:
            raise RuntimeError(f"Error listing zones: {e}")

    def get_zone_details(self, zone_id):
        try:
            return self.cf.zones.get(zone_id=zone_id)
        except APIError as e:
            raise RuntimeError(f"Error getting zone details: {e}")

    def add_zone(self, domain_name, zone_type="full"):
        try:
            url = "https://api.cloudflare.com/client/v4/zones"
            headers = {
                "Authorization": f"Bearer {self.cf.api_token}",
                "Content-Type": "application/json"
            }
            payload = {"name": domain_name, "type": zone_type}

            import requests
            response = requests.post(url, headers=headers, json=payload)
            data = response.json()

            if not response.ok or not data.get("success", False):
                errors = data.get("errors", [])
                for error in errors:
                    if "Requires permission" in error.get("message", ""):
                        permission_needed = error["message"].split('"')[1]
                        raise MissingPermissionError(f"'{permission_needed}'")
                raise RuntimeError(f"Failed to add zone: {errors}")

            return data["result"]

        except MissingPermissionError:
            raise
        except Exception as e:
            raise RuntimeError(f"❌ Failed to add zone '{domain_name}': {e}")

    def delete_zone(self, zone_id):
        try:
            return self.cf.zones.delete(zone_id=zone_id)
        except APIError as e:
            raise RuntimeError(f"Error deleting zone: {e}")

    # ------------------ ACCOUNT ------------------
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

    # ------------------ TOKEN VERIFICATION ------------------
    def verify_token(self):
        try:
            self.cf.zones.list()
        except APIError as e:
            if e.code == 9109:
                permission_name = "Unknown"
                if "zones" in e.request.url:
                    permission_name = REQUIRED_PERMISSIONS['validation_map'].get('Zone:Read', 'Zone.Zone')
                raise MissingPermissionError(
                    f"Token is missing required permission: '{permission_name}'. "
                    "Please ensure your token has Zone:Read and DNS:Read/Edit permissions."
                )
            else:
                raise e
        except Exception as e:
            raise APIError(f"An unexpected error occurred during token verification: {e}")

    # ------------------ DNS RECORDS ------------------
    def list_dns_records(self, zone_id):
        """Returns a list of DNS records for the given zone."""
        try:
            return self.cf.dns.records.list(zone_id=zone_id)
        except APIError as e:
            raise e

    def create_dns_record(self, zone_id, name, type, content, proxied=False, ttl=None):
        """Creates a new DNS record."""
        try:
            return self.cf.dns.records.create(
                zone_id=zone_id,
                name=name,
                type=type,
                content=content,
                proxied=proxied,
                ttl=ttl
            )
        except APIError as e:
            raise e

    def update_dns_record(self, zone_id, dns_record_id, name, type, content, proxied=False, ttl=None):
        """Updates the content of a specific DNS record."""
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
        except APIError as e:
            raise e

    def delete_dns_record(self, zone_id, dns_record_id):
        """Deletes a specific DNS record."""
        try:
            return self.cf.dns.records.delete(
                zone_id=zone_id,
                dns_record_id=dns_record_id
            )
        except APIError as e:
            raise e

    # ------------------ ZONE SETTINGS ------------------
    def get_zone_setting(self, zone_id, setting_name):
        """Fetches a specific setting for a zone."""
        try:
            setting = self.cf.zones.settings.get(zone_id=zone_id, setting_id=setting_name)
            return setting.value
        except APIError as e:
            if "setting not found" in str(e).lower():
                return None
            raise MissingPermissionError(f"Missing permission: 'Zone Settings:Read'") if "permission" in str(e).lower() else e

    def update_zone_setting(self, zone_id, setting_name, new_value):
        """Updates a specific setting for a zone."""
        try:
            self.cf.zones.settings.update(zone_id=zone_id, setting_id=setting_name, value=new_value)
        except APIError as e:
            raise MissingPermissionError(f"Missing permission: 'Zone Settings:Edit'") if "permission" in str(e).lower() else e

    def get_zone_core_settings(self, zone_id):
        """Fetches a dictionary of core settings for a zone."""
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