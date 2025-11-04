SIMU_CC ?= cc
SIMU_CFLAGS ?= -O3 -march=native -ggdb -fsanitize=thread

OUT_DIR := out
EXAMPLES_DIR := examples
PINS_STIR_DIR := pins-stir
LIBPINS_STIR_SO := $(PINS_STIR_DIR)/libpins-stir.so
STIR_BIN_EXPORT := $(PINS_STIR_DIR)/stir-bin-export

LTSMIN_DIR?=

C_SOURCE := $(shell find pins-stir -name "*.c" -or -name "*.h")
PYTHON_SOURCE := $(shell find race_harness/ -name "*.py")
EXAMPLES_SOURCE := $(wildcard $(EXAMPLES_DIR)/*.rh)
EXAMPLES_STIR := $(patsubst $(EXAMPLES_DIR)/%.rh,$(OUT_DIR)/%.stir,$(EXAMPLES_SOURCE))
EXAMPLES_BIN := $(patsubst $(EXAMPLES_DIR)/%.rh,$(OUT_DIR)/%.bin,$(EXAMPLES_SOURCE))
EXAMPLES_CSV := $(patsubst $(EXAMPLES_DIR)/%.rh,$(OUT_DIR)/%.csv,$(EXAMPLES_SOURCE))
EXAMPLES_SIMU_C := $(patsubst $(EXAMPLES_DIR)/%.rh,$(OUT_DIR)/%.simu.c,$(EXAMPLES_SOURCE))
EXAMPLES_SIMU_EXE := $(patsubst $(EXAMPLES_DIR)/%.rh,$(OUT_DIR)/%.simu,$(EXAMPLES_SOURCE))

all: $(EXAMPLES_SIMU_EXE)

all-stir: $(EXAMPLES_STIR)

all-bin: $(EXAMPLES_BIN)

all-csv: $(EXAMPLES_CSV)

all-simu-c: $(EXAMPLES_SIMU_C)

clean:
	rm -rf $(OUT_DIR)
	cd pins-stir && $(MAKE) clean

$(OUT_DIR)/%.stir: $(EXAMPLES_DIR)/%.rh $(PYTHON_SOURCE)
	mkdir -p "$(shell dirname $@)"
	uv run main.py $< > "$@.tmp"
	mv "$@.tmp" "$@"

$(OUT_DIR)/%.bin: $(OUT_DIR)/%.stir $(LIBPINS_STIR_SO)
	PINS_STIR_MODEL=$< PINS_STIR_OUTPUT="$@" $(LTSMIN_DIR)/bin/pins2lts-seq $(LIBPINS_STIR_SO)

$(OUT_DIR)/%.csv: $(OUT_DIR)/%.bin $(STIR_BIN_EXPORT)
	$(STIR_BIN_EXPORT) $(patsubst %.csv,%.stir,$@) $< > "$@.tmp"
	mv "$@.tmp" "$@"

$(OUT_DIR)/%.simu.c: $(OUT_DIR)/%.csv
	uv run generate.py $(patsubst $(OUT_DIR)/%.simu.c,$(EXAMPLES_DIR)/%.rh,$@) $< > "$@.tmp"
	mv "$@.tmp" "$@"

$(OUT_DIR)/%.simu: $(EXAMPLES_DIR)/%.lib.c $(OUT_DIR)/%.simu.c
	$(SIMU_CC) -DRH_IMPL -I$(OUT_DIR) $(SIMU_CFLAGS) -o "$@" $<

$(LIBPINS_STIR_SO): $(C_SOURCE)
	cd pins-stir && $(MAKE) all

$(STIR_BIN_EXPORT): $(C_SOURCE)
	cd pins-stir && $(MAKE) all

.PHONY: all all-stir clean
