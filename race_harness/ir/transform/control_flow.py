from race_harness.ir.ref import RHRef
from race_harness.ir.entities import RHControlFlow, RHModule, RHEffectBlock, RHUnconditionalControlFlowEdge, RHConditionalControlFlowEdge
from race_harness.ir.context import RHContext

def optimize_block_control_flow(context: RHContext, control_flow: RHControlFlow, entry_point: RHEffectBlock):
    fixpoint = False
    while not fixpoint:
        fixpoint = True
        visisted = set()
        queue = [entry_point]
        while queue:
            block = queue.pop()
            if block in visisted:
                continue
            visisted.add(block)

            out_edge = control_flow.edge_from(block.ref)
            if out_edge is not None:
                queue.extend(out_edge.successors)

            drop_block = False
            if block.is_empty:
                for source_ref in list(control_flow.edges_to(block.ref)):
                    source_block = context[source_ref].to_effect_block()
                    in_edge = control_flow.edge_from(source_ref)
                    if isinstance(in_edge, RHUnconditionalControlFlowEdge) and out_edge is None:
                        control_flow.drop_edge(source_ref)
                        drop_block = True
                    elif isinstance(in_edge, RHUnconditionalControlFlowEdge) and isinstance(out_edge, RHUnconditionalControlFlowEdge):
                        control_flow.drop_edge(source_ref)
                        control_flow.add_unconditional_edge(source_block, out_edge.target)
                        drop_block = True
                    elif isinstance(in_edge, RHUnconditionalControlFlowEdge) and isinstance(out_edge, RHConditionalControlFlowEdge):
                        control_flow.drop_edge(source_ref)
                        control_flow.add_conditional_edge(source_block, out_edge.target, out_edge.alternative, out_edge.condition)
                        drop_block = True
                    elif isinstance(in_edge, RHConditionalControlFlowEdge) and isinstance(out_edge, RHUnconditionalControlFlowEdge):
                        if in_edge.target.ref == block.ref:
                            control_flow.drop_edge(source_ref)
                            control_flow.add_conditional_edge(source_block, out_edge.target, in_edge.alternative, in_edge.condition)
                            drop_block = True
                        elif in_edge.alternative.ref == block.ref:
                            control_flow.drop_edge(source_ref)
                            control_flow.add_conditional_edge(source_block, in_edge.target, out_edge.target, in_edge.condition)
                            drop_block = True

            if drop_block:
                fixpoint = False
                if block.ref != entry_point.ref:
                    control_flow.drop_edge(block.ref)
                    context.drop_entity(block.ref)

def optimize_module_control_flow(context: RHContext, module: RHModule):
    for process in module.processes:
        optimize_block_control_flow(context, process.control_flow, process.entry_block)
