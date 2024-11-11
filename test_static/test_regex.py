import re
import pytest

from converter_app.readers.helper.base import Reader

# The regex pattern we are testing
pattern = Reader.float_pattern

def is_match(s: str):
    """
    Helper function to test if a string matches the pattern
    :param s:
    :return:
    """
    rs = re.findall(pattern, s)
    return len(rs) == 1 and len(rs[0]) == len(s)

@pytest.mark.parametrize("test_input,expected", [
    # 1. Simple Integers
    ("42", True),              # Positive integer
    ("-42", True),             # Negative integer
    ("+42", True),             # Leading plus
    ("0", True),               # Zero
    ("000", True),             # Multiple zeros

    # 2. Decimal Numbers
    ("42.5", True),            # Basic decimal
    (".5", True),              # Decimal with leading dot
    ("0.5", True),             # Decimal with leading zero
    ("42.", False),            # Decimal with trailing dot (invalid)
    ("42,5", True),            # Comma as decimal separator

    # 3. Scientific Notation
    ("1e10", True),            # Basic scientific notation
    ("1E10", True),            # Uppercase E
    ("1e-10", True),           # Negative exponent
    ("1e+10", True),           # Positive exponent
    ("e10", False),            # No digits before exponent (invalid)

    # 4. Edge Cases
    ("", False),               # Empty string (invalid)
    ("   ", False),            # Whitespace-only (invalid)
    (" 42 ", False),            # Spaces around number (invalid)
    ("+", False),              # Only sign (invalid)
    ("-", False),              # Only sign (invalid)
    ("++42", False),           # Multiple signs (invalid)
    ("--42", False),           # Multiple signs (invalid)
    ("42abc", False),          # Invalid characters in the number (invalid)

    # 5. Invalid Formats
    ("42.5.1", False),         # Multiple decimal separators (invalid)
    (".", False),              # Only decimal separator (invalid)
    ("1e", False),             # Only scientific notation sign (invalid)
    ("e", False),             # Scientific notation without exponent (invalid)

    # 6. Numbers with Commas (International)
    ("1,000", True),          # Number with commas as thousands separators
    ("1,000.5", False),        # Mixed usage of commas and dots (invalid)

    # 7. Leading and Trailing Spaces
    (" 42", False),             # Leading space (invalid)
    ("42 ", True),             # Trailing space
    ("  42.5  ", False),        # Leading and trailing spaces (invalid)
])

def test_regex_match(test_input, expected):
    """
    tests the float regex

    :param test_input:
    :param expected:
    :return:
    """

    assert is_match(test_input) == expected
