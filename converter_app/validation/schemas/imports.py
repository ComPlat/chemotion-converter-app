from importlib import import_module

SCHEMA_MODULES = (
    'schema_input_tables',
    'schema_identifiers',
    'schema_data_tables',
    'schema_tables',
    'schema_profile',
)

for module_name in SCHEMA_MODULES:
    import_module(f'{__package__}.{module_name}')
