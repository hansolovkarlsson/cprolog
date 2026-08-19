# C Prolog

[![CI](https://github.com/hansolovkarlsson/cprolog/actions/workflows/ci.yml/badge.svg)](https://github.com/hansolovkarlsson/cprolog/actions/workflows/ci.yml)

A Prolog interpreter written from scratch in C99 — reader, engine, garbage
collector and library. No dependencies beyond libc and libm.

```
$ make
$ ./prolog
C Prolog 1.0 -- a Prolog interpreter in C
Type help. for help, halt. to quit.

?- X = hello, atom_length(X, N).
X = hello,
N = 5.

?- member(X, [a,b,c]).
X = a ;
X = b ;
X = c ;
false.
```

Documentation is published at
**[hansolovkarlsson.github.io/cprolog](https://hansolovkarlsson.github.io/cprolog/)**:
a [tutorial](https://hansolovkarlsson.github.io/cprolog/tutorial-1.html) that
teaches Prolog from the beginning using this interpreter,
a [language reference](https://hansolovkarlsson.github.io/cprolog/reference.html)
covering syntax, control, arithmetic, every builtin predicate, grammars and
errors, and an [engine internals](https://hansolovkarlsson.github.io/cprolog/internals.html)
document describing how the interpreter is built and where the design costs
something. Both are generated into `docs/` by `make doc`.

## Building

```
make            # build ./prolog
make test       # run the regression suite (240 tests)
make test-gc    # the same suite with the collector running constantly
make test-asan  # the same suite under ASan + UBSan
make examples   # run the example programs
make install    # install to $(PREFIX)/bin, default /usr/local
```

Builds clean with `-Wall -Wextra` under both clang and gcc. Every push runs the
suite on Linux and macOS, with both compilers, under the sanitizers, and checks
that `docs/` still matches its generators.

## Using it

```
prolog [options] [file ...]

  -g, --goal GOAL   run GOAL after loading the files
  -t, --top         enter the toplevel even after -g
  -q, --quiet       no banner
  -v, --version     print the version
  -h, --help        print the usage message
```

With no `-g` the interpreter loads its arguments and enters the interactive
toplevel; with `-g` it runs the goal and exits, which is how you write
scripts:

```
$ ./prolog -q examples/queens.pl -g "queens(8, Qs), write(Qs), nl"
[4,2,7,3,6,8,5,1]
```

At the toplevel, `;` (or space) asks for the next solution and return stops.
Files are loaded with `[file].` or `consult(file).`, and `:- initialization(main).`
runs `main` once loading has finished. Answers are printed to a depth of 100;
use `write/1` to see a large term in full.

## What the language covers

**Syntax.** The full operator-precedence reader: the standard operator table,
user-defined operators through `op/3`, quoted atoms with the usual escapes,
`0'c` character codes, `0x`/`0o`/`0b` numerals, floats with exponents, lists
with tails, curly terms, block and line comments, and the `double_quotes` flag
(codes, chars or atom). Text is UTF-8 throughout: `atom_length/2`,
`atom_codes/2`, `atom_chars/2`, `char_code/2` and `sub_atom/5` all count
characters, not bytes.

**Control.** `,/2`, `;/2`, `->/2`, `*->/2` (soft cut), `\+/1`, `!/0` with
proper cut barriers, `call/1..8` (opaque to cut), `catch/3` and `throw/1`,
`once/1`, `ignore/1`, `forall/2`, `between/3`, `findall/3,4`, `bagof/3`,
`setof/3` (with `^/2` and free-variable grouping), `aggregate_all/3`.

**Builtins.** Type tests, `=/2` and `\=/2`, `==/2` and the standard order
comparisons, `compare/3`, `=@=/2`, `unify_with_occurs_check/2`, arithmetic
(`is/2` and the comparisons, integer and float, with the usual function set),
`functor/3`, `arg/3`, `=../2`, `copy_term/2`, `term_variables/2`,
`numbervars/3`, `setarg/3`, the atom and number conversions, `sub_atom/5`,
`atom_concat/3`, `atomic_list_concat/2,3` (joining and splitting),
`sort/2,4`, `msort/2`, `keysort/2`, `predsort/3`, `assert/1`, `asserta/1`,
`assertz/1`, `retract/1`, `retractall/1`, `clause/2`, `abolish/1`,
`dynamic/1`, `current_predicate/1`, `op/3`, `current_op/3`, the prolog flags,
`nb_setval/2` and `nb_getval/2`, `statistics/2`, `listing/0,1`,
`portray_clause/1`.

**Lists and apply.** `append/2,3`, `member/2`, `memberchk/2`, `length/2`,
`reverse/2`, `nth0/3`, `nth1/3`, `last/2`, `select/3,4`, `subtract/3`,
`intersection/3`, `union/3`, `delete/3`, `exclude/3`, `include/3`,
`partition/4`, `maplist/2..5`, `foldl/4,5`, `sum_list/2`, `max_list/2`,
`min_list/2`, `max_member/2`, `min_member/2`, `numlist/3`, `permutation/2`,
`flatten/2`, `list_to_set/2`, `pairs_keys_values/3`.

**I/O.** `write/1,2`, `print/1,2`, `writeq/1,2`, `write_canonical/1,2`,
`write_term/2,3`, `writeln/1,2`, `nl/0,1`, `tab/1,2`, `read/1,2`,
`read_term/2,3`, `open/3,4`, `close/1`, `current_input/1`, `current_output/1`,
`set_input/1`, `set_output/1`, `with_output_to/2`, and `format/1,2,3` with
`~w ~q ~p ~a ~s ~d ~D ~f ~e ~g ~c ~r ~R ~n ~i ~t ~| ~+ ~*` and `~~`.

**Grammars.** `-->` rules are translated at load time, including pushback
heads, `{}/1`, `!`, `\+`, `call//N` and string literals; `phrase/2,3` drive
them.

## How it works

| File | Contents |
| --- | --- |
| `src/prolog.h` | shared declarations |
| `src/term.c` | heap, arenas, atom table, unification, standard order, copying, the collector |
| `src/parser.c` | tokeniser, operator table, operator-precedence reader |
| `src/write.c` | the term writer (operator aware, quoting, depth limits) |
| `src/arith.c` | arithmetic evaluation |
| `src/db.c` | predicate table, clauses, first-argument indexing |
| `src/machine.c` | the solver: goals, choice points, cut, exceptions |
| `src/builtins.c` | the builtin predicates |
| `src/stream.c` | streams, including in-memory sinks |
| `src/consult.c` | loading programs, error messages |
| `src/main.c` | command line and the interactive toplevel |
| `lib/boot.pl` | the library written in Prolog, compiled into the binary |

**Terms** are tagged cells: variable, atom, integer (64-bit), float, compound.
Compound arguments are stored inline after the header. Atoms are interned in a
hash table, so comparing them is comparing integers.

**Resolution** is structure-copying, and the solver is a flat loop rather than
a recursive one: the current continuation is a linked list of goal frames, and
the alternatives are an explicit choice point stack. Deep recursion in Prolog
costs heap, not C stack. Each goal frame carries a cut barrier — the choice
point stack height when its clause was entered — so `!` is a single assignment
to the stack top, and cut is correctly transparent in `;/2` and opaque in
`call/1`. If-then-else, negation, soft cut and `catch/3` are all built from
the same choice point machinery, with an internal `'$cut'(N)` goal.

**Memory** has three regions. Clauses, global variables and exception balls
live in arenas that are freed as a unit. Everything a computation builds goes
on a chunked heap that choice points mark and backtracking rewinds, so undoing
a computation costs about what making it did. The heap is released to the
newest choice point's mark, so a generator that retries one choice point in
place — `between/3`, `repeat/0`, or backtracking into a set of facts — drives a
failure-driven loop in constant space, while a generator written as a recursive
predicate leaves its newest mark further up the heap on each iteration and
grows with it. What backtracking cannot reclaim —
a long deterministic recursion — is handled by a copying collector: when the
choice point stack is empty and no builtin is mid-flight, the terms reachable
from the goal stack (plus the C roots registered by the toplevel) are copied
into a fresh heap and the old one is released. Forwarding pointers keep shared
structure shared. `make test-gc` runs the whole suite with the collector firing
every 1024 inferences.

**Indexing** filters clauses on the principal functor of the first argument
before any unification, and the next matching clause is looked up before the
current one binds anything — so `p(a)` against a hundred `p(b_i)` facts leaves
no choice point behind.

**Exceptions** copy the ball into an arena before unwinding, so it survives the
heap being rewound, and are rebuilt on the heap when a catcher matches.

## Limitations

These are deliberate, and each would be a substantial piece of work:

- Integers are 64-bit and overflow raises `evaluation_error(int_overflow)`;
  there are no bignums or rationals.
- No modules, tabling, constraints, attributed variables or threads.
- No occurs check by default (`unify_with_occurs_check/2` is available).
  Building a cyclic term with `X = f(X)` is allowed, but printing or copying
  one will not terminate.
- The collector runs only at deterministic points, so a computation that keeps
  a choice point open never collects. Combined with the mark rule above, a
  failure-driven loop over a generator written as a recursive predicate costs
  about a kilobyte an iteration — a million iterations peak at 754 MB, against
  2.8 MB for the same loop over `between/3`, which retries one choice point in
  place.
- Maximum arity is 256; `read_term/2` reports `singletons` as `[]`.
- One `assert`/`retract` cycle keeps the retracted clause until the predicate
  is abolished, so a program that retracts millions of clauses from one
  predicate will hold them.

## Testing

`tests/test.pl` holds 240 tests as `test(Name, Goal)` facts covering
unification and the standard order, arithmetic and its errors, control and cut,
exceptions, all-solutions predicates, term inspection, atoms and UTF-8 text,
sorting, the list library, the database, the reader and writer (including
round-tripping), `format/2`, grammars, streams, and deep recursion under the
collector. `make check` runs them both normally and with the collector
running constantly; `make test-asan` runs both under the sanitizers.

## Roadmap

Known work and deliberate non-goals are listed in [ROADMAP.md](ROADMAP.md).

## Licence

MIT — see [LICENSE](LICENSE).
