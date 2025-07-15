def display_as_table(data, headers):
    """
    Displays a list of dictionaries as a formatted table.

    :param data: A list of dictionaries.
    :param headers: A list of keys to display as columns.
    """
    if not data:
        print("No data to display.")
        return

    # Calculate column widths
    column_widths = {header: len(header) for header in headers}
    for row in data:
        for header in headers:
            column_widths[header] = max(column_widths[header], len(str(row.get(header, ""))))

    # Print header
    header_line = " | ".join(f"{header:<{column_widths[header]}}" for header in headers)
    print(f"+-{'--+-'.join('-' * column_widths[header] for header in headers)}-+")
    print(f"| {header_line} |")
    print(f"+-{'--+-'.join('-' * column_widths[header] for header in headers)}-+")

    # Print data
    for row in data:
        row_line = " | ".join(f"{str(row.get(header, '')):<{column_widths[header]}}" for header in headers)
        print(f"| {row_line} |")

    print(f"+-{'--+-'.join('-' * column_widths[header] for header in headers)}-+")
