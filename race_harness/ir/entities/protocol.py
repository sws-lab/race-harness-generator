from typing import Optional
from race_harness.ir.ref import RHRef
from race_harness.ir.entities.entity import RHEntity

class RHProtocol(RHEntity):
    def __init__(self, ref: RHRef, label: str, in_proto: Optional[RHRef], out_proto: Optional[RHRef]):
        super().__init__(ref, label)
        self._in_proto = in_proto
        self._out_proto = out_proto

    def as_protocol(self):
        return self
    
    @property
    def in_protocol(self) -> Optional[RHRef]:
        return self._in_proto
    
    @property
    def out_protocol(self) -> Optional[RHRef]:
        return self._out_proto
    
    def __str__(self):
        return 'protocol {}{}{}'.format(
            self.label,
            f' in {self.in_protocol}' if self.in_protocol is not None else '',
            f' out {self.out_protocol}' if self.out_protocol is not None else '',
        )
