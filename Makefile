SIMU_CC ?= cc
SIMU_CFLAGS ?= -O3 -march=native -ggdb -fsanitize=thread

OUT_DIR := out
EXAMPLES_DIR := examples
PINS_STIR_DIR := pins-stir
LIBPINS_STIR_SO := $(PINS_STIR_DIR)/libpins-stir.so
STIR_BIN_EXPORT := $(PINS_STIR_DIR)/stir-bin-export

LTSMIN_DIR?=
GOBLINT?=

C_SOURCE := $(shell find pins-stir -name "*.c" -or -name "*.h")
PYTHON_SOURCE := $(shell find race_harness/ -name "*.py")
EXAMPLES_SOURCE := $(wildcard $(EXAMPLES_DIR)/*.rh)
EXAMPLES_STIR := $(patsubst $(EXAMPLES_DIR)/%.rh,$(OUT_DIR)/%.stir,$(EXAMPLES_SOURCE))
EXAMPLES_BIN := $(patsubst $(EXAMPLES_DIR)/%.rh,$(OUT_DIR)/%.bin,$(EXAMPLES_SOURCE))
EXAMPLES_CSV := $(patsubst $(EXAMPLES_DIR)/%.rh,$(OUT_DIR)/%.csv,$(EXAMPLES_SOURCE))
EXAMPLES_SIMU_C := $(patsubst $(EXAMPLES_DIR)/%.rh,$(OUT_DIR)/%.simu.c,$(EXAMPLES_SOURCE))
EXAMPLES_GOBLINT_C := $(patsubst $(EXAMPLES_DIR)/%.rh,$(OUT_DIR)/%.goblint.c,$(EXAMPLES_SOURCE))
EXAMPLES_H := $(patsubst $(EXAMPLES_DIR)/%.rh,$(OUT_DIR)/%.h,$(EXAMPLES_SOURCE))
EXAMPLES_SIMU_EXE := $(patsubst $(EXAMPLES_DIR)/%.rh,$(OUT_DIR)/%.simu,$(EXAMPLES_SOURCE))
EXAMPLES_GOBLINT_LOGS := $(patsubst $(EXAMPLES_DIR)/%.rh,$(OUT_DIR)/%.goblint.log,$(EXAMPLES_SOURCE))

all: all-simu-exe all-goblint-logs

all-stir: $(EXAMPLES_STIR)

all-bin: $(EXAMPLES_BIN)

all-csv: $(EXAMPLES_CSV)

all-simu-c: $(EXAMPLES_SIMU_C) $(EXAMPLES_H)

all-simu-exe: $(EXAMPLES_SIMU_EXE)

all-goblint-c: $(EXAMPLES_GOBLINT_C) $(EXAMPLES_H)

all-goblint-logs: $(EXAMPLES_GOBLINT_LOGS)

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

$(OUT_DIR)/%.h: $(OUT_DIR)/%.csv
	uv run generate.py $(patsubst $(OUT_DIR)/%.h,$(EXAMPLES_DIR)/%.rh,$@) --reachability $< --encoding header > "$@.tmp"
	mv "$@.tmp" "$@"

$(OUT_DIR)/%.simu.c: $(OUT_DIR)/%.csv
	uv run generate.py $(patsubst $(OUT_DIR)/%.simu.c,$(EXAMPLES_DIR)/%.rh,$@) --reachability $< > "$@.tmp"
	mv "$@.tmp" "$@"

$(OUT_DIR)/%.goblint.c: $(OUT_DIR)/%.csv
	uv run generate.py $(patsubst $(OUT_DIR)/%.goblint.c,$(EXAMPLES_DIR)/%.rh,$@) --reachability $< --encoding goblint > "$@.tmp"
	mv "$@.tmp" "$@"

$(OUT_DIR)/%.simu: $(EXAMPLES_DIR)/%.lib.c $(OUT_DIR)/%.simu.c $(OUT_DIR)/%.h
	$(SIMU_CC) -I$(OUT_DIR) -include $(patsubst $(OUT_DIR)/%.simu,$(OUT_DIR)/%.h,$@) $(SIMU_CFLAGS) -o "$@" $< $(patsubst $(OUT_DIR)/%.simu,$(OUT_DIR)/%.simu.c,$@)

$(OUT_DIR)/%.goblint.log: $(EXAMPLES_DIR)/%.lib.c $(OUT_DIR)/%.goblint.c $(OUT_DIR)/%.h
	$(GOBLINT) --set pre.includes[+] $(OUT_DIR) --set pre.cppflags[+] -include --set pre.cppflags[+] $(patsubst $(OUT_DIR)/%.goblint.log,$(OUT_DIR)/%.h,$@) \
		$(patsubst $(OUT_DIR)/%.goblint.log,$(OUT_DIR)/%.goblint.c,$@) \
		$(patsubst $(OUT_DIR)/%.goblint.log,$(EXAMPLES_DIR)/%.lib.c,$@) 2>&1 | tee "$@.tmp"
	mv "$@.tmp" "$@"

$(LIBPINS_STIR_SO): $(C_SOURCE)
	cd pins-stir && $(MAKE) all

$(STIR_BIN_EXPORT): $(C_SOURCE)
	cd pins-stir && $(MAKE) all

.PHONY: all all-stir all-bin all-csv all-simu-c all-goblint-c all-goblint-logs clean
