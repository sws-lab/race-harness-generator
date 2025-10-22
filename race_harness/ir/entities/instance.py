from race_harness.ir.ref import RHRef
from race_harness.ir.entities.entity import RHEntity
from race_harness.ir.entities.protocol import RHProtocol

class RHInstance(RHEntity):
    def __init__(self, ref: RHRef, label: str, proto: RHProtocol):
        super().__init__(ref, label)
        self._proto = proto

    def as_instance(self):
        return self
    
    @property
    def protocol(self) -> RHProtocol:
        return self._proto
    
    def __str__(self):
        return f'instance {self.label} of {self.protocol.ref}'
