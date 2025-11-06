#include <stdlib.h>
#include <stdio.h>

#include "driver_client.h"

struct state {
    _Atomic int connections;
    _Atomic int value;
};

static struct state *state = NULL;

void load(enum rh_process_instance instance, void **payload) {
    (void) instance;
    (void) payload;

    printf("LOAD\n");
    state = malloc(sizeof(struct state));
    state->connections = 0;
    state->value = 0;
}

void unload(enum rh_process_instance instance, void **payload) {
    (void) instance;
    (void) payload;

    printf("UNLOAD\n");
    free(state);
    state = NULL;
}

void acquire_conn(enum rh_process_instance instance, void **payload) {
    (void) instance;
    (void) payload;

    printf("ACQUIRE %d\n", instance);
    state->connections++;
}

void use_conn(enum rh_process_instance instance, void **payload) {
    (void) instance;
    (void) payload;

    printf("USE %d\n", instance);
    state->value++;
}

void release_conn(enum rh_process_instance instance, void **payload) {
    (void) instance;
    (void) payload;
    
    printf("RELEASE %d\n", instance);
    state->connections--;
}
