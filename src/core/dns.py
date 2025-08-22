"""
Core DNS Record Management Logic.

This module provides the business logic for managing DNS records via the
Cloudflare API. It abstracts the direct API calls for listing, creating,
updating, and deleting DNS records.
"""
from .cloudflare_api import CloudflareAPI

def list_dns_records(api_token, zone_id):
    """
    Lists all DNS records for a given zone.

    Args:
        api_token (str): The Cloudflare API token.
        zone_id (str): The ID of the zone.

    Returns:
        list: A list of DNS record objects from the Cloudflare API.
    """
    cf_api = CloudflareAPI(api_token)
    return list(cf_api.list_dns_records(zone_id))

def create_dns_record(api_token, zone_id, name, record_type, content, proxied=False, ttl=None):
    """
    Creates a new DNS record.

    Args:
        api_token (str): The Cloudflare API token.
        zone_id (str): The ID of the zone.
        name (str): The record name.
        record_type (str): The record type (e.g., 'A', 'CNAME').
        content (str): The record content.
        proxied (bool, optional): Whether the record is proxied. Defaults to False.
        ttl (int, optional): The TTL for the record. Defaults to None.

    Returns:
        dict: The created DNS record object from the Cloudflare API.
    """
    cf_api = CloudflareAPI(api_token)
    return cf_api.create_dns_record(zone_id, name, record_type, content, proxied, ttl)

def update_dns_record(api_token, zone_id, record_id, name, record_type, content, proxied, ttl):
    """
    Updates an existing DNS record.

    Args:
        api_token (str): The Cloudflare API token.
        zone_id (str): The ID of the zone.
        record_id (str): The ID of the record to update.
        name (str): The new name for the record.
        record_type (str): The new type for the record.
        content (str): The new content for the record.
        proxied (bool): The new proxied status.
        ttl (int): The new TTL.
    """
    cf_api = CloudflareAPI(api_token)
    cf_api.update_dns_record(zone_id, record_id, name, record_type, content, proxied, ttl)

def delete_dns_record(api_token, zone_id, record_id):
    """
    Deletes a DNS record.

    Args:
        api_token (str): The Cloudflare API token.
        zone_id (str): The ID of the zone.
        record_id (str): The ID of the record to delete.
    """
    cf_api = CloudflareAPI(api_token)
    cf_api.delete_dns_record(zone_id, record_id)