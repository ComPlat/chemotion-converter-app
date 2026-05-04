import copy
import json
from pathlib import Path
from typing import Optional

import jsonpatch

from converter_app.models import Profile
from converter_app.utils import get_app_root, cli_home_path


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
        def longest_path(graph, node='', memo=None):
            if memo is None:
                memo = {}
            if node in memo:
                return memo[node]

            children = graph.get(node, [])
            if not children:
                memo[node] = [node]
                return memo[node]

            # find the longest path among all children
            max_path = []
            for child in children:
                path = longest_path(graph, child, memo)
                if len(path) > len(max_path):
                    max_path = path

            memo[node] = [node] + max_path
            return memo[node]

        return longest_path(self._registry_tree)[-1]

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
        else:
            self._registry_tree[applied_after] = [script_id]

    def validate_tree(self):
        to_be_applied_after = set(x for after_list in self._registry_tree.values() for x in after_list)
        week_all_registered_registry_not_reachable = list(set(self._registry_tree.keys()) - to_be_applied_after)
        all_registered_registry_not_reachable = list(set(self._registry.keys()) - to_be_applied_after)
        assert week_all_registered_registry_not_reachable == ['']
        assert all_registered_registry_not_reachable == []

    def run_migration(self, profile_dir: str, force: bool = False):
        self.profile_dir = profile_dir
        for client_path in list(Path(profile_dir).iterdir()) + [cli_home_path() / 'profiles/cli']:
            client_id = client_path.stem
            if client_path.is_dir():
                for profile in client_path.iterdir():
                    self._prepare_migration(client_id, profile, force)
        for profile in (get_app_root() / 'converter_app/profiles').iterdir():
            self._prepare_migration('', profile, force)

    def prepare_and_run_migration(self, profile_path: Path, force: bool):
        self.profile_dir = profile_path.parent.parent
        client_id = profile_path.parent.name
        return self._prepare_migration(client_id, profile_path, force, True)

    def restore_unknown_migrations(self, profile, add_history: bool = True):
        """
        Reverts profile changes coming from migration scripts that are no
        longer present in the registry by applying their stored diffs in
        descending version order. When ``add_history`` is ``True`` an
        ``undo:<version>`` entry is appended to the diff history for each
        revert. Returns ``True`` if any migration was reverted.
        """
        history = profile.data.get('diff_history', [])
        list_of_migration = [{
            'idx': i,
            'mig': x['trigger'].removeprefix('migration:'),
            'diff': x['diff'],
            'version': x['profile_version']
        }
            for i, x in enumerate(history) if x['trigger'].startswith('migration:')]
        list_of_migration.sort(key=lambda x: tuple(map(int, x["version"].split("."))), reverse=True)

        ret_val = False
        for x in list_of_migration:

            if x['mig'] not in self._registry:
                restore_diff = next(
                    (h for h in history[x['idx']:] if h["trigger"] == f"undo:{x['version']}"),
                    None
                )
                if not restore_diff:
                    ret_val = True
                    patch = jsonpatch.JsonPatch(x['diff'])
                    origen_data = copy.deepcopy(profile.data)
                    profile.data = patch.apply(profile.data)
                    if add_history:
                        profile.update_change_history(origen_data, f'undo:{x['version']}')
        return ret_val

    def _prepare_migration(self, client_id, profile_path, force, raise_exceptions=False):
        if profile_path.is_file() and profile_path.suffix == '.json':
            try:
                profile = Profile.profile_from_file_path(
                    profile_path, client_id)
                if self.migrate_profile(profile, force):
                    self._save_profile(profile, profile_path)
            except Exception as e:
                if raise_exceptions:
                    raise
                print(f'{profile_path} cannot be migrated: {e}')

    def migrate_profile(self, profile: Profile, force: bool = False, add_history: bool = True):
        if force:
            last_migration = ''
        else:
            last_migration = profile.data.get('last_migration', '')
        is_migration_applied = self.restore_unknown_migrations(profile, add_history)
        is_migration_applied |= self._up_migration(last_migration, profile, add_history)
        return is_migration_applied

    def _up_migration(self, last_migration, profile, add_history: bool = True):
        if last_migration not in self._registry_tree:
            return False

        for next_migration in self._registry_tree[last_migration]:
            origen_data = copy.deepcopy(profile.data)
            self._registry[next_migration].up(profile.data)
            profile.data['last_migration'] = next_migration
            if add_history:
                profile.update_change_history(origen_data, f'migration:{next_migration}')
        for next_migration in self._registry_tree[last_migration]:
            self._up_migration(next_migration, profile)
        return True

    def _save_profile(self, profile: Profile, profile_file_path: Optional[Path] = None):
        if profile_file_path is not None:
            profiles_path = profile_file_path.parent
            file_path = profile_file_path
        else:
            if profile.is_default_profile:
                profiles_path = get_app_root() / 'converter_app/profiles'
            else:
                profiles_path = Path(self.profile_dir).joinpath(profile.client_id)
            file_path = profiles_path.joinpath(profile.id).with_suffix('.json')

        profile.data['id'] = profile.id

        profiles_path.mkdir(parents=True, exist_ok=True)

        if 'isDefaultProfile' in profile.data:
            del profile.data['isDefaultProfile']

        with open(file_path, 'w') as fp:
            json.dump(profile.data, fp, sort_keys=True, indent=4)
