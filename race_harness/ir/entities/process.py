from race_harness.ir.ref import RHRef
from race_harness.ir.entities.entity import RHEntity
from race_harness.ir.entities.protocol import RHProtocol
from race_harness.ir.entities.block import RHInstrBlock

class RHProcess(RHEntity):
    def __init__(self, ref: RHRef, proto: RHProtocol, entry_block: RHInstrBlock):
        super().__init__(ref, None)
        self._proto = proto
        self._entry_block = entry_block

    def as_process(self):
        return self
    
    @property
    def protocol(self) -> RHProtocol:
        return self._proto
    
    @property
    def entry_block(self) -> RHInstrBlock:
        return self._entry_block
    
    def __str__(self):
        return f'process proto {self.protocol.ref} block {self.entry_block.ref}'
