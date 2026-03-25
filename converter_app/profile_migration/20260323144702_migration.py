import copy

from converter_app.profile_migration import ProfileMigration


class ProfileMigrationScript(ProfileMigration):
    """
    ToDo: Add a comment
    """

    default_assay = {
        'description': [
            'A planned process that has the objective to produce information about a material entity (the evaluant) by examining it.'
        ],
        'id': 'obi:class:http://purl.obolibrary.org/obo/OBI_0000070',
        'iri': 'http://purl.obolibrary.org/obo/OBI_0000070',
        'label': 'assay',
        'namespace': 'http://purl.obolibrary.org/obo/',
        'obo_id': 'OBI:0000070',
        'ontology_name': 'obi',
        'ontology_prefix': 'OBI',
        'short_form': 'OBI_0000070',
        'type': 'class'
    }

    def up(self, profile: dict):
        """
        Updates the profile.
        """

        if profile["rootOntology"]["iri"] == "http://purl.obolibrary.org/obo/OBI_0000070":
            profile["rootOntology"] = copy.deepcopy(self.default_assay)

    def to_be_applied_after_migration(self) -> str:
        """
        Uses the unique identifier of the last script to tell the migration process in which order
        the migration script must be applied.
        """

        return '20260319060352'

    @property
    def identifier(self):
        """
        A unique identifier for the migration script.
        This identifier will be used:
         A) in the Profile to determine if a migration has been applied to a certain Profile.
         B) must be returned by the to_be_applied_after_migration method of the following script
        """

        return '20260323144702'
