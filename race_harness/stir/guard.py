import abc
from race_harness.stir.state import STSlotID
from race_harness.util.coerce import with_coercion_methods

@with_coercion_methods
class STGuardCondition(abc.ABC):
    def __init__(self):
        super().__init__()
    
    def as_int(self) -> 'STIntGuardCondition':
        return None

class STIntGuardCondition(STGuardCondition):
    def __init__(self, slot_id: STSlotID, value: int):
        super().__init__()
        self._slot_id = slot_id
        self._value = value

    def as_int(self):
        return self
    
    @property
    def slot_id(self) -> STSlotID:
        return self._slot_id
    
    @property
    def value(self) -> int:
        return self._value
    
    def __str__(self):
        return f'int {self.slot_id} {self.value}'
