from cloudflare import Cloudflare, APIError

class CloudflareAPI:
    def __init__(self, api_token):
        self.cf = Cloudflare(api_token=api_token)

    def list_dns_records(self, zone_id):
        try:
            return self.cf.dns.records.list(zone_id=zone_id)
        except APIError as e:
            raise e

    def list_zones(self):
        """Lists all zones in the account."""
        try:
            return self.cf.zones.get()
        except APIError as e:
            raise e

    def verify_token(self):
        """
        Verifies the API token by attempting to fetch zones.
        If the token is invalid or insufficient, it will raise an APIError.
        """
        try:
            zones = self.cf.zones.get()
            if not isinstance(zones, list):
                raise APIError("Unexpected API response format.")
        except Exception as e:
            raise APIError(f"Cloudflare API Error on token verification: {e}")


    def update_dns_record(self, zone_id, dns_record_id, name, type, content):
        try:
            self.cf.dns.records.update(
                zone_id=zone_id,
                dns_record_id=dns_record_id,
                name=name,
                type=type,
                content=content
            )
        except APIError as e:
            raise e
