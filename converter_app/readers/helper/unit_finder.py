import html
import re
from dataclasses import dataclass
from typing import Iterable

from astropy import units as u


BRACKET_UNIT_PATTERN = re.compile(r"\\?\[([^\]]+)\]")
CELL_SPLIT_PATTERN = re.compile(r"[\t;|]+")


@dataclass(frozen=True)
class UnitRule:
    source_unit: u.UnitBase
    base_unit: u.UnitBase | None = None
    conversion_factor: float | None = None


class UnitFinder:
    """
    Find unit strings in plain text values and convert them to simple SI-like base unit metadata.

    This class intentionally stays small:
    - it does not traverse nested reader results yet
    - it works on plain string iterables
    - it supports instance-specific custom mappings
    """

    default_unit_map = {
        "%": UnitRule(u.percent),
        "°C": UnitRule(u.deg_C, u.K, 1.0),
        "deg C": UnitRule(u.deg_C, u.K, 1.0),
        "deg. C": UnitRule(u.deg_C, u.K, 1.0),
        "bar a": UnitRule(u.bar, u.Pa),
        "bar": UnitRule(u.bar, u.Pa),
        "ml/min": UnitRule(u.mL / u.min),
        "mL/min": UnitRule(u.mL / u.min),
    }

    def __init__(
        self,
        custom_unit_map: dict[str, UnitRule] | None = None,
        ignore_dimless: bool = True,
    ):
        self.unit_map = dict(self.default_unit_map)
        self.ignore_dimless = ignore_dimless
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
        normalized_source_unit = self._to_unit(source_unit)
        normalized_base_unit = self._to_unit(base_unit) if base_unit is not None else None
        self.unit_map[normalized_unit_text] = UnitRule(
            source_unit=normalized_source_unit,
            base_unit=normalized_base_unit,
            conversion_factor=conversion_factor,
        )

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

        return results

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
        rule = self.unit_map.get(unit_text)
        if rule is None:
            try:
                source_unit = u.Unit(unit_text)
            except Exception:
                return None
            rule = UnitRule(source_unit=source_unit)

        base_unit = self._get_base_unit(rule)
        if self.ignore_dimless and base_unit == u.dimensionless_unscaled:
            return None
        conversion_factor = self._get_conversion_factor(rule, base_unit)
        return {
            "found": unit_text,
            "conversion_factor": conversion_factor,
            "base_unit": self._format_unit(base_unit),
        }

    def _get_base_unit(self, rule: UnitRule) -> u.UnitBase:
        if rule.base_unit is not None:
            return rule.base_unit
        return (1 * rule.source_unit).si.unit

    def _get_conversion_factor(self, rule: UnitRule, base_unit: u.UnitBase) -> float:
        if rule.conversion_factor is not None:
            return rule.conversion_factor
        if rule.base_unit is None:
            return (1 * rule.source_unit).si.value
        return (1 * rule.source_unit).to(base_unit).value

    def _to_unit(self, value: str | u.UnitBase) -> u.UnitBase:
        if isinstance(value, str):
            return u.Unit(value)
        return value

    def _format_unit(self, unit: u.UnitBase) -> str:
        if unit == u.dimensionless_unscaled:
            return "dimensionless"
        return unit.to_string()

    @staticmethod
    def normalize_text(value: str) -> str:
        return " ".join(UnitFinder._prepare_raw_text(value).split())

    @staticmethod
    def _prepare_raw_text(value: str) -> str:
        return html.unescape(str(value)).replace("\\[", "[").replace("\\]", "]")
