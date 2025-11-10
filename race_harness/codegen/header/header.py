import io
import hashlib
from typing import Optional
from race_harness.control_flow import CFModuleInterface, CFModule
from race_harness.codegen.base import BaseCodegen
from race_harness.codegen.payloads import CodegenPayloads

class HeaderCodegen(BaseCodegen):
    def __init__(self, out: io.TextIOBase):
        self._out = out

    def codegen_module(self, module: CFModule, payloads: Optional[CodegenPayloads]):
        self._do_codegen(self._codegen_module_interface, module.interface)

    def _module_interface_signature(self, module_iface: CFModuleInterface) -> str:
        m = hashlib.sha256()
        for instance in module_iface.instances:
            m.update(b'instance')
            m.update(instance.encode())
        for external_action in module_iface.external_actions:
            m.update(b'action')
            m.update(external_action.encode())
        return m.hexdigest()

    def _codegen_module_interface(self, module_iface: CFModuleInterface):
        iface_guard = self._module_interface_signature(module_iface)
        yield f'#ifndef RACE_HARNESS_INTERFACE_{iface_guard}_H_'
        yield f'#define RACE_HARNESS_INTERFACE_{iface_guard}_H_'

        instances = list(module_iface.instances)
        yield 'enum rh_process_instance {'
        yield 1
        for instance in instances:
            yield BaseCodegen.NO_NL
            yield f'RH_PROC_{instance.upper()}'
            yield ','
        yield 'RH_NUM_OF_PROCESSES'
        yield -1
        yield '};'

        yield ''
        for external_action in module_iface.external_actions:
            yield f'extern void {external_action}(enum rh_process_instance, void **);'
        yield ''

        yield '#endif'
        yield ''
