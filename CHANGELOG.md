# Changelog

What has shipped, newest first. [ROADMAP.md](ROADMAP.md) holds what has not.

There are no releases yet, so entries are grouped by the day they landed on
`main`. Commit hashes are given so each entry can be read in full with
`git show`.

## 2026-09-12

### Fixed

- **Thirteen tests had never run.** In the arithmetic section of
  `tests/test.pl`, thirteen tests were written as `test(name, G1, G2)` with no
  parentheses around the conjunction, so they consulted as `test/3` and `test/4`
  facts and the harness's `forall(test(Name, Goal), ...)` never reached them.
  The suite reported 256 from the first commit while the file held 269. All
  thirteen pass; they are `test/2` now, and every count that quoted 256 says
  269. (`af41122`)

### Tests

- 256 → 269. No test was added: the thirteen were there all along.

## 2026-08-28

### Added

- **Level 3 of the tutorial** — negation, the cut, terms and operators of your
  own, and the grammar notation. Ships `tutorial/level3.pl`. The figure draws
  the cut as what the engine implements: a choice point stack height, with the
  caller's entry surviving. (`afbc1cb`)
- **Level 4 of the tutorial** — exceptions, the database, and input and output,
  taking the Level 3 stock room and turning it into a program. Ships
  `tutorial/level4.pl`, `tutorial/orders.txt` and `tutorial/restock.pl`, the
  last of these a complete script driven by `initialization/1`. (`78d43c4`)
- **`make tutorials`** — loads each tutorial program and runs a query out of its
  page, so the published pages cannot drift away from the code they quote.
  Run by CI alongside `make examples`. (`78d43c4`)

### Fixed

- **`max_arity` was three different numbers.** `current_prolog_flag(max_arity, V)`
  answered `unbounded`, `=../2` stopped at 255, the reader at 256, and
  `functor/3` at nothing at all — `functor(T, f, 100000)` built the term, and a
  large enough arity would have overflowed the `int` the arity is stored in.
  `MAX_ARITY` in `src/prolog.h` is now the single definition, set to 256; the
  reader, `=../2` and `functor/3` all use it, and the flag reports the integer
  as ISO asks. Six tests, written against the flag rather than a literal.
  (`8831038`)
- **The exercise disclosure marker rendered as `B8?A0Solutions`.** The shared
  CSS was a plain Python string, so the escape `\25B8` was read as an octal
  escape before the browser ever saw it. The block is a raw string now. This
  was on every published page. (`afbc1cb`)
- **Long note titles overlapped their own body text.** `.note-tag` was `nowrap`
  at a fixed width. It wraps now, and the stacked mobile layout puts the flex
  basis back to `auto` so the basis does not become a height. (`afbc1cb`)
- **`*emphasis*` reached six pages as literal asterisks.** The shared `inline()`
  handled `**bold**` and nothing else. Bold is substituted first, and emphasis
  requires non-space on both sides so a multiplication sign written in prose is
  left alone. (`afbc1cb`)
- A section of Level 3 said three predicates where its table listed four.
  (`ded50bd`)

### Documentation

- The reference records three things it had not: there is **no logical update
  view** (a goal backtracking through a predicate sees clauses asserted after it
  started and skips ones retracted ahead of it); there is no
  `setup_call_cleanup/3`; and `dynamic/1` is a predicate rather than a prefix
  operator, so `:- dynamic foo/1.` is a syntax error here. (`78d43c4`)
- The `max_arity` story is now told consistently in the flags table, the error
  table and *Deviations and limits*, including that the reader reports the limit
  as a syntax error while `=../2` and `functor/3` raise
  `representation_error(max_arity)`. (`8831038`)
- `tutorial/level3.pl` says in the file that `max_of/3` is wrong on purpose, for
  anyone reading it without the page. (`a67b322`)

### Tests

- 250 → 256.

## 2026-08-19

### Added

- **The interpreter.** A structure-copying engine with an iterative solver: the
  continuation is an explicit list of goal frames, alternatives live on a choice
  point stack, and cut is the stack height recorded in each frame, so deep
  Prolog recursion costs heap rather than C stack. Memory is a chunked heap that
  choice points mark and backtracking rewinds, arenas for clauses and exception
  balls, and a copying collector for what backtracking cannot reclaim. With a
  full operator-precedence reader and writer, arithmetic, exceptions, grammars,
  streams, `format/1,2,3`, first-argument indexing, 162 builtin predicates, five
  example programs and a 248-test suite. (`e31b881`)
- **The project site** — `docs/` served by GitHub Pages: a front page, the
  language reference and the engine internals, generated from `tools/` and
  sharing one design system. Plus `ROADMAP.md`. (`c17f96a`, `42b5eb5`)
- **CI** — Linux and macOS, clang and gcc, warnings as errors. Each leg runs the
  suite twice (normally, and with the collector forced every 1024 inferences),
  then the examples, then the whole thing again under the address and undefined
  behaviour sanitizers. A second job regenerates `docs/` and fails if anything
  changed. This closed the roadmap's first item. (`09fcdcf`)
- **Levels 1 and 2 of the tutorial** — facts, rules and the search; then lists
  and collecting answers. (`b25bf4f`, `a47faab`)

### Fixed

Everything below was found by CI on its first run, and none of it reproduced on
the machine the interpreter was written on. See
[POSTMORTEM.md](POSTMORTEM.md).

- **`strdup` is POSIX, not C99.** Under `-std=c99` glibc does not declare it, so
  on Linux the call compiled as an implicit declaration returning `int` and the
  pointer was truncated before being stored — corrupting the stream name in
  `open/3` and the text buffer that `atom_length/2`, `atom_codes/2` and
  `format/2` use for numbers. `pl_strdup` is a four-line C99 equivalent.
  (`c486ab3`)
- **gcc's `-Wmaybe-uninitialized` fired seventeen times**, all on the same
  shape: a local passed by address to one of four accessors that gcc cannot
  prove is written on the success path. The accessors now write their outputs
  before doing anything else, which is both what callers assume and what gcc
  needed to see. Also unwraps one statement `-Wmisleading-indentation` objected
  to, reasonably. (`8fbcf05`)
- **`X is -1 << 2` was undefined behaviour.** It produced the expected `-4` on
  both compilers, but the sanitizer build now aborts on undefined behaviour
  rather than printing and continuing, so it would have failed the moment any
  program exercised it. Doing the shift unsigned gives the same two's complement
  answer with defined behaviour. Two tests cover it. (`f81293b`)

### Tests

- 248 → 250.
