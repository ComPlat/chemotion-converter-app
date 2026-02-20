from converter_app.validation.registry import SchemaRegistry

ontology_properties = {
    "properties": {
        "id": {
            "type": "string",
        },
        "iri": {
            "type": "string",
        },
        "namespace": {
            "type": "string",
        },
        "label": {
            "type": "string",
        },
        "obo_id": {
            "type": "string",
        },
        "ontology_name": {
            "type": "string",
        },
        "ontology_prefix": {
            "type": "string",
        },
        "short_form": {
            "type": "string",
        },
        "description": {
            "type": "array",
            "items": {
                "type": "string"
            }
        },
        "type": {
            "type": "string",
        }
    },
    "additionalProperties": False,
    "type": ["object", "null"],
    "required": ["id", "namespace", "iri", "label", "obo_id", "ontology_name", "ontology_prefix", "short_form", "type"]
}

profile_schema = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "chemconverter://profile/base/draft-01",
    "title": "Schema for ChemConverter Profiles",
    "type": "object",
    "properties": {
        "id": {
            "type": "string"
        },
        "converter_version": {
            "type": "string"
        },
        "identifiers": {
            "type": "array",
            "items": {
                "$ref": "chemconverter://profile/identifiers/draft-01"
            }
        },
        "data": {
            "type": "object",
            "properties": {
                "metadata": {
                    "type": "object",
                    "properties": {

                    }
                },
                "tables": {
                    "type": "array",
                    "items": {"$ref": "chemconverter://profile/input_tables/draft-01"}
                }
            },
            "required": ["metadata", "tables"]

        },
        "last_migration": {
            "type": "string"
        },
        "description": {
            "type": "string"
        },
        "title": {
            "type": "string"
        },
        "isDisabled": {
            "type": "boolean"
        },
        "isDefaultProfile": {
            "type": "boolean"
        },
        "rootOntology": ontology_properties,
        "ols": {
            "type": ["string", "null"]
        },
        "ontology": {
            "type": "string"
        },
        "devices": {
            "type": "array",
            "items": {"type": "string"}
        },
        "software": {
            "type": "array",
            "items": {"type": "string"}
        },
        "tables": {
            "type": "array",
            "items": {
                "$ref": "chemconverter://profile/tables/draft-01"
            }
        },
        "subjects": {
            "type": "array",
            "items": ontology_properties
        },
        "predicates": {
            "type": "array",
            "items": ontology_properties
        },
        "datatypes": {
            "type": "array",
            "items": ontology_properties
        },
        "subjectInstances": {
            "type": "object",
            "patternProperties": {
                "^.+$": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string"
                            },
                            "predicate": {
                                "type": ["null", "string"]
                            }
                        },
                        "additionalProperties": False,
                        "required": ["name", "predicate"]
                    }
                }
            }
        }

    },
    "additionalProperties": False,
    "required": [
        "id",
        "data",
        "converter_version",
        "last_migration",
        "description",
        "title",
        "isDisabled",
        "ontology",
        "devices",
        "software",
        "tables",
        "subjectInstances",
        "predicates",
        "datatypes",
        "subjects"
    ]

}

SchemaRegistry.instance().register(profile_schema)
