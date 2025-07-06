import json
import os

CONFIG_PATH = "/opt/Cloudflare-Utils/configs.json"

def load_config():
    if not os.path.exists(CONFIG_PATH):
        return {"accounts": []}
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

def save_config(data):
    with open(CONFIG_PATH, "w") as f:
        json.dump(data, f, indent=2)

def find_account(data, account_name):
    return next((a for a in data["accounts"] if a["name"] == account_name), None)

def find_zone(account, domain):
    return next((z for z in account["zones"] if z["domain"] == domain), None)

def find_record(zone, record_name):
    return next((r for r in zone["records"] if r["name"] == record_name), None)
