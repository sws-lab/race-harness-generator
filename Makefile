OUT_DIR := out
EXAMPLES_DIR := examples
PINS_STIR_DIR := pins-stir
LIBPINS_STIR_SO := $(PINS_STIR_DIR)/libpins-stir.so

LTSMIN_DIR?=

PYTHON_SOURCE := $(shell find race_harness/ -name "*.py")
EXAMPLES_SOURCE := $(wildcard $(EXAMPLES_DIR)/*.rh)
EXAMPLES_STIR := $(patsubst $(EXAMPLES_DIR)/%.rh,$(OUT_DIR)/%.stir,$(EXAMPLES_SOURCE))
EXAMPLES_GCF := $(patsubst $(EXAMPLES_DIR)/%.rh,$(OUT_DIR)/%.gcf,$(EXAMPLES_SOURCE))

all: $(EXAMPLES_GCF)

all-stir: $(EXAMPLES_STIR)

clean:
	rm -rf $(OUT_DIR)
	cd pins-stir && $(MAKE) clean

$(OUT_DIR)/%.stir: $(EXAMPLES_DIR)/%.rh $(PYTHON_SOURCE)
	mkdir -p "$(shell dirname $@)"
	uv run main.py $< > "$@.tmp"
	mv "$@.tmp" "$@"

$(OUT_DIR)/%.gcf: $(OUT_DIR)/%.stir $(LIBPINS_STIR_SO)
	PINS_STIR_MODEL=$< $(LTSMIN_DIR)/bin/pins2lts-seq $(LIBPINS_STIR_SO) $@

$(LIBPINS_STIR_SO):
	cd pins-stir && $(MAKE) all

.PHONY: all all-stir clean
