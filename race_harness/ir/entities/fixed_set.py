from typing import Iterable
from race_harness.ir.ref import RHRef
from race_harness.ir.entities.entity import RHEntity

class RHFixedSet(RHEntity):
    def __init__(self, ref: RHRef, label: str, items: Iterable[RHRef]):
        super().__init__(ref, label)
        self._items = list(items)

    def as_fixed_set(self):
        return self

    @property
    def items(self) -> Iterable[RHRef]:
        yield from self._items

    def has_item(self, item: RHRef) -> bool:
        return item in self._items

    def __iter__(self) -> Iterable[RHRef]:
        yield from self.items

    def __str__(self):
        return 'fixedset {} {{{}}}'.format(
            self.label,
            ', '.join(str(item) for item in self._items)
        )
