#include <stdlib.h>
#include <stdio.h>

#include "cigarette_smokers.h"

static _Atomic int smokers = 0;

void smoke(enum rh_process_instance instance, void **payload) {
    (void) instance;
    (void) payload;

    printf("smoke %u\n", instance);
    if (smokers++ != 0) {
        fprintf(stderr, "Conflict!\n");
        abort();
    }
    smokers--;
}
