import time
import random
from .config import load_config, load_rotation_status, save_rotation_status, DEFAULT_ROTATION_INTERVAL_MINUTES
from .state_manager import load_state, save_state
from .cloudflare_api import CloudflareAPI
from .logger import logger
from cloudflare import APIError

def rotate_ips_between_records(cf_api, zone_id, records, order):
    """
    Rotates IPs among selected DNS records based on a custom order.
    
    Args:
        cf_api: CloudflareAPI instance
        zone_id: Cloudflare zone ID
        records: Full list of records fetched from Cloudflare
        order: List of indices (integers) indicating user-selected order
    """
    logger.info(f"[IP Rotator] Rotating IPs for {len(order)} records by custom order.")

    # Extract the selected records based on user order
    ordered_records = [records[i] for i in order]
    original_ips = [r.content for r in ordered_records]

    logger.debug(f"Original IPs in order: {original_ips}")

    # Perform rotation (left shift): last IP goes to first record
    rotated_ips = original_ips[-1:] + original_ips[:-1]

    logger.info(f"Rotated IPs: {rotated_ips}")

    # Update records with new IPs
    for rec, new_ip in zip(ordered_records, rotated_ips):
        if rec.content == new_ip:
            logger.debug(f"[Skip] {rec.name} already has IP {new_ip}.")
            continue

        try:
            cf_api.update_dns_record(
                zone_id=zone_id,
                dns_record_id=rec.id,
                name=rec.name,
                type=rec.type,
                content=new_ip
            )
            logger.info(f"[Update] {rec.name}: {rec.content} → {new_ip}")
        except APIError as e:
            logger.error(f"[Error] Failed to update {rec.name}: {e}")

    logger.info("[IP Rotator] Custom order IP rotation completed.")

def rotate_ip(ip_list, current_ip, logger):
    if not ip_list:
        logger.warning("IP list is empty. Cannot rotate.")
        return current_ip

    if current_ip not in ip_list:
        return ip_list[0]

    if len(ip_list) == 1:
        return ip_list[0]

    current_idx = ip_list.index(current_ip)
    next_idx = (current_idx + 1) % len(ip_list)
    new_ip = ip_list[next_idx]

    if new_ip == current_ip and len(set(ip_list)) > 1:
        logger.info(f"Initial rotation choice for {current_ip} resulted in the same IP ({new_ip}). Trying to find a different one.")
        next_idx = (next_idx + 1) % len(ip_list)
        new_ip = ip_list[next_idx]

    return new_ip

def run_rotation():
    config = load_config()
    rotation_status = load_rotation_status()
    state = load_state()
    current_time_seconds = time.time()

    # --- Handle Global Rotations ---
    if "global_rotations" in state:
        for name, global_config in state["global_rotations"].items():
            rotation_interval_minutes = global_config.get("rotation_interval_minutes", DEFAULT_ROTATION_INTERVAL_MINUTES)
            rotation_interval_seconds = rotation_interval_minutes * 60
            last_rotated_at_seconds = global_config.get("last_rotated_at", 0)

            if current_time_seconds - last_rotated_at_seconds < rotation_interval_seconds:
                logger.debug(f"Global rotation not due yet for '{name}'. Last rotated { (current_time_seconds - last_rotated_at_seconds) / 60:.1f} minutes ago. Interval: {rotation_interval_minutes} min.")
                continue
            
            account = next((acc for acc in config["accounts"] if acc["name"] == global_config["account_name"]), None)
            if not account:
                logger.warning(f"Account '{global_config['account_name']}' not found for global rotation '{name}'. Skipping.")
                continue
                
            cf_api = CloudflareAPI(account["api_token"])
            zone_id = global_config["zone_id"]
            
            try:
                records_from_cf = list(cf_api.list_dns_records(zone_id))
            except APIError as e:
                logger.error(f"Zone fetch error for global rotation '{name}': {global_config['zone_name']}: {e}")
                continue
                
            records_to_rotate = [r for r in records_from_cf if r.name in global_config["records"]]
            
            if len(records_to_rotate) != len(global_config["records"]):
                logger.warning(f"Could not find all records for global rotation '{name}' in zone '{global_config['zone_name']}'. Skipping rotation.")
                continue

            updated_records, new_rotation_index = rotate_ips_globally(
                records_to_rotate,
                global_config["ip_pool"],
                global_config["rotation_index"]
            )

            for update in updated_records:
                try:
                    cf_api.update_dns_record(
                        zone_id=zone_id,
                        dns_record_id=update["record_id"],
                        name=update["name"],
                        type=update["record_type"],
                        content=update["new_ip"]
                    )
                    logger.info(f"Updated {update['name']} to {update['new_ip']} as part of global rotation '{name}'")
                except APIError as e:
                    logger.error(f"Update error for {update['name']} in global rotation '{name}': {e}")
            
            global_config["rotation_index"] = new_rotation_index
            global_config["last_rotated_at"] = current_time_seconds
            
    save_state(state)

    for account in config["accounts"]:
        cf_api = CloudflareAPI(account["api_token"])
        for zone in account.get("zones", []):
            zone_id = zone["zone_id"]
            try:
                records_from_cf = list(cf_api.list_dns_records(zone_id))
            except APIError as e:
                logger.error(f"Zone fetch error: {zone['domain']}: {e}")
                continue

            # --- Handle single record rotations ---
            for cfg_record in zone.get("records", []):
                record_name = cfg_record["name"]
                record_key = f"{zone_id}_{record_name}"

                custom_interval_minutes = cfg_record.get("rotation_interval_minutes")
                rotation_interval_minutes = custom_interval_minutes if custom_interval_minutes is not None else DEFAULT_ROTATION_INTERVAL_MINUTES
                rotation_interval_seconds = rotation_interval_minutes * 60

                last_rotated_at_seconds = rotation_status.get(record_key, 0)
                if current_time_seconds - last_rotated_at_seconds < rotation_interval_seconds:
                    logger.debug(f"Rotation not due yet for {record_name}. Last rotated { (current_time_seconds - last_rotated_at_seconds) / 60:.1f} minutes ago. Interval: {rotation_interval_minutes} min.")
                    continue
                
                matching_cf_record = next((r for r in records_from_cf if r.name == record_name), None)
                if not matching_cf_record:
                    logger.warning(f"Record not found in Cloudflare: {record_name}")
                    continue

                current_ip_on_cf = matching_cf_record.content
                new_ip = rotate_ip(cfg_record["ips"], current_ip_on_cf, logger)
                
                if new_ip == current_ip_on_cf:
                    logger.info(f"IP for {record_name} is already {new_ip}. No update needed, but resetting rotation timer as per schedule.")
                    rotation_status[record_key] = current_time_seconds
                    continue

                try:
                    cf_api.update_dns_record(
                        zone_id=zone_id,
                        dns_record_id=matching_cf_record.id,
                        name=record_name,
                        type=cfg_record["type"],
                        content=new_ip
                    )
                    logger.info(f"Updated {record_name} to {new_ip}")
                    rotation_status[record_key] = current_time_seconds
                except APIError as e:
                    logger.error(f"Update error for {record_name}: {e}")

            # --- Handle rotation groups ---
            for group in zone.get("rotation_groups", []):
                group_name = group["name"]
                group_key = f"{zone_id}_{group_name}"

                rotation_interval_minutes = group.get("rotation_interval_minutes", DEFAULT_ROTATION_INTERVAL_MINUTES)
                rotation_interval_seconds = rotation_interval_minutes * 60

                last_rotated_at_seconds = rotation_status.get(group_key, 0)
                if current_time_seconds - last_rotated_at_seconds < rotation_interval_seconds:
                    logger.debug(f"Rotation not due yet for group '{group_name}'. Last rotated { (current_time_seconds - last_rotated_at_seconds) / 60:.1f} minutes ago. Interval: {rotation_interval_minutes} min.")
                    continue

                # Find the CF records that match the names in the group
                group_record_names = group["records"]
                group_records_from_cf = [r for r in records_from_cf if r.name in group_record_names]

                if len(group_records_from_cf) != len(group_record_names):
                    logger.warning(f"Could not find all records for group '{group_name}' in zone '{zone['domain']}'. Skipping rotation.")
                    continue
                
                if len(group_records_from_cf) < 2:
                    logger.warning(f"Rotation group '{group_name}' has fewer than 2 valid records. Skipping rotation.")
                    continue

                # The rotate_ips_between_records function expects indices, so we create a list of indices
                # corresponding to the records' positions in the *original* records_from_cf list.
                indices_for_rotation = [i for i, record in enumerate(records_from_cf) if record.name in group_record_names]

                logger.info(f"Rotating IPs for group '{group_name}'...")
                rotate_ips_between_records(cf_api, zone_id, records_from_cf, indices_for_rotation)
                rotation_status[group_key] = current_time_seconds
    
    save_rotation_status(rotation_status)

def rotate_ips_globally(records, ip_pool, rotation_index):
    """
    Rotates a shared list of IPs across multiple DNS records in a synchronized, round-robin manner.

    Args:
        records (list): A list of DNS record objects to be updated. Each object must have 'name' and 'content' attributes.
        ip_pool (list): A shared list of available IPs.
        rotation_index (int): The starting index for the IP rotation.

    Returns:
        tuple: A tuple containing:
            - list: A list of dictionaries, where each dictionary represents an updated record
                    and contains 'name', 'old_ip', and 'new_ip'.
            - int: The updated rotation_index for the next run.
    """
    updated_records = []
    pool_size = len(ip_pool)

    if pool_size == 0:
        logger.warning("[IP Rotator] IP pool is empty. No rotation can be performed.")
        return [], rotation_index

    for i, record in enumerate(records):
        new_ip_index = (rotation_index + i) % pool_size
        new_ip = ip_pool[new_ip_index]
        
        if record.content != new_ip:
            updated_records.append({
                "name": record.name,
                "old_ip": record.content,
                "new_ip": new_ip,
                "record_id": record.id,
                "record_type": record.type
            })
            logger.info(f"Scheduled update for {record.name}: {record.content} → {new_ip}")
        else:
            logger.info(f"No change needed for {record.name}, IP is already {new_ip}.")

    # Update the global rotation index
    new_rotation_index = (rotation_index - 1 + pool_size) % pool_size
    
    logger.info(f"Global rotation index updated from {rotation_index} to {new_rotation_index}")

    return updated_records, new_rotation_index


if __name__ == "__main__":
    run_rotation()