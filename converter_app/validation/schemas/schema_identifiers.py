from converter_app.validation.registry import SchemaRegistry

ontology_properties = {
    "properties": {
        "id": {
            "type": "string",
        },
        "iri": {
            "type": "string",
        },
        "label": {
            "type": "string",
        },
        "obo_id": {
            "type": "string",
        },
        "ontology_name": {
            "type": "string",
        },
        "ontology_prefix": {
            "type": "string",
        },
        "short_form": {
            "type": "string",
        },
        "description": {
            "type": "array",
            "items": {
                "type": "string"
            }
        },
        "type": {
            "type": "string",
        }
    },
    "additionalProperties": False,
    "type": ["object", "null"],
    "required": ["id" ,"iri" ,"label" ,"obo_id","ontology_name" ,"ontology_prefix" ,"short_form" ,"type"]
}

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
            "type": "string"
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
        },
        "predicate": ontology_properties,
        "subject": ontology_properties,
        "datatype": ontology_properties,
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
