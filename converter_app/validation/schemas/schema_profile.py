from converter_app.validation.registry import SchemaRegistry

profile_schema = {
    "$schema": "http://json-schema.org/draft/2020-12/schema",
    "$id": "chemconverter://profile/base/draft-01",
    "title": "Schema for ChemConverter Profiles",
    "type": "object",
    "properties": {
        "id": {
            "type": "string"
        },
        "identifiers": {
            "type": "array",
            "items": {
                "$ref": "#/components/schemas/Identifier"
            }
        },
        "data": {
            "type": "object",
            "properties": {

            }
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
        "ols": {
            "type": "string"
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
        "description",
        "title",
        "isDisabled",
        "ols",
        "tables"
    ]

}

SchemaRegistry.instance().register(profile_schema)
