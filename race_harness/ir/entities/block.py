import dataclasses
from race_harness.ir.ref import RHRef
from race_harness.ir.entities.entity import RHEntity

@dataclasses.dataclass
class RHInstrBlockBranch:
    successor_ref: RHRef

class RHInstrBlock(RHEntity):
    def __init__(self, ref: RHRef):
        super().__init__(ref, None)
        self._branches = list()

    def as_instr_block(self):
        return self
    
    def add_successor(self, successor_ref: RHRef):
        self._branches.append(RHInstrBlockBranch(successor_ref=successor_ref))

    def __str__(self):
        return 'block'
