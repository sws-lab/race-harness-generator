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
            if bool_slot := slot.as_boolean():
                value = 1 if bool_slot.initial_value else 0
                self._out.write(f'slot {bool_slot.identifier.identifier} bool {value}\n')
            elif node_slot := slot.as_node():
                self._out.write(f'slot {node_slot.identifier.identifier} node {node_slot.initial_value.node_id}\n')

    def serialize_transitions(self, module: STModule):
        self._out.write(f'transitions {len(module)}\n')
        for transition in module:
            self._out.write(f'transition {transition.identifier.transition_id} component {transition.node_slot.identifier} src {transition.source_node_id.node_id} dst {transition.target_node_id.node_id} guards {transition.num_of_guards} {1 if transition.invert_guard else 0} instructions {transition.num_of_instructions}\n')
            for guard in transition.guards:
                if bool_guard := guard.as_bool():
                    self._out.write(f'bool_guard {bool_guard.slot_id.identifier} {1 if bool_guard.value else 0}\n')

            for instr in transition.instructions:
                if ext_action := instr.as_external_action():
                    self._out.write(f'do_instr {ext_action.action}\n')
                elif set_bool := instr.as_set_bool():
                    self._out.write(f'set_bool_instr {set_bool.slot_id.identifier} {1 if set_bool.value else 0}\n')