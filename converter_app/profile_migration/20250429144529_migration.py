from datetime import datetime

from converter_app.profile_migration import ProfileMigration


class ProfileMigrationScript(ProfileMigration):
    """
    Initial Migration
    """

    def up(self, profile: dict):
        """
        Updates the profile.
        """

        if profile.get('title', '') == '':
            profile['title'] = f'## Nameless ({datetime.now().strftime("%d/%m/%Y %H:%M:%S")})'

    def to_be_applied_after_migration(self) -> str:
        """
        Uses the unique identifier of the last script to tell the migration process in which order
        the migration script must be applied.
        """

        return ''

    @property
    def identifier(self):
        """
        A unique identifier for the migration script.
        This identifier will be used:
         A) in the Profile to determine if a migration has been applied to a certain Profile.
         B) must be returned by the to_be_applied_after_migration method of the following script
        """

        return '20250429144529'