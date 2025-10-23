import io
from typing import Iterable
from race_harness.state_ir.guard import STGuardCondition
from race_harness.state_ir.instruction import STInstruction

class STNodeID:
    def __init__(self, node_id: int):
        self._node_id = node_id

    @property
    def node_id(self) -> int:
        return self._node_id
    
    def __eq__(self, value):
        return isinstance(value, STNodeID) and self.node_id == value.node_id
    
    def __hash__(self):
        return hash(self.node_id)
    
    def __str__(self):
        return f'&{self.node_id}'
    
class STTransitionID:
    def __init__(self, transition_id: int):
        self._transition_id = transition_id

    @property
    def transition_id(self) -> int:
        return self._transition_id
    
    def __eq__(self, value):
        return isinstance(value, STTransitionID) and self.transition_id == value.transition_id
    
    def __hash__(self):
        return hash(self.transition_id)
    
    def __str__(self):
        return f'@{self.transition_id}'

class STTransition:
    def __init__(self, transition_id: STTransitionID, source_node_id: STNodeID, target_node_id: STNodeID, invert_gurard: bool):
        self._transition_id = transition_id
        self._source_node_id = source_node_id
        self._target_node_id = target_node_id
        self._invert_guard = invert_gurard
        self._guards = list()
        self._instructions = list()

    @property
    def identifier(self) -> STTransitionID:
        return self._transition_id

    @property
    def source_node_id(self) -> STNodeID:
        return self._source_node_id
    
    @property
    def target_node_id(self) -> STNodeID:
        return self._target_node_id
    
    @property
    def invert_guard(self) -> bool:
        return self._invert_guard

    @property
    def guards(self) -> Iterable[STGuardCondition]:
        yield from self._guards

    @property
    def instructions(self) -> Iterable[STInstruction]:
        yield from self._instructions

    def add_guard(self, guard: STGuardCondition):
        self._guards.append(guard)

    def add_instruction(self, instruction: STInstruction):
        self._instructions.append(instruction)

    def __str__(self):
        out = io.StringIO()
        out.write(f'({self.source_node_id} -> {self.target_node_id})')
        if self._guards:
            if self.invert_guard:
                out.write(f' if !(\n')
            else:
                out.write(f' if (\n')
            for guard in self.guards:
                out.write(f'  {guard}\n')
            out.write(')')
        if self._instructions:
            out.write(' {\n')
            for instr in self.instructions:
                out.write(f'  {instr}\n')
            out.write('}')
        return out.getvalue()
