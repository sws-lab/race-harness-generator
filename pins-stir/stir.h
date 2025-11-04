#ifndef STIR_H_
#define STIR_H_

#include <inttypes.h>
#include <unistd.h>

enum stir_model_slot_type {
    STIR_MODEL_SLOT_BOOL,
    STIR_MODEL_SLOT_INT,
    STIR_MODEL_SLOT_NODE
};

struct stir_model_slot {
    size_t slot_id;
    enum stir_model_slot_type type;
    int init_value;
};

struct stir_model_state {
    struct stir_model_slot *slots;
    size_t num_of_slots;
};

enum stir_model_transition_guard_type {
    STIR_MODEL_GUARD_BOOL,
    STIR_MODEL_GUARD_INT
};

enum stir_model_transition_instr_type {
    STIR_MODEL_INSTR_DO,
    STIR_MODEL_INSTR_SET_BOOL,
    STIR_MODEL_INSTR_SET_INT
};

struct stir_model_transition_guard {
    enum stir_model_transition_guard_type type;
    union {
        struct {
            size_t slot_id;
            int value;
        } bool_guard;

        struct {
            size_t slot_id;
            int value;
        } int_guard;
    };
};

struct stir_model_transition_instr {
    enum stir_model_transition_instr_type type;
    union {
        struct {
            size_t slot_id;
            int value;
        } set_bool;
        struct {
            size_t slot_id;
            int value;
        } set_int;
    };
};

struct stir_model_transition {
    size_t transition_id;
    size_t component_slot_id;
    size_t num_of_guards;
    size_t num_of_instr;
    int src_node;
    int dst_node;
    int invert_guard;

    struct stir_model_transition_guard *guards;
    struct stir_model_transition_instr *instructions;
};

struct stir_model {
    struct stir_model_state state;
    struct stir_model_transition *transitions;
    size_t num_of_transitions;
};

_Noreturn void stir_abort(void);

_Noreturn void stir_fatal(const char *, ...);
_Noreturn void stir_perror_fatal(const char *);

void open_stir_model_text(const char *, const char **, size_t *);
void close_stir_model_text(const char *, size_t);

void load_stir_model(const char **, struct stir_model *);
void free_stir_model(struct stir_model *);

#endif
