import itertools
from race_harness.ir import RHRef, RHControlFlow, RHContext
from race_harness.ir.util.reachability import rh_block_reachability

class RHControlFlowDominators:
    def __init__(self, context: RHContext):
        self._ctx = context
        self._doms = dict()

    def build(self, entry_ref: RHRef, control_flow: RHControlFlow):
        self._doms = {
            entry_ref: {entry_ref}
        }
        blocks = list(rh_block_reachability(control_flow, self._ctx[entry_ref].to_effect_block()))
        for block in blocks:
            if block.ref != entry_ref:
                self._doms[block.ref] = {
                    block.ref
                    for block in blocks
                }

        fixpoint_reached = False
        while not fixpoint_reached:
            fixpoint_reached = True

            for block in blocks:
                if block.ref == entry_ref:
                    continue

                block_doms = {
                    block.ref
                    for block in blocks
                }
                for pred in control_flow.edges_to(block.ref):
                    if pred_doms := self._doms.get(pred):
                        block_doms.intersection_update(pred_doms)
                block_doms = block_doms.union((block.ref,))

                if block_doms.symmetric_difference(self._doms[block.ref]):
                    self._doms[block.ref] = block_doms
                    fixpoint_reached = False

    def __getitem__(self, ref: RHRef):
        return self._doms[ref]
