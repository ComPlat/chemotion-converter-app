from converter_app.profile_migration import ProfileMigration


class ProfileMigrationScript(ProfileMigration):
    """
    Replaces the old global loop with the new local loop.
    Since the old loop can only have one table,
    the global loop is equivalent to an 'all' loop over the first table.
    """

    def up(self, profile: dict):
        """
        Updates the profile.
        """

        if 'matchTables' in profile:
            if profile['matchTables'] and len(profile.get('tables',[])) >= 1:
                profile.get('tables')[0]['loopType'] = 'all'
                profile.get('tables')[0]['matchTables'] = True
            del profile['matchTables']

    def to_be_applied_after_migration(self) -> str:
        """
        Uses the unique identifier of the last script to tell the migration process in which order
        the migration script must be applied.
        """

        return '20250429151003'

    @property
    def identifier(self):
        """
        A unique identifier for the migration script.
        This identifier will be used:
         A) in the Profile to determine if a migration has been applied to a certain Profile.
         B) must be returned by the to_be_applied_after_migration method of the following script
        """

        return '20250507140000'