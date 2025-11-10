import tomllib
from typing import Optional

class CodegenPayloads:
    def __init__(self):
        self._payloads = dict()
        self._local_preambles = dict()
        self._global_preamble = None
        self._embed_header = False

    def add_payload(self, identifier: str, payload: str):
        self._payloads[identifier] = payload

    def get_payload(self, identifier: str) -> Optional[str]:
        return self._payloads.get(identifier, None)
    
    def set_preamble(self, preamble: str, embed_header: bool):
        self._global_preamble = preamble
        self._embed_header = embed_header

    @property
    def preamble(self) -> Optional[str]:
        return self._global_preamble
    
    @property
    def embed_header(self) -> bool:
        return self._embed_header
    
    def set_local_preamble(self, identifier: str, preamble: str):
        self._local_preambles[identifier] = preamble

    def get_local_preamble(self, identifier: str) -> Optional[str]:
        return self._local_preambles.get(identifier)

    @staticmethod
    def load(fp) -> 'CodegenPayloads':
        content = tomllib.load(fp)
        payloads = CodegenPayloads()
        for name, section in content.get('payload', dict()).items():
            payloads.add_payload(name, section['code'])

        global_preamble = content.get('preamble', dict()).get('global')
        if global_preamble:
            payloads.set_preamble(global_preamble['code'], global_preamble.get('embed_header', False))

        for name, local_preamble in content.get('preamble', dict()).get('local', dict()).items():
            payloads.set_local_preamble(name, local_preamble['code'])
        return payloads
