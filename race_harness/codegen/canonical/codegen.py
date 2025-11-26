import io
import dataclasses
from typing import Dict, Set, List, Optional
from race_harness.codegen.base import BaseCodegen
from race_harness.ir import RHContext, RHModule, RHInstance, RHProcess, RHRef, RHConditionalControlFlowEdge, RHPredicate, RHEffectBlock, RHSet, RHUnconditionalControlFlowEdge, RHOperation, RHControlFlowEdge

@dataclasses.dataclass
class InstanceState:
    instance: RHInstance
    process: RHProcess
    counterpart_processes: Dict[RHRef, str]
    set_variables: Dict[RHRef, str]

@dataclasses.dataclass
class ModuleState:
    context: RHContext
    module: RHModule
    instances: Dict[RHRef, InstanceState]
    message_channels: Dict[RHRef, RHRef]

class CanonicalCodegen(BaseCodegen):
    def __init__(self, out: io.TextIOBase):
        self._out = out

    def codegen_module(self, context: RHContext, module: RHModule):
        self._do_codegen(self._codegen_module, context, module)

    def _codegen_module(self, context: RHContext, module: RHModule):
        module_state = ModuleState(
            context=context,
            module=module,
            instances=dict(),
            message_channels=dict()
        )
        protocol_map = dict()
        channels = dict()
        for process in module.processes:
            protocol_map[process.protocol.ref] = process
        for instance in module.instances:
            instance_state = InstanceState(
                instance=instance,
                process=protocol_map[instance.protocol.ref],
                counterpart_processes=dict(),
                set_variables=dict(),
            )
            module_state.instances[instance.ref] = instance_state

            for channel in instance.protocol.in_protocol:
                channels[channel.ref] = None
                for msg in channel.items:
                    module_state.message_channels[msg] = channel.ref

            for channel in instance.protocol.out_protocol:
                channels[channel.ref] = None
                for msg in channel.items:
                    module_state.message_channels[msg] = channel.ref

        yield '#include <stdlib.h>'
        yield '#include <stdio.h>'
        yield '#include <pthread.h>'
        yield '#include <assert.h>'
        yield ''

        yield f'static pthread_mutex_t mutexes[{len(module.instances)}][{len(module.instances)}];'
        yield ''
        for channel in channels.keys():
            yield f'static int channel{channel.uid}[{len(module_state.instances)}][{len(module_state.instances)}] = {{'
            yield 1
            yield ', '.join(
                '-1'
                for _ in range(len(module_state.instances) ** 2)
            )
            yield -1
            yield '};'
            yield ''

        yield f'static const int instance_linearization[{len(context)}] = {{'
        yield 1
        for index, instance_state in enumerate(module_state.instances.values()):
            yield f'[{instance_state.instance.ref.uid}] = {index + 1},'
        yield -1
        yield '};'
        yield ''

        yield 'static int get_instance_linear_id(int instance) {'
        yield 1
        yield 'assert(instance_linearization[instance]);'
        yield 'return instance_linearization[instance] - 1;'
        yield -1
        yield '}'
        yield ''

        yield 'static void lock_communication(int from, int to) {'
        yield 1
        yield f'pthread_mutex_lock(&mutexes[get_instance_linear_id(from)][get_instance_linear_id(to)]);'
        yield -1
        yield '}'
        yield ''

        yield 'static void unlock_communication(int from, int to) {'
        yield 1
        yield f'pthread_mutex_unlock(&mutexes[get_instance_linear_id(from)][get_instance_linear_id(to)]);'
        yield -1
        yield '}'
        yield ''

        yield f'static void send_message(int from, int to, int channel[{len(module_state.instances)}][{len(module_state.instances)}], int msg) {{'
        yield 1
        yield f'lock_communication(from, to);'
        yield f'channel[get_instance_linear_id(from)][get_instance_linear_id(to)] = msg;'
        yield f'unlock_communication(from, to);'
        yield -1
        yield '}'
        yield ''

        yield f'static int has_message(int from, int to, int channel[{len(module_state.instances)}][{len(module_state.instances)}], int msg) {{'
        yield 1
        yield 'return channel[get_instance_linear_id(from)][get_instance_linear_id(to)] == msg;'
        yield -1
        yield '}'
        yield ''

        yield f'static void consume_message(int from, int to, int channel[{len(module_state.instances)}][{len(module_state.instances)}]) {{'
        yield 1
        yield 'channel[get_instance_linear_id(from)][get_instance_linear_id(to)] = -1;'
        yield -1
        yield '}'
        yield ''

        for instance_state in module_state.instances.values():
            yield from self._codegen_instance(context, module_state, instance_state)

        yield 'int main(int argc, const char **argv) {'
        yield 1
        yield '(void) argc;'
        yield '(void) argv;'
        yield ''
        for i in range(len(module.instances)):
            for j in range(len(module.instances)):
                yield f'pthread_mutex_init(&mutexes[{i}][{j}], NULL);'
        yield ''

        yield f'pthread_t threads[{len(module_state.instances)}];'
        for i, instance in enumerate(module_state.instances.keys()):
            yield f'pthread_create(&threads[{i}], NULL, proc{instance.uid}, NULL);'
        yield ''

        for i in range(len(module_state.instances)):
            yield f'pthread_join(threads[{i}], NULL);'

        yield 'return EXIT_SUCCESS;'
        yield -1
        yield '}'


    def _codegen_instance(self, context: RHContext, module_state: ModuleState, instance_state: InstanceState):
        yield f'static void *proc{instance_state.instance.ref.uid}(void *arg) {{'
        yield 1
        yield '(void) arg;'
        yield ''

        for edge in instance_state.process.control_flow.edges:
            if isinstance(edge, RHConditionalControlFlowEdge):
                yield from self._codegen_mappings(context, instance_state, edge.condition)

        queue = [instance_state.process.entry_block]
        visited = set()
        while queue:
            block = queue.pop()
            if block.ref in visited:
                continue
            visited.add(block.ref)
            queue.extend(instance_state.process.control_flow.edge_from(block.ref).successors)

            yield from self._codegen_block(module_state, instance_state, block)

        yield 'return NULL;'
        yield -1
        yield '}'
        yield ''

    def _codegen_block(self, module_state: ModuleState, instance_state: InstanceState, block: RHEffectBlock):
        yield f'{self._get_block_label(block.ref)}: {{'
        yield 1
        for operation in block.content:
            yield from self._codegen_operation(module_state, instance_state, operation)

        yield from self._codegen_edge(module_state, instance_state, instance_state.process.control_flow.edge_from(block.ref))
        yield -1
        yield '}'

    def _codegen_operation(self, module_state: ModuleState, instance_state: InstanceState, operation: RHOperation):
        if ext_act := operation.as_external_action():
            yield f'printf("{instance_state.instance.ref.uid}: {ext_act.external_action}\\n");'
        elif trans := operation.as_transmission():
            for dest in trans.destinations:
                def do_transmit(dest: RHRef):
                    destination = f'{module_state.instances[dest].instance.ref.uid}' if dest not in instance_state.counterpart_processes else instance_state.counterpart_processes[dest]
                    yield f'send_message({instance_state.instance.ref.uid}, {destination}, channel{module_state.message_channels[trans.message].uid}, {trans.message.uid});'
                if domain := module_state.context[dest].as_domain():
                    for dest in domain.items:
                        yield from do_transmit(dest)
                else:
                    yield from do_transmit(dest)
        elif set_add := operation.as_set_add():
            if set_add.target_set in instance_state.set_variables:
                destination = str(set_add.value.uid) if set_add.value not in instance_state.counterpart_processes else instance_state.counterpart_processes[set_add.value]
                set_name = instance_state.set_variables[set_add.target_set]
                yield f'{set_name}[mapping_{set_name}[{destination}]] = 1;'
        elif set_del := operation.as_set_del():
            if set_del.target_set in instance_state.set_variables:
                destination = str(set_del.value.uid) if set_del.value not in instance_state.counterpart_processes else instance_state.counterpart_processes[set_del.value]
                set_name = instance_state.set_variables[set_del.target_set]
                yield f'{set_name}[mapping_{set_name}[{destination}]] = 0;'

    def _codegen_edge(self, module_state: ModuleState, instance_state: InstanceState, edge: Optional[RHControlFlowEdge]):
        if edge and isinstance(edge, RHUnconditionalControlFlowEdge):
            yield f'goto {self._get_block_label(edge.target.ref)};'
        elif edge and isinstance(edge, RHConditionalControlFlowEdge):
            yield from self._codegen_conditional_edge(module_state.context, module_state, instance_state, edge.condition, edge.target.ref, edge.alternative.ref)
        else:
            yield 'return NULL;'

    def _codegen_mappings(self, context: RHContext, instance_state: InstanceState, predicate: RHPredicate):
        if conj := predicate.operation.as_conjunction():
            for pred in conj.conjuncts:
                yield from self._codegen_mappings(context, instance_state, context[pred].as_predicate())
        elif predicate.operation.as_receival():
            if predicate.ref not in instance_state.counterpart_processes:
                instance_state.counterpart_processes[predicate.ref] = f'procid{len(instance_state.counterpart_processes)}'
                yield f'int {instance_state.counterpart_processes[predicate.ref]} = -1;'
        elif set_has := predicate.operation.as_set_has():
            yield from self._codegen_set_decl(context, instance_state, context[set_has.target_set].to_set())
        elif set_empty := predicate.operation.as_set_empty():
            yield from self._codegen_set_decl(context, instance_state, context[set_empty.target_set].to_set())

    def _codegen_set_decl(self, context: RHContext, instance_state: InstanceState, target_set: RHSet):
        if target_set.ref not in instance_state.set_variables:
            domain = context[target_set.domain].to_domain()
            target_set_name = f'set{len(instance_state.set_variables)}'
            instance_state.set_variables[target_set.ref] = target_set_name
            yield f'int {target_set_name}[{len(domain)}] = {{0}};'
            yield f'static const int mapping_{target_set_name}[{len(context)}] = {{'
            yield 1
            for index, ref in enumerate(domain):
                yield BaseCodegen.NO_NL
                yield f'[{ref.uid + 1}] = {index + 1}'
                if index + 1 < len(domain):
                    yield ','
                else:
                    yield ''
            yield -1
            yield '};'

    def _codegen_conditional_edge(self, context: RHContext, module_state: ModuleState, instance_state: InstanceState, condition: RHPredicate, target: RHRef, alternative: RHRef):
        yield 'int cond_satisfied = 0;'

        for sender_assignment in self._enumerate_sender_assignments(module_state, condition):
            yield 'if (!cond_satisfied) {'
            yield 1
            for sender_instance in sender_assignment.values():
                yield f'lock_communication({sender_instance.instance.ref.uid}, {instance_state.instance.ref.uid});'
            yield 'if ({}) {{'.format(
                self._build_condition(context, module_state, instance_state, sender_assignment, condition)
            )
            yield 1
            yield 'cond_satisfied = 1;'
            yield from self._consume_messages(context, module_state, instance_state, sender_assignment, condition)
            yield -1
            yield '}'
            for sender_instance in sender_assignment.values():
                yield f'unlock_communication({sender_instance.instance.ref.uid}, {instance_state.instance.ref.uid});'
            yield -1
            yield '}'

        yield 'if (cond_satisfied) {'
        yield 1
        yield f'goto {self._get_block_label(target)};'
        yield -1
        yield '} else {'
        yield 1
        yield f'goto {self._get_block_label(alternative)};'
        yield -1
        yield '}'

    def _enumerate_sender_assignments(self, module_state: ModuleState, condition: RHPredicate):
        if conj := condition.operation.as_conjunction():
            def unroll_conj(predicates: List[RHPredicate]):
                if not predicates:
                    yield from (dict(),)
                    return
                head = predicates[0]
                tail = predicates[1:]
                for sender_assignment in self._enumerate_sender_assignments(module_state, head):
                    for tail_sender_assignment in unroll_conj(tail):
                        yield {
                            **sender_assignment,
                            **tail_sender_assignment
                        }
            yield from unroll_conj(list(conj.conjuncts))
        elif receival := condition.operation.as_receival():
            for msg in receival.messages:
                for instance_state in module_state.instances.values():
                    has_msg = any(msg in channel for channel in instance_state.process.protocol.out_protocol)
                    if has_msg:
                        yield {
                            msg: instance_state
                        }
        else:
            yield from (dict(),)

    def _build_condition(self, context: RHContext, module_state: ModuleState, instance_state: InstanceState, sender_assignment: Dict[RHRef, InstanceState], predicate: RHPredicate):
        if conj := predicate.operation.as_conjunction():
            return ' && '.join(
                self._build_condition(module_state, instance_state, sender_assignment, pred)
                for pred in conj.conjuncts
            )
        elif receival := predicate.operation.as_receival():
            for msg in receival.messages:
                if msg in sender_assignment:
                    return f'has_message({sender_assignment[msg].instance.ref.uid}, {instance_state.instance.ref.uid}, channel{module_state.message_channels[msg].uid}, {msg.uid})'
        elif set_empty := predicate.operation.as_set_empty():
            set_name = instance_state.set_variables[set_empty.target_set]
            return ' && '.join(
                f'!{set_name}[{i}]'
                for i in range(len(context[context[set_empty.target_set].to_set().domain].to_domain()))
            )
        elif set_has := predicate.operation.as_set_has():
            destination = str(set_has.value.uid) if set_has.value not in instance_state.counterpart_processes else instance_state.counterpart_processes[set_has.value]
            set_name = instance_state.set_variables[set_has.target_set]
            return f'{set_name}[mapping_{set_name}[{destination}]]'
        elif predicate.operation.as_nondet():
            return 'rand() % 2'

    def _consume_messages(self, context: RHContext, module_state: ModuleState, instance_state: InstanceState, sender_assignment: Dict[RHRef, InstanceState], predicate: RHPredicate):
        if conj := predicate.operation.as_conjunction():
            for pred in conj:
                yield from self._consume_messages(context, module_state, instance_state, sender_assignment, pred)
        elif receival := predicate.operation.as_receival():
            for msg in receival.messages:
                if msg in sender_assignment:
                    yield f'consume_message({sender_assignment[msg].instance.ref.uid}, {instance_state.instance.ref.uid}, channel{module_state.message_channels[msg].uid});'
                    yield f'{instance_state.counterpart_processes[predicate.ref]} = {sender_assignment[msg].instance.ref.uid};'

    def _get_block_label(self, block_ref: RHRef):
        return f'label{block_ref.uid}'