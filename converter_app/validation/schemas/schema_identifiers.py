import copy

from converter_app.validation.registry import SchemaRegistry

ontology_id = {
    "properties": {
        "id": {
            "type": "string",
        }
    },
    "additionalProperties": False,
    "type": ["object", "null"],
    "required": ["id"]

}

ontology_subjects_id = copy.deepcopy(ontology_id)
ontology_subjects_id['properties'] |= {
    'subjectInstance': {
      "type": "string"
    }
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
            "type": ["number", "string"]
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
        "predicate": ontology_id,
        "subject": ontology_subjects_id,
        "datatype": ontology_id,
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
