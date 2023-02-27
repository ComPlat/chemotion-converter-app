import json
import uuid
from unittest import TestCase

import logging

from werkzeug.datastructures import FileStorage

from converter_app.models import Reader, File
from converter_app.readers import registry, GenericReader


def test_validation(app, test_reader):
    test_reader.clean()
    assert test_reader.clean()

def test_http_put(client, reader_params):
    response = client.put("/readers/%s" % reader_params['reader_id'], data=json.dumps(reader_params['reader_data']))
    assert response.status_code == 200

def test_send_cif_generic(client, reader_params):
    with open("tests/sample_files/SG-V3545-6-13_small.cif" , 'rb') as f:
        response = client.post("/tables", data={'file': f})

    assert response.status_code == 201


def test_find_reader_cif_generic(app, reader_params):
    with open("tests/sample_files/SG-V3545-6-13_small.cif" , 'rb') as f:
        fs = FileStorage(stream=f, filename='SG-V3545-6-13_small.cif', content_type='chemical/x-cif')
        file = File(fs)
        reader = registry.match_reader(file, reader_params['client_id'])
    assert reader.identifier == 'generic_reader[Test_1]'


def test_result_reader_cif_generic(app, reader_params):
    with open("tests/sample_files/SG-V3545-6-13_small.cif" , 'rb') as f:
        fs = FileStorage(stream=f, filename='SG-V3545-6-13_small.cif', content_type='chemical/x-cif')
        file = File(fs)
        reader = GenericReader(file, reader_params['client_id'])
        assert reader.check()
        reader.process()
        reader.validate()
        expected_meta = {'file_name': 'SG-V3545-6-13_small.cif', 'content_type': 'chemical/x-cif', 'mime_type': 'text/plain', 'extension': '.cif', 'reader': 'GenericReader'}
        expected_meta['uploaded'] = reader.metadata['uploaded']
        TestCase().assertDictEqual(expected_meta, reader.metadata)

        expected_tables = [{'header': ['data_sg-v3545-6-13', '_audit_creation_date              2022-01-18 ;; Test', '_audit_creation_method', ';', 'Olex2 1.2', '(compiled 2017.08.10 svn.r3458 for OlexSys, GUI svn.r5381)', ';', "_shelx_SHELXL_version_number      '2018/3'", '_publ_contact_author_address      ?', '_publ_contact_author_email        ?', '_publ_contact_author_id_orcid     ?', "_publ_contact_author_name         ''", '_publ_contact_author_phone        ?', '_publ_section_references', ';', 'Dolomanov, O.V., Bourhis, L.J., Gildea, R.J, Howard, J.A.K. & Puschmann, H.', '(2009), J. Appl. Cryst. 42, 339-341.', '', 'Sheldrick, G.M. (2015). Acta Cryst. A71, 3-8.', '', 'Sheldrick, G.M. (2015). Acta Cryst. C71, 3-8.', ';', '_chemical_name_common             ?', '_chemical_name_systematic         ?', "_chemical_formula_moiety          'C13 H9 Br N2'", "_chemical_formula_sum             'C13 H9 Br N2'", '_chemical_formula_weight          273.13', '_chemical_melting_point           ?', '', '-2 4 faf dasf 3.4 5', "-2 4 'faf ff' dasf 3.4 5", ''], 'metadata': {'NO KEY': 'data_sg-v3545-6-13', '_audit_creation_date': '2022-01-18', 'NO KEY(1)': '_audit_creation_method', '_shelx_SHELXL_version_number': "'2018/3'", '_publ_contact_author_address': '?', '_publ_contact_author_email': '?', '_publ_contact_author_id_orcid': '?', '_publ_contact_author_name': "''", '_publ_contact_author_phone': '?', 'NO KEY(2)': '_publ_section_references', '_chemical_name_common': '?', '_chemical_name_systematic': '?', '_chemical_formula_moiety': "'C13 H9 Br N2'", '_chemical_formula_sum': "'C13 H9 Br N2'", '_chemical_formula_weight': '273.13', '_chemical_melting_point': '?', '-2.col_0': '4', '-2.col_1': 'faf', '-2.col_2': 'dasf', '-2.col_3': '3.4', '-2.col_4': '5', '-2.col_0(1)': '4', '-2.col_1(1)': "'faf ff'", '-2.col_2(1)': 'dasf', '-2.col_3(1)': '3.4', '-2.col_4(1)': '5', 'rows': '0', 'columns': '0'}, 'columns': [], 'rows': []}, {'header': ['loop_', '_atom_type_symbol', '_atom_type_description', '_atom_type_scat_dispersion_real', '_atom_type_scat_dispersion_imag', '_atom_type_scat_source', "'C' 'C' 0.0150 0.0070 'International Tables Vol C Tables 4.2.6.8 and 6.1.1.4'", "'H' 'H' 0.0000 0.0000 'International Tables Vol C Tables 4.2.6.8 and 6.1.1.4'", "'N' 'N' 0.0250 0.0140 'International Tables Vol C Tables 4.2.6.8 and 6.1.1.4'", "'Br' 'Br' -0.9500 1.0410", "'International Tables Vol C Tables 4.2.6.8 and 6.1.1.4'", ';'], 'metadata': {'NO KEY': 'loop_', 'NO KEY(1)': '_atom_type_symbol', 'NO KEY(2)': '_atom_type_description', 'NO KEY(3)': '_atom_type_scat_dispersion_real', 'NO KEY(4)': '_atom_type_scat_dispersion_imag', 'NO KEY(5)': '_atom_type_scat_source', "'C'.col_0": "'C'", "'C'.col_1": '0.0150', "'C'.col_2": '0.0070', "'C'.col_3": "'International Tables Vol C Tables 4.2.6.8 and 6.1.1.4'", "'H'.col_0": "'H'", "'H'.col_1": '0.0000', "'H'.col_2": '0.0000', "'H'.col_3": "'International Tables Vol C Tables 4.2.6.8 and 6.1.1.4'", "'N'.col_0": "'N'", "'N'.col_1": '0.0250', "'N'.col_2": '0.0140', "'N'.col_3": "'International Tables Vol C Tables 4.2.6.8 and 6.1.1.4'", "'Br'.col_0": "'Br'", "'Br'.col_1": '-0.9500', "'Br'.col_2": '1.0410', 'NO KEY(6)': "'International Tables Vol C Tables 4.2.6.8 and 6.1.1.4'", 'rows': '11', 'columns': '6'}, 'columns': [{'key': '0', 'name': 'Column #0'}, {'key': '1', 'name': 'Column #1'}, {'key': '2', 'name': 'Column #2'}, {'key': '3', 'name': 'Column #3'}, {'key': '4', 'name': 'Column #4'}, {'key': '5', 'name': 'Column #5'}], 'rows': [['0', '"Hallo Du 1"', 'Test-1', '150.38', '1.22E-2', '0'], ['1', '"Hallo Du 2"', 'Test-3', '150.38', '1.22e3', '0'], ['2', '"Hallo Du 3"', 'Test', '150.38', '1.22', '0'], ['3', '"Hallo Du 4"', 'Test', '150.38', '1.22', '0'], ['4', '"Hallo Du 5"', 'Test', '150.38', '1.22', '0'], ['5', '"Hallo Du 6"', 'Test', '150.38', '1.22', '0'], ['6', '"Hallo Du 7"', 'Test', '150.38', '1.22', '0'], ['7', '"Hallo Du 8"', 'Test', '150.38', '1.22', '0'], ['8', '"Hallo Du 8"', 'Test', '150.38', '1.22', '0'], ['9', '"Hallo Du 9"', 'Test', '150.38', '1.22', '0'], ['10', '"Hallo Du 22"', 'Test', '150.38', '1.22', '0']]}, {'header': [';', '_shelx_hkl_checksum               22519', "_olex2_submission_special_instructions 'No special instructions were received'"], 'metadata': {'_shelx_hkl_checksum': '22519', '_olex2_submission_special_instructions': "'No special instructions were received'", 'rows': '0', 'columns': '0'}, 'columns': [], 'rows': []}]
        for (table_idx, expected_table) in enumerate(expected_tables):
            logging.info("Table #%d" % table_idx)
            TestCase().assertDictEqual(expected_table, reader.tables[table_idx])


def test_wrong_id_validation(app, reader_params):
    reader_params['reader_id'] = uuid.uuid4().__str__()
    reader = Reader(**reader_params)
    reader.clean()
    assert reader.errors.get('id') is not None


def test_non_valid_id_validation(app, reader_params):
    reader_params['reader_id'] = uuid.uuid4().__str__()[1:]
    reader = Reader(**reader_params)
    reader.clean()
    assert reader.errors.get('id') is not None

def test_no_title_error(app, test_reader):
    del test_reader.data['title']
    test_reader.clean()
    assert test_reader.errors.get('$') is not None

def test_commend_error(app, test_reader):
    test_reader.data['commend'] = "Test Commend"
    test_reader.clean()
    assert test_reader.errors.get('$.commend') is not None




