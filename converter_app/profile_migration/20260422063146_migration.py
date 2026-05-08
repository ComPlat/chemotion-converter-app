from converter_app.profile_migration import ProfileMigration
from converter_app.readers.helper.base import DEFAULT_UNITS


class ProfileMigrationScript(ProfileMigration):
    """
    Adds default units to first input tables
    """


    def up(self, profile: dict):
        """

        """
        try:
            for i, v in enumerate(profile.get('data', [])):
                for (unit_name, value) in DEFAULT_UNITS:
                    if v['tables'][0]['metadata'].get(unit_name) is None:
                        v['tables'][0]['metadata'][unit_name] = value
        except KeyError as e:
            pass

    def to_be_applied_after_migration(self) -> str:
        """
        Uses the unique identifier of the last script to tell the migration process in which order
        the migration script must be applied.
        """

        return '20260417132254'

    @property
    def identifier(self):
        """
        A unique identifier for the migration script.
        This identifier will be used:
         A) in the Profile to determine if a migration has been applied to a certain Profile.
         B) must be returned by the to_be_applied_after_migration method of the following script
        """

        return '20260422063146'
