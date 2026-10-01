from types import SimpleNamespace

import pytest

from converter_app.converters import Converter


def make_converter(profile_data, file_data=None):
    profile = SimpleNamespace(data=profile_data)
    return Converter(profile, file_data or {'metadata': {}, 'tables': []})


COMPOSED_REFERENCES = [
    {
        'id': '#anode',
        'type': 'fileMetadata',
        'key': 'anode',
        'match': 'any',
        'value': '',
        'optional': True,
        'isDatatableOutput': False,
    },
    {
        'id': '#carrier',
        'type': 'tableMetadata',
        'tableIndex': 0,
        'key': 'carrier',
        'match': 'any',
        'value': '',
        'optional': True,
        'isDatatableOutput': False,
    },
]

COMPOSED_FILE_DATA = {
    'metadata': {'anode': 'LiFePO4'},
    'tables': [
        {'header': [], 'metadata': {'carrier': 'aluminium'}, 'columns': [], 'rows': []},
    ],
}


def composed_identifier(**kwargs):
    return {
        'id': '#comment',
        'type': 'composed',
        'optional': True,
        'match': 'any',
        'value': '',
        'template': '{{#anode}} clamped on {{#carrier}}',
        **kwargs,
    }


def make_composed_converter(composed, references=None, file_data=None):
    identifiers = list(COMPOSED_REFERENCES if references is None else references) + [composed]
    return make_converter(
        {'identifiers': identifiers, 'tables': []},
        file_data or COMPOSED_FILE_DATA,
    )


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


def test_composed_identifier_joins_referenced_values_and_free_text():
    converter = make_composed_converter(composed_identifier())
    converter.prepare()

    [match] = [m for m in converter.matches if m['identifier']['type'] == 'composed']
    assert match['result'] == {'value': 'LiFePO4 clamped on aluminium'}


@pytest.mark.parametrize(
    'on_missing,expected',
    [
        ('skip', False),
        ('empty', {'value': 'LiFePO4 clamped on '}),
        ('placeholder', {'value': 'LiFePO4 clamped on unknown'}),
    ],
)
def test_composed_identifier_handles_missing_references(on_missing, expected):
    converter = make_composed_converter(
        composed_identifier(onMissing=on_missing, missingPlaceholder='unknown'),
        file_data={
            'metadata': {'anode': 'LiFePO4'},
            'tables': [{'header': [], 'metadata': {}, 'columns': [], 'rows': []}],
        },
    )

    assert converter.match_identifier(converter.identifiers[-1]) == expected


def test_composed_identifier_treats_removed_references_as_missing():
    converter = make_composed_converter(
        composed_identifier(template='{{#gone}}clamped on {{#carrier}}', onMissing='empty')
    )

    assert converter.match_identifier(converter.identifiers[-1]) == {'value': 'clamped on aluminium'}


def test_composed_identifier_resolves_nested_templates():
    inner = composed_identifier(id='#inner', template='{{#anode}} anode')
    converter = make_composed_converter(
        composed_identifier(template='{{#inner}} clamped on {{#carrier}}'),
        references=COMPOSED_REFERENCES + [inner],
    )

    assert converter.match_identifier(converter.identifiers[-1]) == {
        'value': 'LiFePO4 anode clamped on aluminium'
    }


def test_composed_identifier_breaks_reference_cycles():
    cycle_partner = composed_identifier(id='#b', template='B {{#a}}', onMissing='empty')
    converter = make_composed_converter(
        composed_identifier(id='#a', template='A {{#b}}', onMissing='empty'),
        references=[cycle_partner],
    )

    # a -> b -> a: the reference back to a resolves to nothing, so only the free
    # text of both templates remains instead of recursing forever
    assert converter.match_identifier(converter.identifiers[-1]) == {'value': 'A B '}


def test_composed_identifier_prefers_the_current_input_table():
    converter = make_composed_converter(
        composed_identifier(),
        file_data={
            'metadata': {'anode': 'LiFePO4'},
            'tables': [
                {'header': [], 'metadata': {'carrier': 'aluminium'}, 'columns': [], 'rows': []},
                {'header': [], 'metadata': {'carrier': 'copper'}, 'columns': [], 'rows': []},
                {'header': [], 'metadata': {}, 'columns': [], 'rows': []},
            ],
        },
    )
    identifier = converter.identifiers[-1]

    assert converter.match_identifier(identifier, 1) == {
        'value': 'LiFePO4 clamped on copper',
        'tableIndex': 1,
    }
    # input table #3 holds no carrier, so the table configured on the reference is used
    assert converter.match_identifier(identifier, 2) == {
        'value': 'LiFePO4 clamped on aluminium',
        'tableIndex': 2,
    }


def test_composed_identifier_is_ignored_while_matching_profiles():
    converter = make_composed_converter(
        composed_identifier(optional=False),
        references=[{
            'id': '#anode',
            'type': 'fileMetadata',
            'key': 'anode',
            'match': 'exact',
            'value': 'LiFePO4',
            'optional': False,
        }],
    )

    assert converter.match() == 1


def test_composed_identifier_is_written_to_the_output_table_header():
    composed = composed_identifier(
        isDatatableOutput=True,
        isLoobDatatableOutput=True,
        isFirstMatch=True,
        outputDatatableKey='COMMENT',
        outputTableIndex=['table-uuid'],
    )
    converter = make_converter(
        {
            'identifiers': COMPOSED_REFERENCES + [composed],
            'tables': [
                {
                    'uuid': 'table-uuid',
                    'loopType': 'none',
                    'inputTableIndex': 0,
                    'header': {'TITLE': 'demo'},
                    'table': {'xColumn': {'columnIndex': 0}, 'yColumn': {'columnIndex': 1}},
                }
            ],
        },
        {
            'metadata': {'anode': 'LiFePO4'},
            'tables': [
                {
                    'header': [],
                    'metadata': {'carrier': 'aluminium'},
                    'columns': [{'name': 'x'}, {'name': 'y'}],
                    'rows': [['1', '2']],
                }
            ],
        },
    )

    converter.process()

    [table] = list(converter.tables)
    assert table['header'] == {'TITLE': 'demo', 'COMMENT': 'LiFePO4 clamped on aluminium'}


def test_composed_identifier_keeps_scalar_operations_of_its_references():
    converter = make_composed_converter(
        composed_identifier(template='{{#cycles}} cycles'),
        references=[{
            'id': '#cycles',
            'type': 'fileMetadata',
            'key': 'cycles',
            'match': 'any',
            'value': '',
            'optional': True,
            'operations': [{'operator': '+', 'value': '1'}],
        }],
        file_data={'metadata': {'cycles': '4'}, 'tables': []},
    )

    assert converter.match_identifier(converter.identifiers[-1]) == {'value': '5.0 cycles'}


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
