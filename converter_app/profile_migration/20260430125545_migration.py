from converter_app.profile_migration import ProfileMigration


class ProfileMigrationScript(ProfileMigration):
    """
    Introduce profile versioning and diff support.
    """

    def up(self, profile: dict):
        """
       Add version. Add diff history values
        """
        if 'profile_version' not in profile:
            profile.update({'profile_version': '1.0'})
        if 'diff_history' not in profile:
            profile.update({'diff_history': []})

    def to_be_applied_after_migration(self) -> str:
        """
        Uses the unique identifier of the last script to tell the migration process in which order
        the migration script must be applied.
        """

        return '20260323144702'

    @property
    def identifier(self):
        """
        A unique identifier for the migration script.
        This identifier will be used:
         A) in the Profile to determine if a migration has been applied to a certain Profile.
         B) must be returned by the to_be_applied_after_migration method of the following script
        """

        return '20260430125545'
