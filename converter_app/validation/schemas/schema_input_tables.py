from converter_app.validation.registry import SchemaRegistry

tables_schema = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "chemconverter://profile/input_tables/draft-01",
    "title": "Schema for ChemConverter profile tables",
    "type": "object",
    "properties": {
        "columns": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "key": {
                        "type": "string"
                    },
                    "name": {
                        "type": "string"
                    }
                },
                "additionalProperties": False,
                "required": [
                    "name",
                    "key"
                ]
            }
        },
        "header": {
            "type": "array",
            "items": {
                "type": "string"
            }
        },
        "metadata": {
            "type": "object",
            "patternProperties": {
                "^[^\n]+$": {
                    "type": ["number", "string"]
                }
            }
        },
        "rows": {
            "type": "array",
            "items": {
                "type": "array",
                "items": {
                    "type": ["string", "number"]
                }
            }
        }

    },
    "additionalProperties": False,
    "required": [
        "columns",
        "metadata",
        "header",
        "rows"
    ]

}

SchemaRegistry.instance().register(tables_schema)
