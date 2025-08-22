"""
Core Zone Management Logic.

This module provides the business logic for managing Cloudflare zones.
It handles the interaction with the Cloudflare API for zone-related
operations, without any presentation-layer code.
"""
from .cloudflare_api import CloudflareAPI

def list_zones(api_token):
    """
    Lists all zones for a given account.

    Args:
        api_token (str): The Cloudflare API token.

    Returns:
        list: A list of zone objects from the Cloudflare API.
    """
    cf_api = CloudflareAPI(api_token)
    return list(cf_api.list_zones())

def get_zone_details(api_token, zone_id):
    """
    Retrieves the details for a specific zone.

    Args:
        api_token (str): The Cloudflare API token.
        zone_id (str): The ID of the zone.

    Returns:
        dict: The zone details object from the Cloudflare API.
    """
    cf_api = CloudflareAPI(api_token)
    return cf_api.get_zone_details(zone_id)

def add_zone(api_token, domain_name, zone_type='full'):
    """
    Adds a new zone to Cloudflare.

    Args:
        api_token (str): The Cloudflare API token.
        domain_name (str): The domain name to add.
        zone_type (str): The type of zone to create ('full' or 'partial').

    Returns:
        dict: The new zone object from the Cloudflare API.
    """
    cf_api = CloudflareAPI(api_token)
    return cf_api.add_zone(domain_name, zone_type=zone_type)

def delete_zone(api_token, zone_id):
    """
    Deletes a zone from Cloudflare.

    Args:
        api_token (str): The Cloudflare API token.
        zone_id (str): The ID of the zone to delete.
    """
    cf_api = CloudflareAPI(api_token)
    cf_api.delete_zone(zone_id)

def get_zone_core_settings(api_token, zone_id):
    """
    Retrieves the core settings for a specific zone.

    Args:
        api_token (str): The Cloudflare API token.
        zone_id (str): The ID of the zone.

    Returns:
        dict: A dictionary of the zone's core settings.
    """
    cf_api = CloudflareAPI(api_token)
    return cf_api.get_zone_core_settings(zone_id)

def update_zone_setting(api_token, zone_id, setting_name, value):
    """
    Updates a specific setting for a zone.

    Args:
        api_token (str): The Cloudflare API token.
        zone_id (str): The ID of the zone.
        setting_name (str): The name of the setting to update.
        value (any): The new value for the setting.
    """
    cf_api = CloudflareAPI(api_token)
    cf_api.update_zone_setting(zone_id, setting_name, value)