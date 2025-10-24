#include <stdlib.h>
#include <stdio.h>
#include <stdarg.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <sys/types.h>

#include "stir.h"

_Noreturn void stir_fatal(const char *fmt, ...) {
    va_list args;
    va_start(args, fmt);
    vfprintf(stderr, fmt, args);
    va_end(args);
    stir_abort();
}

_Noreturn void stir_perror_fatal(const char *msg) {
    perror(msg);
    stir_abort();
}

void open_stir_model_text(const char *stir_model_filepath, const char **content, size_t *length) {
    int fd = open(stir_model_filepath, O_RDONLY);
    if (fd == -1) {
        stir_perror_fatal("failed to open stir model");
    }

    struct stat sb;
    if (fstat(fd, &sb) == -1) {
        stir_perror_fatal("failed to fstat stir model");
    }

    void *addr = mmap(NULL, sb.st_size, PROT_READ, MAP_PRIVATE, fd, 0);
    if (addr == MAP_FAILED) {
        stir_perror_fatal("failed to mmap stir model");
    }

    close(fd);

    *content = addr;
    *length = sb.st_size;
}

void close_stir_model_text(const char *content, size_t length) {
    munmap((void *) content, length);
}


static struct stir_model_state load_stir_model_state(const char **content) {
    int read;
    size_t num_of_slots;
    
    int rc = sscanf(*content, "state %zu\n%n", &num_of_slots, &read);
    if (rc == 0) {
        stir_fatal("failed to parse stir model state");
    }
    *content += read;

    struct stir_model_slot *slots = malloc(sizeof(struct stir_model_slot) * num_of_slots);
    if (slots == NULL) {
        stir_fatal("failed to allocate memory");
    }

    for (size_t i = 0; i < num_of_slots; i++) {
        size_t slot_id;

        rc = sscanf(*content, "slot %zu %n", &slot_id, &read);
        if (rc == 0) {
            stir_fatal("Failed to parse stir model slot");
        }
        *content += read;

        slots[i].slot_id = slot_id;
        rc = sscanf(*content, "bool %d\n%n", &slots[i].init_value, &read);
        if (rc != 0) {
            *content += read;
            slots[i].type = STIR_MODEL_SLOT_BOOL;
            continue;
        }

        rc = sscanf(*content, "node %d\n%n", &slots[i].init_value, &read);
        if (rc != 0) {
            *content += read;
            slots[i].type = STIR_MODEL_SLOT_NODE;
            continue;
        }

        stir_fatal("Failed to parse stir model slot");
    }
    
    return (struct stir_model_state) {
        .slots = slots,
        .num_of_slots = num_of_slots
    };
}

static void free_stir_model_state(struct stir_model_state *state) {
    free(state->slots);
    state->slots = NULL;
    state->num_of_slots = 0;
}

static void load_model_transitions(const char **content, struct stir_model *model) {
    int read;
    
    int rc = sscanf(*content, "transitions %zu\n%n", &model->num_of_transitions, &read);
    if (rc == 0) {
        stir_fatal("failed to parse stir model transitions");
    }
    *content += read;

    model->transitions = malloc(sizeof(struct stir_model_transition) * model->num_of_transitions);
    if (model->transitions == NULL) {
        stir_fatal("failed to allocate memory");
    }

    for (size_t i = 0; i < model->num_of_transitions; i++) {
        struct stir_model_transition *transition = &model->transitions[i];

        rc = sscanf(*content, "transition %zu component %zu src %d dst %d guards %zu %d instructions %zu\n%n",
            &transition->transition_id, &transition->component_slot_id, &transition->src_node,
            &transition->dst_node, &transition->num_of_guards, &transition->invert_guard, &transition->num_of_instr,
            &read);
        if (rc == 0) {
            stir_fatal("failed to parse stir model transition");
        }
        *content += read;

        transition->guards = malloc(sizeof(struct stir_model_transition_guard) * transition->num_of_guards);
        if (transition->guards == NULL) {
            stir_fatal("failed to allocate memory");
        }

        transition->instructions = malloc(sizeof(struct stir_model_transition_instr) * transition->num_of_instr);
        if (transition->instructions == NULL) {
            stir_fatal("failed to allocate memory");
        }
        
        for (size_t j = 0; j < transition->num_of_guards; j++) {
            rc = sscanf(*content, "bool_guard %zu %d\n%n",
                &transition->guards[j].bool_guard.slot_id, &transition->guards[j].bool_guard.value, &read);
            if (rc == 0) {
                stir_fatal("failed to parse stir model transition guard");
            }
            *content += read;

            transition->guards[i].type = STIR_MODEL_GUARD_BOOL;
        }

        for (size_t j = 0; j < transition->num_of_instr; j++) {
            const char DO_INSTR[] = "do_instr";
            if (strncmp(DO_INSTR, *content, sizeof(DO_INSTR) - 1) == 0) {
                transition->instructions[j].type = STIR_MODEL_INSTR_DO;
                // Skip do instructions
                for (; **content != '\0'; (*content)++) {
                    if (**content == '\n') {
                        (*content)++;
                        break;
                    }
                }
                continue;
            }
            
            rc = sscanf(*content, "set_bool_instr %zu %d\n%n",
                &transition->instructions[j].set_bool.slot_id, &transition->instructions[j].set_bool.value, &read);
            if (rc != 0) {
                *content += read;
                transition->instructions[j].type = STIR_MODEL_INSTR_SET_BOOL;
                continue;
            }

            stir_fatal("failed to parse stir transition instruction");
        }
    }
}

void load_stir_model(const char **content, struct stir_model *model) {
    model->state = load_stir_model_state(content);
    load_model_transitions(content, model);
}

void free_stir_model(struct stir_model *model) {
    free_stir_model_state(&model->state);

    for (size_t i = 0; i < model->num_of_transitions; i++) {
        free(model->transitions[i].guards);
        free(model->transitions[i].instructions);
    }
    free(model->transitions);
    model->num_of_transitions = 0;
}
