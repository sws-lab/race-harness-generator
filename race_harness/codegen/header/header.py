import io
import string
import random
from race_harness.control_flow import CFModuleInterface, CFModule

class HeaderCodegen:
    NO_NL = object()

    def __init__(self, out: io.TextIOBase):
        self._out = out

    def codegen_module(self, module: CFModule):
        self._do_codegen(self._codegen_module_interface, module.interface)

    def _do_codegen(self, callback, *args, **kwargs):
        indent = 0
        skip_newline = False
        indent_next = True
        for entry in callback(*args, **kwargs):
            if isinstance(entry, int):
                indent += entry
            elif entry == HeaderCodegen.NO_NL:
                skip_newline = True
            else:
                lines = entry.split('\n')
                for idx, line in enumerate(lines):
                    if indent_next:
                        self._out.write(indent * '  ')
                    else:
                        indent_next = True
                    self._out.write(line)
                    if not skip_newline or idx + 1 < len(lines):
                        self._out.write('\n')
                    else:
                        indent_next = False
                skip_newline = False

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
                yield HeaderCodegen.NO_NL
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
