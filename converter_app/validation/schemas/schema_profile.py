from converter_app.validation.registry import SchemaRegistry

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
        "ols": {
            "type": "string"
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
        "tables"
    ]

}

SchemaRegistry.instance().register(profile_schema)
