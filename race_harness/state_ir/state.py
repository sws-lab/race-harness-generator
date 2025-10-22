import io
import enum
import abc
import dataclasses
from typing import Optional, Union
from race_harness.error import RHError
from race_harness.util.coerce import with_coercion_methods

class SlotID:
    def __init__(self, identifier: int):
        self._identifier = identifier

    @property
    def identifier(self) -> int:
        return self._identifier
    
    def __eq__(self, value):
        return isinstance(value, SlotID) and value.identifier == self.identifier
    
    def __hash__(self):
        return hash(self._identifier)
    
    def __str__(self):
        return f'${self.identifier}'

@with_coercion_methods
class Slot(abc.ABC):
    def __init__(self, identifier: SlotID):
        super().__init__()
        self._identifier = identifier

    @property
    def identifier(self) -> SlotID:
        return self._identifier
    
    def as_boolean(self) -> 'BooleanSlot':
        return None
    
    @property
    @abc.abstractmethod
    def initial_value(self) -> Union[bool]: pass

class BooleanSlot(Slot):
    def __init__(self, identifier: SlotID, initial_value: bool):
        super().__init__(identifier)
        self._init_value = initial_value

    def as_boolean(self):
        return self

    @property
    def initial_value(self) -> bool:
        return self._init_value
    
    def __str__(self):
        return f'{self.identifier}: bool = {self.initial_value}'

class SlotSet:
    def __init__(self):
        self._slots = dict()

    def new_boolean_slot(self, init_value: bool) -> SlotID:
        slot_id = SlotID(len(self._slots))
        self._slots[slot_id] = BooleanSlot(slot_id, init_value)
        return slot_id
    
    def get_slot(self, identifier: SlotID) -> Optional[Slot]:
        return self._slots.get(identifier, None)
    
    def __getitem__(self, identifier: SlotID) -> Slot:
        decl = self.get_slot(identifier)
        if decl is None:
            raise RHError(f'Unable to find slot {identifier}')
        return decl
    
    def __str__(self):
        out = io.StringIO()
        out.write('{\n')
        for slot in self._slots.values():
            out.write(f'  {slot}\n')
        out.write('}')
        return out.getvalue()
