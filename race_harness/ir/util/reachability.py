from typing import Iterable
from race_harness.ir.entities import RHEffectBlock, RHControlFlow, RHProcess

def rh_block_reachability(control_flow: RHControlFlow, block: RHEffectBlock) -> Iterable[RHEffectBlock]:
    visited = set()
    queue = [block]
    while queue:
        block = queue.pop()
        if block.ref in visited:
            continue
        visited.add(block.ref)
        yield block

        edge = control_flow.edge_from(block.ref)
        if edge:
            queue.extend(edge.successors)


def rh_process_reachable_blocks(process: RHProcess) -> Iterable[RHEffectBlock]:
    yield from rh_block_reachability(process.control_flow, process.entry_block)
