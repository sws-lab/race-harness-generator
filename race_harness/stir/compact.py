import copy
from race_harness.stir.transition import STTransition
from race_harness.stir.module import STModule

class STTransitionHandle:
    def __init__(self, transition: STTransition):
        self._transition = transition

    @property
    def transition(self) -> STTransition:
        return self._transition
    
    def __hash__(self):
        res = 31 * hash(self.transition.node_slot) + \
            29 * hash(self.transition.source_node_id) + \
            23 * hash(self.transition.target_node_id) + \
            17 * hash(self.transition.invert_guard)
        for guard in self.transition.guards:
            if int_guard := guard.as_int():
                res = res * 13 + 7 * hash(int_guard.slot_id) + 3 * hash(int_guard.value)
        for instr in self.transition.instructions:
            if ext_act := instr.as_external_action():
                res = 13 * res + 7 * hash(ext_act.action)
            elif set_int := instr.as_set_int():
                res = 13 * res + 7 * hash(set_int.slot_id) + 3 * hash(set_int.value)

        return res
    
    def __eq__(self, value):
        if not isinstance(value, STTransitionHandle):
            return False
        
        if self.transition.node_slot != value.transition.node_slot:
            return False
        
        if self.transition.source_node_id != value.transition.source_node_id:
            return False
        
        if self.transition.target_node_id != value.transition.target_node_id:
            return False
        
        if self.transition.invert_guard != value.transition.invert_guard:
            return False
        
        def match_guards(tr1: STTransition, tr2: STTransition):
            for guard in tr1.guards:
                found = False
                for guard2 in tr2.guards:
                    if guard.as_int() and guard2.as_int() and \
                        guard.as_int().slot_id == guard2.as_int().slot_id and \
                        guard.as_int().value == guard2.as_int().value:
                        found = True
                        break
                if not found:
                    return False
            return True
        
        def match_instr(tr1: STTransition, tr2: STTransition):
            for instr in tr1.instructions:
                found = False
                for instr2 in tr2.instructions:
                    if instr.as_external_action() and instr2.as_external_action() and \
                        instr.as_external_action().action == instr2.as_external_action().action:
                        found = True
                        break
                    elif instr.as_set_int() and instr2.as_set_int() and \
                        instr.as_set_int().slot_id == instr2.as_set_int().slot_id and \
                        instr.as_set_int().value == instr2.as_set_int().value:
                        found = True
                        break
                if not found:
                    return False
            return True
        
        if not match_guards(value.transition, self.transition) or \
            not match_guards(self.transition, value.transition) or \
            not match_instr(value.transition, self.transition) or \
            not match_instr(self.transition, value.transition):
            return False
        
        return True
        

def compact_st_module(module: STModule):
    comapcted_module = copy.deepcopy(module)
    comapcted_module._transitions.clear()

    index = dict()
    for transition in module.transitions:
        handle = STTransitionHandle(transition)
        if handle not in index:
            index[handle] = transition.identifier

            copy_trans = comapcted_module.new_transition(
                transition.node_slot,
                transition.source_node_id,
                transition.target_node_id,
                transition.invert_guard
            )
            for guard in transition.guards:
                copy_trans.add_guard(copy.deepcopy(guard))
            for instr in transition.instructions:
                copy_trans.add_instruction(copy.deepcopy(instr))
    return comapcted_module