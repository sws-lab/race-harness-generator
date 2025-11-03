#include "driver_client.simu.c"

struct state {
    _Atomic int connections;
    _Atomic int value;
};

static struct state *state = NULL;

void load(enum rh_process_instance instance) {
    (void) instance;

    printf("LOAD\n");
    state = malloc(sizeof(struct state));
    state->connections = 0;
    state->value = 0;
}

void unload(enum rh_process_instance instance) {
    (void) instance;

    printf("UNLOAD\n");
    free(state);
    state = NULL;
}

void acquire_conn(enum rh_process_instance instance) {
    (void) instance;

    printf("ACQUIRE\n");
    state->connections++;
}

void use_conn(enum rh_process_instance instance) {
    (void) instance;

    printf("USE\n");
    state->value++;
}

void release_conn(enum rh_process_instance instance) {
    (void) instance;
    
    printf("RELEASE\n");
    state->connections--;
}
