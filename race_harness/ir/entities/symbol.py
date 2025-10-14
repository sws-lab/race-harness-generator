from race_harness.ir.ref import RHRef
from race_harness.ir.entities.entity import RHEntity

class RHSymbol(RHEntity):
    def __init__(self, ref: RHRef, label: str):
        super().__init__(ref, label)
    
    def as_symbol(self):
        return self
    
    def __str__(self):
        return f'symbol {self.label}'
