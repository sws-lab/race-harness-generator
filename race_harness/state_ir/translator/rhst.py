import dataclasses
from typing import Dict, List, Tuple, Optional, Iterable
from race_harness.ir import RHModule, RHContext, RHProtocol, RHProcess, RHInstance, RHEffectBlock, RHUnconditionalControlFlowEdge, RHConditionalControlFlowEdge, RHPredicate, RHRef
from race_harness.state_ir import STModule, STNodeID, STExternalActionInstruction, STSetBoolInstruction, SlotID

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

@dataclasses.dataclass
class TranslatorContext:
    module: RHModule
    protocol_impl: Dict[RHProtocol, RHProcess]
    instance_context: Dict[RHInstance, InstanceContext]
    blocks: Dict[Tuple[RHInstance, RHEffectBlock], BlockContext]
    message_slots: Dict[Tuple[RHRef, RHRef], SlotID]
    set_element_slots: Dict[Tuple[RHRef, RHRef, RHRef], SlotID]

class RHSTTranslator:
    def __init__(self, context: RHContext, st_module: STModule):
        self._context = context
        self._st_module = st_module

    @property
    def st_module(self) -> STModule:
        return self._st_module
    
    def translate_module(self, module: RHModule):
        trans_ctx = TranslatorContext(
            module=module,
            protocol_impl=dict(),
            instance_context=dict(),
            blocks=dict(),
            message_slots=dict(),
            set_element_slots=dict()
        )
        for process in module.processes:
            trans_ctx.protocol_impl[process.protocol] = process
        for instance in module.instances:
            trans_ctx.instance_context[instance] = InstanceContext(
                instance=instance,
                process=trans_ctx.protocol_impl[instance.protocol],
                entry_node=self._st_module.new_node(),
                exit_node=self._st_module.new_node()
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
        if condition is not None:
            for variant in self._enumerate_transition_variants(trans_ctx, condition):
                transition = self._st_module.new_transition(pred_node, block_ctx.node)

                for oper in block_ctx.block.content:
                    if oper.as_external_action():
                        action = oper.as_external_action().external_action
                        transition.add_instruction(STExternalActionInstruction(action))
                    elif oper.as_transmission():
                        dsts = oper.as_transmission().destinations
                        msg = oper.as_transmission().message
                        for dst in dsts:
                            dst_entity = self._context[dst]
                            if dst_entity.as_instance():
                                msg_slot = self._get_msg_slot(trans_ctx, dst_entity.ref, msg)
                                transition.add_instruction(STSetBoolInstruction(msg_slot, True))
                            elif dst_entity.as_fixed_set():
                                for subdst in dst_entity.as_fixed_set().items:
                                    msg_slot = self._get_msg_slot(trans_ctx, subdst, msg)
                                    transition.add_instruction(STSetBoolInstruction(msg_slot, True))
                    elif oper.as_set_add():
                        target_set = oper.as_set_add().target_set
                        value = oper.as_set_add().value
                        value = variant.get(value, value)
                        elt_slot = self._get_set_element_slot(trans_ctx, instance_ctx, target_set, value)
                        transition.add_instruction(STSetBoolInstruction(elt_slot, True))
                    elif oper.as_set_del():
                        target_set = oper.as_set_del().target_set
                        value = oper.as_set_del().value
                        value = variant.get(value, value)
                        elt_slot = self._get_set_element_slot(trans_ctx, instance_ctx, target_set, value)
                        transition.add_instruction(STSetBoolInstruction(elt_slot, False))

    def _get_msg_slot(self, trans_ctx: TranslatorContext, receiver_ref: RHRef, message_ref: RHRef) -> SlotID:
        slot_id = trans_ctx.message_slots.get((receiver_ref, message_ref), None)
        if slot_id is None:
            slot_id = self._st_module.state.new_boolean_slot(False)
            trans_ctx.message_slots[(receiver_ref, message_ref)] = slot_id
        return slot_id
    
    def _get_set_element_slot(self, trans_ctx: TranslatorContext, instance_ctx: InstanceContext, set_ref: RHRef, element_ref: RHRef) -> SlotID:
        key = (instance_ctx.instance.ref, set_ref, element_ref)
        slot_id = trans_ctx.set_element_slots.get(key, None)
        if slot_id is None:
            slot_id = self._st_module.state.new_boolean_slot(False)
            trans_ctx.set_element_slots[key] = slot_id
        return slot_id
    
    def _enumerate_transition_variants(self, trans_ctx: TranslatorContext, condition: RHPredicate):
        if condition.operation.as_nondet():
            pass
        elif condition.operation.as_receival():
            for msg in condition.operation.as_receival().messages:
                for process in self._enum_senders(trans_ctx, msg):
                    for instance_ctx in trans_ctx.instance_context.values():
                        if instance_ctx.process.ref == process.ref:
                            yield {
                                condition.ref: instance_ctx.instance.ref
                            }
        elif condition.operation.as_set_empty():
            pass
        elif condition.operation.as_set_has():
            pass
        elif condition.operation.as_conjunction():
            yield from self._enum_transition_variants_conj(trans_ctx, condition.operation.as_conjunction().conjuncts)
        yield dict()

    def _enum_transition_variants_conj(self, trans_ctx: TranslatorContext, conjuncts: List[RHRef]):
        if not conjuncts:
            yield from ()

        conj = conjuncts[0]
        conj_tail = conjuncts[1:]
        
        for variant in self._enumerate_transition_variants(trans_ctx, self._context[conj].as_predicate()):
            for subvariant in self._enum_transition_variants_conj(trans_ctx, conj_tail[1:]):
                yield {
                    *variant,
                    *subvariant
                }

    def _enum_senders(self, trans_ctx: TranslatorContext, msg: RHRef) -> Iterable[RHProcess]:
        for process in trans_ctx.module.processes:
            if process.protocol.out_protocol is not None:
                out_proto = self._context[process.protocol.out_protocol].to_fixed_set()
                if out_proto.has_item(msg):
                    yield process
