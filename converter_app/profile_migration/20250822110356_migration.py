from converter_app.profile_migration import ProfileMigration


class ProfileMigrationScript(ProfileMigration):
    """
    ToDo: Add a comment
    """

    def up(self, profile: dict):
        """
        Updates the profile.
        """
        for identifier in profile['identifiers']:
            if identifier['optional']:
                for k in ['subject', 'datatype', 'predicate']:
                    identifier[k] = identifier.get(k)
        profile['subjects'] = profile.get('subjects', [])
        profile['predicates'] = profile.get('predicates', [])
        profile['datatypes'] = profile.get('datatypes', [])
        profile['subjectInstances'] = profile.get('subjectInstances', {})

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

        return '20250822110356'