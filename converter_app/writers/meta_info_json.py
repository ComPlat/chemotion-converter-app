import json

from converter_app.writers.base import Writer


class MetaInfoWriter(Writer):
    suffix = '.json'
    mimetype = 'application/json'

    def __init__(self, converter):
        super().__init__(converter)
        self.buffer: str | None = None

    def process(self):
        meta_info = {
            'profile_id': self._converter.profile.id,
            'profile_name': self._converter.profile.data['title'],
        }
        self.buffer = json.dumps(meta_info)

    def write(self) -> bytes:
        if self.buffer is None:
            return b''
        return self.buffer.encode()