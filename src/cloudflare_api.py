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
        """
        Returns a list of all zones available in the account.
        """
        try:
            return self.cf.zones.list()
        except APIError as e:
            raise e

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