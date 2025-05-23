from converter_app.validation.registry import SchemaRegistry

tables_schema = {
    "$schema": "http://json-schema.org/draft/2020-12/schema",
    "$id": "chemconverter://profile/tables/draft-01",
    "title": "Schema for ChemConverter profile tables",
    "type": "object",
    "properties": {
        "header": {
            "type": "object",
            "patternProperties": {
                "^[^\n]+$": {
                    "type": "string"
                }
            }
        },
        "loopType": {
            "type": "string"
        },
        "matchTables": {
            "type": "boolean"
        },
        "table": {
            "type": "object",
            "properties": {
                "$ref": "chemconverter://profile/tables/draft-01"
            }
        },

    },
    "additionalProperties": False,
    "required": [
        "data"
    ]

}

SchemaRegistry.instance().register(tables_schema)
