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
        },
    },
    "patternProperties": {
        "[x|y]Operations": {
            "type": "array",
            "items": [
                {
                    "type": "object",
                    "properties": {
                        "column": {
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
                        "operator": {
                            "type": "string"
                        },
                        "type": {
                            "const": "column"

                        }
                    },
                    "required": [
                        "column",
                        "operator",
                        "type"
                    ]
                },
                {
                    "type": "object",
                    "properties": {
                        "operator": {
                            "type": "string"
                        },
                        "type": {
                            "const": "value"
                        },
                        "value": {
                            "type": "string"
                        }
                    },
                    "required": [
                        "operator",
                        "type",
                        "value"
                    ]
                },
                {
                    "type": "object",
                    "properties": {
                        "ignore_missing_values": {
                            "type": "boolean"
                        },
                        "metadata": {
                            "type": "string"
                        },
                        "operator": {
                            "type": "string"
                        },
                        "table": {
                            "type": "string"
                        },
                        "type": {
                            "const": "metadata_value"
                        },
                        "value": {
                            "type": "string"
                        }
                    },
                    "required": [
                        "ignore_missing_values",
                        "metadata",
                        "operator",
                        "table",
                        "type",
                        "value"
                    ]
                },
                {
                    "type": "object",
                    "properties": {
                        "ignore_missing_values": {
                            "type": "boolean"
                        },
                        "line": {
                            "type": "string"
                        },
                        "operator": {
                            "type": "string"
                        },
                        "regex": {
                            "type": "string"
                        },
                        "table": {
                            "type": "string"
                        },
                        "type": {
                            "const": "header_value"
                        }
                    },
                    "required": [
                        "ignore_missing_values",
                        "line",
                        "operator",
                        "regex",
                        "table",
                        "type"
                    ]
                }
            ]
        },
        "[x|y]xOperationsDescription": {
            "type": "array",
            "items": {
                    "type": "string"
                }
        }

    },
    "additionalProperties": False,
    "required": [
        "xColumn",
        "yColumn"
    ]

}

SchemaRegistry.instance().register(tables_schema)
