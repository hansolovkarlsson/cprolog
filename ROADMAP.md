# Roadmap

Known work, roughly in the order it would pay off. Everything here is a
consequence of decisions described in the
[engine internals](https://hansolovkarlsson.github.io/cprolog/internals.html)
document; nothing is speculative.

## Near term

- **Continuous integration.** No CI runs today: the suite is only ever run by
  hand. A workflow should build and test on every push and pull request, on
  Linux and macOS, with both clang and gcc, running `make check` (the suite
  normally and with the collector forced) and `make test-asan` (the suite under
  the address and undefined behaviour sanitizers). It should also run
  `make doc` and fail if the working tree changes, because the documentation is
  generated and can silently drift from its generators. Tracked in #1.

- **The missing character predicates.** `get_char/1,2`, `peek_char/1,2`,
  `at_end_of_stream/0,1` and `put_char/2` are ISO and are not implemented. The
  stream layer already has the pushback needed for `peek_char`.

- **Eight-byte heap alignment.** Every allocation is rounded to 16 bytes where
  8 would do, so a 24-byte term cell occupies 32. Eight-byte alignment is
  enough for every member of the term union on the supported platforms and
  would cut roughly a quarter off the heap. One line, plus measurement.

- **Real singleton reporting.** `read_term/2,3` accepts `singletons(L)` and
  always reports `[]`. The reader already counts variable occurrences.

- **`open/4` options.** The options list is accepted and ignored; at least
  `alias/1` and `eof_action/1` should be honoured or rejected rather than
  silently dropped.

## Medium term

- **Reclaiming retracted clauses.** A retracted clause is held until its
  predicate is abolished, because a choice point may still point at it. A
  reference count or a generation stamp would let the common case be freed.

- **Lambdas.** There is no `yall`, so `maplist([X]>>Goal, L)` does not work and
  every partial application needs a named helper. A small `>>` implementation
  would remove a papercut that shows up constantly in list code.

- **Error context.** The second argument of `error/2` is always an unbound
  variable. Filling in the predicate indicator where the error was raised would
  make messages considerably more useful.

## Structural

These change the shape of the system rather than adding to it.

- **Collecting while choice points are live.** The collector only runs when the
  choice point stack is empty, because heap marks depend on allocation order
  that a copying collector destroys. Doing better means mark-and-slide
  compaction over a cell heap with object headers — at which point the design
  is most of a WAM. This is the single biggest limitation.

- **Unbounded integers.** Integers are 64-bit and overflow raises
  `evaluation_error(int_overflow)`. Bignums would need an allocation strategy
  for numbers that outlive backtracking.

- **Modules.** The predicate table is flat, so every program shares one
  namespace.

- **Tabling and constraints.** Both are large, self-contained projects that the
  current solver has no hooks for.

## Not planned

- **Competing on raw speed.** Calling a predicate copies its clause, which is
  what a compiling system avoids; that costs a factor of a few against SWI and
  is the price of an engine small enough to read in an afternoon.
- **A distinct string type.** Double-quoted text follows the `double_quotes`
  flag, as in ISO.
