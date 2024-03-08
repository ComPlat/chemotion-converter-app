import json
import os
import traceback

from werkzeug.datastructures import FileStorage

from converter_app.models import File

from converter_app.readers import READERS as registry


def compare_reader_result(src_path, res_path, file):
    with open(os.path.join(src_path, file), 'rb') as fp:
        file_storage = FileStorage(fp)
        with open(os.path.join(res_path, file + '.json'), 'r', encoding='utf8') as f_res:
            expected_result = json.loads(f_res.read())
            f_res.close()
            reader = registry.match_reader(File(file_storage))
            if reader:
                reader.process()
                content = reader.as_dict
                return (expected_result, content, True)
            return (expected_result, {}, False)

        f_res.close()
        file_storage.close()