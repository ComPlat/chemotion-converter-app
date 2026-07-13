#!/usr/bin/env python3
"""Check profile result diffs for profileId and JDX data changes."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DIFF_FILE = REPO_ROOT / "changes_results.diff"
DIFF_COMMAND = "git diff master -- test_manager/profile_results > changes_results.diff"
PROFILE_ID_RE = re.compile(r'"profileId"\s*:\s*"([^"]*)"')
DIFF_PATH_RE = re.compile(r"^diff --git a/(.+) b/(.+)$")


@dataclass
class DiffCheckResult:
    profile_id_changes: list[tuple[str, str]] = field(default_factory=list)
    jdx_value_changes: list[tuple[str, str]] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.profile_id_changes or self.jdx_value_changes)


def write_profile_results_diff(diff_file: Path = DIFF_FILE) -> None:
    """Run git diff and write it to changes_results.diff."""
    if diff_file != DIFF_FILE:
        raise ValueError(f"diff_file must be {DIFF_FILE}")

    result = subprocess.run(
        DIFF_COMMAND,
        cwd=REPO_ROOT,
        shell=True,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )

    if result.returncode not in (0, 1):
        raise RuntimeError(result.stderr.strip() or "git diff failed")


def check_diff(diff_file: Path = DIFF_FILE) -> DiffCheckResult:
    result = DiffCheckResult()
    current_file: str | None = None
    current_converter_json: Path | None = None
    current_profile: str | None = None
    old_profile_id: str | None = None
    new_profile_id: str | None = None
    file_has_jdx_value_change = False

    def finish_file() -> None:
        nonlocal old_profile_id, new_profile_id, file_has_jdx_value_change

        if not current_file:
            return
        if current_file.endswith("/converter.json"):
            if old_profile_id is not None and new_profile_id is not None:
                if old_profile_id != new_profile_id:
                    result.profile_id_changes.append((current_file, f'{old_profile_id} -> {new_profile_id}'))
        if current_file.endswith(".jdx") and file_has_jdx_value_change:
            result.jdx_value_changes.append((current_file, str(current_profile)))

        old_profile_id = None
        new_profile_id = None
        file_has_jdx_value_change = False

    with diff_file.open("r", encoding="utf-8", errors="replace") as diff:
        for raw_line in diff:
            line = raw_line.rstrip("\n")
            path_match = DIFF_PATH_RE.match(line)
            if path_match:
                finish_file()
                current_file = path_match.group(2)
                parts = list(Path(str(current_file)).parts)[:6]
                # insert after the 5th element
                parts.append("metadata/converter.json")
                current_converter_json_temp = Path(__file__).parent.parent / Path(*parts)
                if current_converter_json_temp.exists() and current_converter_json != current_converter_json_temp:
                    current_converter_json = current_converter_json_temp
                    with open(current_converter_json, 'r', encoding="utf-8", errors="replace") as f:
                        current_profile = json.load(f).get("profileId")
                continue

            if not current_file:
                continue

            if current_file.endswith("/converter.json"):
                if line.startswith("-") and not line.startswith("---"):
                    match = PROFILE_ID_RE.search(line[1:])
                    if match:
                        old_profile_id = match.group(1)
                elif line.startswith("+") and not line.startswith("+++"):
                    match = PROFILE_ID_RE.search(line[1:])
                    if match:
                        new_profile_id = match.group(1)

            if current_file.endswith(".jdx") and is_changed_jdx_value_line(line):
                file_has_jdx_value_change = True

    finish_file()
    return result


def is_changed_jdx_value_line(line: str) -> bool:
    if not line.startswith(("-", "+")):
        return False
    if line.startswith(("---", "+++")):
        return False

    content = line[1:].strip()
    if not content or content.startswith(("##", "$$")):
        return False
    if content.startswith("\\ No newline at end of file"):
        return False

    return bool(re.search(r"[+-]?\d+(?:\.\d+)?(?:[Ee][+-]?\d+)?", content))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate changes_results.diff and check whether converter.json "
            "profileId values or JDX data rows changed."
        )
    )
    return parser.parse_args()


def main() -> int:
    parse_args()

    write_profile_results_diff()
    result = check_diff()

    print(f"Wrote diff: {DIFF_FILE}")
    print(f"converter.json profileId changed: {bool(result.profile_id_changes)}")
    for (path, value) in result.profile_id_changes:
        print(f"  - {path} ({value})")

    print(f"JDX actual values changed: {bool(result.jdx_value_changes)}")
    for (path, profileId) in result.jdx_value_changes:
        print(f"  - {path} ({profileId})")

    return 1 if result.has_changes else 0


if __name__ == "__main__":
    sys.exit(main())
