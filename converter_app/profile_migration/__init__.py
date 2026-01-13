import importlib
import inspect

from converter_app.profile_migration.utils.base_migration import ProfileMigration
from converter_app.profile_migration.utils.registration import Migrations
from converter_app.utils import get_app_root

for file in (get_app_root() / 'converter_app/profile_migration').glob('*.py'):
    if not file.name.endswith('_migration.py'):
        continue
    file_path = get_app_root() / 'converter_app/profile_migration' / file
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