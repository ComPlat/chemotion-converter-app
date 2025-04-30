import json
from pathlib import Path

from models import Profile


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
        while True:
            if key not in self._registry_tree:
                return key
            key = self._registry_tree[key]

    def register(self, migration_obj):
        """
        Register a migration script
        :param migration_obj: Object which implements ProfileMigration
        :return:
        """

        script_id = migration_obj.identifier
        self._registry[script_id] = migration_obj
        self._registry_tree[migration_obj.to_be_applied_after_migration()] = script_id

    def run_migration(self, profile_dir: str, force: bool = False):
        self.profile_dir = profile_dir
        for client_path in Path(profile_dir).iterdir():
            client_id = client_path.stem
            for profile in client_path.iterdir():
                self._prepare_migration(client_id, profile, force)
        for profile in Path(__file__).parent.parent.parent.joinpath('profiles').iterdir():
            self._prepare_migration('', profile, force)

    def _prepare_migration(self, client_id, profile, force):
        if profile.is_file() and profile.suffix == '.json':
            try:
                self.migrate_profile(Profile.profile_from_file_path(profile, client_id), force)
                self._save_profile(profile)
            except Exception as e:
                print(f'{profile} cannot be migrated: {e}')

    def migrate_profile(self, profile: Profile, force: bool = False):
        if force:
            current_migration = ''
        else:
            current_migration = profile.data.get('current_migration', '')
        while current_migration in self._registry_tree:
            current_migration = self._registry_tree[current_migration]
            self._registry[current_migration].up(profile.data)
            profile.data['last_migration'] = current_migration


    def _save_profile(self, profile: Profile):
        if profile.is_default_profile:
            profiles_path = Path(__file__).parent.parent.parent.joinpath('profiles')
        else:
            profiles_path = Path(self.profile_dir).joinpath(profile.client_id)

        profiles_path.mkdir(parents=True, exist_ok=True)

        file_path = profiles_path.joinpath(profile.id).with_suffix('.json')
        if 'isDefaultProfile' in profile.data:
            del profile.data['isDefaultProfile']

        with open(file_path, 'w+', encoding='utf8') as fp:
            json.dump(profile.data, fp, sort_keys=True, indent=4)
