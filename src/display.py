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
