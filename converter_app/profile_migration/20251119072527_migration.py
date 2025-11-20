import uuid

from converter_app.profile_migration import ProfileMigration


class ProfileMigrationScript(ProfileMigration):
    """
    Add editable flag to all identifier
    Add id to all identifier
    """

    def up(self, profile: dict):
        """
        Updates the profile.
        """

        # ToDo: Updated the profile
        for table in profile.get('tables', []):
            if table['header']['DATA CLASS'] == 'NTUPLES':
                table['header']['NTUPLES_PAGE_HEADER'] = table['header'].get('NTUPLES_PAGE_HEADER', '+')
                table['header']['NTUPLES_ID'] = table['header'].get('NTUPLES_ID', uuid.uuid4().__str__())
        for identifier in profile['identifiers']:
            if identifier.get('editable', True):
                identifier['editable'] = True
            else:
                identifier['editable'] = False
            if identifier.get('id') is None:
                identifier['id'] = f'#{uuid.uuid4().__str__()}'

    def to_be_applied_after_migration(self) -> str:
        """
        Uses the unique identifier of the last script to tell the migration process in which order
        the migration script must be applied.
        """

        return '20251031061716'

    @property
    def identifier(self):
        """
        A unique identifier for the migration script.
        This identifier will be used:
         A) in the Profile to determine if a migration has been applied to a certain Profile.
         B) must be returned by the to_be_applied_after_migration method of the following script
        """

        return '20251119072527'