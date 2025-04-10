def add_to_dict_smart(d: dict, key: str, value: str):
    """
    Adds a value to a dictionary under the given key.
    - If the key doesn't exist, the value is stored as a string.
    - If the key exists and the current value is a string, it is converted into a list.
    - If the key already holds a list, the new value is always appended (duplicates allowed).
    """
    if key not in d:
        # First entry for this key → store as a string
        d[key] = value
    else:
        current = d[key]
        if isinstance(current, list):
            # Append new value even if it's a duplicate
            current.append(value)
        else:
            # Convert single value to list and append new value
            d[key] = [current, value]