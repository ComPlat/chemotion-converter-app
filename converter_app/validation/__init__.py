import os
from pathlib import Path

import converter_app.validation.schemas.imports
from converter_app.validation.registry import SchemaRegistry

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
