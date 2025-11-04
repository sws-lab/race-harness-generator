import io
from race_harness.control_flow import CFModule, CFNode
from race_harness.codegen.base import BaseCodegen

class GoblintLBECodegen(BaseCodegen):
    def __init__(self, out: io.TextIOBase):
        self._out = out

    def codegen_module(self, module: CFModule):
        self._do_codegen(self._codegen_module, module)
    
    def _codegen_module(self, module: CFModule):
        yield '''
#include <stdlib.h>
#include <stdio.h>
#include <pthread.h>
'''

        has_mutexes = False
        for mutex in module.mutexes:
            yield f'static pthread_mutex_t mtx{mutex.mutex_id};'
            has_mutexes = True
        if has_mutexes:
            yield ''

        yield 'static _Atomic unsigned int init_barrier = 0;'
        yield f'#define INIT_BARRIER_CAPACITY {len(module.procedures)}'
        yield ''

        for procedure_name, procedure_body in module.procedures.items():
            yield f'static void *{procedure_name}(void *arg) {{'
            yield 1
            yield '(void) arg;'
            yield ''
            yield from self._codegen_node(module, procedure_name, procedure_body, top_level_node=True)
            yield 'return NULL;'
            yield -1
            yield '}'
            yield ''

        yield 'int main(int argv, const char **argc) {'
        yield 1
        yield '(void) argv;'
        yield '(void) argc;'
        yield ''

        has_mutexes = False
        for mutex in module.mutexes:
            yield f'pthread_mutex_init(&mtx{mutex.mutex_id}, NULL);'
            has_mutexes = True

        if has_mutexes:
            yield ''

        has_processes = False
        for procedure_name, procedure_body in module.procedures.items():
            yield f'pthread_t {procedure_name}_process;'
            has_processes = True

        if has_processes:
            yield ''

        for procedure_name, procedure_body in module.procedures.items():
            yield f'pthread_create(&{procedure_name}_process, NULL, {procedure_name}, NULL);'

        if has_processes:
            yield ''


        for procedure_name, procedure_body in module.procedures.items():
            yield f'pthread_join({procedure_name}_process, NULL);'

        yield 'return EXIT_SUCCESS;'
        yield -1
        yield '}'

    def _codegen_node(self, module: CFModule, procedure_name: str, node: CFNode, *, top_level_node: bool = False):
        if stmt := node.as_statement():
            yield f'{stmt.action}({procedure_name.upper()});'
        elif seq := node.as_sequence():
            if not top_level_node:
                yield '{'
                yield 1
            for item in seq.sequence:
                yield from self._codegen_node(module, procedure_name, item)
            if not top_level_node:
                yield -1
                yield '}'
        elif label := node.as_labelled():
            yield BaseCodegen.NO_NL
            yield f'label{label.label.label_id}: '
            yield from self._codegen_node(module, procedure_name, label.node)
        elif goto := node.as_goto():
            yield f'goto label{goto.label.label_id};'
        elif branch := node.as_branch():
            for idx, item in enumerate(branch.branches):
                if idx == 0:
                    if len(branch.branches) > 1:
                        yield BaseCodegen.NO_NL
                        yield f'if (random() % {len(branch.branches) - idx} == 0) '
                        yield from self._codegen_node(module, procedure_name, item)
                    else:
                        yield from self._codegen_node(module, procedure_name, item)
                elif idx + 1 < len(branch.branches):
                    yield BaseCodegen.NO_NL
                    yield f'else if (random() % {len(branch.branches) - idx} == 0) '
                    yield from self._codegen_node(module, procedure_name, item)
                else:
                    yield BaseCodegen.NO_NL
                    yield 'else '
                    yield from self._codegen_node(module, procedure_name, item)
        elif node.as_return():
            yield 'return NULL;'
        elif sync := node.as_synchronization():
            for unlock in sorted(sync.lock_mutexes):
                yield f'pthread_mutex_lock(&mtx{unlock.mutex_id});'
            for unlock in reversed(sorted(sync.unlock_mutexes)):
                yield f'pthread_mutex_unlock(&mtx{unlock.mutex_id});'
        elif node.as_init_barrier():
            yield 'init_barrier++;'
            yield 'while (init_barrier < INIT_BARRIER_CAPACITY) {}'