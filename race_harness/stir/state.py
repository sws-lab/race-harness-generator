import io
import abc
from typing import Optional, Union, Iterable
from race_harness.error import RHError
from race_harness.stir.node import STNodeID
from race_harness.util.coerce import with_coercion_methods

class STSlotID:
    def __init__(self, identifier: int):
        self._identifier = identifier

    @property
    def identifier(self) -> int:
        return self._identifier
    
    def __eq__(self, value):
        return isinstance(value, STSlotID) and value.identifier == self.identifier
    
    def __hash__(self):
        return hash(self._identifier)
    
    def __str__(self):
        return f'${self.identifier}'

@with_coercion_methods
class STSlot(abc.ABC):
    def __init__(self, identifier: STSlotID):
        super().__init__()
        self._identifier = identifier

    @property
    def identifier(self) -> STSlotID:
        return self._identifier
    
    def as_int(self) -> Optional['STIntSlot']:
        return None
    
    def as_node(self) -> Optional['STNodeSlot']:
        return None
    
    @property
    @abc.abstractmethod
    def initial_value(self) -> Union[bool, int]: pass

class STIntSlot(STSlot):
    def __init__(self, identifier: STSlotID, initial_value: int):
        super().__init__(identifier)
        self._init_value = initial_value

    def as_int(self):
        return self

    @property
    def initial_value(self) -> int:
        return self._init_value
    
    def __str__(self):
        return f'{self.identifier}: int = {self.initial_value}'
    
class STNodeSlot(STSlot):
    def __init__(self, identifier: STSlotID, initial_value: STNodeID):
        super().__init__(identifier)
        self._init_value = initial_value

    def as_node(self):
        return self

    @property
    def initial_value(self) -> STNodeID:
        return self._init_value
    
    def __str__(self):
        return f'{self.identifier}: node = {self.initial_value}'

class STState:
    def __init__(self):
        self._slots = dict()

    def new_int_slot(self, init_value: int) -> STSlotID:
        slot_id = STSlotID(len(self._slots))
        self._slots[slot_id] = STIntSlot(slot_id, init_value)
        return slot_id
    
    def new_node_slot(self, init_value: STNodeID) -> STSlotID:
        slot_id = STSlotID(len(self._slots))
        self._slots[slot_id] = STNodeSlot(slot_id, init_value)
        return slot_id
    
    def get_slot(self, identifier: STSlotID) -> Optional[STSlot]:
        return self._slots.get(identifier, None)
    
    def __getitem__(self, identifier: STSlotID) -> STSlot:
        decl = self.get_slot(identifier)
        if decl is None:
            raise RHError(f'Unable to find slot {identifier}')
        return decl
    
    def __len__(self):
        return len(self._slots)
    
    def __iter__(self) -> Iterable[STSlot]:
        yield from self._slots.values()
    
    def __str__(self):
        out = io.StringIO()
        out.write('{\n')
        for slot in self._slots.values():
            out.write(f'  {slot}\n')
        out.write('}')
        return out.getvalue()
