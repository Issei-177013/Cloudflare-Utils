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
        Raises an APIError if the token is invalid or lacks permissions.
        """
        try:
            response = self.cf.zones.list()
            if not isinstance(response, dict) or "result" not in response:
                raise APIError("Unexpected API response format", request=None, body=response)
        except APIError:
            raise  # Let upstream handle it
        except Exception as e:
            raise APIError("Cloudflare API Error during token verification", request=None, body=str(e))


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