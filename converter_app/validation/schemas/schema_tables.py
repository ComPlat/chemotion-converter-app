from converter_app.validation.registry import SchemaRegistry

tables_schema = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "chemconverter://profile/tables/draft-01",
    "title": "Schema for ChemConverter profile tables",
    "type": "object",
    "properties": {
        "header": {
            "type": "object",
            "patternProperties": {
                "^[^\n]+$": {
                    "type": ["number", "string"]
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
                "$ref": "chemconverter://profile/data_tables/draft-01"
            }
        },

    },
    "additionalProperties": False,
    "required": [
        "header",
        "table"
    ]

}

SchemaRegistry.instance().register(tables_schema)
