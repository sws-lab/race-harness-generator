from typing import Iterable
from race_harness.ir.ref import RHRef
from race_harness.ir.context import RHContext
from race_harness.ir.entities import RHInstance, RHModule, RHEffectBlock
from race_harness.ir.util import rh_process_reachable_blocks
from race_harness.error import RHError

class RHMutualInclusion:
    def __init__(self):
        self._mutual_inclusion = set()

    def add_cooccuring_states(self, instance1_ref: RHRef, block1_ref: RHRef, instance2_ref: RHRef, block2_ref: RHRef):
        key1 = (instance1_ref, block1_ref)
        key2 = (instance2_ref, block2_ref)
        min_key = min(key1, key2)
        max_key = max(key1, key2)
        self._mutual_inclusion.add((min_key, max_key))

    def is_cooccuring(self, instance1_ref: RHRef, block1_ref: RHRef, instance2_ref: RHRef, block2_ref: RHRef) -> bool:
        key1 = (instance1_ref, block1_ref)
        key2 = (instance2_ref, block2_ref)
        min_key = min(key1, key2)
        max_key = max(key1, key2)
        return (min_key, max_key) in self._mutual_inclusion

class RHMutualExclusion:
    def __init__(self, context: RHContext, mutinc: RHMutualInclusion):
        self._context = context
        self._mutinc = mutinc

    def get_mutually_exclusive_blocks(self, module: RHModule, instance1: RHInstance, block1: RHEffectBlock, instance2: RHInstance) -> Iterable[RHEffectBlock]:
        process2 = module.find_process_for(instance2.protocol.ref)
        if process2 is None:
            raise RHError(f'Unable to find process for instance {instance2.ref}')
        
        for block2 in rh_process_reachable_blocks(process2):
            if not self._mutinc.is_cooccuring(instance1.ref, block1.ref, instance2.ref, block2.ref):
                yield block2

    def get_all_mutually_exclusive_blocks(self, module: RHModule, instance: RHInstance, block: RHEffectBlock) -> Iterable[tuple[RHInstance, RHEffectBlock]]:
        for other_instance in module.instances:
            if instance.ref != other_instance.ref:
                for other_block in self.get_mutually_exclusive_blocks(module, instance, block, other_instance):
                    yield other_instance, other_block
