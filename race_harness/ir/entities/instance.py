from typing import Iterable
from race_harness.ir.ref import RHRef
from race_harness.ir.entities.entity import RHEntity
from race_harness.ir.entities.protocol import RHProtocol

class RHInstance(RHEntity):
    def __init__(self, ref: RHRef, label: str, proto: RHProtocol):
        super().__init__(ref, label)
        self._proto = proto
        self._params = list()

    def as_instance(self):
        return self
    
    @property
    def protocol(self) -> RHProtocol:
        return self._proto
    
    @property
    def parameters(self) -> Iterable[RHRef]:
        yield from self._params

    def add_parameter(self, param: RHRef):
        self._params.append(param)
    
    def __str__(self):
        return 'instance {} of {} ({})'.format(
            self.label,
            self.protocol.label,
            ', '.join(
                str(param)
                for param in self.parameters
            )
        )
