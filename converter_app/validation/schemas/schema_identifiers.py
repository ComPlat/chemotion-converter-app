from converter_app.validation.registry import SchemaRegistry

identifiers_schema = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "chemconverter://profile/identifiers/draft-01",
    "title": "Schema for ChemConverter profile tables",
    "type": "object",
    "properties": {

    },
    "additionalProperties": True,
    "required": [
    ]

}

SchemaRegistry.instance().register(identifiers_schema)
