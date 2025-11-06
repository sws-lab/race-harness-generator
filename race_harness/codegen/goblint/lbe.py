import io
from race_harness.control_flow import CFModule, CFNode
from race_harness.codegen.base import BaseCodegen

class GoblintLBECodegen(BaseCodegen):
    def __init__(self, out: io.TextIOBase, *, userspace: bool = True):
        self._out = out
        self._userspace = userspace

    def codegen_module(self, module: CFModule):
        self._do_codegen(self._codegen_module, module)
    
    def _codegen_module(self, module: CFModule):
        if self._userspace:
            yield '''
#include <stdlib.h>
#include <pthread.h>

#define __harness_NULL NULL
#define __harness_EXIT_SUCCESS EXIT_SUCCESS

typedef pthread_t __harness_thread_t;
typedef pthread_mutex_t __harness_mutex_t;

#define __harness_thread_create(_thread, _attr, _entry, _param) pthread_create((_thread), (_attr), (_entry), (_param))
#define __harness_thread_join(_thread, _result) pthread_join((_thread), (_result))
#define __harness_mutex_init(_mutex, _attr) pthread_mutex_init((_mutex), (_attr))
#define __harness_mutex_lock(_mutex) pthread_mutex_lock((_mutex))
#define __harness_mutex_unlock(_mutex) pthread_mutex_unlock((_mutex))
#define __harness_rand() random()
'''
        else:
            yield '''
#define __harness_NULL ((void *) 0)
#define __harness_EXIT_SUCCESS 0

typedef unsigned int __harness_thread_t;
typedef unsigned int __harness_mutex_t;

extern void __harness_thread_create(__harness_thread_t *, void *, void *(*)(void *), void *);
extern void __harness_thread_join(__harness_thread_t, void **);
extern void __harness_mutex_init(__harness_mutex_t *, void *);
extern void __harness_mutex_lock(__harness_mutex_t *);
extern void __harness_mutex_unlock(__harness_mutex_t *);
extern int __harness_rand(void);
'''
            

        has_mutexes = False
        for mutex in module.mutexes:
            yield f'static __harness_mutex_t mtx{mutex.mutex_id};'
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
            yield 'void *payload = __harness_NULL;'
            yield ''
            yield from self._codegen_node(module, procedure_name, procedure_body, top_level_node=True)
            yield 'return __harness_NULL;'
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
            yield f'__harness_mutex_init(&mtx{mutex.mutex_id}, __harness_NULL);'
            has_mutexes = True

        if has_mutexes:
            yield ''

        has_processes = False
        for procedure_name, procedure_body in module.procedures.items():
            yield f'__harness_thread_t {procedure_name}_process;'
            has_processes = True

        if has_processes:
            yield ''

        for procedure_name, procedure_body in module.procedures.items():
            yield f'__harness_thread_create(&{procedure_name}_process, __harness_NULL, {procedure_name}, __harness_NULL);'

        if has_processes:
            yield ''


        for procedure_name, procedure_body in module.procedures.items():
            yield f'__harness_thread_join({procedure_name}_process, __harness_NULL);'

        yield 'return __harness_EXIT_SUCCESS;'
        yield -1
        yield '}'

    def _codegen_node(self, module: CFModule, procedure_name: str, node: CFNode, *, top_level_node: bool = False):
        if stmt := node.as_statement():
            yield f'{stmt.action}(RH_PROC_{procedure_name.upper()}, &payload);'
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
                        yield f'if (__harness_rand() % {len(branch.branches) - idx} == 0) '
                        yield from self._codegen_node(module, procedure_name, item)
                    else:
                        yield from self._codegen_node(module, procedure_name, item)
                elif idx + 1 < len(branch.branches):
                    yield BaseCodegen.NO_NL
                    yield f'else if (__harness_rand() % {len(branch.branches) - idx} == 0) '
                    yield from self._codegen_node(module, procedure_name, item)
                else:
                    yield BaseCodegen.NO_NL
                    yield 'else '
                    yield from self._codegen_node(module, procedure_name, item)
        elif node.as_return():
            yield 'return __harness_NULL;'
        elif sync := node.as_synchronization():
            for unlock in sorted(sync.lock_mutexes):
                yield f'__harness_mutex_lock(&mtx{unlock.mutex_id});'
            for unlock in reversed(sorted(sync.unlock_mutexes)):
                yield f'__harness_mutex_unlock(&mtx{unlock.mutex_id});'
        elif node.as_init_barrier():
            yield 'init_barrier++;'
            yield 'while (init_barrier < INIT_BARRIER_CAPACITY) {}'