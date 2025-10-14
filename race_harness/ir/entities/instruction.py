from race_harness.ir.ref import RHRef
from race_harness.ir.entities.entity import RHEntity
from race_harness.ir.operation import RHOperation

class RHInstruction(RHEntity):
    def __init__(self, ref: RHRef, operation: RHOperation):
        super().__init__(ref)
        self._operation = operation

    def as_instruction(self):
        return self

    @property
    def operation(self) -> RHOperation:
        return self._operation
    
    @property
    def is_effect(self) -> bool:
        return self.operation.as_effect() is not None
    
    @property
    def is_predicate(self) -> bool:
        return self.operation.as_predicate() is not None
    
    def __str__(self):
        return str(self.operation)
