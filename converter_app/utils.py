import base64
import datetime
import hashlib
import inspect
import os
import re
import shutil
import sys
import tempfile
import time
import uuid
from pathlib import Path
from typing import Optional

import git
import astropy.units as u

from converter_app.writers.jcamp import JcampWriter
from converter_app.writers.jcampzip import JcampZipWriter
from converter_app.writers.rdf import RDFWriter
from converter_app.writers.meta_info_json import MetaInfoWriter


def cli_home_path():
    return Path.home().joinpath('.ChemConverter')


def human2bytes(string):
    """
    Bytes size converter
    :param string: input unit string for example 100kb
    """
    if not string:
        return 0

    m = re.match(r'([0-9.]+)\s*([A-Za-z]+)', string)
    number, unit = float(m.group(1)), m.group(2).strip().lower()

    if unit in ['kb', 'k']:
        number = number * 1000
    elif unit in ['mb', 'm']:
        number = number * 1000 ** 2
    elif unit in ['gb', 'g']:
        number = number * 1000 ** 3
    elif unit in ['tb', 't']:
        number = number * 1000 ** 4
    elif unit in ['pb', 'p']:
        number = number * 1000 ** 5
    elif unit == 'kib':
        number = number * 1024
    elif unit == 'mib':
        number = number * 1024 ** 2
    elif unit == 'gib':
        number = number * 1024 ** 3
    elif unit == 'tib':
        number = number * 1024 ** 4
    elif unit == 'pib':
        number = number * 1024 ** 5
    return number


def check_uuid(string):
    """
    :param string: uuid string
    :return: True if string is a uuid
    """
    try:
        return uuid.UUID(string, version=4)
    except ValueError:
        return False


def checkpw(password, hashed_password):
    """
    :param password: Password string
    :param hashed_password: hashed password in htaccess
    :return: True if password is correct
    """
    m = hashlib.sha1()
    m.update(password)
    return (b'{SHA}' + base64.b64encode(m.digest())) == hashed_password


def run_conversion(converter, conversion_format):
    if converter:
        converter.process()
        if conversion_format == 'metajson':
            writer = MetaInfoWriter(converter)
        elif conversion_format == 'jcampzip':
            writer = JcampZipWriter(converter)
        elif conversion_format == 'rdf':
            writer = RDFWriter(converter)
        elif conversion_format == 'jcamp':
            if len(converter.tables) == 1:
                writer = JcampWriter(converter)
            else:
                raise ValueError('Conversion to a single JCAMP file is not supported for this file.')
        else:
            raise ValueError('Conversion format is not supported.')

        writer.process()
        return writer

    raise ValueError('Your file could not be processed. No Profile available!')


def load_public_profiles(profiles: Optional[str | Path] = None, data_files: Optional[str | Path] = None):
    with tempfile.TemporaryDirectory() as t:
        # Clone into temporary dir
        git.Repo.clone_from('https://github.com/ComPlat/chemotion_saurus.git', t, branch='added_data_files', depth=1)

        if profiles:
            os.makedirs(os.path.dirname(profiles), exist_ok=True)
            shutil.move(os.path.join(t, 'static/files/shared_ChemConverter_files/profiles'), profiles)
        if data_files:
            os.makedirs(os.path.dirname(data_files), exist_ok=True)
            shutil.move(os.path.join(t, 'static/files/shared_ChemConverter_files/data_files'), data_files)


def get_app_root() -> Path:
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)  # PyInstaller temp extraction dir
    else:
        return Path(__file__).parent.parent


def remove_keys(obj, keys_to_remove):
    """
    Returns a deep copy of ``obj`` with the given keys removed from any
    dictionaries it contains. Lists are traversed recursively. ``keys_to_remove``
    may be a single key or a list of keys.
    """
    if not isinstance(keys_to_remove, list):
        keys_to_remove = [keys_to_remove]

    if isinstance(obj, dict):
        return {
            k: v
            for k, v in obj.items()
            if k not in keys_to_remove
        }
    if isinstance(obj, list):
        return [remove_keys(item, keys_to_remove) for item in obj]
    return obj


def str_to_bool(value):
    """
    Converts the given value to a boolean by comparing its lowercase string
    representation against a set of truthy literals.
    """
    return str(value).lower() in ("true", "1", "yes", "on")


class FunctionTimer:

    class TimeMark:
        def __init__(self, function, lineno, filename):
            self.function = function
            self.lineno = lineno
            self.filename = filename
            self.start = time.perf_counter()
            self.end = None

        def stop(self):
            self.end = time.perf_counter()

        def toStr(self):
            return f'{self.function}\t{self.filename}:{self.lineno}\t{self.end-self.start}'

    def __init__(self):
        self.marks = []

    def start(self):
        stack = inspect.stack()
        caller = stack[1]
        print("Called from:", caller.function)
        print("Line:", caller.lineno)
        print("File:", caller.filename)
        marker = FunctionTimer.TimeMark(caller.function, caller.lineno, caller.filename)
        self.marks.append(marker)
        return marker

    def print(self):
        markers = [marker.toStr() for marker in self.marks]
        for marker in markers:
            print(marker)
        os.makedirs('___timer_results', exist_ok=True)
        with open(f'./___timer_results/timer{datetime.datetime.now(datetime.UTC).isoformat()}.txt', 'w+') as f:
            f.write('\n'.join(markers))

def _register_custom_units():
    """
    Register domain-specific units that astropy does not know out of the box,
    so that normalize_unit() output can always be parsed by ``u.Unit``.
    """
    u.imperial.enable()  # deg_F and other imperial units

    namespace = {}
    u.def_unit('rpm', u.cycle / u.min, namespace=namespace)          # agitation
    u.def_unit('U', u.umol / u.min, prefixes=True, namespace=namespace)  # enzyme unit (+ mU, ...)
    u.def_unit('ppm', 1e-6 * u.one, namespace=namespace)             # dimensionless concentration
    u.def_unit('ppb', 1e-9 * u.one, namespace=namespace)
    u.def_unit('px', u.pix, namespace=namespace)                     # pixel
    u.def_unit('Fd', 96485.33212 * u.C, namespace=namespace)         # faraday (charge per mol of e-)
    u.def_unit('atm', 101325 * u.Pa, namespace=namespace)            # standard atmosphere

    u.add_enabled_units(list(namespace.values()))


_register_custom_units()

UNIT_ALIASES = {
    # ---------- Length ----------
    "meter": "m",
    "meters": "m",
    "metre": "m",
    "metres": "m",

    "millimeter": "mm",
    "millimeters": "mm",
    "millimetre": "mm",

    "micrometer": "um",
    "micrometers": "um",
    "micrometre": "um",
    "µm": "um",

    "nanometer": "nm",
    "nanometers": "nm",

    "centimeter": "cm",
    "centimeters": "cm",

    "kilometer": "km",
    "kilometers": "km",

    "angstrom": "Angstrom",
    "ångström": "Angstrom",
    "Å": "Angstrom",

    # ---------- Mass ----------
    "gram": "g",
    "grams": "g",

    "kilogram": "kg",
    "kilograms": "kg",

    "milligram": "mg",
    "milligrams": "mg",

    "microgram": "ug",
    "micrograms": "ug",
    "µg": "ug",

    "nanogram": "ng",

    "tonne": "t",
    "metric ton": "t",

    # ---------- Time ----------
    "second": "s",
    "seconds": "s",

    "millisecond": "ms",
    "milliseconds": "ms",

    "microsecond": "us",
    "µs": "us",

    "minute": "min",
    "minutes": "min",

    "hour": "h",
    "hours": "h",

    # ---------- Temperature ----------
    "kelvin": "K",

    "°c": "deg_C",
    "deg c": "deg_C",
    "celsius": "deg_C",

    "°f": "deg_F",
    "deg f": "deg_F",
    "fahrenheit": "deg_F",

    # ---------- Amount ----------
    "mole": "mol",
    "moles": "mol",

    "millimole": "mmol",
    "millimoles": "mmol",

    "micromole": "umol",
    "µmol": "umol",

    "nanomole": "nmol",

    # ---------- Volume ----------
    "liter": "L",
    "liters": "L",
    "litre": "L",
    "litres": "L",

    "milliliter": "mL",
    "milliliters": "mL",
    "millilitre": "mL",

    "microliter": "uL",
    "microliters": "uL",
    "µl": "uL",
    "µL": "uL",

    "nanoliter": "nL",

    # ---------- Pressure ----------
    "pascal": "Pa",
    "pascals": "Pa",

    "kilopascal": "kPa",
    "megapascal": "MPa",

    "bar": "bar",
    "millibar": "mbar",

    "atmosphere": "atm",
    "atmospheres": "atm",

    "torr": "Torr",

    "mmhg": "mmHg",

    # ---------- Energy ----------
    "joule": "J",
    "joules": "J",

    "kilojoule": "kJ",

    "calorie": "cal",
    "calories": "cal",

    "kilocalorie": "kcal",

    "electronvolt": "eV",

    # ---------- Power ----------
    "watt": "W",
    "watts": "W",

    "kilowatt": "kW",

    # ---------- Force ----------
    "newton": "N",
    "newtons": "N",

    # ---------- Frequency ----------
    "hertz": "Hz",

    "kilohertz": "kHz",
    "megahertz": "MHz",
    "gigahertz": "GHz",

    # ---------- Voltage ----------
    "volt": "V",
    "volts": "V",

    "millivolt": "mV",

    "kilovolt": "kV",

    # ---------- Current ----------
    "amp": "A",
    "amps": "A",
    "ampere": "A",
    "amperes": "A",

    "milliamp": "mA",
    "microamp": "uA",

    # ---------- Resistance ----------
    "ohm": "Ohm",
    "Ω": "Ohm",

    "kiloohm": "kOhm",
    "megaohm": "MOhm",

    # ---------- Conductance ----------
    "siemens": "S",

    # ---------- Capacitance ----------
    "farad": "F",

    "microfarad": "uF",
    "µf": "uF",

    "nanofarad": "nF",
    "picofarad": "pF",

    # ---------- Inductance ----------
    "henry": "H",

    # ---------- Magnetic ----------
    "tesla": "T",
    "gauss": "G",

    # ---------- Radiation ----------
    "becquerel": "Bq",
    "gray": "Gy",
    "sievert": "Sv",

    # ---------- Concentration ----------
    "molar": "M",
    "molarity": "M",

    "mm": "mmol/L",
    "millimolar": "mmol/L",

    "um": "umol/L",
    "µmolar": "umol/L",

    "nm": "nmol/L",

    # ---------- Optical ----------
    "absorbance unit": "",
    "au": "",

    # ---------- Dimensionless ----------
    "%": "percent",
    "percent": "percent",
    "ppm": "ppm",
    "ppb": "ppb",

    # ---------- Compound units (astropy needs explicit operators) ----------
    # Electrical capacity (charge)
    "mah": "mA h",
    "ah": "A h",
    "as": "A s",
    "mah/g": "mA h / g",
    "ah/g": "A h / g",

    # Dynamic viscosity
    "pas": "Pa s",
    "mpas": "mPa s",

    # Reaction rate
    "mol/lmin": "mol / (L min)",
    "mol/ls": "mol / (L s)",

    # Electrical potential vs. reference/counter electrode (annotation is not a unit)
    "v vs. re": "V",
    "mv vs. re": "mV",
    "v vs. ce": "V",
    "mv vs. ce": "mV",
}

def normalize_unit(unit: str) -> str:
    unit = unit.strip()

    def replace_superscripts(s: str) -> str:
        return re.sub(r"<sup>(-?\d+)</sup>", r"\1", s)

    # Unicode normalization
    unit = replace_superscripts(
        unit.replace("µ", "u")
            .replace("μ", "u")
            .replace("°", "deg ")
            .replace("Ω", "Ohm")
            .replace("Ω", "Ohm")
    )

    return UNIT_ALIASES.get(unit.lower(), unit)