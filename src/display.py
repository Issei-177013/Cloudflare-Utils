from tabulate import tabulate

def truncate_text(text, max_length=30):
    """Truncates text to a certain length, adding '...' if truncated."""
    if len(text) > max_length:
        return text[:max_length-3] + "..."
    return text

def summarize_list(items, max_items=2):
    """
    Summarizes a list of strings for display.
    If the list has more than max_items, it shows the first and last items separated by '...'.
    """
    if not items:
        return ""
    if len(items) > max_items:
        return f"{items[0]}...{items[-1]}"
    return ", ".join(items)

from .config import REQUIRED_PERMISSIONS

def display_as_table(data, headers):
    """
    Displays a list of dictionaries as a formatted table using the tabulate library.

    :param data: A list of dictionaries.
    :param headers: A list of keys to display as columns.
    """
    if not data:
        print("No data to display.")
        return

    # The tabulate function can directly take a list of dictionaries and headers.
    print(tabulate(data, headers=headers, tablefmt="grid"))

def display_token_guidance():
    """
    Displays guidance for creating a Cloudflare API token, including required permissions.
    """
    print("\n🔐 How to create a valid Cloudflare API Token:")
    print("Go to: https://dash.cloudflare.com/profile/api-tokens")
    print('1. Click "Create Token"')
    print('2. Select "Custom Token"')
    print("3. Add the following permissions:")

    # Prepare data for the table
    permissions_list = []
    for perm, level in REQUIRED_PERMISSIONS['permissions'].items():
        permissions_list.append({
            'Permission': perm,
            'Access': level
        })

    # Display the table
    headers = {'Permission': 'Permission', 'Access': 'Access'}
    display_as_table(permissions_list, headers)

    print("\n4. Apply to all zones")
    print("5. Create and copy the token")
