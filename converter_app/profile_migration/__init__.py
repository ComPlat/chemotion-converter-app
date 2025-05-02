import importlib
import inspect
import os
from pathlib import Path

from converter_app.profile_migration.utils.base_migration import ProfileMigration
from converter_app.profile_migration.utils.registration import Migrations

for file in Path(__file__).parent.glob('*.py'):
    if not file.name.endswith('_migration.py'):
        continue
    file_path = os.path.join(os.path.dirname(__file__), file)
    module_name = file.stem

    # Load the module
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)


    for name, cls in inspect.getmembers(module, inspect.isclass):
        if issubclass(cls, ProfileMigration) and cls is not ProfileMigration:
            cls()



try:
    Migrations().validate_tree()
except AssertionError:
    raise EnvironmentError('Validation of migration scripts failed')