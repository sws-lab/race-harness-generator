from typing import Iterable, List, Optional
from race_harness.ir.ref import RHRef
from race_harness.ir.entities.entity import RHEntity
from race_harness.ir.entities.instance import RHInstance
from race_harness.ir.entities.process import RHProcess
from race_harness.ir.entities.protocol import RHProtocol

class RHModule(RHEntity):
    def __init__(self, ref: RHRef, processes: Iterable[RHProcess], instances: Iterable[RHInstance]):
        super().__init__(ref, None)
        self._processes = list(processes)
        self._instances = list(instances)

    def as_module(self):
        return self

    @property
    def processes(self) -> List[RHProcess]:
        return self._processes
    
    @property
    def instances(self) -> List[RHInstance]:
        return self._instances
    
    def find_process_for(self, protocol_ref: RHRef) -> Optional[RHProcess]:
        for process in self.processes:
            if process.protocol.ref == protocol_ref:
                return process
        return None

    def __str__(self):
        return 'module proc [{}] instance [{}]'.format(
            ', '.join(
                str(proc.ref)
                for proc in self._processes
            ),
            ', '.join(
                str(inst.ref)
                for inst in self._instances
            )
        )
