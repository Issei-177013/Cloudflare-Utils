"""
Client-side helper functions.
"""
import datetime

def format_period_date(entry: dict, period: str) -> str:
    """
    Formats a date for a given period from a vnstat data entry.

    Args:
        entry (dict): The data entry from vnstat, which may contain
                      a 'timestamp' or a 'date' dictionary.
        period (str): The time period, one of 'f', 'h', 'd', 'm', 'y', 't'.

    Returns:
        str: A human-readable, formatted date string.
    """
    if 'timestamp' in entry:
        dt = datetime.datetime.fromtimestamp(entry['timestamp'], datetime.timezone.utc)
        if period == 'f':
            return dt.strftime('%Y-%m-%d %H:%M')
        if period == 'h':
            return dt.strftime('%Y-%m-%d %H:00')
        if period in ['d', 't']:
            return dt.strftime('%Y-%m-%d')
        if period == 'm':
            return dt.strftime('%Y-%m')
        if period == 'y':
            return dt.strftime('%Y')

    date_info = entry.get('date', {})
    year = date_info.get('year', 'YYYY')
    month = date_info.get('month')
    day = date_info.get('day')

    # Yearly: YYYY
    if period == 'y':
        return str(year)

    # Monthly: YYYY-MM
    if period == 'm':
        return f"{year}-{month:02d}" if month else str(year)

    # Daily / Top Days: YYYY-MM-DD
    if period in ['d', 't']:
        if month and day:
            return f"{year}-{month:02d}-{day:02d}"
        elif month:
            return f"{year}-{month:02d}"
        else:
            return str(year)

    time_info = entry.get('time', {})
    hour = time_info.get('hour', 0)
    minute = time_info.get('minute', 0)

    # Hourly: YYYY-MM-DD HH:00
    if period == 'h':
        date_part = f"{year}-{month:02d}-{day:02d}" if month and day else str(year)
        return f"{date_part} {hour:02d}:00"

    # Five Minutes: YYYY-MM-DD HH:MM
    if period == 'f':
        date_part = f"{year}-{month:02d}-{day:02d}" if month and day else str(year)
        return f"{date_part} {hour:02d}:{minute:02d}"

    return "Invalid Period"
