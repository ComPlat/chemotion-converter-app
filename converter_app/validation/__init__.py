import json
import logging
import os
from pathlib import Path

import jsonschema

import converter_app.validation.schemas.imports
from converter_app.validation.registry import SchemaRegistry

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    A = []
    schema_directory = Path(__file__).parent / 'schemas'

    for module in os.listdir(schema_directory):
        if module.startswith('schema_') and module[-3:] == '.py':
            A.append(f'import converter_app.validation.schemas.{module[:-3]}')

    with open(schema_directory / 'imports.py', 'w') as f:
        f.write('\n'.join(A))
    exit()


def validate_profile(json_to_test: dict):
    validator = SchemaRegistry.instance().validator_for('chemconverter://profile/base/draft-01')
    validator.validate(json_to_test)


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

