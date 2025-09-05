from converter_app.validation.registry import SchemaRegistry

identifiers_schema = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "chemconverter://profile/identifiers/draft-01",
    "title": "Schema for ChemConverter profile tables",
    "type": "object",
    "properties": {
        "key": {
            "type": "string"
        },
        "lineNumber": {
            "type": ["string", "number", "null"],
        },
        "match": {
            "type": "string",
            "enum": ["exact", "any", "regex"]
        },
        "optional": {
            "type": "boolean"
        },
        "tableIndex": {
            "type": "integer"
        },
        "type": {
            "type": "string",
            "enum": ["fileMetadata", "tableMetadata", "tableHeader"]
        },
        "value": {
            "type": "string"
        }
    },
    "additionalProperties": True,

    "required": [
        "match",
        "optional",
        "type",
        "value"
    ]

}

SchemaRegistry.instance().register(identifiers_schema)
