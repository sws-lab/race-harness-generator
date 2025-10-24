CC?=cc
CFLAGS?=-std=c17 -Wall -Wextra -pedantic -O0 -ggdb
LDFLAGS?=

LTSMIN_DIR?=

LIBPINS_STIR_SO=libpins-stir.so
SOURCE_FILES=$(wildcard *.c)
OBJECT_FILES=$(patsubst %.c,%.o,$(SOURCE_FILES))

all: $(LIBPINS_STIR_SO)

clean:
	rm -rf *.o *.gcf $(LIBPINS_STIR_SO)

test: test.gcf

%.o: %.c stir.h
	$(CC) -fPIC -I$(LTSMIN_DIR)/include $(CFLAGS) $< -c -o $@

$(LIBPINS_STIR_SO): $(OBJECT_FILES)
	$(CC) -shared $^ -o $@ $(LDFLAGS)

test.gcf: $(LIBPINS_STIR_SO)
	$(LTSMIN_DIR)/bin/pins2lts-seq $(LIBPINS_STIR_SO) $@

.PHONY: all clean test