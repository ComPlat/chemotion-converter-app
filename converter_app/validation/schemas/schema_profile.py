from converter_app.validation.registry import SchemaRegistry

profile_schema = {
    "$schema": "http://json-schema.org/draft/2020-12/schema",
    "$id": "chemconverter://profile/base/draft-01",
    "title": "Schema for ChemConverter Profiles",
    "type": "object",
    "properties": {
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
        "tables": {
            "type": "array",
            "items": {
                "$ref": "chemconverter://profile/tables/draft-01"
            }
        },

    },
    "additionalProperties": False,
    "required": [
        "data"
    ]

}

SchemaRegistry.instance().register(profile_schema)
