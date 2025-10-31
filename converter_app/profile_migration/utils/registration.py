import json
from pathlib import Path

from converter_app.models import Profile


class Migrations:
    """
    This calls manages all reader. It must be used as Singleton
    """
    _instance = None
    profile_dir = None

    _registry = {}
    _registry_tree = {}

    def __new__(cls, *args, **kwargs):
        """
        Singleton constructor
        :return: Readers Singleton
        """

        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def last(self) -> str:
        key = ''
        for _ in range(len(self._registry_tree) + 1):
            if key not in self._registry_tree:
                return key
            key = self._registry_tree[key]
        return ''

    def register(self, migration_obj):
        """
        Register a migration script
        :param migration_obj: Object which implements ProfileMigration
        :return:
        """

        script_id = migration_obj.identifier
        if script_id in self._registry:
            raise ValueError(f'Script {script_id} already registered')
        self._registry[script_id] = migration_obj
        applied_after = migration_obj.to_be_applied_after_migration()
        if applied_after == script_id:
            raise ValueError(
                f'to_be_applied_after_migration: {applied_after} must not be identifier{script_id} of the same script')
        if applied_after in self._registry_tree:
            self._registry_tree[applied_after].append(script_id)
        else :
            self._registry_tree[applied_after] = [script_id]

    def validate_tree(self):
        to_be_applied_after = set(x for after_list in self._registry_tree.values() for x  in after_list)
        week_all_registered_registry_not_reachable = list(set(self._registry_tree.keys()) - to_be_applied_after)
        all_registered_registry_not_reachable = list(set(self._registry.keys()) - to_be_applied_after)
        assert week_all_registered_registry_not_reachable == ['']
        assert all_registered_registry_not_reachable == []

    def run_migration(self, profile_dir: str, force: bool = False):
        self.profile_dir = profile_dir
        for client_path in Path(profile_dir).iterdir():
            client_id = client_path.stem
            if client_path.is_dir():
                for profile in client_path.iterdir():
                    self._prepare_migration(client_id, profile, force)
        for profile in Path(__file__).parent.parent.parent.joinpath('profiles').iterdir():
            self._prepare_migration('', profile, force)

    def _prepare_migration(self, client_id, profile_path, force):
        if profile_path.is_file() and profile_path.suffix == '.json':
            try:
                profile = Profile.profile_from_file_path(
                    profile_path, client_id)
                if self.migrate_profile(profile, force):
                    self._save_profile(profile)
            except Exception as e:
                print(f'{profile_path} cannot be migrated: {e}')

    def migrate_profile(self, profile: Profile, force: bool = False):
        if force:
            last_migration = ''
        else:
            last_migration = profile.data.get('last_migration', '')
        is_migration_applied = self._up_migration(last_migration, profile)
        return is_migration_applied

    def _up_migration(self, last_migration, profile):
        if last_migration not in self._registry_tree:
            return False

        for next_migration in self._registry_tree[last_migration]:
            self._registry[next_migration].up(profile.data)
            profile.data['last_migration'] = next_migration
        for next_migration in self._registry_tree[last_migration]:
            self._up_migration(next_migration, profile)
        return True

    def _save_profile(self, profile: Profile):
        if profile.is_default_profile:
            profiles_path = Path(
                __file__).parent.parent.parent.joinpath('profiles')
        else:
            profiles_path = Path(self.profile_dir).joinpath(profile.client_id)

        profile.data['id'] = profile.id
        profiles_path.mkdir(parents=True, exist_ok=True)

        file_path = profiles_path.joinpath(profile.id).with_suffix('.json')
        if 'isDefaultProfile' in profile.data:
            del profile.data['isDefaultProfile']

        with open(file_path, 'w') as fp:
            json.dump(profile.data, fp, sort_keys=True, indent=4)
