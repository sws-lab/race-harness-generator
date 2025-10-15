import io
import abc
import dataclasses
from typing import List, Iterable, Optional, Union
from race_harness.util.coerce import with_coercion_methods
from race_harness.error import RHError
from race_harness.ir.ref import RHRef
from race_harness.ir.entities.entity import RHEntity
from race_harness.ir.entities.predicate import RHPredicate

@with_coercion_methods
class RHOperation(abc.ABC):
    def as_external_action(self) -> 'RHExternalActionOp':
        return None
    
    def as_transmission(self) -> 'RHTransmissionOp':
        return None
    
    def as_set_add(self) -> 'RHSetAddOp':
        return None
    
    def as_set_del(self) -> 'RHSetDelOp':
        return None
    
    def _coerce(self, value):
        if value is None:
            raise RHError('Operation type mismatch')
        return value

class RHExternalActionOp(RHOperation):
    def __init__(self, action: str):
        super().__init__()
        self._action = action

    def as_external_action(self):
        return self

    @property
    def external_action(self) -> str:
        return self._action
    
    def __str__(self):
        return f'do {self.external_action}'

class RHTransmissionOp(RHOperation):
    def __init__(self, destinations: Iterable[RHRef], message: RHRef):
        super().__init__()
        self._destinations = list(destinations)
        self._message = message

    def as_transmission(self):
        return self
    
    @property
    def destinations(self) -> List[RHRef]:
        return self._destinations
    
    @property
    def message(self) -> RHRef:
        return self._message
    
    def __str__(self):
        return 'send {} [{}]'.format(
            self.message,
            ', '.join(str(dest) for dest in self.destinations)
        )
    
class RHSetAddOp(RHOperation):
    def __init__(self, target_set: RHRef, value: RHRef):
        super().__init__()
        self._target_set = target_set
        self._value = value

    @property
    def target_set(self) -> RHRef:
        return self._target_set
    
    @property
    def value(self) -> RHRef:
        return self._value
    
    def __str__(self):
        return f'set.add {self.target_set} {self.value}'
    
class RHSetDelOp(RHOperation):
    def __init__(self, target_set: RHRef, value: RHRef):
        super().__init__()
        self._target_set = target_set
        self._value = value

    @property
    def target_set(self) -> RHRef:
        return self._target_set
    
    @property
    def value(self) -> RHRef:
        return self._value
    
    def __str__(self):
        return f'set.del {self.target_set} {self.value}'
    

@dataclasses.dataclass
class RHUnconditionalBranch:
    target_block: 'RHEffectBlock'

@dataclasses.dataclass
class RHConditionalBranch:
    target_block: 'RHEffectBlock'
    alternative_block: Optional['RHEffectBlock']
    condition: 'RHPredicate'

class RHEffectBlock(RHEntity):
    def __init__(self, ref: RHRef):
        super().__init__(ref)
        self._items = list()
        self._successor = None

    def as_effect_block(self):
        return self

    def add_operation(self, operation: RHOperation):
        self._items.append(operation)

    def set_unconditional_successor(self, successor: 'RHEffectBlock'):
        if self._successor is not None:
            if isinstance(self._successor, RHConditionalBranch) and self._successor.alternative_block is None:
                self._successor.alternative_block = successor
                return
            raise RHError(f'Block {self.ref} already has been assigned a terminator')
        self._successor = RHUnconditionalBranch(successor)

    def set_conditional_successor(self, target: 'RHEffectBlock', alternative: Optional['RHEffectBlock'], predicate: 'RHPredicate'):
        if self._successor is not None:
            raise RHError(f'Block {self.ref} already has been assigned a terminator')
        self._successor = RHConditionalBranch(target, alternative, predicate)

    @property
    def content(self) -> List[RHOperation]:
        return self._items
    
    @property
    def successor(self) -> Optional[Union[RHUnconditionalBranch, RHConditionalBranch]]:
        return self._successor
    
    def __str__(self):
        out = io.StringIO()
        if self.content or self.successor:
            out.write('block {\n')
            for op in self.content:
                out.write(f'  {op}\n')
            if isinstance(self.successor, RHUnconditionalBranch):
                out.write(f'  jmp {self.successor.target_block.ref}\n')
            elif isinstance(self.successor, RHConditionalBranch) and self.successor.alternative_block:
                out.write(f'  branch {self.successor.condition.ref} {self.successor.target_block.ref} {self.successor.alternative_block.ref}\n')
            elif isinstance(self.successor, RHConditionalBranch) and self.successor.alternative_block:
                out.write(f'  branch {self.successor.condition.ref} {self.successor.target_block.ref}\n')
            out.write('}')
        else:
            out.write(f'block')
        return out.getvalue()
