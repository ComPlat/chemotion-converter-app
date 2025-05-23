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


def validate_selection_options(json_to_test: dict):
    validator = SchemaRegistry.instance().validator_for('chmotion://generic/select_option/draft-01')
    validator.validate(json_to_test)


def validate_generic_element(json_to_test: dict):
    validator = SchemaRegistry.instance().validator_for('chmotion://generic/element/draft-01')
    validator.validate(json_to_test)


def validate_generic_dataset(json_to_test: dict):
    validator = SchemaRegistry.instance().validator_for('chmotion://generic/dataset/draft-01')
    validator.validate(json_to_test)


def validate_generic_segment(json_to_test: dict):
    validator = SchemaRegistry.instance().validator_for('chmotion://generic/segment/draft-01')
    validator.validate(json_to_test)


def validate_generic_properties(json_to_test: dict):
    validator = SchemaRegistry.instance().validator_for('chmotion://generic/properties/draft-01')
    validator.validate(json_to_test)


def validate_generic_dataset_properties(json_to_test: dict):
    validator = SchemaRegistry.instance().validator_for('chmotion://generic/dataset_properties/draft-01')
    validator.validate(json_to_test)


def validate_generic_segment_properties(json_to_test: dict):
    validator = SchemaRegistry.instance().validator_for('chmotion://generic/segment_properties/draft-01')
    validator.validate(json_to_test)


def validate_generic_layer(json_to_test: dict):
    validator = SchemaRegistry.instance().validator_for('chmotion://generic/layer/draft-01')
    validator.validate(json_to_test)
