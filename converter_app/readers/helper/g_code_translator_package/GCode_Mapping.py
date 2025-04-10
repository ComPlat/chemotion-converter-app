import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from abc import ABC, abstractmethod
from enum import Enum, auto


class GCodeFlavor(Enum):
    GENERIC = auto()
    MARLIN = auto()
    KLIPPER = auto()
    # REPETIER = auto()


class GCode_Mapping(ABC):
    def __init__(self):
        self.gcode_type = GCodeFlavor.GENERIC
        print("Initializing GCode Mapping for ...")

    def fetch_gcode_mapping(self):
        pass

    def set_type(self, found_type):
        self.gcode_type = found_type


class MarlinGcodeScraper(GCode_Mapping):
    def __init__(self, url="https://marlinfw.org/meta/gcode/"):
        """
        Initializes a headless Chrome driver via Selenium
        to load JavaScript-based content from the Marlin G-code page.
        """
        super().__init__()
        print("... Marlin")
        self.url = url
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run browser in headless mode
        chrome_options.add_argument("--disable-gpu")
        self.driver = webdriver.Chrome(options=chrome_options)

    def close(self):
        """Close the Selenium browser session."""
        self.driver.quit()

    def fetch_gcode_mapping(self):
        """
        Loads the Marlin G-code page in a real browser session,
        extracts the fully rendered HTML, and parses it into a single dictionary.
        If a code is a range (e.g. G0-G1), it splits into multiple entries:
            {
              "G0": "Linear Move",
              "G1": "Linear Move",
              ...
            }
        """
        self.driver.get(self.url)
        # Wait for JavaScript to load the dynamic content (adjust as needed or use explicit waits)
        time.sleep(3)

        # Get the rendered HTML
        html = self.driver.page_source
        soup = BeautifulSoup(html, "html.parser")

        gcode_map = {}

        # Find all <li> items that potentially contain G- or M-code info
        for li in soup.find_all("li"):
            li_text = li.get_text().strip()
            # Example of li_text could be: "G0-G1: Linear Move" or "G2: Arc or Circle Move"

            # Use a regex that captures:
            #   group(1): code(s) like "G0-G1" or "G2" or "M104"
            #   group(2): the description after a colon, space, or dash
            match = re.match(r'^([GM]\d+(?:-[GM]?\d+)?)(?:[:\s-]+)(.*)$', li_text, re.IGNORECASE)
            if not match:
                continue

            code_text, description = match.groups()
            description = description.strip()

            # Check if there's a dash (range), e.g. "G0-G1"
            if '-' in code_text:
                # e.g. "G0-G1", "G17-G19", "M104-M105"
                range_match = re.match(r'^([GM])(\d+)-([GM])?(\d+)$', code_text, re.IGNORECASE)
                if range_match:
                    letter_start, start_num, letter_end, end_num = range_match.groups()
                    # If letter_end is None, assume it's the same letter as the start
                    if not letter_end:
                        letter_end = letter_start

                    start_int = int(start_num)
                    end_int = int(end_num)
                    # Add an entry for each code in the range
                    for i in range(start_int, end_int + 1):
                        key = f"{letter_start}{i}"
                        gcode_map[key] = description
                else:
                    # If the format is unexpected, just store it as-is
                    gcode_map[code_text] = description
            else:
                # Single code, e.g. "G4"
                gcode_map[code_text] = description

        return gcode_map


if __name__ == "__main__":
    scraper = MarlinGcodeScraper()
    try:
        mapping = scraper.fetch_gcode_mapping()
        # Print each code sorted by alphanumeric order
        for code in sorted(mapping.keys()):
            print(f"{code}: {mapping[code]}")
    finally:
        scraper.close()
