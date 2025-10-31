#include <stdlib.h>
#include <string.h>

#include <ltsmin/pins.h>
#include <ltsmin/lts-type.h>
#include <ltsmin/dlopen-api.h>

#include "stir.h"

char pins_plugin_name[] = "PINS STIR model loader";

struct pins_types {
    lts_type_t ltstype;
    int node_type;
    int bool_type;
};

static struct stir_model STIR_MODEL = {0};
static FILE *STIR_STATES_FP = NULL;

static void write_pins_stir_state(const struct stir_model *model, int *state) {
    fwrite(state, sizeof(int), model->state.num_of_slots, STIR_STATES_FP);
}

static void init_pins_types_from_stir(const struct stir_model *stir_model, model_t model, struct pins_types *types) {
    types->ltstype = lts_type_create();
    lts_type_set_state_length(types->ltstype, stir_model->state.num_of_slots);

    types->node_type = lts_type_add_type(types->ltstype, "node", NULL);
    types->bool_type = lts_type_add_type(types->ltstype, "bool", NULL);

    for (size_t i = 0; i < stir_model->state.num_of_slots; i++) {
        char name[32];
        snprintf(name, sizeof(name), "slot%zu", stir_model->state.slots[i].slot_id);
        lts_type_set_state_name(types->ltstype, stir_model->state.slots[i].slot_id, name);
        switch (stir_model->state.slots[i].type) {
            case STIR_MODEL_SLOT_NODE:
                lts_type_set_state_typeno(types->ltstype, stir_model->state.slots[i].slot_id, types->node_type);
                break;

            case STIR_MODEL_SLOT_BOOL:
                lts_type_set_state_typeno(types->ltstype, stir_model->state.slots[i].slot_id, types->bool_type);
                break;
        }
    }

    GBsetLTStype(model, types->ltstype);
}

static void init_pins_state_from_stir(const struct stir_model *stir_model, model_t model) {
    int *initial_state = malloc(sizeof(int) * stir_model->state.num_of_slots);
    for (size_t i = 0; i < stir_model->state.num_of_slots; i++) {
        initial_state[i] = stir_model->state.slots[i].init_value;
    }

    write_pins_stir_state(stir_model, initial_state);
    GBsetInitialState(model, initial_state);
    free(initial_state);
}

static void init_pins_dependency_matrix_from_stir(const struct stir_model *stir_model, model_t model) {
    matrix_t *dm_info = malloc(sizeof(matrix_t));
    if (dm_info == NULL) {
        stir_fatal("failed to allocate memory");
    }

    dm_create(dm_info, stir_model->num_of_transitions, stir_model->state.num_of_slots);
    for (size_t i = 0; i < stir_model->num_of_transitions; i++) {
        const struct stir_model_transition *transition = &stir_model->transitions[i];

        dm_set(dm_info, transition->transition_id, transition->component_slot_id);
        for (size_t j = 0; j < transition->num_of_guards; j++) {
            switch (transition->guards[j].type) {
                case STIR_MODEL_GUARD_BOOL:
                    dm_set(dm_info, transition->transition_id, transition->guards[j].bool_guard.slot_id);
                    break;
            }
        }

        for (size_t j = 0; j < transition->num_of_instr; j++) {
            switch (transition->instructions[j].type) {
                case STIR_MODEL_INSTR_SET_BOOL:
                    dm_set(dm_info, transition->transition_id, transition->instructions[j].set_bool.slot_id);
                    break;

                case STIR_MODEL_INSTR_DO:
                    // Intentionally left blank
                    break;
            }
        }
    }

    GBsetDMInfo(model, dm_info);
}

static int next_state(model_t model, int group, int *src, TransitionCB cb, void *user_context) {
    (void) model;

    static _Thread_local int *dst = NULL;
    if (dst == NULL) {
        dst = malloc(sizeof(int) * STIR_MODEL.state.num_of_slots);
        if (dst == NULL) {
            stir_fatal("failed to allocate memory");
        }
    }

    const struct stir_model_transition *transition = &STIR_MODEL.transitions[group];

    if (src[transition->component_slot_id] != transition->src_node) {
        return 0;
    }
    for (size_t i = 0; i < transition->num_of_guards; i++) {
        switch (transition->guards[i].type) {
            case STIR_MODEL_GUARD_BOOL:
                if ((!transition->invert_guard && src[transition->guards[i].bool_guard.slot_id] != transition->guards[i].bool_guard.value) ||
                    (transition->invert_guard && src[transition->guards[i].bool_guard.slot_id] == transition->guards[i].bool_guard.value)) {
                    return 0;
                }
                break;
        }
    }

    memcpy(dst, src, sizeof(int) * STIR_MODEL.state.num_of_slots);
    dst[transition->component_slot_id] = transition->dst_node;
    for (size_t i = 0; i <transition->num_of_instr; i++) {
        switch (transition->instructions[i].type) {
            case STIR_MODEL_INSTR_SET_BOOL:
                dst[transition->instructions[i].set_bool.slot_id] = transition->instructions[i].set_bool.value;
                break;

            case STIR_MODEL_INSTR_DO:
                // Intentionally left blank
                break;
        }
    }

    transition_info_t ti = GB_TI(NULL, group);
    cb(user_context, &ti, dst, NULL);
    write_pins_stir_state(&STIR_MODEL, dst);
    return 1;
}

static void init_pins_from_stir(const struct stir_model *stir_model, model_t model) {
    struct pins_types types;
    init_pins_types_from_stir(stir_model, model, &types);
    init_pins_state_from_stir(stir_model, model);
    init_pins_dependency_matrix_from_stir(stir_model, model);

    GBsetContext(model, (void *) stir_model);
    GBsetNextStateLong(model, next_state);
}

static void exit_cb(model_t model) {
    (void) model;

    fflush(STIR_STATES_FP);
    fclose(STIR_STATES_FP);
    free_stir_model(&STIR_MODEL);
}

_Noreturn void stir_abort(void) {
    ltsmin_abort(-1);
}

void pins_model_init(model_t m) {
    const char *stir_model_filepath = getenv("PINS_STIR_MODEL");
    if (stir_model_filepath == NULL) {
        stir_fatal("expected PINS_STIR_MODEL to contain a valid filepath");
    }

    const char *stir_output_filepath = getenv("PINS_STIR_OUTPUT");
    if (stir_output_filepath == NULL) {
        stir_fatal("expected PINS_STIR_OUTPUT to contain a valid filepath");
    }

    STIR_STATES_FP = fopen(stir_output_filepath, "wb");

    const char *stir_model_text;
    size_t stir_model_text_length;
    open_stir_model_text(stir_model_filepath, &stir_model_text, &stir_model_text_length);
    load_stir_model(&stir_model_text, &STIR_MODEL);
    close_stir_model_text(stir_model_text, stir_model_text_length);

    init_pins_from_stir(&STIR_MODEL, m);

    GBsetExit(m, exit_cb);
}
