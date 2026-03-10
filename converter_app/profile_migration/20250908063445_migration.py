import re

import requests

from converter_app.profile_migration import ProfileMigration


def _add_namespace_to_ontology(ontology: dict) -> dict:
    # Regex: split into "everything up to last / or #" and the last part
    match = re.match(r"(.+[/#])([^/#]+)", ontology.get("iri", ""))
    if not match:
        return ontology  # if iri is missing or doesn't match, return unchanged

    namespace, _term = match.groups()

    # Return a new dict including namespace
    return {
        **ontology,
        "namespace": namespace
    }


class ProfileMigrationScript(ProfileMigration):
    """
    ToDo: Add a comment
    """

    def up(self, profile: dict):
        """
        Updates the profile.
        """
        profile["rootOntology"] = {
            "iri": "http://purl.obolibrary.org/obo/OBI_0000070",
            "namespace": "http://purl.obolibrary.org/obo/",
            "ontology_name": "chmo",
            "ontology_prefix": "CHMO",
            "short_form": "OBI_0000070",
            "description": [
                "A planned process that has the objective to produce information about a material entity (the evaluant) by examining it."
            ],
            "id": "OBI:property:http://purl.obolibrary.org/obo/OBI_0000070",
            "label": "assay",
            "obo_id": "OBI:0000070",
            "type": "class"
        }
        if not profile.get('ols'):
            profile['ols'] = None
            return

        url = f"https://www.ebi.ac.uk/ols4/api/ontologies/CHMO/terms?obo_id={profile['ols']}&lang=en"
        res = requests.get(url)
        if res.status_code != 200:
            return

        data = res.json()
        terms = data.get("_embedded", {}).get("terms", [])
        if not terms:
            return

        term = terms[0]
        iri = term.get("iri")
        ontology_name = term.get("ontology_name")
        ontology_prefix = term.get("ontology_prefix")
        short_form = term.get("short_form")
        description = term.get("description")
        id_ = term.get("id", f"{ontology_prefix}:properties:{iri}")
        label = term.get("label")
        obo_id = term.get("obo_id")
        type_ = term.get("type", "class")

        profile["rootOntology"] = _add_namespace_to_ontology({
            "iri": iri,
            "ontology_name": ontology_name,
            "ontology_prefix": ontology_prefix,
            "short_form": short_form,
            "description": description,
            "id": id_,
            "label": label,
            "obo_id": obo_id,
            "type": type_
        })

    def to_be_applied_after_migration(self) -> str:
        """
        Uses the unique identifier of the last script to tell the migration process in which order
        the migration script must be applied.
        """

        return '20250822110356'

    @property
    def identifier(self):
        """
        A unique identifier for the migration script.
        This identifier will be used:
         A) in the Profile to determine if a migration has been applied to a certain Profile.
         B) must be returned by the to_be_applied_after_migration method of the following script
        """

        return '20250908063445'
