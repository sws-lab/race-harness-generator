import abc

class BaseCodegen(abc.ABC):
    NO_NL = object()

    def _do_codegen(self, callback, *args, **kwargs):
        indent = 0
        skip_newline = False
        indent_next = True
        for entry in callback(*args, **kwargs):
            if isinstance(entry, int):
                indent += entry
            elif entry == BaseCodegen.NO_NL:
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
