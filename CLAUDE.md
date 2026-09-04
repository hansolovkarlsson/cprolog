# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Start here

`scratch/daily-standup.md` — written at the end of the previous working day to
be read at the start of the next: where the tree was left, what went in, and
what is outstanding. `scratch/` is gitignored and is not part of this
repository, so the file is absent on a fresh clone and on any day that was not
closed out. When it is absent, `git log` and the documents named below are the
way in.

## What this is

A Prolog interpreter written from scratch in C99 — reader, engine, garbage
collector and library. No dependencies beyond libc and libm.

## Commands

`make`, `make test`, `make check`, `make test-gc`, `make test-asan`,
`make tutorials`, `make examples`, `make clean`.

## The records

**They are at the repository root, not in `docs/`:** `JOURNAL.md`,
`POSTMORTEM.md`, `ROADMAP.md`, `CHANGELOG.md`.

`JOURNAL.md` is why, in the order it happened; `POSTMORTEM.md` is what a defect
taught and, more to the point, what found it; `ROADMAP.md` is what is left;
`CHANGELOG.md` is what shipped and when — and here it also holds the finished
work that a separate `COMPLETED.md` would otherwise carry, because `ROADMAP.md`
says entries move there when they are done.

Each of those opens with a note stating its own job. That note is the
specification for what belongs in the document — follow it over any general
instruction, including this one.

`docs/` holds **generated HTML only** — `make doc` builds it from the Markdown
above via `tools/gen_*.py`. Never hand-edit a file in `docs/`; edit the
Markdown at the root and regenerate.
