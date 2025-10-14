import io
from typing import Optional, Iterable
from race_harness.error import RHError
from race_harness.ir.ref import RHRef
from race_harness.ir.entities.entity import RHEntity
from race_harness.ir.entities import RHSymbol, RHFixedSet, RHProtocol, RHInstance, RHInstrBlock, RHProcess, RHModule, RHScope

class RHContext:
    def __init__(self):
        self._next_ref = 0
        self._entities = dict()
    
    def new_symbol(self, name: str) -> RHSymbol:
        symbol = RHSymbol(self._new_ref(), name)
        self._add_entity(symbol)
        return symbol
    
    def new_fixed_set(self, name: str, items: Iterable[RHRef]) -> RHFixedSet:
        fixed_set = RHFixedSet(self._new_ref(), name, {
            self._check_ref(item)
            for item in items
        })
        self._add_entity(fixed_set)
        return fixed_set
    
    def new_protocol(self, name: str, in_proto: Optional[RHRef], out_proto: Optional[RHRef]) -> RHProtocol:
        if in_proto:
            self._check_ref(in_proto)
        if out_proto:
            self._check_ref(out_proto)
        decl = RHProtocol(self._new_ref(), name, in_proto, out_proto)
        self._add_entity(decl)
        return decl
    
    def new_instance(self, name: str, proto: RHRef) -> RHInstance:
        instance = RHInstance(self._new_ref(), name, self._check_ref(proto))
        self._add_entity(instance)
        return instance
    
    def new_instr_block(self) -> RHInstrBlock:
        block = RHInstrBlock(self._new_ref())
        self._add_entity(block)
        return block
    
    def new_process(self, proto: RHRef, entry_block: RHRef) -> RHProcess:
        proc = RHProcess(self._new_ref(), self[proto], self[entry_block])
        self._add_entity(proc)
        return proc
    
    def new_scope(self, parent: Optional[RHRef]) -> 'RHScope':
        parent = self[parent].to_scope() if parent else None
        scope = RHScope(self._new_ref(), parent)
        self._add_entity(scope)
        return scope
    
    def new_module(self, processes: Iterable[RHRef], instances: Iterable[RHRef]) -> RHModule:
        processes = (
            self[ref].to_process()
            for ref in processes
        )
        instances = (
            self[ref].to_instance()
            for ref in instances
        )
        module = RHModule(self._new_ref(), processes, instances)
        self._add_entity(module)
        return module
    
    def get(self, ref: RHRef) -> Optional[RHEntity]:
        return self._entities.get(ref)
    
    def __getitem__(self, ref: RHRef) -> RHEntity:
        entity = self.get(ref)
        if entity is None:
            raise RHError(f'Reference {ref} does not belong to the context')
        return entity

    def _new_ref(self) -> RHRef:
        ref = RHRef(uid=self._next_ref, context=self)
        self._next_ref += 1
        return ref
    
    def _check_ref(self, ref: RHRef) -> RHRef:
        if ref not in self._entities:
            raise RHError(f'Reference {ref} does not belong to the context')
        return ref
    
    def _add_entity(self, entity: RHEntity):
        self._entities[entity.ref] = entity
    
    def __str__(self):
        out = io.StringIO()
        for entity in self._entities.values():
            out.write(f'{entity.ref} = {entity}\n')
        return out.getvalue().strip()
