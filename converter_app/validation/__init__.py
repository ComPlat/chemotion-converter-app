import json
import logging
import os
from pathlib import Path

import jsonschema

import converter_app.validation.schemas.imports
from converter_app.validation.registry import SchemaRegistry
from converter_app.utils import get_app_root

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    A = []
    schema_directory = get_app_root() / 'converter_app/validation/schemas'

    for module in os.listdir(schema_directory):
        if module.startswith('schema_') and module[-3:] == '.py':
            A.append(f'import converter_app.validation.schemas.{module[:-3]}')

    with open(schema_directory / 'imports.py', 'w') as f:
        f.write('\n'.join(A))
    exit()


def validate_profile(json_to_test: dict):
    validator = SchemaRegistry.instance().validator_for('chemconverter://profile/base/draft-01')
    validator.validate(json_to_test)


def profile_validation_errors(json_to_test: dict) -> set[str]:
    """
    Reports every way ``json_to_test`` violates the profile schema, rather than
    stopping at the first one like :func:`validate_profile`.

    Callers use this to compare a profile before and after a transformation: an empty
    set means valid, and a result that is a subset of the original means the
    transformation fixed some violations without introducing any.

    The message is part of the signature, not decoration: ``required`` reports one
    error per absent property, all sharing the same path and validator, so without it
    every missing field would collapse into a single indistinguishable entry and a
    transformation that dropped one field while adding another would look like a no-op.

    :return: one ``path: validator: message`` signature per violation, stable across runs
    """
    validator = SchemaRegistry.instance().validator_for('chemconverter://profile/base/draft-01')
    return {
        f"{'->'.join(str(x) for x in e.absolute_path)}: {e.validator}: {e.message}"
        for e in validator.iter_errors(json_to_test)
    }


def validate_all_profiles(profile_dir: str | Path):
    for client_path in Path(profile_dir).iterdir():
        for profile in client_path.glob("*.json"):
            with open(profile, 'r', encoding='utf-8') as f:
                try:
                    validate_profile(json.loads(f.read()))
                    logger.info(f'✅ {profile.name}')
                except jsonschema.exceptions.ValidationError as e:
                    logger.error(f'⚠️ {profile.name}')
                    print(f"{profile.name}: {'->'.join(str(x) for x in e.path)}, {e.message}")

