from race_harness.ir.ref import RHRef
from race_harness.ir.entities.entity import RHEntity

class RHSet(RHEntity):
    def __init__(self, ref, name: str, domain: RHRef):
        super().__init__(ref, name)
        self._domain = domain

    def as_set(self):
        return self

    @property
    def domain(self) -> RHRef:
        return self._domain
    
    def __str__(self):
        return f'set {self.label} {self.domain}'
    