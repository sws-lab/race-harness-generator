from race_harness.ir.ref import RHRef
from race_harness.ir.entities.entity import RHEntity
from race_harness.ir.entities.protocol import RHProtocol
from race_harness.ir.entities.block import RHEffectBlock
from race_harness.ir.entities.control_flow import RHControlFlow

class RHProcess(RHEntity):
    def __init__(self, ref: RHRef, label: str, proto: RHProtocol, entry_block: RHEffectBlock, control_flow: RHControlFlow):
        super().__init__(ref, label)
        self._proto = proto
        self._entry_block = entry_block
        self._control_flow = control_flow

    def as_process(self):
        return self
    
    @property
    def protocol(self) -> RHProtocol:
        return self._proto
    
    @property
    def entry_block(self) -> RHEffectBlock:
        return self._entry_block
    
    @property
    def control_flow(self) -> RHControlFlow:
        return self._control_flow
    
    def __str__(self):
        return f'process {self.label} proto {self.protocol.ref} entry {self.entry_block.ref} control {self.control_flow.ref}'
