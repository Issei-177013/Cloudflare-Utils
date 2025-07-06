from config_manager import load_config, save_config, find_account, find_zone, find_record
import os

def input_list(prompt):
    return input(prompt).strip().split(',')

def add_account():
    data = load_config()
    name = input("Account name: ").strip()
    token = input("API Token: ").strip()
    if find_account(data, name):
        print("❌ Account already exists")
        return
    data["accounts"].append({"name": name, "api_token": token, "zones": []})
    save_config(data)
    print("✅ Account added")

def add_zone():
    data = load_config()
    name = input("Account name: ").strip()
    acc = find_account(data, name)
    if not acc:
        print("❌ Account not found")
        return
    domain = input("Zone domain (e.g. example.com): ").strip()
    zone_id = input("Zone ID: ").strip()
    if find_zone(acc, domain):
        print("❌ Zone already exists")
        return
    acc["zones"].append({"domain": domain, "zone_id": zone_id, "records": []})
    save_config(data)
    print("✅ Zone added")

def add_record():
    data = load_config()
    acc_name = input("Account name: ").strip()
    acc = find_account(data, acc_name)
    if not acc:
        print("❌ Account not found")
        return

    domain = input("Zone domain: ").strip()
    zone = find_zone(acc, domain)
    if not zone:
        print("❌ Zone not found")
        return

    name = input("Record name (e.g. vpn.example.com): ").strip()
    if find_record(zone, name):
        print("❌ Record already exists")
        return
    ip_list = input_list("Enter IPs (comma separated): ")
    rec_type = input("Record type (A/CNAME): ").strip().upper()
    proxied = input("Proxied (yes/no): ").strip().lower() == 'yes'

    zone["records"].append({
        "name": name,
        "type": rec_type,
        "ips": ip_list,
        "proxied": proxied
    })

    save_config(data)
    print("✅ Record added")

def list_all():
    data = load_config()
    for acc in data["accounts"]:
        print(f"🧾 Account: {acc['name']}")
        for zone in acc["zones"]:
            print(f"  🌐 Zone: {zone['domain']}")
            for r in zone["records"]:
                print(f"    📌 Record: {r['name']} | Type: {r['type']} | IPs: {r['ips']}")

def main_menu():
    while True:
        print("\n--- Cloudflare Utils Manager ---")
        print("1. Add Account")
        print("2. Add Zone to Account")
        print("3. Add Record to Zone")
        print("4. List All Records")
        print("5. Exit")

        choice = input("Enter your choice: ").strip()
        if choice == "1":
            add_account()
        elif choice == "2":
            add_zone()
        elif choice == "3":
            add_record()
        elif choice == "4":
            list_all()
        elif choice == "5":
            break
        else:
            print("❌ Invalid choice")

if __name__ == "__main__":
    main_menu()
