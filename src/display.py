from tabulate import tabulate

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
