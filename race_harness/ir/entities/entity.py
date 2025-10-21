import abc
from typing import Optional
from race_harness.error import RHError
from race_harness.util.coerce import with_coercion_methods
from race_harness.ir.ref import RHRef

@with_coercion_methods
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
    
    def as_fixed_set(self) -> Optional['RHFixedSet']:
        return None
    
    def as_protocol(self) -> Optional['RHProtocol']:
        return None
    
    def as_instance(self) -> Optional['RHInstance']:
        return None
    
    def as_effect_block(self) -> Optional['RHEffectBlock']:
        return None
    
    def as_process(self) -> Optional['RHProcess']:
        return None
    
    def as_module(self) -> Optional['RHModule']:
        return None
    
    def as_instruction(self) -> 'RHInstruction':
        return None
    
    def as_predicate(self) -> 'RHPredicate':
        return None
    
    def as_set(self) -> 'RHSet':
        return None
    
    def as_control_flow(self) -> 'RHControlFlow':
        return None
    
    def _coerce(self, value):
        if value is None:
            raise RHError('Entity type mismatch')
        return value
