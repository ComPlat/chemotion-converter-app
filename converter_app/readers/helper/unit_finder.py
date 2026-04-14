import inspect
import html
import re
import uuid
from dataclasses import dataclass
from types import MappingProxyType
from typing import Iterable

from astropy import units as u
from astropy.units import NamedUnit, PrefixUnit, StructuredUnit
from converter_app import options

BRACKET_UNIT_PATTERN = re.compile(r"\\?\[([^\]]+)\]")
PARENTHESIS_UNIT_PATTERN = re.compile(r"\(([^()]+)\)")
CELL_SPLIT_PATTERN = re.compile(r"[\t;|]+")
UNIT_MULTIPLY_SPACE_PATTERN = re.compile(r"(?<=[0-9A-Za-zµΩ°⁰¹²³⁴⁵⁶⁷⁸⁹]) (?=[A-Za-zµΩ°])")
UNICODE_POWER_TRANSLATION = str.maketrans({
    "⁰": "0",
    "¹": "1",
    "²": "2",
    "³": "3",
    "⁴": "4",
    "⁵": "5",
    "⁶": "6",
    "⁷": "7",
    "⁸": "8",
    "⁹": "9",
    "⁻": "-",
})
EXPONENT_PATTERN = re.compile(r"(?<=[A-Za-zµΩ°])(-?\d+)")

UNIT_RESULT_NAMESPACE = uuid.uuid5(
    uuid.NAMESPACE_DNS,
    "chemConverter-unit-finder-namespace",
)


@dataclass(frozen=True)
class UnitRule:
    source_unit: u.UnitBase
    base_unit: u.UnitBase | None = None
    conversion_factor: float | None = None


StdUnits = MappingProxyType({
    "%": UnitRule(u.percent),
    "°C": UnitRule(u.deg_C, u.K, 1.0),
    "deg C": UnitRule(u.deg_C, u.K, 1.0),
    "deg. C": UnitRule(u.deg_C, u.K, 1.0),
    "bar a": UnitRule(u.bar, u.Pa),
    "bar": UnitRule(u.bar, u.Pa),
    "hPa": UnitRule(u.hPa, u.Pa),
    "mbar": UnitRule(u.mbar, u.Pa),
    "Torr": UnitRule(u.Torr, u.Pa),
    "ml/min": UnitRule(u.mL / u.min),
    "mL/min": UnitRule(u.mL / u.min),
    "L/h": UnitRule(u.L / u.h, u.m**3 / u.s),
    "mL/h": UnitRule(u.mL / u.h, u.m**3 / u.s),
    "µL/min": UnitRule(u.uL / u.min, u.m**3 / u.s),
    "uL/min": UnitRule(u.uL / u.min, u.m**3 / u.s),
    "kWh": UnitRule(u.kW * u.h, u.J),
    "Wh": UnitRule(u.W * u.h, u.J),
    "Ah": UnitRule(u.A * u.h, u.C),
    "mAh": UnitRule(u.mA * u.h, u.C),
    "mS/cm": UnitRule(u.mS / u.cm, u.S / u.m),
    "µS/cm": UnitRule(u.uS / u.cm, u.S / u.m),
    "uS/cm": UnitRule(u.uS / u.cm, u.S / u.m),
    "cm-1": UnitRule(1 / u.cm, 1 / u.m),
    "cm^-1": UnitRule(1 / u.cm, 1 / u.m),
    "1/cm": UnitRule(1 / u.cm, 1 / u.m),
    "N/mm²": UnitRule(u.N / (u.mm ** 2), u.Pa),
    "N/mm2": UnitRule(u.N / (u.mm ** 2), u.Pa),
    "mg/L": UnitRule(u.mg / u.L, u.kg / (u.m ** 3)),
    "µg/L": UnitRule(u.ug / u.L, u.kg / (u.m ** 3)),
    "ug/L": UnitRule(u.ug / u.L, u.kg / (u.m ** 3)),
    "g/L": UnitRule(u.g / u.L, u.kg / (u.m ** 3)),
    "mg/mL": UnitRule(u.mg / u.mL, u.kg / (u.m ** 3)),
    "deg/s": UnitRule(u.deg / u.s, u.rad / u.s),
    "°/s": UnitRule(u.deg / u.s, u.rad / u.s),
    "unix seconds": UnitRule(u.s),
    "Time (unix seconds)": UnitRule(u.s),
})


class UnitFinder:
    """
    Find unit strings in plain text values and convert them to simple SI-like base unit metadata.

    This class intentionally stays small:
    - it does not traverse nested reader results yet
    - it works on plain string iterables
    - it supports instance-specific custom mappings
    """

    def __init__(
        self,
        custom_unit_map: dict[str, UnitRule] | None = None,
        ignore_dimless: bool = True,
    ):
        self.unit_map = dict(StdUnits)
        self.ignore_dimless = ignore_dimless
        self.found_units = []
        if custom_unit_map:
            self.unit_map.update(custom_unit_map)

    def add_custom_unit(
        self,
        unit_text: str,
        source_unit: str | u.UnitBase,
        base_unit: str | u.UnitBase | None = None,
        conversion_factor: float | None = None,
    ) -> None:
        normalized_unit_text = self.normalize_text(unit_text)
        normalized_source_unit = self.to_unit(source_unit)
        normalized_base_unit = self.to_unit(base_unit) if base_unit is not None else None
        self.unit_map[normalized_unit_text] = UnitRule(
            source_unit=normalized_source_unit,
            base_unit=normalized_base_unit,
            conversion_factor=conversion_factor,
        )

    @staticmethod
    def get_si_units(include_prefixes: bool = False) -> list[u.UnitBase]:
        """
        Return named units registered in the Astropy SI unit namespace.

        By default, prefixed units such as ``cm`` or ``mA`` are excluded, so the
        result contains SI base units and non-prefixed derived SI units only.
        """
        units = []
        seen = set()

        for _, unit in inspect.getmembers(u.si):
            if not isinstance(unit, NamedUnit):
                continue
            if not include_prefixes and isinstance(unit, PrefixUnit):
                continue

            unit_key = unit.to_string()
            if unit_key in seen:
                continue

            seen.add(unit_key)
            units.append(unit)

        return units

    def find_units(self, values: Iterable[str]) -> list[dict[str, str | float]]:
        results = []
        seen_units = set()

        for value in values:
            for unit_text in self._extract_candidates(value):
                if unit_text in seen_units:
                    continue

                result = self._build_result(unit_text)
                if result is None:
                    continue

                seen_units.add(unit_text)
                results.append(result)

        self.found_units = results
        return results

    def found_units_to_options_list(self):
        """only usable in the front end if you manage to update the api endpoint.
        For the web app use the self.units.append method *inside a reader* and fill the dropdowns using JS in the front end instead."""
        for unit in self.found_units:
            options.XUNITS += tuple([unit["found"]])
            options.YUNITS += tuple([unit["found"]])

    def get_rule(self, unit_text: str) -> UnitRule | None:
        normalized_unit_text = self.normalize_text(unit_text)
        rule = self.unit_map.get(normalized_unit_text)
        if rule is not None:
            return rule

        try:
            source_unit = self.to_unit(normalized_unit_text)
        except Exception:
            return None

        if isinstance(source_unit, StructuredUnit):
            return None

        return UnitRule(source_unit=source_unit)

    def resolve_unit(self, unit_text: str) -> u.UnitBase | None:
        rule = self.get_rule(unit_text)
        if rule is None:
            return None
        return rule.source_unit


    def _extract_candidates(self, value: str) -> list[str]:
        candidates = []
        seen_candidates = set()

        for segment in self._split_segments(value):
            normalized_segment = self.normalize_text(segment)
            if not normalized_segment:
                continue

            for match in BRACKET_UNIT_PATTERN.findall(normalized_segment):
                normalized_match = self.normalize_text(match)
                if normalized_match and normalized_match not in seen_candidates:
                    seen_candidates.add(normalized_match)
                    candidates.append(normalized_match)

            for match in PARENTHESIS_UNIT_PATTERN.findall(normalized_segment):
                normalized_match = self.normalize_text(match)
                if normalized_match and normalized_match not in seen_candidates:
                    seen_candidates.add(normalized_match)
                    candidates.append(normalized_match)

            if normalized_segment not in seen_candidates:
                seen_candidates.add(normalized_segment)
                candidates.append(normalized_segment)

        return candidates

    def _split_segments(self, value: str) -> list[str]:
        raw_value = self._prepare_raw_text(value)
        segments = [raw_value]

        if CELL_SPLIT_PATTERN.search(raw_value):
            segments.extend(CELL_SPLIT_PATTERN.split(raw_value))

        return segments

    def _build_result(self, unit_text: str) -> dict[str, str | float] | None:
        rule = self.get_rule(unit_text)
        if rule is None:
            return None

        base_unit = self._get_base_unit(rule)
        if self.ignore_dimless and base_unit == u.dimensionless_unscaled:
            return None
        conversion_factor = self._get_conversion_factor(rule, base_unit)

        base_unit = self._format_unit(base_unit)

        uuid_name = f"{unit_text}|{conversion_factor:.12g}|{base_unit}"

        return {
            "found": unit_text,
            "conversion_factor": conversion_factor,
            "base_unit": base_unit,
            "uuid": uuid.uuid5(UNIT_RESULT_NAMESPACE, uuid_name)
        }

    def _get_base_unit(self, rule: UnitRule) -> u.UnitBase:
        if rule.base_unit is not None:
            return rule.base_unit
        return (1 * rule.source_unit).si.unit

    def _get_conversion_factor(self, rule: UnitRule, base_unit: u.UnitBase) -> float:
        """
        Return the numeric conversion factor that belongs to the resolved base unit.

        The important detail is that Astropy keeps the scale and the unit separate by
        converting a unit into a Quantity first.

        Example with ``cm``:
        - ``source_unit`` is ``u.cm``
        - ``1 * source_unit`` creates the Quantity ``1 cm``
        - ``(1 * source_unit).si`` returns the SI Quantity ``0.01 m``
        - ``(1 * source_unit).si.value`` is ``0.01``
        - ``(1 * source_unit).si.unit`` is ``m``

        This means:
        - the base unit comes from the SI Quantity's ``unit``
        - the conversion factor comes from the SI Quantity's ``value``

        That is why auto-detected units use ``(1 * rule.source_unit).si.value``.
        It correctly separates the scale from the final unit representation.

        Without this Quantity step, scaled SI units such as ``mA`` could end up looking
        like ``0.001 A`` as the base unit, while the factor would incorrectly stay at
        ``1.0``. Using the SI Quantity avoids that problem:
        - ``(1 * u.mA).si.value`` -> ``0.001``
        - ``(1 * u.mA).si.unit`` -> ``A``

        When a custom rule already defines ``base_unit``, this method instead converts
        directly to that explicit target unit and returns only the numeric factor.
        """
        if rule.conversion_factor is not None:
            return rule.conversion_factor
        if rule.base_unit is None:
            return (1 * rule.source_unit).si.value
        return (1 * rule.source_unit).to(base_unit).value

    def to_unit(self, value: str | u.UnitBase) -> u.UnitBase:
        return self._to_unit(value)

    def _to_unit(self, value: str | u.UnitBase) -> u.UnitBase:
        if isinstance(value, str):
            return u.Unit(self._normalize_for_parser(value))
        return value

    def _format_unit(self, unit: u.UnitBase) -> str:
        if unit == u.dimensionless_unscaled:
            return "dimensionless"
        formatted_unit = unit.to_string("unicode")
        return UNIT_MULTIPLY_SPACE_PATTERN.sub("*", formatted_unit)

    @staticmethod
    def _normalize_for_parser(value: str) -> str:
        normalized_value = UnitFinder.normalize_text(value).translate(UNICODE_POWER_TRANSLATION)
        return EXPONENT_PATTERN.sub(r"**\1", normalized_value)

    @staticmethod
    def normalize_text(value: str) -> str:
        return " ".join(UnitFinder._prepare_raw_text(value).split())

    @staticmethod
    def _prepare_raw_text(value: str) -> str:
        return html.unescape(str(value)).replace("\\[", "[").replace("\\]", "]")

if __name__ == "__main__":
    testData = ["1000 [mL]; Hallo; Test \t kg/m*s² | km/h | kW*h"] # data allows splitting via tab, semicolon or pipe
    finder = UnitFinder()
    print(finder.find_units(testData))

    print("-----\n")

    print("All SI base units from the astropy package:")
    si_bases = getattr(u.si, "bases")
    print(si_bases)
    si_derived = UnitFinder.get_si_units()
    print(si_derived)

    print("-----\n")

    print("Adding found units to options for frontend usage:")
    finder.found_units_to_options_list()
    print(options.XUNITS)
    print(options.YUNITS)

    print("-----\n")

    print("EOC reached")
