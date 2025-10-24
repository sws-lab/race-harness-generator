#include <stdlib.h>
#include <stdio.h>
#include <inttypes.h>
#include <string.h>

#include "stir.h"

static void process_bin_content(const struct stir_model *model, const char *bin_content, size_t bin_length, FILE *out) {
    size_t *slot_id_mapping = malloc(sizeof(size_t) * model->state.num_of_slots);
    if (slot_id_mapping == NULL) {
        stir_fatal("failed to allocate memory");
    }
    memset(slot_id_mapping, -1, sizeof(size_t) * model->state.num_of_slots);

    size_t num_of_nodes = 0;
    int max_node_value = 0;
    for (size_t i = 0; i < model->state.num_of_slots; i++) {
        if (model->state.slots[i].type == STIR_MODEL_SLOT_NODE) {
            slot_id_mapping[num_of_nodes++] = i;
            if (model->state.slots[i].init_value > max_node_value) {
                max_node_value = model->state.slots[i].init_value;
            }
        }
    }

    for (size_t i = 0; i < model->num_of_transitions; i++) {
        const struct stir_model_transition *transition = &model->transitions[i];
        if (transition->dst_node > max_node_value) {
            max_node_value = transition->dst_node;
        }
    }

    size_t matrix_len = num_of_nodes * (max_node_value + 1) * num_of_nodes * (max_node_value + 1);
    _Bool *matrix = malloc(sizeof(_Bool) * matrix_len);
    if (matrix == NULL) {
        stir_fatal("failed to allocate memory");
    }
    memset(matrix, 0, sizeof(_Bool) * matrix_len);

    for (size_t i = 0; i < bin_length / (sizeof(int) * model->state.num_of_slots); i++) {
        const int *state = (const int *) (((uintptr_t) bin_content) + i * sizeof(int) * model->state.num_of_slots);
        for (size_t j = 0; j < num_of_nodes; j++) {
            size_t node1 = slot_id_mapping[j];
            for (size_t k = 0; k < num_of_nodes; k++) {
                if (k == j) {
                    continue;
                }

                size_t node2 = slot_id_mapping[k];
                size_t index = (j * (max_node_value + 1) + state[node1]) * num_of_nodes * (max_node_value + 1) + k * (max_node_value + 1) + state[node2];
                matrix[index] = 1;
            }    
        }
    }

    fprintf(out, "slot1,value1,slot2,value2\n");
    for (size_t i = 0; i < num_of_nodes; i++) {
        size_t node1 = slot_id_mapping[i];
        for (int j = 0; j < max_node_value; j++) {
            for (size_t k = 0; k < num_of_nodes; k++) {
                size_t node2 = slot_id_mapping[k];
                for (int l = 0; l < max_node_value; l++) {
                    size_t index = (i * (max_node_value + 1) + j) * num_of_nodes * (max_node_value + 1) + k * (max_node_value + 1) + l;
                    if (matrix[index]) {
                        fprintf(out, "%zu,%d,%zu,%d\n", node1, j, node2, l);
                    }
                }
            }
        }
    }

    free(matrix);
    free(slot_id_mapping);
}

_Noreturn void stir_abort() {
    abort();
}

int main(int argc, const char **argv) {
    if (argc < 3) {
        stir_fatal("usage: %s stir_file bin_file", argv[0]);
    }

    struct stir_model model;
    const char *model_text, *bin_content;
    size_t model_len, bin_length;

    open_stir_model_text(argv[1], &model_text, &model_len);
    open_stir_model_text(argv[2], &bin_content, &bin_length);
    load_stir_model(&model_text, &model);

    process_bin_content(&model, bin_content, bin_length, stdout);

    free_stir_model(&model);
    close_stir_model_text(model_text, model_len);
    close_stir_model_text(bin_content, bin_length);
    return EXIT_SUCCESS;
}