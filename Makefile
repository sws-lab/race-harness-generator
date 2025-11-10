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
EXAMPLES_RHIR := $(patsubst $(EXAMPLES_DIR)/%.rh,$(OUT_DIR)/%.rhir,$(EXAMPLES_SOURCE))
EXAMPLES_STIR := $(patsubst $(EXAMPLES_DIR)/%.rh,$(OUT_DIR)/%.stir,$(EXAMPLES_SOURCE))
EXAMPLES_CSV := $(patsubst $(EXAMPLES_DIR)/%.rh,$(OUT_DIR)/%.csv,$(EXAMPLES_SOURCE))
EXAMPLES_H := $(patsubst $(EXAMPLES_DIR)/%.rh,$(OUT_DIR)/%.h,$(EXAMPLES_SOURCE))
EXAMPLES_SIMU_C := $(patsubst $(EXAMPLES_DIR)/%.rh,$(OUT_DIR)/%.simu.c,$(EXAMPLES_SOURCE))
EXAMPLES_STIR_C := $(patsubst $(EXAMPLES_DIR)/%.rh,$(OUT_DIR)/%.stir.c,$(EXAMPLES_SOURCE))
EXAMPLES_GOBLINT_C := $(patsubst $(EXAMPLES_DIR)/%.rh,$(OUT_DIR)/%.goblint.c,$(EXAMPLES_SOURCE))
EXAMPLES_SIMU_EXE := $(patsubst $(EXAMPLES_DIR)/%.rh,$(OUT_DIR)/%.simu,$(EXAMPLES_SOURCE))
EXAMPLES_SIMU_STIR_EXE := $(patsubst $(EXAMPLES_DIR)/%.rh,$(OUT_DIR)/%.simu.stir,$(EXAMPLES_SOURCE))
EXAMPLES_GOBLINT_LOGS := $(patsubst $(EXAMPLES_DIR)/%.rh,$(OUT_DIR)/%.goblint.log,$(EXAMPLES_SOURCE))

all: all-rhir all-stir all-simu-exe all-goblint-logs all-stir-c all-simu-stir-exe

all-rhir: $(EXAMPLES_RHIR)

all-stir: $(EXAMPLES_STIR)

all-csv: $(EXAMPLES_CSV)

all-simu-c: $(EXAMPLES_SIMU_C) $(EXAMPLES_H)

all-simu-exe: $(EXAMPLES_SIMU_EXE)

all-stir-c: $(EXAMPLES_STIR_C)

all-simu-stir-exe: $(EXAMPLES_SIMU_STIR_EXE)

all-goblint-c: $(EXAMPLES_GOBLINT_C) $(EXAMPLES_H)

all-goblint-logs: $(EXAMPLES_GOBLINT_LOGS)

clean:
	rm -rf $(OUT_DIR)
	cd pins-stir && $(MAKE) clean

$(OUT_DIR)/%.rhir: $(EXAMPLES_DIR)/%.rh $(PYTHON_SOURCE)
	mkdir -p "$(shell dirname $@)"
	./driver.py --encoding rhir $< --output "$@.tmp"
	mv "$@.tmp" "$@"

$(OUT_DIR)/%.stir: $(EXAMPLES_DIR)/%.rh $(PYTHON_SOURCE)
	mkdir -p "$(shell dirname $@)"
	./driver.py --encoding stir $< --output "$@.tmp"
	mv "$@.tmp" "$@"

$(OUT_DIR)/%.csv: $(EXAMPLES_DIR)/%.rh $(PYTHON_SOURCE) $(LIBPINS_STIR_SO) $(STIR_BIN_EXPORT)
	mkdir -p "$(shell dirname $@)"
	./driver.py --ltsmin "$(LTSMIN_DIR)" --pins-stir "$(PINS_STIR_DIR)" --encoding state_space $< --output "$@.tmp"
	mv "$@.tmp" "$@"

$(OUT_DIR)/%.h: $(OUT_DIR)/%.csv
	./driver.py --encoding header --output "$@.tmp" \
		--ltsmin "$(LTSMIN_DIR)" --pins-stir "$(PINS_STIR_DIR)" \
		--state-space "$(patsubst $(OUT_DIR)/%.h,$(OUT_DIR)/%.csv,$@)" \
		"$(patsubst $(OUT_DIR)/%.h,$(EXAMPLES_DIR)/%.rh,$@)"
	mv "$@.tmp" "$@"

$(OUT_DIR)/%.simu.c: $(OUT_DIR)/%.csv $(EXAMPLES_DIR)/%.lib.toml
	./driver.py --encoding executable --output "$@.tmp" \
		--payloads "$(patsubst $(OUT_DIR)/%.simu.c,$(EXAMPLES_DIR)/%.lib.toml,$@)" \
		--ltsmin "$(LTSMIN_DIR)" --pins-stir "$(PINS_STIR_DIR)" \
		--state-space "$(patsubst $(OUT_DIR)/%.simu.c,$(OUT_DIR)/%.csv,$@)" \
		"$(patsubst $(OUT_DIR)/%.simu.c,$(EXAMPLES_DIR)/%.rh,$@)"
	mv "$@.tmp" "$@"

$(OUT_DIR)/%.stir.c: $(OUT_DIR)/%.csv
	./driver.py --encoding executable-stir --output "$@.tmp" \
		"$(patsubst $(OUT_DIR)/%.stir.c,$(EXAMPLES_DIR)/%.rh,$@)"
	mv "$@.tmp" "$@"

$(OUT_DIR)/%.goblint.c: $(OUT_DIR)/%.csv $(EXAMPLES_DIR)/%.lib.toml
	./driver.py --encoding goblint --output "$@.tmp" \
		--payloads "$(patsubst $(OUT_DIR)/%.goblint.c,$(EXAMPLES_DIR)/%.lib.toml,$@)" \
		--ltsmin "$(LTSMIN_DIR)" --pins-stir "$(PINS_STIR_DIR)" \
		--state-space "$(patsubst $(OUT_DIR)/%.goblint.c,$(OUT_DIR)/%.csv,$@)" \
		"$(patsubst $(OUT_DIR)/%.goblint.c,$(EXAMPLES_DIR)/%.rh,$@)"
	mv "$@.tmp" "$@"

$(OUT_DIR)/%.simu: $(EXAMPLES_DIR)/%.lib.c $(OUT_DIR)/%.simu.c $(OUT_DIR)/%.h
	$(SIMU_CC) -I$(OUT_DIR) -include $(patsubst $(OUT_DIR)/%.simu,$(OUT_DIR)/%.h,$@) $(SIMU_CFLAGS) -o "$@" $< $(patsubst $(OUT_DIR)/%.simu,$(OUT_DIR)/%.simu.c,$@)

$(OUT_DIR)/%.simu.stir: $(OUT_DIR)/%.stir.c
	$(SIMU_CC) $(SIMU_CFLAGS) -o "$@" $< -latomic

$(OUT_DIR)/%.goblint.log: $(EXAMPLES_DIR)/%.lib.c $(OUT_DIR)/%.goblint.c $(OUT_DIR)/%.h
	$(GOBLINT) --set pre.includes[+] $(OUT_DIR) --set pre.cppflags[+] -include --set pre.cppflags[+] $(patsubst $(OUT_DIR)/%.goblint.log,$(OUT_DIR)/%.h,$@) \
		$(patsubst $(OUT_DIR)/%.goblint.log,$(OUT_DIR)/%.goblint.c,$@) \
		$(patsubst $(OUT_DIR)/%.goblint.log,$(EXAMPLES_DIR)/%.lib.c,$@) 2>&1 | tee "$@.tmp"
	mv "$@.tmp" "$@"

$(LIBPINS_STIR_SO): $(C_SOURCE)
	cd pins-stir && $(MAKE) all

$(STIR_BIN_EXPORT): $(LIBPINS_STIR_SO)

.PHONY: all all-rhir all-stir all-csv all-simu-c all-goblint-c all-goblint-logs all-stir-c all-simu-stir-exe clean
