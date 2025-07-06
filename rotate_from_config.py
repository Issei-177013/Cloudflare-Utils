from config_manager import load_config
from cloudflare import Cloudflare, APIError

def rotate_ip(ip_list, current_ip):
    if current_ip not in ip_list:
        return ip_list[0]
    idx = ip_list.index(current_ip)
    return ip_list[(idx + 1) % len(ip_list)]

def run_rotation():
    config = load_config()
    for account in config["accounts"]:
        cf = Cloudflare(api_token=account["api_token"])
        for zone in account.get("zones", []):
            zone_id = zone["zone_id"]
            try:
                records = cf.dns.records.list(zone_id=zone_id)
            except APIError as e:
                print(f"❌ Zone fetch error: {zone['domain']}: {e}")
                continue

            for cfg_record in zone.get("records", []):
                matching = next((r for r in records if r["name"] == cfg_record["name"]), None)
                if not matching:
                    print(f"⚠️ Record not found: {cfg_record['name']}")
                    continue

                new_ip = rotate_ip(cfg_record["ips"], matching["content"])
                try:
                    cf.dns.records.update(
                        zone_id=zone_id,
                        dns_record_id=matching["id"],
                        name=cfg_record["name"],
                        type=cfg_record["type"],
                        content=new_ip,
                        proxied=cfg_record.get("proxied", False)
                    )
                    print(f"✅ Updated {cfg_record['name']} to {new_ip}")
                except APIError as e:
                    print(f"❌ Update error: {e}")

if __name__ == "__main__":
    run_rotation()
