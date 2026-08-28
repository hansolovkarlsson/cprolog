# C Prolog -- a Prolog interpreter written in C.

CC      ?= cc
CFLAGS  ?= -std=c99 -O2 -Wall -Wextra
LDLIBS   = -lm
PREFIX  ?= /usr/local

SRCS = src/term.c src/parser.c src/write.c src/arith.c src/db.c \
       src/machine.c src/stream.c src/builtins.c src/consult.c \
       src/boot_pl.c src/main.c
OBJS = $(SRCS:.c=.o)
BIN  = prolog

all: $(BIN)

$(BIN): $(OBJS)
	$(CC) $(CFLAGS) -o $@ $(OBJS) $(LDLIBS)

# The bootstrap library is written in Prolog and compiled into the binary.
src/boot_pl.c: lib/boot.pl tools/pl2c.awk
	awk -f tools/pl2c.awk lib/boot.pl > $@

$(OBJS): src/prolog.h

.c.o:
	$(CC) $(CFLAGS) -c $< -o $@

# The regression suite.
test: $(BIN)
	./$(BIN) -q tests/test.pl -g run_tests

# The same suite with the collector running as often as it can, which
# exercises garbage collection on every code path.
test-gc: $(BIN)
	PROLOG_GC_THRESHOLD=1 ./$(BIN) -q tests/test.pl -g run_tests

# The suite under the address and undefined behaviour sanitizers.
# -fno-sanitize-recover makes undefined behaviour abort rather than print and
# carry on, so a finding fails the run instead of scrolling past.
test-asan:
	$(MAKE) clean
	$(MAKE) CFLAGS="-std=c99 -O1 -g -fsanitize=address,undefined \
	                -fno-sanitize-recover=undefined -fno-omit-frame-pointer"
	./$(BIN) -q tests/test.pl -g run_tests
	PROLOG_GC_THRESHOLD=1 ./$(BIN) -q tests/test.pl -g run_tests
	$(MAKE) clean

check: test test-gc

# The tutorial programs are what the published tutorial pages quote from, so
# loading each one and running a query out of its page keeps the two in step.
tutorials: $(BIN)
	./$(BIN) -q tutorial/level1.pl -g "ancestor(esther,D), format('~w~n',[D])"
	./$(BIN) -q tutorial/level2.pl -g "eldest_child(esther,C), format('~w~n',[C])"
	./$(BIN) -q tutorial/level3.pl -g "parse_order(\"3 hammer, 2 rope\", L), order_total(L,T), format('~w~n',[T])"
	./$(BIN) -q tutorial/level3.pl -g "fillable(C), format('~w~n',[C])"

examples: $(BIN)
	./$(BIN) -q examples/hanoi.pl -g "hanoi(3)"
	./$(BIN) -q examples/queens.pl -g "queens(8,Qs), print_board(Qs)"
	./$(BIN) -q examples/zebra.pl -g "zebra(_,W,Z), format('water: ~w, zebra: ~w~n',[W,Z])"
	./$(BIN) -q examples/calc.pl -g "calc(\"2 + 3 * (4 - 1)\", X), format('~w~n',[X])"
	./$(BIN) -q examples/family.pl -g "descendants(esther,D), format('~w~n',[D])"

# The documentation is generated; tools/docpage.py holds the shared shell.
doc: docs/index.html docs/tutorial-1.html docs/tutorial-2.html \
     docs/tutorial-3.html docs/reference.html docs/internals.html

docs/index.html: tools/gen_index.py tools/docpage.py
	python3 tools/gen_index.py

docs/tutorial-1.html: tools/gen_tutorial1.py tools/docpage.py tutorial/level1.pl
	python3 tools/gen_tutorial1.py

docs/tutorial-2.html: tools/gen_tutorial2.py tools/docpage.py tutorial/level2.pl
	python3 tools/gen_tutorial2.py

docs/tutorial-3.html: tools/gen_tutorial3.py tools/docpage.py tutorial/level3.pl
	python3 tools/gen_tutorial3.py

docs/reference.html: tools/gen_reference.py tools/docpage.py
	python3 tools/gen_reference.py

docs/internals.html: tools/gen_internals.py tools/docpage.py
	python3 tools/gen_internals.py

install: $(BIN)
	install -d $(DESTDIR)$(PREFIX)/bin
	install -m 755 $(BIN) $(DESTDIR)$(PREFIX)/bin/$(BIN)

clean:
	rm -f $(OBJS) $(BIN) src/boot_pl.c

.PHONY: all test test-gc test-asan check examples tutorials doc install clean
