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

all: $(EXAMPLES_CSV)

all-stir: $(EXAMPLES_STIR)

all-bin: $(EXAMPLES_BIN)

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

$(LIBPINS_STIR_SO): $(C_SOURCE)
	cd pins-stir && $(MAKE) all

$(STIR_BIN_EXPORT): $(C_SOURCE)
	cd pins-stir && $(MAKE) all

.PHONY: all all-stir clean
