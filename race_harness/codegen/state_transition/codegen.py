import io
from race_harness.codegen.base import BaseCodegen
from race_harness.stir import STModule, STTransition

class ExecutableStirCodegen(BaseCodegen):
    def __init__(self, out: io.TextIOBase):
        self._out = out

    def codegen_module(self, module: STModule):
        self._do_codegen(self._codegen_module, module)

    def _codegen_module(self, module: STModule):
        yield '#include <stdlib.h>'
        yield '#include <stdio.h>'
        yield '#include <pthread.h>'
        yield '#include <stdatomic.h>'
        yield ''
        
        yield '_Atomic struct State {'
        yield 1
        yield f'int slots[{len(module.state)}];'
        yield -1
        yield f'}} state = (struct State) {{'
        yield 1
        for idx, slot in enumerate(module.state):
            yield BaseCodegen.NO_NL
            if int_slot := slot.as_int():
                yield str(int_slot.initial_value)
            elif node_slot := slot.as_node():
                yield str(node_slot.initial_value.node_id)
            if idx + 1 < len(module.state):
                yield ','
            else:
                yield ''
        yield -1
        yield '};'
        yield ''

        for transition in module.transitions:
            yield from self._codegen_transition(module, transition)

        yield 'int main(int argc, const char **argv) {'
        yield 1
        yield '(void) argc;'
        yield '(void) argv;'
        yield ''
        num_of_transitions = len(module)
        yield f'pthread_t transition_threads[{num_of_transitions}];'
        for idx in range(num_of_transitions):
            yield f'pthread_create(&transition_threads[{idx}], NULL, transition{idx}, NULL);'
        for idx in range(num_of_transitions):
            yield f'pthread_join(transition_threads[{idx}], NULL);'
        yield 'return EXIT_SUCCESS;'
        yield -1
        yield '}'

    def _codegen_transition(self, module: STModule, transition: STTransition):
        yield f'void *transition{transition.identifier.transition_id}(void *arg) {{'
        yield 1
        yield '(void) arg;'
        yield 'for (;;) {'
        yield 1

        yield 'struct State current_state = state;'
        yield 'struct State next_state = current_state;'
        
        slots = set()
        slots.add(transition.node_slot)
        guards = list()
        for guard in transition.guards:
            if int_guard := guard.as_int():
                slots.add(int_guard.slot_id)
                guards.append(
                    f'current_state.slots[{int_guard.slot_id.identifier}] == {int_guard.value}'
                )

        guards_flat = ' && '.join(guards)
        conditions = [
            f'current_state.slots[{transition.node_slot.identifier}] == {transition.source_node_id.node_id}'
        ]
        if guards_flat:
            if transition.invert_guard:
                conditions.append(f'!({guards_flat})')
            else:
                conditions.append(guards_flat)
        yield 'if (!({})) continue;'.format(' && '.join(conditions))

        actions = [
            # f'printf("DO {transition.identifier.transition_id}\\n");'
        ]
        yield f'next_state.slots[{transition.node_slot.identifier}] = {transition.target_node_id.node_id};'
        for instr in transition.instructions:
            if set_int := instr.as_set_int():
                yield f'next_state.slots[{set_int.slot_id.identifier}] = {set_int.value};'
            elif ext_act := instr.as_external_action():
                actions.append(f'printf("{ext_act.action}\\n");')

        yield 'atomic_compare_exchange_strong(&state, &current_state, next_state);'

        yield from actions

        yield -1
        yield '}'
        yield 'return NULL;'
        yield -1
        yield '}'
        yield ''
