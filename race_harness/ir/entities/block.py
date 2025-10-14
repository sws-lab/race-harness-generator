import dataclasses
import io
from typing import List
from race_harness.error import RHError
from race_harness.ir.ref import RHRef
from race_harness.ir.entities.entity import RHEntity
from race_harness.ir.entities.instruction import RHInstruction

# @dataclasses.dataclass
# class RHInstrBlockBranch:
#     successor_ref: RHRef

# class RHInstructionBlock(RHEntity):
#     def __init__(self, ref: RHRef):
#         super().__init__(ref, None)
#         self._branches = list()

#     def as_instr_block(self):
#         return self
    
#     def add_successor(self, successor_ref: RHRef):
#         self._branches.append(RHInstrBlockBranch(successor_ref=successor_ref))

#     def __str__(self):
#         return 'block'

class RHPredicateBlock(RHEntity):
    def __init__(self, ref: RHRef):
        super().__init__(ref)
        self._items = list()

    def add_instruction(self, instruction: RHInstruction):
        if not instruction.is_predicate:
            raise RHError('Expected predicate instruction')
        self._items.append(instruction)

    @property
    def content(self) -> List[RHInstruction]:
        return self._items
    
    def __str__(self):
        out = io.StringIO()
        if self.content:
            out.write('predicate_block {\n')
            for instr in self.content:
                out.write(f'  {instr.ref} = {instr}\n')
            out.write('}')
        else:
            out.write(f'predicate_block')
        return out.getvalue()

class RHEffectBlock(RHEntity):
    def __init__(self, ref: RHRef):
        super().__init__(ref)
        self._items = list()

    def add_instruction(self, instruction: RHInstruction):
        if not instruction.is_effect:
            raise RHError('Expected effect instruction')
        self._items.append(instruction)

    @property
    def content(self) -> List[RHInstruction]:
        return self._items
    
    def __str__(self):
        out = io.StringIO()
        if self.content:
            out.write('effect_block {\n')
            for instr in self.content:
                out.write(f'  {instr.ref} = {instr}\n')
            out.write('}')
        else:
            out.write(f'effect_block')
        return out.getvalue()
