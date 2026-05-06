from converter_app.profile_migration import ProfileMigration


class ProfileMigrationScript(ProfileMigration):
    """
    Add Reaction variations autofill identifier
    """

    def up(self, profile: dict):
        """
        Add profile['reactionVariations'] = {'identifiers': [], 'elements': []} only if profile['reactionVariations'] is None
        """

        if profile.get('reactionVariations') is None:
            profile['reactionVariations'] = {'identifiers': [], 'elements': []}

    def to_be_applied_after_migration(self) -> str:
        """
        Uses the unique identifier of the last script to tell the migration process in which order
        the migration script must be applied.
        """

        return '20260401123327'

    @property
    def identifier(self):
        """
        A unique identifier for the migration script.
        This identifier will be used:
         A) in the Profile to determine if a migration has been applied to a certain Profile.
         B) must be returned by the to_be_applied_after_migration method of the following script
        """

        return '20260417132254'