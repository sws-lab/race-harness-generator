import abc
import io
import dataclasses
from typing import Optional, Union, Iterable
from race_harness.error import RHError
from race_harness.ir.ref import RHRef
from race_harness.ir.entities.entity import RHEntity
from race_harness.ir.entities.block import RHEffectBlock
from race_harness.ir.entities.predicate import RHPredicate

class RHControlFlowEdge(abc.ABC):
    @property
    @abc.abstractmethod
    def successors(self) -> Iterable[RHEffectBlock]:
        pass

@dataclasses.dataclass
class RHUnconditionalControlFlowEdge(RHControlFlowEdge):
    target: RHEffectBlock

    @property
    def successors(self) -> Iterable[RHEffectBlock]:
        yield self.target

@dataclasses.dataclass
class RHConditionalControlFlowEdge(RHControlFlowEdge):
    target: RHEffectBlock
    alternative: RHEffectBlock
    condition: RHPredicate

    @property
    def successors(self) -> Iterable[RHEffectBlock]:
        yield self.target
        yield self.alternative

class RHControlFlow(RHEntity):
    def __init__(self, ref: RHRef):
        super().__init__(ref)
        self._edges = dict()
        self._reverse_edges = dict()

    def as_control_flow(self):
        return self

    def add_unconditional_edge(self, source: RHEffectBlock, target: RHEffectBlock):
        if source.ref in self._edges:
            raise RHError(f'Control flow edge for {source.ref} has already been defined')
        self._edges[source.ref] = RHUnconditionalControlFlowEdge(target=target)
        self._register_reverse(source, target)
    
    def add_conditional_edge(self, source: RHEffectBlock, target: RHEffectBlock, alternative: RHEffectBlock, condition: RHPredicate):
        if source.ref in self._edges:
            raise RHError(f'Control flow edge for {source.ref} has already been defined')
        self._edges[source.ref] = RHConditionalControlFlowEdge(target=target, alternative=alternative, condition=condition)
        self._register_reverse(source, target)
        self._register_reverse(source, alternative)

    def drop_edge(self, source: RHRef):
        if source in self._edges:
            edge = self._edges[source]
            for successor in edge.successors:
                self._reverse_edges[successor.ref].remove(source)
            del self._edges[source]

    def edge_from(self, source: RHRef) -> Optional[Union[RHUnconditionalControlFlowEdge, RHConditionalControlFlowEdge]]:
        return self._edges.get(source, None)
    
    def edges_to(self, target: RHRef) -> Iterable[RHRef]:
        yield from self._reverse_edges.get(target, ())

    @property
    def edges(self) -> Iterable[RHControlFlowEdge]:
        yield from self._edges.values()

    def _register_reverse(self, source: RHEffectBlock, target: RHEffectBlock):
        if target.ref not in self._reverse_edges:
            self._reverse_edges[target.ref] = set()
        self._reverse_edges[target.ref].add(source.ref)
    
    def __getitem__(self, source: RHRef) -> Union[RHUnconditionalControlFlowEdge, RHConditionalControlFlowEdge]:
        edge = self.edge_from(source)
        if edge is None:
            raise RHError(f'Unable to find control flow edge for block {source}')
        return edge

    def __str__(self):
        out = io.StringIO()
        out.write('control_flow')
        if self._edges:
            out.write(' {\n')
            for source, edge in self._edges.items():
                if isinstance(edge, RHUnconditionalControlFlowEdge):
                    out.write(f'  {source} -> {edge.target.ref}\n')
                else:
                    out.write(f'  {source} -> {edge.target.ref} if {edge.condition.ref} else {edge.alternative.ref}\n')
            out.write('}')
        return out.getvalue()
