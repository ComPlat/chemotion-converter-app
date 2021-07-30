import re


def human2bytes(string):
    if not string:
        return 0

    m = re.match(r'([0-9.]+)\s*([A-Za-z]+)', string)
    number, unit = float(m.group(1)), m.group(2).strip().lower()

    if unit == 'kb' or unit == 'k':
        return number * 1000
    elif unit == 'mb' or unit == 'm':
        return number * 1000**2
    elif unit == 'gb' or unit == 'g':
        return number * 1000**3
    elif unit == 'tb' or unit == 't':
        return number * 1000**4
    elif unit == 'pb' or unit == 'p':
        return number * 1000**5
    elif unit == 'kib':
        return number * 1024
    elif unit == 'mib':
        return number * 1024**2
    elif unit == 'gib':
        return number * 1024**3
    elif unit == 'tib':
        return number * 1024**4
    elif unit == 'pib':
        return number * 1024**5
