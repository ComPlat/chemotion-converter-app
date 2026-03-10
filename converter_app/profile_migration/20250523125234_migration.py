import re
from pathlib import Path

from flask import current_app, has_app_context

from converter_app.profile_migration import ProfileMigration
from converter_app.utils import get_app_root


class ProfileMigrationScript(ProfileMigration):
    """
    Add App version to profiles
    """

    def __init__(self):
        super().__init__()
        if has_app_context():
            self.app_config = current_app.config
        else:
            cp = get_app_root()/ 'converter_app/__init__.py'
            with open(cp, 'r', encoding='utf-8') as f:
                kv_list = [(k.upper(), v) for (k, v) in re.findall(r'__(.*)__ = [\']([^\']*)[\']', f.read())]
                self.app_config = dict(kv_list)


    def up(self, profile: dict):
        """
        Add App version to profiles as 'converter_version'
        """

        profile['converter_version'] = self.app_config.get('VERSION')
        profile['ontology'] = profile.get('ontology', '')
        profile['devices'] = profile.get('devices', [])
        profile['software'] = profile.get('software', [])

    def to_be_applied_after_migration(self) -> str:
        """
        Uses the unique identifier of the last script to tell the migration process in which order
        the migration script must be applied.
        """

        return '20250507140000'

    @property
    def identifier(self):
        """
        A unique identifier for the migration script.
        This identifier will be used:
         A) in the Profile to determine if a migration has been applied to a certain Profile.
         B) must be returned by the to_be_applied_after_migration method of the following script
        """

        return '20250523125234'