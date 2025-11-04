import io
import string
import random
from race_harness.control_flow import CFModuleInterface, CFModule
from race_harness.codegen.base import BaseCodegen

class HeaderCodegen(BaseCodegen):
    def __init__(self, out: io.TextIOBase):
        self._out = out

    def codegen_module(self, module: CFModule):
        self._do_codegen(self._codegen_module_interface, module.interface)

    def _codegen_module_interface(self, module_iface: CFModuleInterface):
        iface_guard = ''.join(random.choices(string.ascii_uppercase, k=16))
        yield f'#ifndef RACE_HARNESS_INTERFACE_{iface_guard}_H_'
        yield f'#define RACE_HARNESS_INTERFACE_{iface_guard}_H_'

        instances = list(module_iface.instances)
        for idx, instance in enumerate(instances):
            if idx == 0:
                yield ''
                yield 'enum rh_process_instance {'
                yield 1
                
            if idx + 1 < len(instances):
                yield BaseCodegen.NO_NL
                yield instance.upper()
                yield ','
            else:
                yield instance.upper()
        if instances:
            yield -1
            yield '};'

        yield ''
        for external_action in module_iface.external_actions:
            yield f'extern void {external_action}(enum rh_process_instance);'
        yield ''

        yield '#endif'
        yield ''
