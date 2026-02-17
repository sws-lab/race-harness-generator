import dataclasses
from typing import Dict, List, Tuple, Optional, Iterable, Set
from race_harness.ir import RHModule, RHContext, RHProtocol, RHProcess, RHInstance, RHEffectBlock, RHUnconditionalControlFlowEdge, RHConditionalControlFlowEdge, RHPredicate, RHRef, RHSet, RHDomain
from race_harness.stir import STModule, STNodeID, STExternalActionInstruction, STSlotID, STTransition, STSetIntInstruction, STIntGuardCondition
from race_harness.stir.translator.mapping import STRHMapping

@dataclasses.dataclass
class BlockContext:
    block: RHEffectBlock
    node: STNodeID

@dataclasses.dataclass
class InstanceContext:
    instance: RHInstance
    process: RHProcess
    entry_node: STNodeID
    exit_node: STNodeID
    node_slot: STSlotID

@dataclasses.dataclass
class TranslatorContext:
    module: RHModule
    protocol_impl: Dict[RHProtocol, RHProcess]
    instance_context: Dict[RHInstance, InstanceContext]
    blocks: Dict[Tuple[RHInstance, RHEffectBlock], BlockContext]
    message_slots: Dict[Tuple[RHRef, RHRef, RHRef], STSlotID]
    set_element_slots: Dict[Tuple[RHRef, RHRef, RHRef], STSlotID]
    message_domains: Dict[RHRef, RHDomain]
    outbound_messaging: Dict[RHRef, Set[RHProcess]]
    inbound_messaging: Dict[RHRef, Set[RHProcess]]

@dataclasses.dataclass
class BindingsContainer:
    bindings: Dict[RHRef, RHRef]

    def __hash__(self):
        res = 0
        for key, value in self.bindings.items():
            res = res * 31 + hash(key) * 17 + hash(value)
        return res
    
    def __eq__(self, other):
        if not isinstance(other, BindingsContainer):
            return False
        
        for key, value in self.bindings.items():
            if key not in other.bindings or value != other.bindings[key]:
                return False
            
        for key, value in other.bindings.items():
            if key not in self.bindings or value != self.bindings[key]:
                return False
        
        return True

class RHSTTranslator:
    def __init__(self, context: RHContext, st_module: STModule):
        self._context = context
        self._st_module = st_module
        self._mapping = STRHMapping()

    @property
    def st_module(self) -> STModule:
        return self._st_module
    
    @property
    def mapping(self) -> STRHMapping:
        return self._mapping
    
    def translate_module(self, module: RHModule):
        trans_ctx = TranslatorContext(
            module=module,
            protocol_impl=dict(),
            instance_context=dict(),
            blocks=dict(),
            message_slots=dict(),
            set_element_slots=dict(),
            message_domains=dict(),
            outbound_messaging=dict(),
            inbound_messaging=dict()
        )
        for process in module.processes:
            trans_ctx.protocol_impl[process.protocol] = process
            for domain in process.protocol.in_protocol:
                for message in domain:
                    trans_ctx.message_domains[message] = domain
                if domain not in trans_ctx.inbound_messaging:
                    trans_ctx.inbound_messaging[domain.ref] = set()
                trans_ctx.inbound_messaging[domain.ref].add(process)

            for domain in process.protocol.out_protocol:
                for message in domain:
                    trans_ctx.message_domains[message] = domain
                if domain not in trans_ctx.outbound_messaging:
                    trans_ctx.outbound_messaging[domain.ref] = set()
                trans_ctx.outbound_messaging[domain.ref].add(process)
        for instance in module.instances:
            entry_node = self._st_module.new_node()
            trans_ctx.instance_context[instance] = InstanceContext(
                instance=instance,
                process=trans_ctx.protocol_impl[instance.protocol],
                entry_node=entry_node,
                exit_node=self._st_module.new_node(),
                node_slot=self._st_module.state.new_node_slot(entry_node)
            )

        for instance_ctx in trans_ctx.instance_context.values():
            self.translate_instance(trans_ctx, instance_ctx)

    def translate_instance(self, trans_ctx: TranslatorContext, instance_ctx: InstanceContext):
        visited_blocks = set()
        block_queue = [(instance_ctx.entry_node, False, None, instance_ctx.process.entry_block)]

        while block_queue:
            pred_node, neg_condition, condition, block = block_queue.pop()
            if (pred_node, block) in visited_blocks:
                continue
            visited_blocks.add((pred_node, block))

            block_ctx = trans_ctx.blocks.get((instance_ctx.instance, block), None)
            if block_ctx is None:
                block_ctx = BlockContext(
                    block=block,
                    node=self._st_module.new_node()
                )
                trans_ctx.blocks[(instance_ctx.instance, block)] = block_ctx
                self._mapping.map_to(block_ctx.node, instance_ctx.instance.ref, block.ref)
            self.traverse_block(instance_ctx, block_ctx, block_queue)
            self.translate_block(trans_ctx, instance_ctx, block_ctx, pred_node, neg_condition, condition)

    def traverse_block(self, instance_ctx: InstanceContext, block_ctx: BlockContext, block_queue: List[Tuple[STNodeID, bool, RHPredicate, RHEffectBlock]]):
        edge = instance_ctx.process.control_flow.edge_from(block_ctx.block.ref)
        if edge is not None:
            if isinstance(edge, RHUnconditionalControlFlowEdge):
                block_queue.append((block_ctx.node, False, None, edge.target))
            elif isinstance(edge, RHConditionalControlFlowEdge):
                block_queue.append((block_ctx.node, False, edge.condition, edge.target))
                block_queue.append((block_ctx.node, True, edge.condition, edge.alternative))

    def translate_block(self, trans_ctx: TranslatorContext, instance_ctx: InstanceContext, block_ctx: BlockContext, pred_node: STNodeID, neg_condition: bool, condition: Optional[RHPredicate]):
        for bindings in self._enumerate_condition_bindings(trans_ctx, instance_ctx, condition):
            transition = self._st_module.new_transition(instance_ctx.node_slot, pred_node, block_ctx.node, neg_condition)
            if condition is not None:
                self.translate_condition(trans_ctx, instance_ctx, transition, neg_condition, condition, bindings)

            for oper in block_ctx.block.content:
                if ext_action := oper.as_external_action():
                    transition.add_instruction(STExternalActionInstruction(ext_action.external_action))
                elif trans := oper.as_transmission():
                    for dst in trans.destinations:
                        _, dst = bindings.get(dst, (None, dst))
                        dst_entity = self._context[dst]
                        if dst_entity.as_instance():
                            msg_slot = self._get_msg_slot(trans_ctx, instance_ctx.instance.ref, dst_entity.ref, trans.message)
                            transition.add_instruction(STSetIntInstruction(msg_slot, trans.message.uid))
                        elif dst_entity.as_domain():
                            for subdst in dst_entity.as_domain().items:
                                msg_slot = self._get_msg_slot(trans_ctx, instance_ctx.instance.ref, subdst, trans.message)
                                transition.add_instruction(STSetIntInstruction(msg_slot, trans.message.uid))
                elif set_add := oper.as_set_add():
                    _, value = bindings.get(set_add.value, (None, set_add.value))
                    elt_slot = self._get_set_element_slot(trans_ctx, instance_ctx, set_add.target_set, value)
                    transition.add_instruction(STSetIntInstruction(elt_slot, 1))
                elif set_del := oper.as_set_del():
                    _, value = bindings.get(set_del.value, (None, set_del.value))
                    elt_slot = self._get_set_element_slot(trans_ctx, instance_ctx, set_del.target_set, value)
                    transition.add_instruction(STSetIntInstruction(elt_slot, 0))

    def translate_condition(self, trans_ctx: TranslatorContext, instance_ctx: InstanceContext, transition: STTransition, neg_condition: bool, condition: RHPredicate, bindings: Dict[RHRef, Tuple[RHRef, RHRef]]):
        if condition.operation.as_nondet():
            pass
        elif set_empty := condition.operation.as_set_empty():
            set: RHSet = self._context[set_empty.target_set].to_set()
            for elt in self._context[set.domain].to_domain():
                slot_id = self._get_set_element_slot(trans_ctx, instance_ctx, set_empty.target_set, elt)
                transition.add_guard(STIntGuardCondition(slot_id, 0))
        elif set_has := condition.operation.as_set_has():
            value = bindings.get(set_has.value, set_has.value)
            slot_id = self._get_set_element_slot(trans_ctx, instance_ctx, set_has.target_set, value)
            transition.add_guard(STIntGuardCondition(slot_id, 1))
        elif condition.operation.as_receival():
            if condition.ref in bindings:
                msg, sender = bindings[condition.ref]
                slot_id = self._get_msg_slot(trans_ctx, sender, instance_ctx.instance.ref, msg)
                transition.add_guard(STIntGuardCondition(slot_id, msg.uid))
                if not neg_condition:
                    transition.add_instruction(STSetIntInstruction(slot_id, -1))
        elif conjunction := condition.operation.as_conjunction():
            for conj in conjunction.conjuncts:
                self.translate_condition(trans_ctx, instance_ctx, transition, neg_condition, self._context[conj].to_predicate(), bindings)

    def _get_msg_slot(self, trans_ctx: TranslatorContext, sender_ref: RHRef, receiver_ref: RHRef, message_ref: RHRef) -> STSlotID:
        domain_ref = trans_ctx.message_domains[message_ref]
        key = (sender_ref, receiver_ref, domain_ref)
        slot_id = trans_ctx.message_slots.get(key, None)
        if slot_id is None:
            slot_id = self._st_module.state.new_int_slot(-1)
            trans_ctx.message_slots[key] = slot_id
        return slot_id
    
    def _get_set_element_slot(self, trans_ctx: TranslatorContext, instance_ctx: InstanceContext, set_ref: RHRef, element_ref: RHRef) -> STSlotID:
        key = (instance_ctx.instance.ref, set_ref, element_ref)
        slot_id = trans_ctx.set_element_slots.get(key, None)
        if slot_id is None:
            slot_id = self._st_module.state.new_int_slot(0)
            trans_ctx.set_element_slots[key] = slot_id
        return slot_id
    
    def _enumerate_condition_bindings(self, trans_ctx: TranslatorContext, instance_ctx: InstanceContext, condition: Optional[RHPredicate]) -> Iterable[Dict[RHRef, Tuple[RHRef, RHRef]]]:
        base = {
            param_id: (None, param)
            for param_id, param in zip(instance_ctx.instance.protocol.parameters, instance_ctx.instance.parameters)
        }

        if condition is None:
            yield base
            return
        
        visited = set()
        for binding in self._enumerate_condition_bindings_impl(trans_ctx, instance_ctx, condition):
            container = BindingsContainer(binding)
            if container not in visited:
                yield {
                    **base,
                    **binding
                }
                visited.add(container)
        if not visited:
            yield base
    
    def _enumerate_condition_bindings_impl(self, trans_ctx: TranslatorContext, instance_ctx: InstanceContext, condition: RHPredicate) -> Iterable[Dict[RHRef, Tuple[RHRef, RHRef]]]:
        if condition.operation.as_receival():
            for msg in condition.operation.as_receival().messages:
                for instance in self._enum_sender_instances(trans_ctx, msg):
                    yield {
                        condition.ref: (msg, instance.ref)
                    }
        elif condition.operation.as_conjunction():
            yield from self._enum_conjunction_bindings(trans_ctx, instance_ctx, condition.operation.as_conjunction().conjuncts)

    def _enum_conjunction_bindings(self, trans_ctx: TranslatorContext, instance_ctx: InstanceContext, conjuncts: List[RHRef]) -> Iterable[Dict[RHRef, Tuple[RHRef, RHRef]]]:
        if not conjuncts:
            return

        conj_head = conjuncts[0]
        conj_tail = conjuncts[1:]

        if not conj_tail:
            yield from self._enumerate_condition_bindings(trans_ctx, instance_ctx, self._context[conj_head].to_predicate())
            return
        
        for variant in self._enumerate_condition_bindings(trans_ctx, instance_ctx, self._context[conj_head].to_predicate()):
            for subvariant in self._enum_conjunction_bindings(trans_ctx, instance_ctx, conj_tail):
                yield {
                    **variant,
                    **subvariant
                }

    def _enum_sender_instances(self, trans_ctx: TranslatorContext, msg: RHRef) -> Iterable[RHInstance]:
        for process in self._enum_senders(trans_ctx, msg):
            for instance_ctx in trans_ctx.instance_context.values():
                if instance_ctx.process.ref == process.ref:
                    yield instance_ctx.instance

    def _enum_senders(self, trans_ctx: TranslatorContext, msg: RHRef) -> Iterable[RHProcess]:
        yield from trans_ctx.outbound_messaging.get(trans_ctx.message_domains[msg].ref, ())
