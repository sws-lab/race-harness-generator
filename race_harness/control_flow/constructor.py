import dataclasses
from typing import Dict, Iterable, Optional, Tuple
from race_harness.control_flow.node import CFSequence, CFStatement, CFLabelID, CFReturn, CFGoto, CFBranch, CFLabelledNode, CFInitBarrier, CFModule, CFMutexID, CFSynchronization, CFModuleInterface
from race_harness.ir import RHModule, RHContext, RHInstance, RHProcess, RHEffectBlock, RHRef
from race_harness.ir.mutex import RHMutualExclusion
from race_harness.error import RHError

@dataclasses.dataclass
class ModuleConstructionState:
    module: RHModule
    cf_module: CFModule

    mutexes: Dict[Tuple[RHRef, RHRef, RHRef, RHRef], CFMutexID]

@dataclasses.dataclass
class InstanceConstructionState:
    process: RHProcess
    instance: RHInstance

    block_label_map: Dict[RHRef, CFLabelID]
    labels: Dict[CFLabelID, CFLabelledNode]
    top_level_sequence: CFSequence

class CFConstructor:
    def __init__(self, rh_context: RHContext, mutual_exclusion: RHMutualExclusion):
        self._rh_context = rh_context
        self._mutual_exclusion = mutual_exclusion

    def construct_module(self, module: RHModule) -> CFModule:
        module_state = ModuleConstructionState(
            module=module,
            cf_module=CFModule(dict()),
            mutexes=dict()
        )
        for instance in module.instances:
            self._construct_instance(module_state, instance)
        return module_state.cf_module
    
    def _construct_synchronization(self, current_locks: Iterable[CFMutexID], required_locks: Iterable[CFMutexID], rollback: Optional[CFLabelID]):
        current_lockset = set(current_locks)
        required_lockset = set(required_locks)

        return CFSynchronization(
            lock=required_lockset.difference(current_lockset),
            unlock=current_lockset.difference(required_lockset),
            rollback=rollback
        )

    def _required_locks(self, module_state: ModuleConstructionState, instance: RHInstance, block: RHEffectBlock) -> Iterable[CFMutexID]:
        for other_instance, other_block in self._mutual_exclusion.get_all_mutually_exclusive_blocks(module_state.module, instance, block):
            min_instance_ref = min(instance.ref, other_instance.ref)
            max_instance_ref = max(instance.ref, other_instance.ref)
            min_block_ref = block.ref if min_instance_ref == instance.ref else other_block.ref
            max_block_ref = block.ref if max_instance_ref == instance.ref else other_block.ref
            key = (min_instance_ref, min_block_ref, max_instance_ref, max_block_ref)
            mutex = module_state.mutexes.get(key, None)
            if mutex is None:
                mutex = module_state.cf_module.new_mutex()
                module_state.mutexes[key] = mutex
            yield mutex

    def _construct_instance(self, module_state: ModuleConstructionState, instance: RHInstance):
        process = module_state.module.find_process_for(instance.protocol.ref)
        if process is None:
            raise RHError(f'Unable to find process for instance {instance.ref}')
        
        instance_state = InstanceConstructionState(
            process=process,
            instance=instance,
            block_label_map=dict(),
            labels=dict(),
            top_level_sequence=CFSequence(())
        )
        entry_label = self._construct_block(module_state, instance_state, process.entry_block)
        module_state.cf_module.interface.declare_instance(instance.label)

        prologue = CFSequence(())
        prologue.add_node(self._construct_synchronization((), self._required_locks(module_state, instance, process.entry_block), None))
        prologue.add_node(CFInitBarrier())
        prologue.add_node(CFGoto(entry_label))
        prologue.add_node(instance_state.top_level_sequence)

        module_state.cf_module.add_procedure(instance.label, process.label, prologue)
    
    def _construct_block(self, module_state: ModuleConstructionState, instance_state: InstanceConstructionState, block: RHEffectBlock) -> CFLabelledNode:
        if block.ref in instance_state.block_label_map:
            return instance_state.block_label_map[block.ref]
        
        label = module_state.cf_module.new_label()
        instance_state.block_label_map[block.ref] = label

        cf_seq = CFSequence(())
        for op in block.content:
            if ext_act := op.as_external_action():
                cf_seq.add_node(CFStatement(ext_act.external_action))
                module_state.cf_module.interface.declare_external_action(ext_act.external_action)

        edge = instance_state.process.control_flow.edge_from(block.ref)
        successor_labels = [
            (successor, self._construct_block(module_state, instance_state, successor))
            for successor in edge.successors
        ] if edge else list()
        if len(successor_labels) == 0:
            cf_seq.add_node(CFReturn())
        elif len(successor_labels) == 1:
            cf_seq.add_node(self._construct_synchronization(
                self._required_locks(module_state, instance_state.instance, block),
                self._required_locks(module_state, instance_state.instance, successor_labels[0][0]), None))
            cf_seq.add_node(CFGoto(successor_labels[0][1]))
        else:
            branches_label = module_state.cf_module.new_label()
            branches = list()
            for succ, succ_label in successor_labels:
                branch = CFSequence(())
                branch.add_node(self._construct_synchronization(
                    self._required_locks(module_state, instance_state.instance, block),
                    self._required_locks(module_state, instance_state.instance, succ), branches_label))
                branch.add_node(CFGoto(succ_label))
                branches.append(branch)
            cf_seq.add_node(CFLabelledNode(branches_label, CFBranch(
                branches
            )))

        block_node = CFLabelledNode(label, cf_seq)
        instance_state.labels[label] = block_node
        instance_state.top_level_sequence.add_node(block_node)
        return label
