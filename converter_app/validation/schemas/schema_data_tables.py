from converter_app.validation.registry import SchemaRegistry

tables_schema = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "chemconverter://profile/data_tables/draft-01",
    "title": "Schema for ChemConverter profile tables",
    "type": "object",
    "properties": {
        "xColumn": {
            "type": "object",
            "properties": {
                "columnIndex": {
                    "type": "integer"
                },
                "tableIndex": {
                    "type": "integer"
                }
            },
            "required": [
                "columnIndex",
                "tableIndex"
            ]
        },
        "yColumn": {
            "type": "object",
            "properties": {
                "columnIndex": {
                    "type": "integer"
                },
                "tableIndex": {
                    "type": "integer"
                }
            },
            "required": [
                "columnIndex",
                "tableIndex"
            ]
        }
    },
    "additionalProperties": False,
    "required": [
        "xColumn",
        "yColumn"
    ]

}

SchemaRegistry.instance().register(tables_schema)
