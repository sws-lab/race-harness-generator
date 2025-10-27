from typing import Tuple, Optional
from race_harness.stir import STNodeID
from race_harness.ir import RHRef
from race_harness.error import RHError

class STRHMapping:
    def __init__(self):
        self._mapping = dict()

    def map_to(self, st_node_id: STNodeID, instance_ref: RHRef, block_ref: RHRef):
        self._mapping[st_node_id] = (block_ref, instance_ref)

    def get_mapping(self, st_node_id: STNodeID) -> Optional[Tuple[RHRef, RHRef]]:
        return self._mapping.get(st_node_id, None)
    
    def __getitem__(self, key) -> Tuple[RHRef, RHRef]:
        value = self.get_mapping(key)
        if value is None:
            raise RHError(f'Unable to find STIR-RH mapping for {key}')
        return value
    
    def __iter__(self):
        yield from self._mapping.items()

    def __len__(self):
        return len(self._mapping)
