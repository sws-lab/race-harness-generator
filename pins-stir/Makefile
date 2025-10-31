CC?=cc
CFLAGS?=-std=c17 -Wall -Wextra -pedantic -O3 -march=native -ggdb
LDFLAGS?=

LTSMIN_DIR?=

LIBPINS_STIR_SO=libpins-stir.so
LIBPINS_STIR_SOURCES=stir.c pins-stir.c
LIBPINS_STIR_OBJECTS=$(patsubst %.c,%.o,$(LIBPINS_STIR_SOURCES))

STIR_BIN_EXPORT=stir-bin-export
STIR_BIN_EXPORT_SOURCES=stir.c export.c
STIR_BIN_EXPORT_OBJECTS=$(patsubst %.c,%.o,$(STIR_BIN_EXPORT_SOURCES))

all: $(LIBPINS_STIR_SO) $(STIR_BIN_EXPORT)

clean:
	rm -rf *.o *.gcf $(LIBPINS_STIR_SO) $(STIR_BIN_EXPORT)

test: test.gcf

%.o: %.c stir.h
	$(CC) -fPIC -I$(LTSMIN_DIR)/include $(CFLAGS) $< -c -o $@

$(LIBPINS_STIR_SO): $(LIBPINS_STIR_OBJECTS)
	$(CC) -shared $^ -o $@ $(LDFLAGS)

$(STIR_BIN_EXPORT): $(STIR_BIN_EXPORT_OBJECTS)
	$(CC) $^ -o $@ $(LDFLAGS)

test.gcf: $(LIBPINS_STIR_SO)
	$(LTSMIN_DIR)/bin/pins2lts-seq $(LIBPINS_STIR_SO) $@

.PHONY: all clean test