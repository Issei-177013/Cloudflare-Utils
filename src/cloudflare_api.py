from cloudflare import Cloudflare, APIError

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

    def verify_token(self):
        """
        Verifies the API token by attempting to list zones.
        If the token is invalid, an APIError is raised.
        """
        try:
            zones = self.cf.zones.list()  # This returns an iterable of Zone objects
            # Just check if we got something iterable with expected attributes
            if not hasattr(zones, '__iter__'):
                raise APIError("Unexpected API response format", request=None, body=None)
            # Optionally check if first item has id and name (basic sanity check)
            first_zone = next(iter(zones), None)
            if first_zone is None or not hasattr(first_zone, 'id') or not hasattr(first_zone, 'name'):
                raise APIError("Unexpected API response format", request=None, body=None)
        except Exception as e:
            # Wrap all exceptions into APIError with message
            raise APIError(f"Cloudflare API Error on token verification: {e}", request=None, body=None)

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