import importlib.metadata

from converter_app.profile_migration import ProfileMigration


class ProfileMigrationScript(ProfileMigration):
    """
    Added a profile version to the converter profiles
    """

    def up(self, profile: dict):
        """
        Updates the profile.
        """

        if profile.get('converter_version') is None:
            profile['converter_version'] = importlib.metadata.version('chemotion-converter-app')
            if profile['converter_version'] is None:
                # Unknown converter version
                profile['converter_version'] = '-'


    def to_be_applied_after_migration(self) -> str:
        """
        Uses the unique identifier of the last script to tell the migration process in which order
        the migration script must be applied.
        """

        return '20250523125234'

    @property
    def identifier(self):
        """
        A unique identifier for the migration script.
        This identifier will be used:
         A) in the Profile to determine if a migration has been applied to a certain Profile.
         B) must be returned by the to_be_applied_after_migration method of the following script
        """

        return '20251031061716'