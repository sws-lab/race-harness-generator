import io
from race_harness.stir import STModule, STState

class STSerialize:
    def __init__(self, out: io.TextIOBase):
        self._out = out

    def serialize_module(self, module: STModule):
        self.serialize_state(module.state)
        self.serialize_transitions(module)

    def serialize_state(self, state: STState):
        self._out.write(f'state {len(state)}\n')
        for slot in state:
            if int_slot := slot.as_int():
                self._out.write(f'slot {int_slot.identifier.identifier} int {int_slot.initial_value}\n')
            elif node_slot := slot.as_node():
                self._out.write(f'slot {node_slot.identifier.identifier} node {node_slot.initial_value.node_id}\n')

    def serialize_transitions(self, module: STModule):
        self._out.write(f'transitions {len(module)}\n')
        for transition in module:
            num_of_instr = sum(
                1
                for instr in transition.instructions
                if instr.as_set_int() is not None
            )
            self._out.write(f'transition {transition.identifier.transition_id} component {transition.node_slot.identifier} src {transition.source_node_id.node_id} dst {transition.target_node_id.node_id} guards {transition.num_of_guards} {1 if transition.invert_guard else 0} instructions {num_of_instr}\n')
            for guard in transition.guards:
                if int_guard := guard.as_int():
                    self._out.write(f'int_guard {int_guard.slot_id.identifier} {int_guard.value}\n')

            for instr in transition.instructions:
                if set_int := instr.as_set_int():
                    self._out.write(f'set_int_instr {set_int.slot_id.identifier} {set_int.value}\n')