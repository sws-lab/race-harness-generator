from typing import Iterable, List
from race_harness.error import RHError
from race_harness.util.coerce import with_coercion_methods
from race_harness.ir.ref import RHRef
from race_harness.ir.entities.entity import RHEntity

@with_coercion_methods
class RHPredicateOp:
    def as_nondet(self) -> 'RHNondetPred':
        return None
    
    def as_set_empty(self) -> 'RHSetEmptyPred':
        return None
    
    def as_set_has(self) -> 'RHSetHasPred':
        return None
    
    def as_conjunction(self) -> 'RHConjunctionPred':
        return None
    
    def as_receival(self) -> 'RHReceivalPred':
        return None
    
    def _coerce(self, value):
        if value is None:
            raise RHError('Predicate type mismatch')
        return value
    
class RHPredicate(RHEntity):
    def __init__(self, ref: RHRef, op: RHPredicateOp):
        super().__init__(ref)
        self._op = op

    def as_predicate(self):
        return self
    
    @property
    def operation(self) -> RHPredicateOp:
        return self._op
    
    def __str__(self):
        return str(self.operation)
    
class RHNondetPred(RHPredicateOp):
    def as_nondet(self):
        return self

    def __str__(self):
        return 'nondet'
    
class RHSetEmptyPred(RHPredicateOp):
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
    
class RHSetHasPred(RHPredicateOp):
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
    
class RHConjunctionPred(RHPredicateOp):
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

class RHReceivalPred(RHPredicateOp):
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
