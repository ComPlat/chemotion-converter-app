from narwhals import Object

from converter_app.profile_migration import ProfileMigration


class ProfileMigrationScript(ProfileMigration):
    """
    ToDo: Add a comment
    """
    default_predicate = {
        "description": [
            "The class resource, everything."
        ],
        "id": "RDFS:property:http://www.w3.org/2000/01/rdf-schema#Resource",
        "iri": "http://www.w3.org/2000/01/rdf-schema#Resource",
        "label": "Resource",
        "namespace": "http://www.w3.org/2000/01/rdf-schema#",
        "obo_id": "RDFS:Resource",
        "ontology_name": "rdfs",
        "ontology_prefix": "RDFS",
        "short_form": "RDFS_Resource",
        "type": "Class"
    }

    def up(self, profile: dict):
        """
        Updates the profile.
        """

        if 'objects' in profile:
            return


        all_ontologies = [*profile.get('predicates', [])] + [self.default_predicate]

        def find_ontology_id(ontology_id: str, key):
            for ontology in all_ontologies:
                if ontology_id == ontology.get('id'):
                    profile[key].append(ontology)
                    return

        profile['objects'] = []
        profile['predicates'] = []

        for instances in profile['subjectInstances'].values():
            for instance in instances:
                find_ontology_id(instance['predicate'], 'predicates')

        for i, identifier in enumerate(profile['identifiers']):
            if identifier['optional']:
                object_item = identifier.get('predicate')
                profile['identifiers'][i]['object'] = object_item
                if object_item:
                    find_ontology_id(object_item.get('id'), 'objects')
                profile['identifiers'][i]['predicate'] = {'id': self.default_predicate['id']}
                find_ontology_id(self.default_predicate['id'], 'predicates')


    def to_be_applied_after_migration(self) -> str:
        """
        Uses the unique identifier of the last script to tell the migration process in which order
        the migration script must be applied.
        """

        return '20260113143334'

    @property
    def identifier(self):
        """
        A unique identifier for the migration script.
        This identifier will be used:
         A) in the Profile to determine if a migration has been applied to a certain Profile.
         B) must be returned by the to_be_applied_after_migration method of the following script
        """

        return '20260319060352'
