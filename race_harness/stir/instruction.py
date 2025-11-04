import abc
from race_harness.util.coerce import with_coercion_methods
from race_harness.stir.state import STSlotID

@with_coercion_methods
class STInstruction(abc.ABC):
    def __init__(self):
        super().__init__()

    def as_external_action(self) -> 'STExternalActionInstruction':
        return None
    
    def as_set_int(self) -> 'STSetIntInstruction':
        return None

class STExternalActionInstruction(STInstruction):
    def __init__(self, action: str):
        super().__init__()
        self._action = action

    def as_external_action(self):
        return self

    @property
    def action(self) -> str:
        return self._action
    
    def __str__(self):
        return f'do {self.action}'
    
class STSetIntInstruction(STInstruction):
    def __init__(self, slot_id: STSlotID, value: int):
        super().__init__()
        self._slot_id = slot_id
        self._value = value

    def as_set_int(self):
        return self

    @property
    def slot_id(self) -> STSlotID:
        return self._slot_id
    
    @property
    def value(self) -> int:
        return self._value
    
    def __str__(self):
        return f'setint {self.slot_id} {self.value}'

    
