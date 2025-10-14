import abc
from typing import Iterable, List
from race_harness.error import RHError
from race_harness.ir import RHRef

class RHOperation(abc.ABC):
    def as_effect(self) -> 'RHEffectOp':
        return None
    
    def to_effect(self) -> 'RHEffectOp':
        return self._coerce(self.as_effect())
    
    def as_predicate(self) -> 'RHPredicateOp':
        return None
    
    def to_predicate(self) -> 'RHPredicateOp':
        return self._coerce(self.as_predicate())

    def as_external_action(self) -> 'RHExternalActionOp':
        return None
    
    def to_external_action(self) -> 'RHExternalActionOp':
        return self._coerce(self.as_external_action())
    
    def as_transmission(self) -> 'RHTransmissionOp':
        return None
    
    def to_transmission(self) -> 'RHTransmissionOp':
        return self._coerce(self.as_transmission())
    
    def as_set_add(self) -> 'RHSetAddOp':
        return None
    
    def to_set_add(self) -> 'RHSetAddOp':
        return self._coerce(self.as_set_add())
    
    def as_set_del(self) -> 'RHSetDelOp':
        return None
    
    def to_set_del(self) -> 'RHSetDelOp':
        return self._coerce(self.as_set_del())
    
    def as_true(self) -> 'RHTrueOp':
        return None
    
    def to_true(self) -> 'RHTrueOp':
        return self._coerce(self.as_true())
    
    def as_false(self) -> 'RHFalseOp':
        return None
    
    def to_false(self) -> 'RHFalseOp':
        return self._coerce(self.as_false())
    
    def as_set_empty(self) -> 'RHSetEmptyOp':
        return None
    
    def to_set_empty(self) -> 'RHSetEmptyOp':
        return self._coerce(self.as_set_empty())
    
    def as_set_has(self) -> 'RHSetHasOp':
        return None
    
    def to_set_has(self) -> 'RHSetHasOp':
        return self._coerce(self.as_set_has())
    
    def as_conjunction(self) -> 'RHConjunctionOp':
        return None
    
    def to_conjunction(self) -> 'RHConjunctionOp':
        return self._coerce(self.as_conjunction())
    
    def as_disjunction(self) -> 'RHDisjunctionOp':
        return None
    
    def to_disjunction(self) -> 'RHDisjunctionOp':
        return self._coerce(self.as_disjunction())
    
    def as_receival(self) -> 'RHReceivalOp':
        return None
    
    def to_receival(self) -> 'RHReceivalOp':
        return self._coerce(self.as_receival())
    
    def _coerce(self, value):
        if value is None:
            raise RHError('Instruction type mismatch')
        return value
    
class RHEffectOp(RHOperation):
    def as_effect(self):
        return self

class RHExternalActionOp(RHEffectOp):
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

class RHTransmissionOp(RHEffectOp):
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
    
class RHSetAddOp(RHEffectOp):
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
    
class RHSetDelOp(RHEffectOp):
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
    
class RHPredicateOp(RHOperation):
    def as_predicate(self):
        return self
    
class RHTrueOp(RHPredicateOp):
    def as_true(self):
        return self

    def __str__(self):
        return 'true'
    
class RHFalseOp(RHPredicateOp):
    def as_false(self):
        return self

    def __str__(self):
        return 'false'
    
class RHSetEmptyOp(RHPredicateOp):
    def __init__(self, target_set: RHRef):
        super().__init__()
        self._target_set = target_set

    def as_set_empty(self):
        return self

    @property
    def target_set(self) -> RHRef:
        return self._target_set
    
    def __str__(self):
        return f'set.empty {self.target_set}'
    
class RHSetHasOp(RHPredicateOp):
    def __init__(self, target_set: RHRef, value: RHRef):
        super().__init__()
        self._target_set = target_set
        self._value = value

    def as_set_has(self):
        return self

    @property
    def target_set(self) -> RHRef:
        return self._target_set
    
    @property
    def value(self) -> RHRef:
        return self._value
    
    def __str__(self):
        return f'set.has {self.target_set} {self.value}'
    
class RHConjunctionOp(RHPredicateOp):
    def __init__(self, conjuncts: Iterable[RHRef]):
        super().__init__()
        self._conjuncts = list(conjuncts)

    def as_conjunction(self):
        return self

    @property
    def conjuncts(self) -> List[RHRef]:
        return self._conjuncts
    
    def __str__(self):
        return 'conj [{}]'.format(
            ', '.join(
                str(ref)
                for ref in self.conjuncts
            )
        )
    
class RHDisjunctionOp(RHPredicateOp):
    def __init__(self, disjuncts: Iterable[RHRef]):
        super().__init__()
        self._disjuncts = list(disjuncts)

    def as_disjunction(self):
        return self

    @property
    def disjuncts(self) -> List[RHRef]:
        return self._disjuncts
    
    def __str__(self):
        return 'disj [{}]'.format(
            ', '.join(
                str(ref)
                for ref in self.disjuncts
            )
        )

class RHReceivalOp(RHPredicateOp):
    def __init__(self, messages: Iterable[RHRef]):
        super().__init__()
        self._messages = list(messages)

    def as_receival(self):
        return self

    @property
    def messages(self) -> List[RHRef]:
        return self._messages

    def __str__(self):
        return 'receive [{}]'.format(
            ', '.join(
                str(ref)
                for ref in self.messages
            )
        )
