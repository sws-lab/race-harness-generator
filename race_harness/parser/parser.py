import pathlib
import dataclasses
from typing import Optional
import lark
from race_harness.error import RHError
from race_harness.ir import RHContext, RHTransmissionOp, RHExternalActionOp, RHSetAddOp, RHSetDelOp, RHNondetPred, RHSetEmptyPred, RHSetHasPred, RHReceivalPred, RHConjunctionPred, RHEffectBlock, RHPredicate, RHModule
from race_harness.parser.scope import RHScope

SCRIPT_FILEPATH = pathlib.Path(__file__)

@dataclasses.dataclass
class BlockUncondSucc:
    successor: RHEffectBlock

@dataclasses.dataclass
class BlockCondSucc:
    target: RHEffectBlock
    alternative: Optional[RHEffectBlock]
    condition: RHPredicate

class RHInterp(lark.visitors.Interpreter):
    def __init__(self, context: RHContext, scope: RHScope):
        super().__init__()
        self._ctx = context
        self._scopes = [scope]
        self._proto = None
        self._current_block = None
        self._block_succs = None
        self._control_flow = None

    def module(self, tree: lark.Tree):
        protos = dict()
        instances = list()
        for tld in tree.children:
            proc = self.visit(tld)
            if proc[0] is not None:
                type, payload = proc[0]
                if type == 'proto':
                    protos[payload[0]] = payload[1]
                elif type == 'instance':
                    instances.extend(payload)

        processes = list()
        for proto, tree in protos.items():
            proc_scope = RHScope(self._scope)
            self._scopes.append(proc_scope)
            self._proto = proto
            self._block_succs = dict()
            entry_block = self._ctx.new_effect_block()
            self._current_block = entry_block
            self._control_flow = self._ctx.new_control_flow()
            self.visit(tree)
            self._link_blocks()
            processes.append(self._ctx.new_process(proto.ref, entry_block.ref, self._control_flow.ref).ref)
            self._block_succs = None
            self._control_flow = None
            self._proto = None
            self._current_block = None
            self._scopes.pop()

        module = self._ctx.new_module(processes, instances)
        return module

    def enum_decl(self, tree: lark.Tree):
        enum_name = str(tree.children[1])
        refs = list()
        for child in tree.children[3].children:
            name = str(child.children[0])
            ref = self._ctx.new_symbol(name).ref
            self._scope.bind(name, ref)
            refs.append(ref)
        ref = self._ctx.new_fixed_set(enum_name, refs).ref
        self._scope.bind(enum_name, ref)

    def proc_decl(self, tree: lark.Tree):
        decl_name = str(tree.children[1])
        in_proto, out_proto = self.visit(tree.children[2])
        decl = self._ctx.new_protocol(decl_name, in_proto, out_proto)
        self._scope.bind(decl_name, decl.ref)
        return ('proto', (decl, tree.children[3]))

    def proc_protocol_decl(self, tree: lark.Tree):
        in_proto, out_proto = None, None
        if len(tree.children) > 0:
            in_proto = self._scope.resolve(str(tree.children[1]))
            if len(tree.children) > 2:
                out_proto = self._scope.resolve(str(tree.children[3]))
        return (in_proto, out_proto)

    def proc_single_instance(self, tree: lark.Tree):
        instance_name = str(tree.children[1])
        proc_name = str(tree.children[2])
        proc_ref = self._scope.resolve(proc_name)
        instance = self._ctx.new_instance(instance_name, proc_ref)
        self._scope.bind(instance_name, instance.ref)
        return ('instance', [instance.ref])

    def proc_multi_instance(self, tree: lark.Tree):
        instance_name = str(tree.children[1])
        cardinality = int(tree.children[3])
        proc_name = str(tree.children[5])
        proc_ref = self._scope.resolve(proc_name)
        items = list()
        for i in range(cardinality):
            items.append(self._ctx.new_instance(f'{instance_name}{i}', proc_ref).ref)
        ref = self._ctx.new_fixed_set(instance_name, items).ref
        self._scope.bind(instance_name, ref)
        return ('instance', items)

    def compound_stmt(self, tree: lark.Tree):
        scope = RHScope(self._scope)
        self._scopes.append(scope)
        for item in tree.children[1:-1]:
            open_blocks = self.visit(item)
            if open_blocks:
                self._current_block = self._ctx.new_effect_block()
                for block in open_blocks:
                    # block.set_unconditional_successor(self._current_block)
                    self._set_successor(block, self._current_block)
        self._scopes.pop()
        return []
    
    def var_decl_stmt(self, tree: lark.Tree):
        name = self.visit(tree.children[1])
        var_type = self.visit(tree.children[3])
        if var_type[0] == 'set':
            set = self._ctx.new_set(name, var_type[1])
            self._scope.bind(name, set.ref)

    def symbol(self, tree: lark.Tree):
        return str(tree.children[0])
    
    def symbol_set(self, tree: lark.Tree):
        return [
            self.visit(item)
            for item in tree.children[1:-1]
        ]
    
    def set_var_type(self, tree: lark.Tree):
        name = self.visit(tree.children[1])
        ref = self._scope[name]
        return ('set', ref)
    
    def unicast_send_stmt(self, tree: lark.Tree):
        msg_name = self.visit(tree.children[1])
        destination_name = self.visit(tree.children[2])
        msg = self._scope[msg_name]
        destination = self._scope[destination_name]
        self._ctx.add_operation(self._current_block.ref, RHTransmissionOp((destination,), msg))
        next_block = self._ctx.new_effect_block()
        self._set_successor(self._current_block, next_block)
        self._current_block = next_block
    
    def multicast_send_stmt(self, tree: lark.Tree):
        msg_name = self.visit(tree.children[1])
        destination_names = tree.children[3:-1]
        msg = self._scope[msg_name]
        destinations = (
            self._scope[self.visit(destination_name)]
            for destination_name in destination_names
        )
        self._ctx.add_operation(self._current_block.ref, RHTransmissionOp(destinations, msg))
        next_block = self._ctx.new_effect_block()
        self._set_successor(self._current_block, next_block)
        self._current_block = next_block
    
    def action_stmt(self, tree: lark.Tree):
        action_name = str(tree.children[1])
        self._ctx.add_operation(self._current_block.ref, RHExternalActionOp(action_name))
        next_block = self._ctx.new_effect_block()
        self._set_successor(self._current_block, next_block)
        self._current_block = next_block
    
    def loop_stmt(self, tree: lark.Tree):
        loop_head_block = self._ctx.new_effect_block()
        loop_entry_block = self._ctx.new_effect_block()
        loop_tail_block = self._ctx.new_effect_block()

        # self._current_block.set_unconditional_successor(loop_head_block)
        self._set_successor(self._current_block, loop_head_block)
        self._set_successor(loop_head_block, loop_entry_block)
        # self._set_branch(loop_head_block, loop_entry_block, loop_tail_block, self._ctx.new_predicate(RHNondetPred()))
        # loop_head_block.set_conditional_successor(loop_entry_block, loop_tail_block, self._ctx.new_predicate(RHNondetPred()))
        self._current_block = loop_entry_block
        open_blocks = self.visit(tree.children[1])
        if open_blocks:
            for block in open_blocks:
                self._set_successor(block, loop_head_block)
                # block.set_unconditional_successor(loop_head_block)
        else:
            self._set_successor(self._current_block, loop_head_block)
            # self._current_block.set_unconditional_successor(loop_head_block)
        self._current_block = loop_tail_block
    
    def break_stmt(self, tree: lark.Tree):
        label = self.visit(tree.children[1])        
        tail = self._scope[f'snd:{label}']
        self._set_successor(self._current_block, self._ctx[tail])
        # self._current_block.set_unconditional_successor(self._ctx[tail])
        self._current_block = self._ctx.new_effect_block()
    
    def continue_stmt(self, tree: lark.Tree):
        label = self.visit(tree.children[1])        
        head = self._scope[f'fst:{label}']
        self._set_successor(self._current_block, self._ctx[head])
        # self._current_block.set_unconditional_successor(self._ctx[head])
        self._current_block = self._ctx.new_effect_block()
    
    def half_branch_stmt(self, tree: lark.Tree):
        condition_tree = tree.children[1]
        body_tree = tree.children[3]

        self._scopes.append(RHScope(self._scope))
        branch_entry_block = self._ctx.new_effect_block()
        current_block = self._current_block

        condition_pred = self.visit(condition_tree)
        self._set_branch(self._current_block, branch_entry_block, None, condition_pred)
        # self._current_block.set_conditional_successor(branch_entry_block, None, condition_pred)
        self._current_block = branch_entry_block
        
        open_blocks = self.visit(body_tree)
        self._scopes.pop()
        if open_blocks:
            return [*open_blocks, current_block]
        else:
            return [self._current_block, current_block]
    
    def full_branch_stmt(self, tree: lark.Tree):
        condition_tree = tree.children[1]
        then_tree = tree.children[3]
        else_tree = tree.children[5]

        self._scopes.append(RHScope(self._scope))
        condition_pred = self.visit(condition_tree)
        branch_then_entry_block = self._ctx.new_effect_block()
        branch_else_entry_block = self._ctx.new_effect_block()

        self._set_branch(self._current_block, branch_then_entry_block, branch_else_entry_block, condition_pred)
        # self._current_block.set_conditional_successor(branch_then_entry_block, branch_else_entry_block, condition_pred)

        exit_blocks = []
        self._current_block = branch_then_entry_block
        open_blocks = self.visit(then_tree)
        if open_blocks:
            exit_blocks.extend(open_blocks)
        else:
            exit_blocks.append(self._current_block)
        self._scopes.pop()

        self._current_block = branch_else_entry_block
        open_blocks = self.visit(else_tree)
        if open_blocks:
            exit_blocks.extend(open_blocks)
        else:
            exit_blocks.append(self._current_block)

        return exit_blocks
    
    def set_add_stmt(self, tree: lark.Tree):
        set_name = self.visit(tree.children[1])
        value_name = self.visit(tree.children[3])

        set_ref = self._scope[set_name]
        value_ref = self._scope[value_name]
        self._ctx.add_operation(self._current_block.ref, RHSetAddOp(set_ref, value_ref))
    
    def set_del_stmt(self, tree: lark.Tree):
        set_name = self.visit(tree.children[1])
        value_name = self.visit(tree.children[3])

        set_ref = self._scope[set_name]
        value_ref = self._scope[value_name]
        self._ctx.add_operation(self._current_block.ref, RHSetDelOp(set_ref, value_ref))

    def labelled_stmt(self, tree: lark.Tree):
        label = self.visit(tree.children[0])

        head_block = self._ctx.new_effect_block()
        tail_block = self._ctx.new_effect_block()
        self._scopes.append(RHScope(self._scope))
        self._scope.bind(f'fst:{label}', head_block.ref)
        self._scope.bind(f'snd:{label}', tail_block.ref)

        self._set_successor(self._current_block, head_block)
        # self._current_block.set_unconditional_successor(head_block)
        self._current_block = head_block
        open_blocks = self.visit(tree.children[2])
        if open_blocks:
            for block in open_blocks:
                self._set_successor(block, tail_block)
                # block.set_unconditional_successor(tail_block)
        else:
            self._set_successor(self._current_block, tail_block)
            # self._current_block.set_unconditional_successor(tail_block)
        self._scopes.pop()
        self._current_block = tail_block

    def cond_nondet(self, tree: lark.Tree):
        return self._ctx.new_predicate(RHNondetPred())
    
    def cond_single_recv(self, tree: lark.Tree):
        msg_tree = tree.children[1]
        sender = self.visit(tree.children[3]) if len(tree.children) > 2 else None

        msg = self._scope[self.visit(msg_tree)]
        pred = self._ctx.new_predicate(RHReceivalPred((msg,)))
        if sender:
            self._scope.bind(sender, pred.ref)
        return pred
    
    def cond_multi_recv(self, tree: lark.Tree):
        msg_tree = tree.children[1]
        sender = self.visit(tree.children[3]) if len(tree.children) > 2 else None

        msgs = [
            self._scope[msg_name]
            for msg_name in self.visit(msg_tree)
        ]
        pred = self._ctx.new_predicate(RHReceivalPred(msgs))
        if sender:
            self._scope.bind(sender, pred.ref)
        return pred
    
    def cond_set_has(self, tree: lark.Tree):
        set_name = self.visit(tree.children[1])
        value_name = self.visit(tree.children[3])

        set_ref = self._scope[set_name]
        value_ref = self._scope[value_name]
        return self._ctx.new_predicate(RHSetHasPred(set_ref, value_ref))
    
    def cond_set_empty(self, tree: lark.Tree):
        set_name = self.visit(tree.children[1])
        set_ref = self._scope[set_name]
        return self._ctx.new_predicate(RHSetEmptyPred(set_ref))
    
    def cond_and(self, tree: lark.Tree):
        conj = list()
        for i in range(0, len(tree.children), 2):
            conj.append(self.visit(tree.children[i]).ref)
        return self._ctx.new_predicate(RHConjunctionPred(conj))
    
    @property
    def _scope(self) -> RHScope:
        return self._scopes[-1]
    
    def _set_successor(self, block: RHEffectBlock, successor: RHEffectBlock):
        existing = self._block_succs.get(block)
        if existing is not None:
            if isinstance(existing, BlockCondSucc) and existing.alternative is None:
                existing.alternative = successor
            else:
                raise RHError('Internal error in effect block successor graph encoding')
        else:
            self._block_succs[block] = BlockUncondSucc(successor=successor)

    def _set_branch(self, block: RHEffectBlock, target: RHEffectBlock, alternative: Optional[RHEffectBlock], condition: RHPredicate):
        if block in self._block_succs:
            raise RHError('Internal error in effect block successor graph encoding')
        self._block_succs[block] = BlockCondSucc(target=target, alternative=alternative, condition=condition)

    def _link_blocks(self):
        for block, successor in self._block_succs.items():
            if isinstance(successor, BlockUncondSucc):
                self._control_flow.add_unconditional_edge(block, successor.successor)
            elif isinstance(successor, BlockCondSucc):
                if successor.alternative is None:
                    raise RHError('Internal error in effect block successor graph encoding')
                self._control_flow.add_conditional_edge(block, successor.target, successor.alternative, successor.condition)

class RHParser:
    def __init__(self):
        with open(SCRIPT_FILEPATH.parent / 'rh.lark') as grammar_file:
            self._grammar = lark.Lark(grammar_file.read(), start='module')
    
    def parse(self, text: str, context: RHContext) -> RHModule:
        tree = self._grammar.parse(text)
        interp = RHInterp(context, RHScope(None))
        return interp.visit(tree)
