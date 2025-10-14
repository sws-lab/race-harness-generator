import abc
from typing import Optional
from race_harness.error import RHError
from race_harness.ir.ref import RHRef

class RHEntity(abc.ABC):
    def __init__(self, ref: RHRef, label: Optional[str] = None):
        super().__init__()
        self._ref = ref
        self._label = label

    @property
    def ref(self) -> RHRef:
        return self._ref

    @property
    def label(self) -> Optional[str]:
        return self._label
    
    def as_symbol(self) -> Optional['RHSymbol']:
        return None
    
    def to_symbol(self) -> 'RHSymbol':
        return self._coerce(self.as_symbol())
    
    def as_fixed_set(self) -> Optional['RHFixedSet']:
        return None
    
    def to_fixed_set(self) -> 'RHFixedSet':
        return self._coerce(self.as_fixed_set())
    
    def as_protocol(self) -> Optional['RHProtocol']:
        return None
    
    def to_protocol(self) -> 'RHProtocol':
        return self._coerce(self.as_protocol())
    
    def as_instance(self) -> Optional['RHInstance']:
        return None
    
    def to_instance(self) -> 'RHInstance':
        return self._coerce(self.as_instance())
    
    def as_scope(self) -> Optional['RHScope']:
        return None
    
    def to_scope(self) -> 'RHScope':
        return self._coerce(self.as_scope())
    
    def as_instr_block(self) -> Optional['RHInstrBlock']:
        return None
    
    def to_instr_block(self) -> 'RHInstrBlock':
        return self._coerce(self.as_instr_block())
    
    def as_process(self) -> Optional['RHProcess']:
        return None
    
    def to_process(self) -> 'RHProcess':
        return self._coerce(self.as_process())
    
    def as_module(self) -> Optional['RHModule']:
        return None
    
    def to_module(self) -> 'RHModule':
        return self._coerce(self.as_module())
    
    def _coerce(self, value):
        if value is None:
            raise RHError('Entity type mismatch')
        return value
