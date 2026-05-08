from converter_app.profile_migration import ProfileMigration


class ProfileMigrationScript(ProfileMigration):
    """
    Extents identifier with output options
    """

    def up(self, profile: dict):
        """

        Adds isDatasetOutput {bool}
        Adds isDatatableOutput {bool}
        Adds isRdfOutput {bool}
        """
        for i, identifier in enumerate(profile['identifiers']):
            if identifier['optional']:
                profile['identifiers'][i]['isDatasetOutput'] = identifier.get('isDatasetOutput', True)
                profile['identifiers'][i]['isDatatableOutput'] = identifier.get('isDatatableOutput', False)
                profile['identifiers'][i]['isLoobDatatableOutput'] = identifier.get('isLoobDatatableOutput', True)
                profile['identifiers'][i]['isRdfOutput'] = identifier.get('isRdfOutput', False)
                if not isinstance(identifier['outputTableIndex'], list):
                    profile['identifiers'][i]['outputTableIndex'] = [identifier['outputTableIndex']]

    def to_be_applied_after_migration(self) -> str:
        """
        Uses the unique identifier of the last script to tell the migration process in which order
        the migration script must be applied.
        """

        return '20260430125545'

    @property
    def identifier(self):
        """
        A unique identifier for the migration script.
        This identifier will be used:
         A) in the Profile to determine if a migration has been applied to a certain Profile.
         B) must be returned by the to_be_applied_after_migration method of the following script
        """

        return '20260506160404'