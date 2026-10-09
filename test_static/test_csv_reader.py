from pathlib import Path
from test_static.utils import HandleTestReader


def test_csv_duration_column():
    test_file = Path(__file__).parent / 'test_files/csv_ELE-65-1.csv'
    with HandleTestReader(str(test_file), 'csv_reader') as reader:
        table = reader.as_dict['tables'][0]
        assert len(table['rows']) == 774
        assert len(table['columns']) == 4
        assert table['columns'][3] == {'key': '3', 'name': 'Column #3 (duration_s)'}
        assert table['metadata']['column_03'] == 'duration_s'
        assert table['rows'][0][3] == '0.0'
        assert table['rows'][1][3] == '3.740894'
        assert table['rows'][-1][3] == '3523.061038'


def test_csv_without_datetime_has_no_duration_column(tmp_path):
    # time of day without a date must not be treated as a date+time column
    test_file = tmp_path / 'no_datetime.csv'
    test_file.write_text('time,value\n' + ''.join(f'10:{i:02d}:00,{i}.5\n' for i in range(30)))
    with HandleTestReader(str(test_file), 'csv_reader') as reader:
        table = reader.as_dict['tables'][0]
        assert len(table['rows']) == 30
        assert len(table['columns']) == 2
        assert all(len(row) == 2 for row in table['rows'])
