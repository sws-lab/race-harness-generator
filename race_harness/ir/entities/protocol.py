from typing import Iterable
from race_harness.ir.ref import RHRef
from race_harness.ir.entities.entity import RHEntity
from race_harness.ir.entities.domain import RHDomain

class RHProtocol(RHEntity):
    def __init__(self, ref: RHRef, label: str, in_proto: Iterable[RHDomain], out_proto: Iterable[RHDomain]):
        super().__init__(ref, label)
        self._in_proto = list(in_proto)
        self._out_proto = list(out_proto)

    def as_protocol(self):
        return self
    
    @property
    def in_protocol(self) -> Iterable[RHDomain]:
        yield from self._in_proto
    
    @property
    def out_protocol(self) -> Iterable[RHDomain]:
        yield from self._out_proto
    
    def __str__(self):
        return 'protocol {}{}{}'.format(
            self.label,
            ' in {}'.format(', '.join(
                str(chan.ref)
                for chan in self.in_protocol
            )) if self._in_proto else '',
            ' out {}'.format(', '.join(
                str(chan.ref)
                for chan in self.out_protocol
            )) if self._in_proto else ''
        )
