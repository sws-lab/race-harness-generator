import abc
from typing import Optional, Iterable, List, Dict
from race_harness.util.coerce import with_coercion_methods

class CFMutexID:
    def __init__(self, mutex_id: int):
        self._mutex_id = mutex_id

    @property
    def mutex_id(self) -> int:
        return self._mutex_id
    
    def __hash__(self):
        return hash(self._mutex_id)
    
    def __eq__(self, value):
        return isinstance(value, CFMutexID) and value.mutex_id == self.mutex_id
    
    def __lt__(self, value):
        return isinstance(value, CFMutexID) and self.mutex_id < value.mutex_id
    
    def __str__(self):
        return f'mutex{self.mutex_id}'
    
class CFLabelID:
    def __init__(self, label_id: int):
        self._label_id = label_id

    @property
    def label_id(self) -> int:
        return self._label_id
    
    def __hash__(self):
        return hash(self._label_id)
    
    def __eq__(self, value):
        return isinstance(value, CFLabelID) and value.label_id == self.label_id
    
    def __str__(self):
        return f'label{self.label_id}'

@with_coercion_methods
class CFNode(abc.ABC):
    def as_statement(self) -> Optional['CFStatement']:
        return None
    
    def as_sequence(self) -> Optional['CFSequence']:
        return None
    
    def as_branch(self) -> Optional['CFBranch']:
        return None
    
    def as_synchronization(self) -> Optional['CFSynchronization']:
        return None

    def as_labelled(self) -> Optional['CFLabelledNode']:
        return None
    
    def as_goto(self) -> Optional['CFGoto']:
        return None
    
    def as_return(self) -> Optional['CFReturn']:
        return None
    
    def as_init_barrier(self) -> Optional['CFInitBarrier']:
        return None
    
    def as_module(self) -> Optional['CFModule']:
        return None
    
class CFStatement(CFNode):
    def __init__(self, action: str):
        super().__init__()
        self._action = action

    def as_statement(self):
        return self
    
    @property
    def action(self) -> str:
        return self._action
    
class CFSequence(CFNode):
    def __init__(self, sequence: Iterable[CFNode]):
        super().__init__()
        self._sequence = list(sequence)

    def as_sequence(self):
        return self
    
    @property
    def sequence(self) -> List[CFNode]:
        return self._sequence
    
    def add_node(self, node: CFNode):
        self._sequence.append(node)
    
class CFBranch(CFNode):
    def __init__(self, branches: Iterable[CFNode]):
        super().__init__()
        self._branches = list(branches)

    def as_branch(self):
        return self
    
    @property
    def branches(self) -> List[CFNode]:
        return self._branches
    
class CFSynchronization(CFNode):
    def __init__(self, lock: Iterable[CFMutexID], unlock: Iterable[CFMutexID], rollback: Optional[CFLabelID]):
        super().__init__()
        self._lock = list(lock)
        self._unlock = list(unlock)
        self._rollback = rollback

    def as_synchronization(self):
        return self
    
    @property
    def lock_mutexes(self) -> List[CFMutexID]:
        return self._lock
    
    @property
    def unlock_mutexes(self) -> List[CFMutexID]:
        return self._unlock
    
    @property
    def rollback_label(self) -> Optional[CFLabelID]:
        return self._rollback

class CFLabelledNode(CFNode):
    def __init__(self, label: CFLabelID, node: CFNode):
        super().__init__()
        self._label = label
        self._node = node

    def as_labelled(self):
        return self
    
    @property
    def label(self) -> CFLabelID:
        return self._label
    
    @property
    def node(self) -> CFNode:
        return self._node
    
class CFGoto(CFNode):
    def __init__(self, label: CFLabelID):
        super().__init__()
        self._label = label

    def as_goto(self):
        return self
    
    @property
    def label(self) -> CFLabelID:
        return self._label
    
class CFReturn(CFNode):
    def as_return(self):
        return self
    
class CFInitBarrier(CFNode):
    def as_init_barrier(self):
        return self

class CFModuleInterface(CFNode):
    def __init__(self):
        super().__init__()
        self._external_actions = dict()
        self._instances = dict()

    def declare_external_action(self, action: str):
        self._external_actions[action] = None

    def declare_instance(self, instance: str):
        self._instances[instance] = None

    @property
    def external_actions(self) -> Iterable[str]:
        yield from self._external_actions.keys()

    @property
    def instances(self) -> Iterable[str]:
        yield from self._instances.keys()

class CFModule(CFNode):
    def __init__(self, procedures: Dict[str, CFNode]):
        super().__init__()
        self._next_mutex_id = 0
        self._next_label_id = 0
        self._procedures = procedures.copy()
        self._interface = CFModuleInterface()

    def as_module(self):
        return self
    
    @property
    def interface(self) -> CFModuleInterface:
        return self._interface

    @property
    def procedures(self) -> Dict[str, CFNode]:
        return self._procedures
    
    def add_procedure(self, name: str, body: CFNode):
        self._procedures[name] = body

    def new_mutex(self) -> CFMutexID:
        mutex_id = CFMutexID(self._next_mutex_id)
        self._next_mutex_id += 1
        return mutex_id
    
    def new_label(self) -> CFLabelID:
        label_id = CFLabelID(self._next_label_id)
        self._next_label_id += 1
        return label_id
    
    @property
    def mutexes(self) -> Iterable[CFMutexID]:
        for mutex_id in range(self._next_mutex_id):
            yield CFMutexID(mutex_id)
