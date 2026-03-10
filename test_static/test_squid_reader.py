from pathlib import Path
from test_static.utils import TestReader


def test_Squid():
    test_file = Path(__file__).parent.parent / 'test_static/test_files/squid_JGB-C1_10K-300K_0.1T.dat'
    with TestReader(test_file.__str__(), 'squid_reader') as reader:
        assert len(reader.as_dict['tables']) == 1
        assert len(reader.as_dict['tables'][0]['rows']) == 59
        assert len(reader.as_dict['tables'][0]['columns']) == 89
        assert reader.as_dict['tables'][0]['metadata']['INFO.SQUID_MODULE_NAME'] == 'Quantum Design Squid Module'