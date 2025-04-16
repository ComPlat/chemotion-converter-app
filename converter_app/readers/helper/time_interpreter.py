import re

def time_string_to_hours(time_str):
    """
    Converts a flexible time string like '1 hour 5 minutes 30.5 seconds' to float hours.
    Handles any order of units, missing parts, and decimal commas.
    """
    # Normalize the string: lowercase and replace comma with dot for decimals
    time_str = time_str.replace(",", ".").lower()

    # Initialize time values
    hours = minutes = seconds = 0.0

    # Use regex to find all (number, unit) pairs
    matches = re.findall(r'([\d\.]+)\s*(hours|minutes|seconds)', time_str)
    for value, unit in matches:
        value = float(value)
        if unit == "hours":
            hours = value
        elif unit == "minutes":
            minutes = value
        elif unit == "seconds":
            seconds = value

    # Convert total time to hours
    return hours + (minutes / 60) + (seconds / 3600)