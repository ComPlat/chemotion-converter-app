from pathlib import Path

from test_static.utils import TestReader


def test_bio_logic():
    test_file = Path(
        __file__).parent.parent / 'test_static/test_files/bio_logic_FK155_JLGU_GE_50-2_15_m1p233mg_Li_LP30_RT_rate_stability_20230906.tar.xz'
    with TestReader(test_file.__str__(), 'bio_logic_080ecac4-8fa2-4c47-b7cc-4ef5db082b07') as reader:
        tables = reader.as_dict['tables']
        assert tables[-1]['header'] == ['EC-Lab LOG FILE', 'Galvanostatic Cycling with Potential Limitation',
                                        'CE vs. WE compliance from -10 V to 10 V',
                                        'EC-Lab for windows v11.43 (software)', 'Internet server v11.40 (firmware)',
                                        'Command interpretor v11.40 (firmware)']

        assert tables[-1]['metadata']["Run on channel"] == "7 (SN 67339)"
        assert tables[-1]['metadata']["Electrode connection"] == "standard"
        assert tables[-1]['metadata']["Potential control"] == "Ewe"
        assert tables[-1]['metadata']["Ewe ctrl range"] == "min = -10.00 V, max = 10.00 V"
        assert tables[-1]['metadata']["Safety Limits"] == "Do not start on E overload"
        assert tables[-1]['metadata']["Acquisition started on"] == "09/06/2023 15:18:20.995"
        assert tables[-1]['metadata']["Loaded Setting File"] == "D:\\Fabian\\LiBOB in EiPS\\Graphite half cell\\FK125_JLGU_GE_LP30_RateAndCyclab_1p26mg_PlOldPress_090823\\FK125_JLGU_GE_LP30_RateAndCyclab_1p26mg_PlOldPress_090823.mps"


        assert len(tables[0]['rows']) == 16154
        assert tables[0]['columns'] == [{"key": "0", "name": "uts (s)"}, {"key": "1", "name": "Ns"},
                                        {"key": "2", "name": "time (s)"},
                                        {"key": "3", "name": "time standard_error (s)"},
                                        {"key": "4", "name": "dq (mA\u00b7h)"},
                                        {"key": "5", "name": "dq standard_error (mA\u00b7h)"},
                                        {"key": "6", "name": "(Q-Qo) (mA\u00b7h)"},
                                        {"key": "7", "name": "(Q-Qo) standard_error (mA\u00b7h)"},
                                        {"key": "8", "name": "Ewe (V)"}, {"key": "9", "name": "Ewe standard_error (V)"},
                                        {"key": "10", "name": "I Range"},
                                        {"key": "11", "name": "Q charge or discharge (C)"},
                                        {"key": "12", "name": "Q charge or discharge standard_error (C)"},
                                        {"key": "13", "name": "half cycle"}, {"key": "14", "name": "mode"},
                                        {"key": "15", "name": "ox or red"}, {"key": "16", "name": "error"},
                                        {"key": "17", "name": "control changes"}, {"key": "18", "name": "Ns changes"},
                                        {"key": "19", "name": "counter inc."}, {"key": "20", "name": "control_V (V)"},
                                        {"key": "21", "name": "control_V standard_error (V)"},
                                        {'key': '22', 'name': 'control_I (mA)'},
                                        {'key': '23', 'name': 'control_I standard_error (mA)'}]
