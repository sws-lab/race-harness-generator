import io
from typing import Optional
from race_harness.error import RHError
from race_harness.ir.ref import RHRef
from race_harness.ir.entities.entity import RHEntity

class RHScope(RHEntity):
    def __init__(self, ref: RHRef, parent: Optional['RHScope']):
        super().__init__(ref)
        self._parent = parent
        self._bindings = dict()

    def as_scope(self):
        return self
    
    @property
    def parent(self) -> Optional['RHScope']:
        return self._parent
    
    def bind(self, name: str, ref: RHRef):
        if name in self._bindings:
            raise RHError(f'Scope already contains bindings {name}')
        self._bindings[name] = ref

    def try_resolve(self, name: str) -> Optional[RHRef]:
        ref = self._bindings.get(name, None)
        if ref is None and self.parent is not None:
            ref = self._parent.try_resolve(name)
        return ref
    
    def resolve(self, name: str) -> RHRef:
        ref = self.try_resolve(name)
        if ref is None:
            raise RHError(f'Unable to find binding {name} is scope')
        return ref

    def __str__(self):
        out = io.StringIO()
        if self._bindings:
            out.write('scope{} {{\n'.format(f' {self.parent.ref}' if self.parent is not None else ''))
            for name, ref in self._bindings.items():
                out.write(f'  {name}: {ref}\n')
            out.write('}')
        else:
            out.write('scope{}'.format(f' {self.parent.ref}' if self.parent is not None else ''))
        return out.getvalue().strip()