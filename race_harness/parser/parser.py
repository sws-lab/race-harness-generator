import pathlib
from typing import Optional
import lark
from race_harness.ir import RHContext, RHProtocol, RHInstrBlock, RHScope

SCRIPT_FILEPATH = pathlib.Path(__file__)

class RHInterp(lark.visitors.Interpreter):
    def __init__(self, context: RHContext, scope: RHScope, proto: Optional[RHProtocol] = None):
        super().__init__()
        self._ctx = context
        self._scope = scope
        self._proto = proto
        self._instr_block = None

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
            proc_scope = self._ctx.new_scope(self._scope.ref)
            subinterp = RHInterp(self._ctx, proc_scope, proto)
            body = subinterp.visit(tree)
            processes.append(self._ctx.new_process(proto.ref, body.ref).ref)

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
            items.append(self._ctx.new_instance(f'{instance_name}[{i}]', proc_ref).ref)
        ref = self._ctx.new_fixed_set(instance_name, items).ref
        self._scope.bind(instance_name, ref)
        return ('instance', items)

    def _get_instr_block(self) -> RHInstrBlock:
        if self._instr_block is None:
            self._instr_block = self._ctx.new_instr_block()
        return self._instr_block

    def compound_stmt(self, tree: lark.Tree):
        block = self._get_instr_block()
        return block

class RHParser:
    def __init__(self):
        with open(SCRIPT_FILEPATH.parent / 'rh.lark') as grammar_file:
            self._grammar = lark.Lark(grammar_file.read(), start='module')
    
    def parse(self, text: str, context: RHContext):
        tree = self._grammar.parse(text)
        interp = RHInterp(context, context.new_scope(None))
        return interp.visit(tree)
