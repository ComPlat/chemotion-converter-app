from .utils_test import compare_reader_result
from converter_app.readers import READERS as registry

all_reader = set()



def test_1_LA_P37cd_DUT52Zr_Thermo_XRD_5_90_45min_25_C_1_xy():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/Powder Diffraction/Malvern Panalytical/Unkown-xy','../test_files/ConverterAutoResults/Powder Diffraction/Malvern Panalytical/Unkown-xy','LA_P37cd_DUT52Zr-Thermo-XRD-5-90-45min_25°C_1.xy')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_2_LA_P_37cd_DUT_52_Zr__act_EtOH_xyd():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/Powder Diffraction/Malvern Panalytical/Unkown-xy','../test_files/ConverterAutoResults/Powder Diffraction/Malvern Panalytical/Unkown-xy','LA_P-37cd_DUT-52(Zr)_act_EtOH.xyd')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_3_LA_P_37cd_DUT_52_Zr__act_EtOH_raw():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/Powder Diffraction/Malvern Panalytical/Bruker-RAW','../test_files/ConverterAutoResults/Powder Diffraction/Malvern Panalytical/Bruker-RAW','LA_P-37cd_DUT-52(Zr)_act_EtOH.raw')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_4_LA_P37cd_DUT52Zr_Thermo_XRD_5_90_45min_25_C_1_xrdml():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/Powder Diffraction/Malvern Panalytical/Data Collector-xrdml','../test_files/ConverterAutoResults/Powder Diffraction/Malvern Panalytical/Data Collector-xrdml','LA_P37cd_DUT52Zr-Thermo-XRD-5-90-45min_25°C_1.xrdml')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_5_PD_01_02_2__UXD():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/Powder Diffraction/Diffrac Plus/XCH-UXD','../test_files/ConverterAutoResults/Powder Diffraction/Diffrac Plus/XCH-UXD','PD-01-02(2).UXD')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_6_PD_01_02_1__dat():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/Powder Diffraction/Diffrac Plus/Unkown-dat','../test_files/ConverterAutoResults/Powder Diffraction/Diffrac Plus/Unkown-dat','PD-01-02(1).dat')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_7_PD_01_02_2__raw():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/Powder Diffraction/Diffrac Plus/Bruker-RAW','../test_files/ConverterAutoResults/Powder Diffraction/Diffrac Plus/Bruker-RAW','PD-01-02(2).raw')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_8_PowDLL_XY_XRD_Thursday__February_08__2024_xls():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/Powder Diffraction/Diffrac Plus/Bruker-RAW','../test_files/ConverterAutoResults/Powder Diffraction/Diffrac Plus/Bruker-RAW','PowDLL_XY_XRD_Thursday, February 08, 2024.xls')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_9_BS_17_WU_dpt():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/IR/Bruker/Opus-dpt','../test_files/ConverterAutoResults/IR/Bruker/Opus-dpt','BS-17-WU.dpt')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_10_SCH_176_dry_0_dpt():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/IR/Bruker/Opus-dpt','../test_files/ConverterAutoResults/IR/Bruker/Opus-dpt','SCH-176-dry.0.dpt')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_11_SCH_176_0_dpt():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/IR/Bruker/Opus-dpt','../test_files/ConverterAutoResults/IR/Bruker/Opus-dpt','SCH-176.0.dpt')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_12_BS_17_WU_pdf():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/IR/Bruker/pics-pdf','../test_files/ConverterAutoResults/IR/Bruker/pics-pdf','BS-17-WU.pdf')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_13_SCH_176_pdf():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/IR/Bruker/pics-pdf','../test_files/ConverterAutoResults/IR/Bruker/pics-pdf','SCH-176.pdf')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_14_SCH_176_dry_pdf():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/IR/Bruker/pics-pdf','../test_files/ConverterAutoResults/IR/Bruker/pics-pdf','SCH-176-dry.pdf')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_15_SG_V3551_15_19_cif():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/Crystallographie/OlafFuhrINT/Unkown-cif','../test_files/ConverterAutoResults/Crystallographie/OlafFuhrINT/Unkown-cif','SG-V3551-15-19.cif')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_16_SG_V3545_6_13_cif():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/Crystallographie/OlafFuhrINT/Unkown-cif','../test_files/ConverterAutoResults/Crystallographie/OlafFuhrINT/Unkown-cif','SG-V3545-6-13.cif')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_17_SG_V3551_15_19_cfx_LANA():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/Crystallographie/OlafFuhrINT/Unkown-cfx','../test_files/ConverterAutoResults/Crystallographie/OlafFuhrINT/Unkown-cfx','SG-V3551-15-19.cfx_LANA')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_18_File062_brml():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/X-Ray Diffraction/Unknown/Unknown-brml','../test_files/ConverterAutoResults/X-Ray Diffraction/Unknown/Unknown-brml','File062.brml')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_19_DD_HSSE158_xls():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/Thermogravimetric Analysis TGA/TA Instruments/TRIOS-xls','../test_files/ConverterAutoResults/Thermogravimetric Analysis TGA/TA Instruments/TRIOS-xls','DD-HSSE158.xls')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_20_DD_HSSE155_xls():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/Thermogravimetric Analysis TGA/TA Instruments/TRIOS-xls','../test_files/ConverterAutoResults/Thermogravimetric Analysis TGA/TA Instruments/TRIOS-xls','DD-HSSE155.xls')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_21_DD_F43_xls():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/Thermogravimetric Analysis TGA/TA Instruments/TRIOS-xls','../test_files/ConverterAutoResults/Thermogravimetric Analysis TGA/TA Instruments/TRIOS-xls','DD-F43.xls')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_22_DD_SiO2_xls():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/Thermogravimetric Analysis TGA/TA Instruments/TRIOS-xls','../test_files/ConverterAutoResults/Thermogravimetric Analysis TGA/TA Instruments/TRIOS-xls','DD-SiO2.xls')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_23_VLL_R444__1__xls():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/Thermogravimetric Analysis TGA/TA Instruments/TRIOS-xls','../test_files/ConverterAutoResults/Thermogravimetric Analysis TGA/TA Instruments/TRIOS-xls','VLL-R444 (1).xls')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_24_AG_015_xls():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/Thermogravimetric Analysis TGA/TA Instruments/TRIOS-xls','../test_files/ConverterAutoResults/Thermogravimetric Analysis TGA/TA Instruments/TRIOS-xls','AG_015.xls')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_25_DD_HSSE157_xls():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/Thermogravimetric Analysis TGA/TA Instruments/TRIOS-xls','../test_files/ConverterAutoResults/Thermogravimetric Analysis TGA/TA Instruments/TRIOS-xls','DD-HSSE157.xls')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_26_DD_HSSE159_xls():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/Thermogravimetric Analysis TGA/TA Instruments/TRIOS-xls','../test_files/ConverterAutoResults/Thermogravimetric Analysis TGA/TA Instruments/TRIOS-xls','DD-HSSE159.xls')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_27_DD_HSSE152_xls():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/Thermogravimetric Analysis TGA/TA Instruments/TRIOS-xls','../test_files/ConverterAutoResults/Thermogravimetric Analysis TGA/TA Instruments/TRIOS-xls','DD-HSSE152.xls')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_28_DD_HSSE156_xls():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/Thermogravimetric Analysis TGA/TA Instruments/TRIOS-xls','../test_files/ConverterAutoResults/Thermogravimetric Analysis TGA/TA Instruments/TRIOS-xls','DD-HSSE156.xls')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_29_TGA_example_with_derivative_xls():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/Thermogravimetric Analysis TGA/TA Instruments/TRIOS-xls','../test_files/ConverterAutoResults/Thermogravimetric Analysis TGA/TA Instruments/TRIOS-xls','TGA example with derivative.xls')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_30_AG_030_neu_xls():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/Thermogravimetric Analysis TGA/TA Instruments/TRIOS-xls','../test_files/ConverterAutoResults/Thermogravimetric Analysis TGA/TA Instruments/TRIOS-xls','AG_030_neu.xls')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_31_DD_SiO2_2_xls():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/Thermogravimetric Analysis TGA/TA Instruments/TRIOS-xls','../test_files/ConverterAutoResults/Thermogravimetric Analysis TGA/TA Instruments/TRIOS-xls','DD-SiO2-2.xls')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_32_DD_F41_xls():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/Thermogravimetric Analysis TGA/TA Instruments/TRIOS-xls','../test_files/ConverterAutoResults/Thermogravimetric Analysis TGA/TA Instruments/TRIOS-xls','DD-F41.xls')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_33_VLL_R444_tri():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/Thermogravimetric Analysis TGA/TA Instruments/TRIOS-tri','../test_files/ConverterAutoResults/Thermogravimetric Analysis TGA/TA Instruments/TRIOS-tri','VLL-R444.tri')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_34_AG_030_neu_pdf():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/Thermogravimetric Analysis TGA/TA Instruments/pics-pdf','../test_files/ConverterAutoResults/Thermogravimetric Analysis TGA/TA Instruments/pics-pdf','AG_030_neu.pdf')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_35_AG_015_pdf():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/Thermogravimetric Analysis TGA/TA Instruments/pics-pdf','../test_files/ConverterAutoResults/Thermogravimetric Analysis TGA/TA Instruments/pics-pdf','AG_015.pdf')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_36_AG_030_pdf():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/Thermogravimetric Analysis TGA/TA Instruments/pics-pdf','../test_files/ConverterAutoResults/Thermogravimetric Analysis TGA/TA Instruments/pics-pdf','AG_030.pdf')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_37_VLL_R444_txt():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/Thermogravimetric Analysis TGA/TA Instruments/TRIOS-txt','../test_files/ConverterAutoResults/Thermogravimetric Analysis TGA/TA Instruments/TRIOS-txt','VLL-R444.txt')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_38_DHM_Cudmp_EISPOT___Copy_DTA():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/EIS/Gamry/Framework-DTA','../test_files/ConverterAutoResults/EIS/Gamry/Framework-DTA','DHM-Cudmp_EISPOT - Copy.DTA')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_39_CHD048_CHD050_60C_C01_mgr():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/EIS/BioLogic/ECLab-mgr','../test_files/ConverterAutoResults/EIS/BioLogic/ECLab-mgr','CHD048_CHD050_60C_C01.mgr')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_40_CHD048_CHD050_60C_C05_mgr():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/EIS/BioLogic/ECLab-mgr','../test_files/ConverterAutoResults/EIS/BioLogic/ECLab-mgr','CHD048_CHD050_60C_C05.mgr')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_41_testCHD048_CHD050_401_201_60C_C01_mgr():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/EIS/BioLogic/ECLab-mgr','../test_files/ConverterAutoResults/EIS/BioLogic/ECLab-mgr','testCHD048_CHD050_401_201_60C_C01.mgr')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_42_CHD048_CHD050_60C_C07_mgr():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/EIS/BioLogic/ECLab-mgr','../test_files/ConverterAutoResults/EIS/BioLogic/ECLab-mgr','CHD048_CHD050_60C_C07.mgr')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_43_CHD048_CHD050_60C_C06_mgr():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/EIS/BioLogic/ECLab-mgr','../test_files/ConverterAutoResults/EIS/BioLogic/ECLab-mgr','CHD048_CHD050_60C_C06.mgr')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_44_CHD048_CHD050_60C_C02_mgr():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/EIS/BioLogic/ECLab-mgr','../test_files/ConverterAutoResults/EIS/BioLogic/ECLab-mgr','CHD048_CHD050_60C_C02.mgr')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_45_CHD048_CHD050_60C_C02_mpr():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/EIS/BioLogic/ECLab-mpr','../test_files/ConverterAutoResults/EIS/BioLogic/ECLab-mpr','CHD048_CHD050_60C_C02.mpr')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_46_CHD048_CHD050_60C_C06_mpr():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/EIS/BioLogic/ECLab-mpr','../test_files/ConverterAutoResults/EIS/BioLogic/ECLab-mpr','CHD048_CHD050_60C_C06.mpr')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_47_testCHD048_CHD050_401_201_60C_C01_mpr():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/EIS/BioLogic/ECLab-mpr','../test_files/ConverterAutoResults/EIS/BioLogic/ECLab-mpr','testCHD048_CHD050_401_201_60C_C01.mpr')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_48_Readme_md():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/EIS/BioLogic/ECLab-mpr','../test_files/ConverterAutoResults/EIS/BioLogic/ECLab-mpr','Readme.md')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_49_CHD048_CHD050_60C_C01_mpr():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/EIS/BioLogic/ECLab-mpr','../test_files/ConverterAutoResults/EIS/BioLogic/ECLab-mpr','CHD048_CHD050_60C_C01.mpr')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_50_CHD048_CHD050_60C_C07_mpr():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/EIS/BioLogic/ECLab-mpr','../test_files/ConverterAutoResults/EIS/BioLogic/ECLab-mpr','CHD048_CHD050_60C_C07.mpr')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_51_CHD048_CHD050_60C_C05_mpr():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/EIS/BioLogic/ECLab-mpr','../test_files/ConverterAutoResults/EIS/BioLogic/ECLab-mpr','CHD048_CHD050_60C_C05.mpr')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_52_CHD048_CHD050_60C_D128_C01_sta():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/EIS/BioLogic/ECLab-sta','../test_files/ConverterAutoResults/EIS/BioLogic/ECLab-sta','CHD048_CHD050_60C_D128_C01.sta')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_53_CHD048_CHD050_60C_D128_C02_sta():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/EIS/BioLogic/ECLab-sta','../test_files/ConverterAutoResults/EIS/BioLogic/ECLab-sta','CHD048_CHD050_60C_D128_C02.sta')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_54_Readme_md():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/EIS/BioLogic/ECLab-sta','../test_files/ConverterAutoResults/EIS/BioLogic/ECLab-sta','Readme.md')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_55_CHD048_CHD050_60C_mps():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/EIS/BioLogic/ECLab-mps','../test_files/ConverterAutoResults/EIS/BioLogic/ECLab-mps','CHD048_CHD050_60C.mps')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_56_testCHD048_CHD050_401_201_60C_mps():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/EIS/BioLogic/ECLab-mps','../test_files/ConverterAutoResults/EIS/BioLogic/ECLab-mps','testCHD048_CHD050_401_201_60C.mps')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_57_testCHD048_CHD050_401_201_60C_C01_mpl():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/EIS/BioLogic/ECLab-mpl','../test_files/ConverterAutoResults/EIS/BioLogic/ECLab-mpl','testCHD048_CHD050_401_201_60C_C01.mpl')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_58_CD_Carminic_acid_water__1__csv():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/Circular dichroism CDS/Unkown/Unknown-csv','../test_files/ConverterAutoResults/Circular dichroism CDS/Unkown/Unknown-csv','CD_Carminic_acid_water (1).csv')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_59_Peak_JM_03_pdf():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/Size-exclusion chromatography SEC/Agilent/pics-pdf','../test_files/ConverterAutoResults/Size-exclusion chromatography SEC/Agilent/pics-pdf','Peak_JM_03.pdf')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_60_2022_02_04_MS170_crudefull_pdf():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/Size-exclusion chromatography SEC/Agilent/pics-pdf','../test_files/ConverterAutoResults/Size-exclusion chromatography SEC/Agilent/pics-pdf','2022-02-04 MS170_crudefull.pdf')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_61_2021_07_22_MS139_pdf():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/Size-exclusion chromatography SEC/Agilent/pics-pdf','../test_files/ConverterAutoResults/Size-exclusion chromatography SEC/Agilent/pics-pdf','2021-07-22 MS139.pdf')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_62_All_JM_03_pdf():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/Size-exclusion chromatography SEC/Agilent/pics-pdf','../test_files/ConverterAutoResults/Size-exclusion chromatography SEC/Agilent/pics-pdf','All_JM_03.pdf')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_63_2022_02_11_MS170_dialysis25_pdf():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/Size-exclusion chromatography SEC/Agilent/pics-pdf','../test_files/ConverterAutoResults/Size-exclusion chromatography SEC/Agilent/pics-pdf','2022-02-11 MS170_dialysis25.pdf')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_64_MS_185_MALS_Daten_pdf():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/Size-exclusion chromatography SEC/Agilent/pics-pdf','../test_files/ConverterAutoResults/Size-exclusion chromatography SEC/Agilent/pics-pdf','MS-185_MALS-Daten.pdf')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_65_MS_185_Lichtstreuung_pdf():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/Size-exclusion chromatography SEC/Agilent/pics-pdf','../test_files/ConverterAutoResults/Size-exclusion chromatography SEC/Agilent/pics-pdf','MS-185_Lichtstreuung.pdf')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_66_MS_185_PMMA_Calibration_pdf():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/Size-exclusion chromatography SEC/Agilent/pics-pdf','../test_files/ConverterAutoResults/Size-exclusion chromatography SEC/Agilent/pics-pdf','MS-185_PMMA Calibration.pdf')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_67_2022_02_04_MS170_crudezoom_pdf():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/Size-exclusion chromatography SEC/Agilent/pics-pdf','../test_files/ConverterAutoResults/Size-exclusion chromatography SEC/Agilent/pics-pdf','2022-02-04 MS170_crudezoom.pdf')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_68_1_Inj__Vial__71__JM_03___1_TXT():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/Size-exclusion chromatography SEC/Agilent/WinGPC-TXT','../test_files/ConverterAutoResults/Size-exclusion chromatography SEC/Agilent/WinGPC-TXT','1_Inj_ Vial  71  JM_03 - 1.TXT')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_69_2022_02_04_MS170_crudezoom_TXT():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/Size-exclusion chromatography SEC/Agilent/WinGPC-TXT','../test_files/ConverterAutoResults/Size-exclusion chromatography SEC/Agilent/WinGPC-TXT','2022-02-04 MS170_crudezoom.TXT')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_70_2022_02_11_MS170_dialysis25_TXT():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/Size-exclusion chromatography SEC/Agilent/WinGPC-TXT','../test_files/ConverterAutoResults/Size-exclusion chromatography SEC/Agilent/WinGPC-TXT','2022-02-11 MS170_dialysis25.TXT')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_71_2023_05_31_XW09P_TXT():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/Size-exclusion chromatography SEC/Agilent/WinGPC-TXT','../test_files/ConverterAutoResults/Size-exclusion chromatography SEC/Agilent/WinGPC-TXT','2023_05_31_XW09P.TXT')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_72_2022_02_04_MS170_crudefull_TXT():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/Size-exclusion chromatography SEC/Agilent/WinGPC-TXT','../test_files/ConverterAutoResults/Size-exclusion chromatography SEC/Agilent/WinGPC-TXT','2022-02-04 MS170_crudefull.TXT')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_73_DMAC_SEC_TXT():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/Size-exclusion chromatography SEC/Agilent/WinGPC-TXT','../test_files/ConverterAutoResults/Size-exclusion chromatography SEC/Agilent/WinGPC-TXT','DMAC-SEC.TXT')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_74_MS_185_MALS_Daten_TXT():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/Size-exclusion chromatography SEC/Agilent/WinGPC-TXT','../test_files/ConverterAutoResults/Size-exclusion chromatography SEC/Agilent/WinGPC-TXT','MS-185_MALS-Daten.TXT')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_75_THF_SEC_TXT():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/Size-exclusion chromatography SEC/Agilent/WinGPC-TXT','../test_files/ConverterAutoResults/Size-exclusion chromatography SEC/Agilent/WinGPC-TXT','THF-SEC.TXT')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_76_MS_185_Lichtstreuung_TXT():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/Size-exclusion chromatography SEC/Agilent/WinGPC-TXT','../test_files/ConverterAutoResults/Size-exclusion chromatography SEC/Agilent/WinGPC-TXT','MS-185_Lichtstreuung.TXT')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_77_File069_TXT():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/Size-exclusion chromatography SEC/Agilent/WinGPC-TXT','../test_files/ConverterAutoResults/Size-exclusion chromatography SEC/Agilent/WinGPC-TXT','File069.TXT')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_78_MS_185_PMMA_Calibration_TXT():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/Size-exclusion chromatography SEC/Agilent/WinGPC-TXT','../test_files/ConverterAutoResults/Size-exclusion chromatography SEC/Agilent/WinGPC-TXT','MS-185_PMMA Calibration.TXT')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_79_SEC2_2021_07_22_MS139_TXT():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/Size-exclusion chromatography SEC/Agilent/WinGPC-TXT','../test_files/ConverterAutoResults/Size-exclusion chromatography SEC/Agilent/WinGPC-TXT','SEC2_2021-07-22 MS139.TXT')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_80_FeBr3_TMGasme____100mV_txt():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/CV/Metrohm/NOVA-txt','../test_files/ConverterAutoResults/CV/Metrohm/NOVA-txt','FeBr3(TMGasme) - 100mV.txt')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_81__Cu_TMG2cHexqu_2_PF6_txt():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/CV/Metrohm/NOVA-txt','../test_files/ConverterAutoResults/CV/Metrohm/NOVA-txt','[Cu(TMG2cHexqu)2]PF6.txt')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_82_SCR167Fc_txt():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/CV/Metrohm/NOVA-txt','../test_files/ConverterAutoResults/CV/Metrohm/NOVA-txt','SCR167Fc.txt')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_83_Readme_md():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/CV/Metrohm/NOVA-txt','../test_files/ConverterAutoResults/CV/Metrohm/NOVA-txt','Readme.md')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_84_FeBr3_TMG5NMe2asme____100mV_txt():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/CV/Metrohm/NOVA-txt','../test_files/ConverterAutoResults/CV/Metrohm/NOVA-txt','FeBr3(TMG5NMe2asme) - 100mV.txt')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_85_File021_CV_txt():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/CV/Metrohm/NOVA-txt','../test_files/ConverterAutoResults/CV/Metrohm/NOVA-txt','File021_CV.txt')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_86_01_CV_DTA():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/CV/Gamry/Framework-DTA','../test_files/ConverterAutoResults/CV/Gamry/Framework-DTA','01_CV.DTA')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_87_20200703_acn_SGV3375_100_redox5_DTA():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/CV/Gamry/Framework-DTA','../test_files/ConverterAutoResults/CV/Gamry/Framework-DTA','20200703_acn_SGV3375_100_redox5.DTA')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_88_DHM_15_CV_Demo_DTA():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/CV/Gamry/Framework-DTA','../test_files/ConverterAutoResults/CV/Gamry/Framework-DTA','DHM-15-CV-Demo.DTA')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_89_20200702_dcm_PH884_100_red2_DTA():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/CV/Gamry/Framework-DTA','../test_files/ConverterAutoResults/CV/Gamry/Framework-DTA','20200702_dcm_PH884_100_red2.DTA')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_90_p_Cl_Ph_CO2Me_MeCN_xlsx():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/CV/PalmSens/PSTrace-Excel','../test_files/ConverterAutoResults/CV/PalmSens/PSTrace-Excel','p-Cl-Ph-CO2Me_MeCN.xlsx')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_91_p_Br_Ph_CO2Me_MeCN_xlsx():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/CV/PalmSens/PSTrace-Excel','../test_files/ConverterAutoResults/CV/PalmSens/PSTrace-Excel','p-Br-Ph-CO2Me_MeCN.xlsx')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_92_Readme_md():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/CV/PalmSens/PSTrace-Excel','../test_files/ConverterAutoResults/CV/PalmSens/PSTrace-Excel','Readme.md')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_93_p_Cl_Ph_CO2Me_MeCN_pssession():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/CV/PalmSens/PSTrace-pssession','../test_files/ConverterAutoResults/CV/PalmSens/PSTrace-pssession','p-Cl-Ph-CO2Me_MeCN.pssession')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_94_File053_pssession():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/CV/PalmSens/PSTrace-pssession','../test_files/ConverterAutoResults/CV/PalmSens/PSTrace-pssession','File053.pssession')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_95_p_Br_Ph_CO2Me_MeCN_pssession():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/CV/PalmSens/PSTrace-pssession','../test_files/ConverterAutoResults/CV/PalmSens/PSTrace-pssession','p-Br-Ph-CO2Me_MeCN.pssession')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_96_20230328_DMF_baseline_CSW():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/UVVIS/Agilent/Cary300-CSW','../test_files/ConverterAutoResults/UVVIS/Agilent/Cary300-CSW','20230328_DMF_baseline.CSW')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_97_Readme_md():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/UVVIS/Agilent/Cary300-CSW','../test_files/ConverterAutoResults/UVVIS/Agilent/Cary300-CSW','Readme.md')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_98_20230329_YA_100_DMF_10uM__1__xlsx():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/UVVIS/Agilent/Cary300-Excel','../test_files/ConverterAutoResults/UVVIS/Agilent/Cary300-Excel','20230329_YA_100_DMF_10uM (1).xlsx')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_99_File015_UV_Vis_RWTH_Cary60_csv():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/UVVIS/Agilent/Cary60-csv','../test_files/ConverterAutoResults/UVVIS/Agilent/Cary60-csv','File015_UV_Vis_RWTH_Cary60.csv')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_100_Absorbance_14_38_40_588_txt():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/UVVIS/OceanInsight/OceanView-txt','../test_files/ConverterAutoResults/UVVIS/OceanInsight/OceanView-txt','Absorbance_14-38-40-588.txt')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_101_Absorbance_14_44_30_644_txt():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/UVVIS/OceanInsight/OceanView-txt','../test_files/ConverterAutoResults/UVVIS/OceanInsight/OceanView-txt','Absorbance_14-44-30-644.txt')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_102_Absorbance_14_38_32_818_txt():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/UVVIS/OceanInsight/OceanView-txt','../test_files/ConverterAutoResults/UVVIS/OceanInsight/OceanView-txt','Absorbance_14-38-32-818.txt')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_103_Absorbance_14_42_39_645_txt():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/UVVIS/OceanInsight/OceanView-txt','../test_files/ConverterAutoResults/UVVIS/OceanInsight/OceanView-txt','Absorbance_14-42-39-645.txt')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_104_BF2PhOEtAcPh_2_1__dx():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/UVVIS/JASCO/Unknown-dx','../test_files/ConverterAutoResults/UVVIS/JASCO/Unknown-dx','BF2PhOEtAcPh-2(1).dx')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_105_PhCOEtPhAcetylen_1__dx():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/UVVIS/JASCO/Unknown-dx','../test_files/ConverterAutoResults/UVVIS/JASCO/Unknown-dx','PhCOEtPhAcetylen(1).dx')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_106_9_PhOEtAcetylen_1__dx():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/UVVIS/JASCO/Unknown-dx','../test_files/ConverterAutoResults/UVVIS/JASCO/Unknown-dx','9-PhOEtAcetylen(1).dx')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_107_BF2PhOEtAcPh_2_txt():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/UVVIS/JASCO/V570-txt','../test_files/ConverterAutoResults/UVVIS/JASCO/V570-txt','BF2PhOEtAcPh-2.txt')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_108_ADG_P_05_Sample_Raw_2__csv():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/UVVIS/Unknown/Unkown-csv','../test_files/ConverterAutoResults/UVVIS/Unknown/Unkown-csv','ADG_P_05.Sample.Raw(2).csv')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_109_UVVIS_RawCsv_json():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/UVVIS/Unknown/Unkown-csv','../test_files/ConverterAutoResults/UVVIS/Unknown/Unkown-csv','UVVIS-RawCsv.json')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_110_File73_dsp():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/UVVIS/ThermoScientific/VISIONlite-dsp','../test_files/ConverterAutoResults/UVVIS/ThermoScientific/VISIONlite-dsp','File73.dsp')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_111_File72_dsp():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/UVVIS/ThermoScientific/VISIONlite-dsp','../test_files/ConverterAutoResults/UVVIS/ThermoScientific/VISIONlite-dsp','File72.dsp')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_112_File75_dsp():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/UVVIS/ThermoScientific/VISIONlite-dsp','../test_files/ConverterAutoResults/UVVIS/ThermoScientific/VISIONlite-dsp','File75.dsp')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_113_File74_dsp():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/UVVIS/ThermoScientific/VISIONlite-dsp','../test_files/ConverterAutoResults/UVVIS/ThermoScientific/VISIONlite-dsp','File74.dsp')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_114_SVS_1163_A_EA_pdf():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/Elementary Analysis/KIT-CN/ELA-PDF','../test_files/ConverterAutoResults/Elementary Analysis/KIT-CN/ELA-PDF','SVS-1163-A EA.pdf')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_115_SVS_1175_A_EA_pdf():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/Elementary Analysis/KIT-CN/ELA-PDF','../test_files/ConverterAutoResults/Elementary Analysis/KIT-CN/ELA-PDF','SVS-1175-A EA.pdf')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_116_SVS_1150_A_EA_pdf():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/Elementary Analysis/KIT-CN/ELA-PDF','../test_files/ConverterAutoResults/Elementary Analysis/KIT-CN/ELA-PDF','SVS-1150-A EA.pdf')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_117_SVS_1172_A_EA_pdf():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/Elementary Analysis/KIT-CN/ELA-PDF','../test_files/ConverterAutoResults/Elementary Analysis/KIT-CN/ELA-PDF','SVS-1172-A EA.pdf')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_118_SVS_1049_A_EA_pdf():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/Elementary Analysis/KIT-CN/ELA-PDF','../test_files/ConverterAutoResults/Elementary Analysis/KIT-CN/ELA-PDF','SVS-1049-A EA.pdf')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_119_SPECTAB_CSV():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/Mass Spectrometry/Agilent/MassHunter-csv','../test_files/ConverterAutoResults/Mass Spectrometry/Agilent/MassHunter-csv','SPECTAB.CSV')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_120_processed_spectrum_dx():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/NMR/Magritek/SpinsolveSPA1109-dx','../test_files/ConverterAutoResults/NMR/Magritek/SpinsolveSPA1109-dx','processed_spectrum.dx')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_121_File067_1d():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/NMR/Magritek/Unkown-1d','../test_files/ConverterAutoResults/NMR/Magritek/Unkown-1d','File067.1d')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_122_Readme_md():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/NMR/Magritek/Unkown-1d','../test_files/ConverterAutoResults/NMR/Magritek/Unkown-1d','Readme.md')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_123_9551_T_2037_02_A2_Lk29589_40A_log():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/new/unknown/lithographie','../test_files/ConverterAutoResults/new/unknown/lithographie','9551_T_2037_02_A2_Lk29589_40A.log')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_124_9520_T_0603_07_A7_Gittertest_Lk31781_01_log():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/new/unknown/lithographie','../test_files/ConverterAutoResults/new/unknown/lithographie','9520_T_0603_07_A7_Gittertest_Lk31781_01.log')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_125_031352_02_TestMultiDIE_2023_05_15_17_33_02_result():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/new/unknown/lithographie','../test_files/ConverterAutoResults/new/unknown/lithographie','031352-02 TestMultiDIE_2023.05.15_17.33.02.result')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_126_031352_01_TestSingleDIE_2023_05_15_17_24_25_result():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/new/unknown/lithographie','../test_files/ConverterAutoResults/new/unknown/lithographie','031352-01 TestSingleDIE_2023.05.15_17.24.25.result')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_127_SEM_AMT_0595_XY_G1_011_txt():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/new/unknown/SEM','../test_files/ConverterAutoResults/new/unknown/SEM','SEM-AMT_0595_XY_G1_011.txt')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_128_SEM_AMT_0595_XY_G1_012_txt():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/new/unknown/SEM','../test_files/ConverterAutoResults/new/unknown/SEM','SEM-AMT_0595_XY_G1_012.txt')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_129_DHM_15_CV_Demo_DTA():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/new/unknown/dta','../test_files/ConverterAutoResults/new/unknown/dta','DHM-15-CV-Demo.DTA')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_130_20210118_AP_Hol5_01_zip():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/new/unknown/elabFTW','../test_files/ConverterAutoResults/new/unknown/elabFTW','20210118_AP-Hol5-01.zip')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_131_Au_Gr_06_tif():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/new/unknown/tif','../test_files/ConverterAutoResults/new/unknown/tif','Au-Gr_06.tif')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_132_HZ_BA_1ba_5yl_xml():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/LC/microTOFLC-Bruker/CompassDataAnalysis-xml','../test_files/ConverterAutoResults/LC/microTOFLC-Bruker/CompassDataAnalysis-xml','HZ_BA_1ba_5yl.xml')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_133_HZ_BA_1ba_5yl_dx():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/LC/microTOFLC-Bruker/Unkown-dx','../test_files/ConverterAutoResults/LC/microTOFLC-Bruker/Unkown-dx','HZ_BA_1ba_5yl.dx')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_134_HZ_BA_1ba_5yl_ascii():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/LC/microTOFLC-Bruker/Unkown-ascii','../test_files/ConverterAutoResults/LC/microTOFLC-Bruker/Unkown-ascii','HZ_BA_1ba_5yl.ascii')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_135_Raman_txt_json():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/Raman/Unknown/Unkown-txt','../test_files/ConverterAutoResults/Raman/Unknown/Unkown-txt','Raman-txt.json')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_136_PD_01_02_Average_1__txt():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/Raman/Unknown/Unkown-txt','../test_files/ConverterAutoResults/Raman/Unknown/Unkown-txt','PD-01-02_Average(1).txt')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_137_A_021_610_722_230059_pdf():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/3DPrinter/Lithoz/Unknown-pdf','../test_files/ConverterAutoResults/3DPrinter/Lithoz/Unknown-pdf','A-021-610-722-230059.pdf')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_138_A_021_610_722_230028_pdf():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/3DPrinter/Lithoz/Unknown-pdf','../test_files/ConverterAutoResults/3DPrinter/Lithoz/Unknown-pdf','A-021-610-722-230028.pdf')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_139_DSC_example_xlsx():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/Differential Scanning Calorimetry DSC/Netzsch/Proteus-Excel','../test_files/ConverterAutoResults/Differential Scanning Calorimetry DSC/Netzsch/Proteus-Excel','DSC example.xlsx')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_140_ExpDat_SCH_179_3_csv():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/Differential Scanning Calorimetry DSC/Netzsch/Proteus-csv','../test_files/ConverterAutoResults/Differential Scanning Calorimetry DSC/Netzsch/Proteus-csv','ExpDat_SCH-179-3.csv')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_141_ExpDat_SB_175_5_4_csv():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/Differential Scanning Calorimetry DSC/Netzsch/Proteus-csv','../test_files/ConverterAutoResults/Differential Scanning Calorimetry DSC/Netzsch/Proteus-csv','ExpDat_SB 175-5-4.csv')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_142_SCH_179_3_ngb_odg():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/Differential Scanning Calorimetry DSC/Netzsch/Proteus-ngb-odg','../test_files/ConverterAutoResults/Differential Scanning Calorimetry DSC/Netzsch/Proteus-ngb-odg','SCH-179-3.ngb-odg')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_143_Readme_md():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/Differential Scanning Calorimetry DSC/Netzsch/Proteus-ngb-odg','../test_files/ConverterAutoResults/Differential Scanning Calorimetry DSC/Netzsch/Proteus-ngb-odg','Readme.md')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_144_SCH_179_3_pdf():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/Differential Scanning Calorimetry DSC/Netzsch/pics-pdf','../test_files/ConverterAutoResults/Differential Scanning Calorimetry DSC/Netzsch/pics-pdf','SCH-179-3.pdf')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_145_SB_175_5_4_pdf():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/Differential Scanning Calorimetry DSC/Netzsch/pics-pdf','../test_files/ConverterAutoResults/Differential Scanning Calorimetry DSC/Netzsch/pics-pdf','SB 175-5-4.pdf')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_146_EF_R205_2__GC_BID_inc_5min_30_GC_3min_40_7min_180_2min_Calibrated_11142023_1210_002_gcd_txt():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/GCBID/Shimadzu/LabSolutions-gcdtxt','../test_files/ConverterAutoResults/GCBID/Shimadzu/LabSolutions-gcdtxt','EF-R205.2__GC-BID_inc-5min-30_GC-3min-40-7min-180-2min_Calibrated_11142023_1210_002.gcd.txt')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_147_EF_R205_3__GC_BID_inc_5min_30_GC_3min_40_7min_180_2min_Calibrated_11142023_1210_003_gcd_txt():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/GCBID/Shimadzu/LabSolutions-gcdtxt','../test_files/ConverterAutoResults/GCBID/Shimadzu/LabSolutions-gcdtxt','EF-R205.3__GC-BID_inc-5min-30_GC-3min-40-7min-180-2min_Calibrated_11142023_1210_003.gcd.txt')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_148_EF_R205_1__GC_BID_inc_5min_30_GC_3min_40_7min_180_2min_Calibrated_11142023_1210_001_gcd_txt():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/GCBID/Shimadzu/LabSolutions-gcdtxt','../test_files/ConverterAutoResults/GCBID/Shimadzu/LabSolutions-gcdtxt','EF-R205.1__GC-BID_inc-5min-30_GC-3min-40-7min-180-2min_Calibrated_11142023_1210_001.gcd.txt')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_149_cm1c01804_si_004_txt():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/Sorption/BEL/AIF-txt','../test_files/ConverterAutoResults/Sorption/BEL/AIF-txt','cm1c01804_si_004.txt')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_150_cm1c01804_si_003_txt():
    global all_reader
    (b,a,c)=compare_reader_result('../test_files/ChemConverter/Sorption/BEL/AIF-txt','../test_files/ConverterAutoResults/Sorption/BEL/AIF-txt','cm1c01804_si_003.txt')
    if not c:
        assert a == {}
        return
    all_reader.add(a['metadata']['reader'])
    assert a['tables'] == b['tables']
    assert a['metadata']['extension'] == b['metadata']['extension']
    assert a['metadata']['reader'] == b['metadata']['reader']
    assert a['metadata']['mime_type'] == b['metadata']['mime_type']


def test_all_reder():
    assert sorted(all_reader) == sorted([x.__name__ for k,x in registry.readers.items()])