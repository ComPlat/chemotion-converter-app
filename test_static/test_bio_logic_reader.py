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
        assert tables[-1]['metadata']["Saved on.File"] == "FK155_JLGU_GE_50-2_15_m1p233mg_Li_LP30_RT_rate_stability_20230906_03_GCPL_C07.mpr"
        assert tables[-1]['metadata']["Saved on.Directory"] == "D:\\Fabian\\LiBOB in EiPS\\Graphite half cell\\FK155_JLGU_GE_50-2_15_m1p233mg_Li_LP30_RT_rate_stability_20230906\\"
        assert tables[-1]['metadata']["Saved on.Host"] == "192.109.209.100"

        assert tables[-1]['metadata']["Device"] == "MPG-2 (SN 0328)"
        assert tables[-1]['metadata']["Address"] == "192.109.209.99"

        assert tables[-1]['metadata']["Electrode material"] == "GE (S\u00fcdchemie)"
        assert tables[-1]['metadata']["Initial state"] == "discharged"
        assert tables[-1]['metadata']["Electrolyte"] == "LP30"
        assert tables[-1]['metadata']["Comments"] == "rate + cyclability"
        assert tables[-1]['metadata']["Mass of active material"] == "1.260 mg"
        assert tables[-1]['metadata']["at x"] == "0.000"
        assert tables[-1]['metadata']["Molecular weight of active material (at x = 0)"] == "0.001 g/mol"
        assert tables[-1]['metadata']["Atomic weight of intercalated ion"] == "0.001 g/mol"
        assert tables[-1]['metadata']["Acquisition started at"] == "xo = 0.000"
        assert tables[-1]['metadata']["Number of e- transfered per intercalated ion"] == "1"
        assert tables[-1]['metadata']["for DX"] == "1"
        assert tables[-1]['metadata']["DQ"] == "33769.888 mA.h"
        assert tables[-1]['metadata']["Battery capacity"] == "0.458 mA.h"
        assert tables[-1]['metadata']["Reference electrode"] == "Li/Li+ (3.050 V)"
        assert tables[-1]['metadata']["Electrode surface area"] == "1.130 cm\u00b2"
        assert tables[-1]['metadata']["Characteristic mass"] == "1.260 mg"
        assert tables[-1]['metadata']["Volume (V)"] == "0.001 cm\u00b3"
        assert tables[-1]['metadata']["Cycle Definition"] == "Charge/Discharge alternance"
        assert tables[-1]['metadata']["Ns [COLUMN: 0]"] == "0"
        assert tables[-1]['metadata']["Ns [COLUMN: 1]"] == "1"
        assert tables[-1]['metadata']["Ns [COLUMN: 2]"] == "2"
        assert tables[-1]['metadata']["Ns"] == "[0,1,2]"
        assert tables[-1]['metadata']["Set I/C [COLUMN: 0]"] == "I"
        assert tables[-1]['metadata']["Set I/C [COLUMN: 1]"] == "C x N"
        assert tables[-1]['metadata']["Set I/C [COLUMN: 2]"] == "C x N"
        assert tables[-1]['metadata']["Set I/C"] == "[I,C x N,C x N]"
        assert tables[-1]['metadata']["Is [COLUMN: 0]"] == "0.000"
        assert tables[-1]['metadata']["Is [COLUMN: 1]"] == "10.000"
        assert tables[-1]['metadata']["Is [COLUMN: 2]"] == "-10.000"
        assert tables[-1]['metadata']["Is"] == "[0.000,10.000,-10.000]"
        assert tables[-1]['metadata']["unit Is [COLUMN: 0]"] == "mA"
        assert tables[-1]['metadata']["unit Is [COLUMN: 1]"] == "mA"
        assert tables[-1]['metadata']["unit Is [COLUMN: 2]"] == "mA"
        assert tables[-1]['metadata']["unit Is"] == "[mA,mA,mA]"
        assert tables[-1]['metadata']["vs. [COLUMN: 0]"] == "<None>"
        assert tables[-1]['metadata']["vs. [COLUMN: 1]"] == "<None>"
        assert tables[-1]['metadata']["vs. [COLUMN: 2]"] == "<None>"
        assert tables[-1]['metadata']["vs."] == "[<None>,<None>,<None>]"
        assert tables[-1]['metadata']["N [COLUMN: 0]"] == "1.00"
        assert tables[-1]['metadata']["N [COLUMN: 1]"] == "0.10"
        assert tables[-1]['metadata']["N [COLUMN: 2]"] == "0.10"
        assert tables[-1]['metadata']["N"] == "[1.00,0.10,0.10]"
        assert tables[-1]['metadata']["I sign [COLUMN: 0]"] == "< 0"
        assert tables[-1]['metadata']["I sign [COLUMN: 1]"] == "< 0"
        assert tables[-1]['metadata']["I sign [COLUMN: 2]"] == "> 0"
        assert tables[-1]['metadata']["I sign"] == "[< 0,< 0,> 0]"
        assert tables[-1]['metadata']["t1 (h:m:s) [COLUMN: 0]"] == "0:00:0.0000"
        assert tables[-1]['metadata']["t1 (h:m:s) [COLUMN: 1]"] == "20:00:0.0000"
        assert tables[-1]['metadata']["t1 (h:m:s) [COLUMN: 2]"] == "20:00:0.0000"
        assert tables[-1]['metadata']["t1 (h:m:s)"] == "[0:00:0.0000,20:00:0.0000,20:00:0.0000]"
        assert tables[-1]['metadata']["I Range [COLUMN: 0]"] == "100 \u00b5A"
        assert tables[-1]['metadata']["I Range [COLUMN: 1]"] == "100 \u00b5A"
        assert tables[-1]['metadata']["I Range [COLUMN: 2]"] == "100 \u00b5A"
        assert tables[-1]['metadata']["I Range"] == "[100 \u00b5A,100 \u00b5A,100 \u00b5A]"
        assert tables[-1]['metadata']["Bandwidth [COLUMN: 0]"] == "5"
        assert tables[-1]['metadata']["Bandwidth [COLUMN: 1]"] == "5"
        assert tables[-1]['metadata']["Bandwidth [COLUMN: 2]"] == "5"
        assert tables[-1]['metadata']["Bandwidth"] == "[5,5,5]"
        assert tables[-1]['metadata']["dE1 (mV) [COLUMN: 0]"] == "0.00"
        assert tables[-1]['metadata']["dE1 (mV) [COLUMN: 1]"] == "10.00"
        assert tables[-1]['metadata']["dE1 (mV) [COLUMN: 2]"] == "10.00"
        assert tables[-1]['metadata']["dE1 (mV)"] == "[0.00,10.00,10.00]"
        assert tables[-1]['metadata']["dt1 (s) [COLUMN: 0]"] == "0.0000"
        assert tables[-1]['metadata']["dt1 (s) [COLUMN: 1]"] == "10.0000"
        assert tables[-1]['metadata']["dt1 (s) [COLUMN: 2]"] == "10.0000"
        assert tables[-1]['metadata']["dt1 (s)"] == "[0.0000,10.0000,10.0000]"
        assert tables[-1]['metadata']["EM (V) [COLUMN: 0]"] == "0.000"
        assert tables[-1]['metadata']["EM (V) [COLUMN: 1]"] == "0.005"
        assert tables[-1]['metadata']["EM (V) [COLUMN: 2]"] == "2.000"
        assert tables[-1]['metadata']["EM (V)"] == "[0.000,0.005,2.000]"
        assert tables[-1]['metadata']["tM (h:m:s) [COLUMN: 0]"] == "0:00:0.0000"
        assert tables[-1]['metadata']["tM (h:m:s) [COLUMN: 1]"] == "0:00:0.0000"
        assert tables[-1]['metadata']["tM (h:m:s) [COLUMN: 2]"] == "0:00:0.0000"
        assert tables[-1]['metadata']["tM (h:m:s)"] == "[0:00:0.0000,0:00:0.0000,0:00:0.0000]"
        assert tables[-1]['metadata']["Im [COLUMN: 0]"] == "0.000"
        assert tables[-1]['metadata']["Im [COLUMN: 1]"] == "0.000"
        assert tables[-1]['metadata']["Im [COLUMN: 2]"] == "0.000"
        assert tables[-1]['metadata']["Im"] == "[0.000,0.000,0.000]"
        assert tables[-1]['metadata']["unit Im [COLUMN: 0]"] == "mA"
        assert tables[-1]['metadata']["unit Im [COLUMN: 1]"] == "mA"
        assert tables[-1]['metadata']["unit Im [COLUMN: 2]"] == "mA"
        assert tables[-1]['metadata']["unit Im"] == "[mA,mA,mA]"
        assert tables[-1]['metadata']["dI/dt [COLUMN: 0]"] == "0.000"
        assert tables[-1]['metadata']["dI/dt [COLUMN: 1]"] == "0.000"
        assert tables[-1]['metadata']["dI/dt [COLUMN: 2]"] == "0.000"
        assert tables[-1]['metadata']["dI/dt"] == "[0.000,0.000,0.000]"
        assert tables[-1]['metadata']["dunit dI/dt [COLUMN: 0]"] == "mA/s"
        assert tables[-1]['metadata']["dunit dI/dt [COLUMN: 1]"] == "mA/s"
        assert tables[-1]['metadata']["dunit dI/dt [COLUMN: 2]"] == "mA/s"
        assert tables[-1]['metadata']["dunit dI/dt"] == "[mA/s,mA/s,mA/s]"
        assert tables[-1]['metadata']["E range min (V) [COLUMN: 0]"] == "-10.000"
        assert tables[-1]['metadata']["E range min (V) [COLUMN: 1]"] == "-10.000"
        assert tables[-1]['metadata']["E range min (V) [COLUMN: 2]"] == "-10.000"
        assert tables[-1]['metadata']["E range min (V)"] == "[-10.000,-10.000,-10.000]"
        assert tables[-1]['metadata']["E range max (V) [COLUMN: 0]"] == "10.000"
        assert tables[-1]['metadata']["E range max (V) [COLUMN: 1]"] == "10.000"
        assert tables[-1]['metadata']["E range max (V) [COLUMN: 2]"] == "10.000"
        assert tables[-1]['metadata']["E range max (V)"] == "[10.000,10.000,10.000]"
        assert tables[-1]['metadata']["dq [COLUMN: 0]"] == "0.000"
        assert tables[-1]['metadata']["dq [COLUMN: 1]"] == "1.000"
        assert tables[-1]['metadata']["dq [COLUMN: 2]"] == "1.000"
        assert tables[-1]['metadata']["dq"] == "[0.000,1.000,1.000]"
        assert tables[-1]['metadata']["unit dq [COLUMN: 0]"] == "mA.h"
        assert tables[-1]['metadata']["unit dq [COLUMN: 1]"] == "mA.h"
        assert tables[-1]['metadata']["unit dq [COLUMN: 2]"] == "mA.h"
        assert tables[-1]['metadata']["rows"] == "0"

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
