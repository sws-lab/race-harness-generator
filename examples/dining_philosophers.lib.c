#include <stdlib.h>
#include <stdio.h>

#include "dining_philosophers.h"

static _Atomic int eaters = 0;

void think(enum rh_process_instance instance, void **payload) {
    (void) instance;
    (void) payload;

    printf("think %u\n", instance);
}

void take_forks(enum rh_process_instance instance, void **payload) {
    (void) instance;
    (void) payload;

    printf("take forks %u\n", instance);
    if (eaters == 2) {
        fprintf(stderr, "Conflict!\n");
        abort();
    }
    eaters++;
}

void eat(enum rh_process_instance instance, void **payload) {
    (void) instance;
    (void) payload;

    printf("eat %u\n", instance);
}

void put_forks(enum rh_process_instance instance, void **payload) {
    (void) instance;
    (void) payload;

    printf("put forks %u\n", instance);
    eaters--;
}
