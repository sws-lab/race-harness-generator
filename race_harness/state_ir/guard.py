import abc
from race_harness.state_ir.state import SlotID
from race_harness.util.coerce import with_coercion_methods

@with_coercion_methods
class STGuardCondition(abc.ABC):
    def __init__(self):
        super().__init__()

    def as_bool(self) -> 'STBoolGuardCondition':
        return None
    
class STBoolGuardCondition(STGuardCondition):
    def __init__(self, slot_id: SlotID, value: bool):
        super().__init__()
        self._slot_id = slot_id
        self._value = value

    def as_bool(self):
        return self

    @property
    def slot_id(self) -> SlotID:
        return self._slot_id
    
    @property
    def value(self) -> bool:
        return self._value
    
    def __str__(self):
        return f'bool {self.slot_id} {self.value}'
