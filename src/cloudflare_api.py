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
        Verifies the API token by making a simple request to list zones.
        This is a lightweight way to check for authentication errors.
        """
        try:
            # We only need to know if the request succeeds, so we can limit the results.
            self.cf.zones.get(params={'per_page': 1})
        except APIError as e:
            # Re-raise the exception to be handled by the caller
            raise e

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
