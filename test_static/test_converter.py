from types import SimpleNamespace

import pytest

from converter_app.converters import Converter


def make_converter(profile_data, file_data=None):
    profile = SimpleNamespace(data=profile_data)
    return Converter(profile, file_data or {'metadata': {}, 'tables': []})


def test_match_identifier_supports_metadata_and_header_regex():
    converter = make_converter(
        {'identifiers': [], 'tables': []},
        {
            'metadata': {'instrument': 'LCMS-01'},
            'tables': [
                {
                    'header': ['Run: sample-a'],
                    'metadata': {'sample': 'sample-a'},
                    'columns': [],
                    'rows': [],
                }
            ],
        },
    )

    assert converter.match_identifier({
        'type': 'fileMetadata',
        'key': 'instrument',
        'match': 'exact',
        'value': 'LCMS-01',
    }) == {'value': 'LCMS-01'}
    assert converter.match_identifier({
        'type': 'tableMetadata',
        'tableIndex': 0,
        'key': 'sample',
        'match': 'any',
    }) == {'value': 'sample-a', 'tableIndex': 0}
    assert converter.match_identifier({
        'type': 'tableHeader',
        'tableIndex': 0,
        'lineNumber': 1,
        'match': 'regex',
        'value': r'Run: (.+)',
    }) == {'value': 'sample-a', 'tableIndex': 0, 'lineNumber': 1}


@pytest.mark.parametrize(
    'loop_type,input_table_index,expected',
    [
        ('all', 0, (True, )),
        ('all', 1, (True, )),
        ('none', 0, (True, )),
        ('none', 1, (False, )),
    ],
)
def test_compute_check_loop_condition_handles_all_and_non_looped_tables(
        loop_type,
        input_table_index,
        expected,
):
    converter = make_converter(
        {
            'identifiers': [],
            'tables': [
                {
                    'loopType': loop_type,
                    'inputTableIndex': 0,
                    'table': {},
                }
            ],
        },
        {'tables': [{'header': [], 'metadata': {}, 'columns': [], 'rows': []}]},
    )

    assert converter._compute_check_loop_condition(0, input_table_index) == expected


def test_compute_check_loop_condition_groups_matching_loop_tables():
    converter = make_converter(
        {
            'identifiers': [],
            'tables': [
                {
                    'loopType': 'matching',
                    'inputTableIndex': 0,
                    'table': {
                        'loop_header': [{'column': 'Potential'}],
                        'loop_theader': [{'regex': r'Run: (.+)', 'ignoreValue': False}],
                        'loop_metadata': [
                            {'metadata': 'sample', 'matchMode': 'group'},
                            {'metadata': 'kind', 'matchMode': 'exact', 'value': 'cv'},
                        ],
                    },
                }
            ],
        },
        {
            'tables': [
                {
                    'header': ['Run: sample-a'],
                    'metadata': {'sample': 'sample-a', 'kind': 'cv'},
                    'columns': [{'name': 'Potential'}, {'name': 'Current'}],
                    'rows': [],
                }
            ],
        },
    )
    converter.prepare()

    assert converter._compute_check_loop_condition(0, 0) == (True, 'sample-a', 'sample-a')


def test_compute_check_loop_condition_rejects_non_matching_loop_metadata():
    converter = make_converter(
        {
            'identifiers': [],
            'tables': [
                {
                    'loopType': 'matching',
                    'inputTableIndex': 0,
                    'table': {
                        'loop_header': [{'column': 'Potential'}],
                        'loop_theader': [],
                        'loop_metadata': [
                            {'metadata': 'kind', 'matchMode': 'exact', 'value': 'cv'},
                        ],
                    },
                }
            ],
        },
        {
            'tables': [
                {
                    'header': [],
                    'metadata': {'kind': 'gc-ms'},
                    'columns': [{'name': 'Potential'}],
                    'rows': [],
                }
            ],
        },
    )

    assert converter._compute_check_loop_condition(0, 0) == (False, )


def test_process_builds_output_table_and_applies_operations():
    converter = make_converter(
        {
            'identifiers': [],
            'tables': [
                {
                    'loopType': 'none',
                    'inputTableIndex': 0,
                    'header': {'TITLE': 'demo'},
                    'table': {
                        'xColumn': {'columnIndex': 0},
                        'yColumn': {'columnIndex': 1},
                        'xOperations': [],
                        'yOperations': [{'type': 'value', 'value': '2', 'operator': '*'}],
                        'yOperationsDescription': 'double y',
                    },
                }
            ],
        },
        {
            'tables': [
                {
                    'header': [],
                    'metadata': {},
                    'columns': [{'name': 'x'}, {'name': 'y'}],
                    'rows': [
                        ['1,5', '2'],
                        ['3', '4'],
                    ],
                }
            ],
        },
    )

    converter.process()

    [table] = list(converter.tables)
    assert table['header'] == {'TITLE': 'demo'}
    assert table['x'] == ['1.5', '3']
    assert table['y'] == ['4.0', '8.0']
    assert table['applied_y_operator'] is True
    assert table['applied_operator_failed'] is False
    assert table['y_operations_description'] == 'double y'
