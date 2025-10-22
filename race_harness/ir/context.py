import io
from typing import Optional, Iterable
from race_harness.error import RHError
from race_harness.ir.ref import RHRef
from race_harness.ir.entities.entity import RHEntity
from race_harness.ir.entities import RHSymbol, RHFixedSet, RHProtocol, RHInstance, RHEffectBlock, RHProcess, RHModule, RHSet, RHPredicate, RHPredicateOp, RHOperation, RHControlFlow

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
        instance = RHInstance(self._new_ref(), name, self[proto].to_protocol())
        self._add_entity(instance)
        return instance
    
    def new_effect_block(self) -> RHEffectBlock:
        block = RHEffectBlock(self._new_ref())
        self._add_entity(block)
        return block
    
    def add_operation(self, block: RHRef, operation: RHOperation):
        self[block].to_effect_block().add_operation(operation)

    def new_predicate(self, predicate_op: RHPredicateOp) -> RHPredicate:
        predicate = RHPredicate(self._new_ref(), predicate_op)
        self._add_entity(predicate)
        return predicate
    
    def new_process(self, proto: RHRef, entry_block: RHRef, control_flow: RHRef) -> RHProcess:
        proc = RHProcess(self._new_ref(), self[proto].to_protocol(), self[entry_block].to_effect_block(), self[control_flow].to_control_flow())
        self._add_entity(proc)
        return proc
    
    def new_control_flow(self) -> RHControlFlow:
        control_flow = RHControlFlow(self._new_ref())
        self._add_entity(control_flow)
        return control_flow
    
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
    
    def new_set(self, name: str, domain: RHRef) -> RHSet:
        set = RHSet(self._new_ref(), name, self._check_ref(domain))
        self._add_entity(set)
        return set
    
    def drop_entity(self, ref: RHRef):
        if ref not in self._entities:
            raise RHError(f'Reference {ref} does not belong to the context')
        del self._entities[ref]
    
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
