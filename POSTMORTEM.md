# Postmortem

Every defect this project has found in itself, what caused it, and — the part
worth the paper — **what found it**. The tally at the end is the only real
argument for the checks the project now runs on every push.

[JOURNAL.md](JOURNAL.md) is the narrative; [CHANGELOG.md](CHANGELOG.md) is what
shipped. This is the failures.

## Scope

Seventeen defects, in four cohorts that failed for four different reasons:

- **Design era** — five bugs about memory lifetime and ordering, produced by the
  choice to copy structures and manage memory by hand. Fixed before the first
  commit; documented in full in the [engine
  internals](https://hansolovkarlsson.github.io/cprolog/internals.html)
  under *Five bugs this design produced*, and summarised here.
- **Portability** — three bugs that existed from the first commit and were
  invisible on the machine the interpreter was written on. All three fell out of
  CI's first run.
- **Consistency** — eight defects in which the code, the documentation and the
  flag reporting the behaviour did not agree with each other. All found while
  writing the tutorials.
- **The suite about itself**: one defect in the test file, invisible to the
  suite because the suite was the thing that was wrong. Found by an audit that
  counted the file against the runner.

## Cohort A — the design era

Five bugs, every one a mistake about **lifetime** or about **when a value is
read**. That is not a coincidence: it is the specific failure mode of a
structure-copying engine with three memory regions and no compiler checking
which is which.

| Symptom | Cause | Found by |
| --- | --- | --- |
| A nested `findall` read freed memory | Instantiating a clause shared constant cells instead of copying them; a `findall` buffer is freed while its results are live | Address sanitizer |
| `clause/2` and `retract/1` returned only their first solution | The next candidate clause was chosen *after* head unification had bound the arguments, so indexing rejected everything remaining | Test suite |
| A soft cut produced an extra answer | The flag marking the alternative dead was trailed, so backtracking brought it back | Test suite |
| Retrying a choice point read freed memory | The if-then-else alternative was built *after* the choice point took its heap mark | Reading the code |
| `write_canonical` output would not read back | The atom `.` was written unquoted, and `atom_codes` returned bytes rather than character codes | Test suite |

Two of these are worth restating as rules, because both are easy to reintroduce:

- **Anything a choice point refers to must be older than the mark it holds.**
  The fix was to move the constants involved outside the heap entirely.
- **Anything derived from a call must be derived before the call binds
  anything.** Indexing that reads state unification is about to change is
  indexing that is always one step stale.

The internals page adds the observation that none of the five was found by
*using* the interpreter — only by the sanitizer, by tests that asked for every
solution rather than the first, and by reading. That is the argument for
`make test-asan` and for writing `\+ more_solutions` style tests.

## Cohort B — portability

Three bugs, all present from the first commit, none reproducible on the
development machine, all found by CI's first run. Adding the matrix was the
roadmap's first item; it paid for itself immediately.

### `strdup` is POSIX, not C99

Under `-std=c99`, glibc does not declare `strdup`. The call therefore compiled
as an implicit declaration returning `int`, and **the pointer was truncated to
32 bits before being stored**. On Linux this corrupted the stream name in
`open/3` and the text buffer that `atom_length/2`, `atom_codes/2` and
`format/2` use for numbers.

macOS headers declare `strdup` whatever the standard setting, which is exactly
why it was never seen locally. The fix is `pl_strdup`, four lines of C99.
(`c486ab3`)

*What this says:* a warning suppressed by one platform's headers is not a
warning that has been dealt with. `-std=c99` means the standard library is
smaller than habit assumes.

### Seventeen gcc warnings clang never mentioned

`-Wmaybe-uninitialized` fired seventeen times, all on one shape: a local passed
by address to one of four accessor functions, which gcc cannot prove is written
on the success path.

The tempting fix — initialise seventeen call sites — was rejected in favour of
fixing the four accessors so they write their outputs before doing anything
else. That is what every caller already assumed, so the warnings were pointing
at a real (if latent) contract that had never been written down. (`8fbcf05`)

*What this says:* when a warning fires seventeen times in one shape, the warning
is describing an interface, not seventeen accidents. Fix the interface.

### `X is -1 << 2` was undefined behaviour

Shifting a negative value left is undefined in C. It produced the expected `-4`
on both compilers, every time, which is the worst way for undefined behaviour to
behave. It surfaced when the sanitizer build was tightened to **abort** on
undefined behaviour rather than print and continue — at which point it would
have failed the build the moment any program exercised the path. Doing the shift
unsigned gives the same two's complement answer with defined behaviour, and two
tests now exercise it under the sanitizer. (`f81293b`)

*What this says:* `-fsanitize=undefined` without `-fno-sanitize-recover` is a
log file, not a test. A finding has to fail the run or it scrolls past.

## Cohort C — consistency

Eight defects in which two parts of the project disagreed. All were found while
writing the four tutorial levels, which is the interesting part: writing
documentation is a different test from writing tests, and it found things the
256-test suite never would have.

### `max_arity` was three different numbers

`current_prolog_flag(max_arity, V)` answered `unbounded`. `=../2` stopped at
255 — its buffer held the functor name and 255 arguments, and the bound was
checked against the list length rather than the arity. The reader stopped at
256. And `functor/3` **had no check at all**: `functor(T, f, 100000)` built the
term, and a large enough arity would have overflowed the `int` the arity is
stored in.

Found by writing a sentence in the reference and then testing whether it was
true. `MAX_ARITY` in `src/prolog.h` is now the single definition; all three
paths use it, and the flag reports the integer. (`8831038`)

*What this says:* a limit that appears in more than one place is not a limit, it
is a coincidence waiting to be discovered. And a flag that reports a policy the
code does not enforce is worse than no flag.

### The disclosure marker rendered as `B8?A0Solutions`

The shared CSS block was a plain Python string. `content: "\25B8\00A0"` — a
perfectly good CSS escape for `▸` plus a non-breaking space — was read by
**Python** first, where `\25` is an octal escape. The browser received a control
character, `B8`, a NUL and `A0`.

Live on every published page since the site went up. Found by rendering a page
and looking at it. The block is a raw string now. (`afbc1cb`)

*What this says:* generated markup passes through two languages' escaping rules,
and the first one wins silently.

### Note titles overlapped their own body text

`.note-tag` was `white-space: nowrap` at a fixed `7.5rem`, so any title longer
than that overflowed into the prose beside it. Also live since the site went up,
on pages that had been reviewed. Found by rendering. (`afbc1cb`)

### `*emphasis*` reached six pages as literal asterisks

The shared `inline()` handled `**bold**` and nothing else, so every author's
single-asterisk emphasis was published verbatim. Found by grepping the rendered
output for asterisks that had survived. (`afbc1cb`)

*What the last three say together:* the pages are generated, so they were
checked by regenerating them — which proves only that the generator is
deterministic. Three defects sat in the output for nine days because nobody had
**looked at** it.

### Two deviations from ISO that nothing recorded

Writing Level 4 turned up two behaviours the reference did not mention:

- **There is no logical update view.** A goal backtracking through a predicate
  sees clauses asserted after it started, and skips clauses retracted ahead of
  it. This announced itself by **hanging**: a transcript query that asserted to
  the predicate it was walking ran forever. Retracting the clause the goal is
  currently on is safe; nothing else is.
- **There is no `setup_call_cleanup/3`**, and `dynamic/1` is a predicate rather
  than a prefix operator, so `:- dynamic foo/1.` is a syntax error.

Neither is a bug — both are consequences of a small implementation — but the
reference claims to list *anything the interpreter does not provide*, and it did
not list these. Both are in *Deviations and limits* now. (`78d43c4`)

*What this says:* the deviations list decays silently, because nothing tests a
list of absences. The only thing that finds a missing entry is somebody trying
to do the thing.

### Two worked exercise solutions were wrong

Both in a draft of Level 4, both caught by running them:

- A solution that handled some exceptions and let others through by letting the
  recovery **fail**. A failing recovery does not re-throw — `catch/3` simply
  fails and the ball is gone. The correct form has to `throw/1` it again
  explicitly.
- A cleanup predicate written as `catch(Goal, E, true)` followed by the cleanup
  goals. That handles success and exceptions but not **failure**: a failing Goal
  makes `catch/3` fail and the cleanup never runs.

Both were plausible enough to write down and wrong enough to teach the reader a
bug. Neither would have been caught by re-reading.

*What this says:* worked solutions are code. The fact that they live in a
document does not change what they are.

## Cohort D — the suite about itself

One defect, and it gets a cohort of its own because it failed for a reason none
of the three above name: the check that would have found it was the check that
had it.

### Thirteen tests that never ran

The arithmetic section of `tests/test.pl` held thirteen tests written as

    test(ar_add,          X is 2 + 3, X =:= 5).

with no parentheses around the conjunction, next to a hundred written as
`test(name, (G1, G2))`. Prolog reads the first form as a fact of arity three,
or four for `ar_intdiv`, and the harness runs `forall(test(Name, Goal), ...)`,
which is `test/2`. The thirteen consulted without complaint, sat in the database
under a name nothing queried, and the suite printed **256** from the first
commit (`e31b881`) while the file held 269.

Every record quoted the 256: the README twice, this document, the journal, the
site's front page. All of them were true of what ran and none of them was true
of what was written.

Found on 2026-09-12 by an audit whose rule is that every number in its report is
one it watched come out of a command. It counted `^test\(` lines in the file,
got 269, counted what the harness enumerated, got 256, and `comm` named the
thirteen. Run by hand as conjunctions, all thirteen pass: the interpreter was
never wrong about arithmetic, only the suite about itself. They are `test/2` now,
and the suite is 269. (`af41122`)

*What this says:* a suite reports what it ran, not what was written, and the
gap between the two is a number no check was producing. A count that has been
stable since the first commit is not a count that has been verified; it is one
nobody has had a reason to look at. And the day-three lesson has a mirror
image: green is not the same as quiet, and quiet is not the same as complete.

## What found what

| Found by | Count |
| --- | --- |
| Writing the documentation, then testing the claim | 5 |
| CI's first run (matrix, `-Werror`, sanitizer configuration) | 3 |
| The test suite | 3 |
| Rendering the pages and looking at them | 3 |
| Address sanitizer | 1 |
| Reading the code | 1 |
| An audit counting the test file against the runner | 1 |

Two things stand out.

**The test suite found three of seventeen.** It is a good suite — 269 tests,
run twice per leg, run again under two sanitizers — and it found under a fifth
of the defects. Everything it found was a wrong *answer*. Everything it missed
was a wrong *limit*, a wrong *platform assumption*, a wrong *claim in the
documentation*, or, in the last case, a wrong *count of itself*, and no
realistic number of additional tests would have changed that.

**Writing the documentation found the most.** Five defects, and they were the
ones nothing else could have reached, because the question a document asks is
"is this sentence true?" — which is a different question from "does this goal
succeed?". The most productive single activity in the project was writing a
tutorial for a beginner, because a beginner's questions have no respect for
which parts were carefully implemented.

## What changed as a result

Each standing check exists because of something above:

| Check | Added because of |
| --- | --- |
| The build matrix, Linux and macOS, clang and gcc, `-Werror` | `strdup`, the seventeen gcc warnings |
| `-fno-sanitize-recover=undefined` | the shift, which the sanitizer had been printing and continuing past |
| `make test-asan` on every leg | the use-after-free class; it found one of the two directly |
| `make check` running the suite with the collector forced | the collector, which only runs when the computation is deterministic and so is never exercised by an ordinary run |
| `make doc` + `git diff --exit-code` | pages drifting from their generators |
| `make tutorials` | four tutorial programs that nothing was loading |
| Tests written against `current_prolog_flag(max_arity, N)` rather than `256` | `max_arity`, so the tests stay honest if the limit moves |

## What is probably still wrong

Stated plainly, since the pattern above is that the unlisted things are the
expensive ones:

- **The deviations list is still incomplete.** Two entries were added by
  accident, in the course of writing one tutorial level. There is no reason to
  think that was the last of them.
- **Nothing systematically checks the reference against the interpreter.** Every
  signature in it was verified by hand once. A predicate whose behaviour changes
  will not update its own entry.
- **The error-context argument is always unbound**, so every `error/2` term the
  interpreter raises is missing the information that would say where it came
  from. That is on the roadmap, and until it is done, debugging anything
  non-trivial is harder than it should be.
- **The reader reports the arity limit as a syntax error**, not
  `representation_error(max_arity)`. Documented rather than fixed, because
  fixing it means reworking the parser's error path.
- **Nothing stops a test from consulting under the wrong arity again.** The
  thirteen were fixed by hand; the harness still runs `test/2` and says nothing
  about a `test/3` beside it. A harness that refused to start while any other
  arity of `test` existed would have failed on the first commit.
