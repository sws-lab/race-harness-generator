import io
from typing import Iterable, Optional
from race_harness.stir.state import STState, STSlotID
from race_harness.stir.node import STNodeID
from race_harness.stir.transition import STTransition, STTransitionID
from race_harness.error import RHError

class STModule:
    def __init__(self):
        self._nodes = set()
        self._transitions = dict()
        self._state = STState()

    def new_node(self) -> STNodeID:
        node = STNodeID(len(self._nodes))
        self._nodes.add(node)
        return node

    def new_transition(self, node_slot: STSlotID, source_node: STNodeID, target_node: STNodeID, invert_guard: bool) -> STTransition:
        trans_id = STTransitionID(len(self._transitions))
        trans = STTransition(trans_id, node_slot, source_node, target_node, invert_guard)
        self._transitions[trans_id] = trans
        return trans
    
    @property
    def nodes(self) -> Iterable[STNodeID]:
        yield from self._nodes
    
    @property
    def transitions(self) -> Iterable[STTransition]:
        yield from self._transitions.values()

    @property
    def state(self) -> STState:
        return self._state

    def get_transition(self, transiton_id: STTransitionID) -> Optional[STTransition]:
        return self._transitions.get(transiton_id, None)
    
    def __getitem__(self, transition_id: STTransitionID) -> STTransition:
        transition = self.get_transition(transition_id)
        if transition is None:
            raise RHError(f'Unable to find transition {transition_id} in module')
        return transition
    
    def __len__(self) -> int:
        return len(self._transitions)
    
    def __iter__(self) -> Iterable[STTransition]:
        yield from self._transitions.values()
    
    def __str__(self):
        out = io.StringIO()
        out.write(str(self.state))
        out.write('\n')
        for transition in self.transitions:
            out.write(f'{transition.identifier} = {transition}\n')
        return out.getvalue()
