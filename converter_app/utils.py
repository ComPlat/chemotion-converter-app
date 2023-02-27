import base64
import hashlib
import re
import uuid


def human2bytes(string):
    if not string:
        return 0

    m = re.match(r'([0-9.]+)\s*([A-Za-z]+)', string)
    number, unit = float(m.group(1)), m.group(2).strip().lower()

    if unit == 'kb' or unit == 'k':
        return number * 1000
    elif unit == 'mb' or unit == 'm':
        return number * 1000**2
    elif unit == 'gb' or unit == 'g':
        return number * 1000**3
    elif unit == 'tb' or unit == 't':
        return number * 1000**4
    elif unit == 'pb' or unit == 'p':
        return number * 1000**5
    elif unit == 'kib':
        return number * 1024
    elif unit == 'mib':
        return number * 1024**2
    elif unit == 'gib':
        return number * 1024**3
    elif unit == 'tib':
        return number * 1024**4
    elif unit == 'pib':
        return number * 1024**5


def check_uuid(string):
    try:
        return uuid.UUID(string, version=4)
    except ValueError:
        return False


def checkpw(password, hashed_password):
    m = hashlib.sha1()
    m.update(password)
    return (b'{SHA}' + base64.b64encode(m.digest())) == hashed_password


_reader_json_shema = None
def reader_json_shema():
    global _reader_json_shema
    if _reader_json_shema is not None:
        return _reader_json_shema
    def sub_schema_identifier(type='global'):
        a = {
            "type": "object",
            "properties": {
                "match": {'type': "string", 'enum': ["any", "regex", "exact"]},
                "optional": {'type': "boolean"},
                "show": {'type': "boolean"},

                "value": {'type': "string"}
            },
            "required": ["match", "optional", "value", "type"]

        }

        a['properties']['type'] = {'type': "string", 'enum': [type]}
        if type == 'file':
            a['properties']['lineNumber'] = {'type': 'number'}

        return a


    def sub_schema_options():
        return {
            "type": "array",
            "uniqueItems": True,
            "minItems": 6,
            "maxItems": 6,
            "items": {
                "type": "object",
                "properties": {

                    "active": {'type': "boolean"},
                    "symbol": {'type': "string", 'enum': [";", ",", "\t", " ", "=", ""]},
                    "name": {'type': "string"}
                },
                "required": ["active", "symbol", "name"]
            }

        }


    _reader_json_shema = {
        "type": "object",
        "properties": {
            "description": {'type': "string"},
            "id": {'type': "string"},
            "title": {'type': "string"},
            "commend": {
                "type": "object",
                "properties": {
                    "line_commend": sub_schema_identifier(),
                    "multi_line_commend_end": sub_schema_identifier(),
                    "multi_line_commend_start": sub_schema_identifier()
                },
                "required": ["line_commend", "multi_line_commend_end", "multi_line_commend_start"]
            },
            "identifiers": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "array",
                        "items": sub_schema_identifier("file")
                    },
                    "meta": {
                        "type": "object",
                        "properties": {"file_extension": {"type": "string"}}
                    }
                },
                "required": ["content", "meta"]
            },
            "delimiters": {
                "type": "object",
                "properties": {
                    "free_identifier": sub_schema_identifier(),
                    "ignore_within_quotes": {"type": "boolean"},
                    "options": sub_schema_options(),
                    "table_delimiters": {
                        "type": "array",
                        "items": sub_schema_identifier()
                    }
                },

                "required": ["free_identifier", "ignore_within_quotes", "options", "table_delimiters"]
            },
            "tables": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "allow_empty_col": {'type': "boolean"},
                        "allow_str_col": {'type': "string"},
                        "has_col_header_row": {'type': "boolean"},
                        "has_row_header_col": {'type': "boolean"},
                        "has_start_identifier": {'type': "boolean"},
                        "max_number_of_col": {'type': 'number'},
                        "min_number_of_col": {'type': 'number'},
                        "number_value_regex": {'type': "string"},
                        "start_identifier": sub_schema_identifier()
                    },
                    "required": ["allow_empty_col", "allow_str_col", "has_col_header_row", "has_row_header_col",
                                 "has_start_identifier", "max_number_of_col", "min_number_of_col", "number_value_regex",
                                 "start_identifier"]
                }
            }
        },
        "required": ["commend", "delimiters", "title", "identifiers"]
    }

    return _reader_json_shema
