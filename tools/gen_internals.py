# -*- coding: utf-8 -*-
"""Generates doc/internals.html, the engine design document.

    Run from the top of the source tree:  make doc

    The HTML is generated, so edit the content here rather than in
    doc/internals.html, which is overwritten.
"""
from docpage import (esc, inline, para, ul, pre, table, note, preds, figure,
                     section, render)

# ---------------------------------------------------------------- figures

def svg(body, w, h, label):
    return ('<div class="svg-frame"><svg viewBox="0 0 %d %d" role="img" '
            'aria-label="%s" xmlns="http://www.w3.org/2000/svg">'
            '<defs><marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" '
            'markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
            '<path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker>'
            '<marker id="ara" viewBox="0 0 10 10" refX="9" refY="5" '
            'markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
            '<path d="M0,0 L10,5 L0,10 z" fill="var(--accent)"/></marker>'
            '</defs>%s</svg></div>' % (w, h, esc(label), body))

BOX = ('<rect x="%d" y="%d" width="%d" height="%d" rx="3" fill="none" '
       'stroke="currentColor" stroke-width="1.2" opacity="%s"/>')
TXT = ('<text x="%d" y="%d" font-family="IBM Plex Mono, monospace" '
       'font-size="%d" fill="currentColor" text-anchor="%s" opacity="%s">%s</text>')
LBL = ('<text x="%d" y="%d" font-family="IBM Plex Sans, sans-serif" '
       'font-size="%d" fill="currentColor" text-anchor="%s" opacity="%s" '
       'letter-spacing="0.06em">%s</text>')

def box(x, y, w, h, op='0.55'): return BOX % (x, y, w, h, op)
def txt(x, y, s, size=12, anchor='start', op='0.95'):
    return TXT % (x, y, size, anchor, op, esc(s))
def lbl(x, y, s, size=10, anchor='start', op='0.6'):
    return LBL % (x, y, size, anchor, op, esc(s))
def line(x1, y1, x2, y2, arrow=True, accent=False, dash=None):
    return ('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="1.2"%s%s/>'
            % (x1, y1, x2, y2,
               'var(--accent)' if accent else 'currentColor',
               ' marker-end="url(#%s)"' % ('ara' if accent else 'ar') if arrow else '',
               ' stroke-dasharray="%s"' % dash if dash else ''))
def abox(x, y, w, h):
    return ('<rect x="%d" y="%d" width="%d" height="%d" rx="3" fill="var(--accent-bg)" '
            'stroke="var(--accent)" stroke-width="1.4"/>' % (x, y, w, h))

# --- Figure A: the three stacks and what a choice point marks
def fig_stacks():
    p = []
    p.append(lbl(0, 14, 'GOAL CONTINUATION'))
    for i, (name, y) in enumerate([('q(X), r(X)', 30), ('s(X)', 78), ('true', 126)]):
        p.append(box(0, y, 150, 34))
        p.append(txt(10, y + 15, name, 11))
        p.append(lbl(10, y + 28, 'cut barrier %d' % (2 - i), 9))
        if y < 126:
            p.append(line(75, y + 34, 75, y + 44))
    p.append(lbl(215, 14, 'CHOICE POINTS'))
    p.append(box(215, 110, 170, 46))
    p.append(txt(225, 128, 'CP_CLAUSES  p/1', 11))
    p.append(lbl(225, 143, 'clause 2 of 3', 9))
    p.append(abox(215, 30, 170, 72))
    p.append(txt(225, 48, 'CP_CLAUSES  q/1', 11))
    p.append(lbl(225, 64, 'next clause', 9))
    p.append(lbl(225, 79, 'trail mark', 9))
    p.append(lbl(225, 94, 'heap mark', 9))
    for x0, x1, title in [(455, 499, 'TRAIL'), (578, 622, 'HEAP')]:
        p.append(lbl(x0, 14, title))
        p.append(box(x0, 30, 44, 130))
        p.append('<rect x="%d" y="30" width="44" height="42" fill="var(--accent-bg)"/>' % x0)
        p.append('<line x1="%d" y1="72" x2="%d" y2="72" stroke="var(--accent)" '
                 'stroke-width="1.6"/>' % (x0, x1))
    p.append(line(390, 82, 452, 72, accent=True))
    p.append(line(390, 96, 575, 72, accent=True))
    p.append(lbl(505, 56, 'undone', 9))
    p.append(lbl(505, 96, 'kept', 9))
    p.append(lbl(628, 56, 'released', 9))
    p.append(lbl(628, 96, 'kept', 9))
    p.append(lbl(455, 178, 'the mark is where backtracking puts each one back', 9))
    return svg(''.join(p), 700, 195,
               'A choice point stores marks into the trail and the heap; '
               'backtracking rewinds both to those marks.')

# --- Figure B: cut is one assignment to the stack height
def fig_cut():
    p = []
    cols = [(0, 'on entry to p/1', 2), (240, 'inside the body', 5), (480, 'after the !', 2)]
    for x, caption, n in cols:
        p.append(lbl(x, 16, caption, 10, op='0.75'))
        for i in range(5):
            y = 170 - i * 26
            if i < n:
                p.append(box(x, y, 130, 22, '0.55'))
                p.append(txt(x + 10, y + 15, 'choice point %d' % (i + 1), 10, op='0.8'))
            else:
                p.append('<rect x="%d" y="%d" width="130" height="22" rx="3" '
                         'fill="none" stroke="currentColor" stroke-width="1" '
                         'stroke-dasharray="3 3" opacity="0.22"/>' % (x, y))
    p.append('<line x1="0" y1="142" x2="610" y2="142" stroke="var(--accent)" '
             'stroke-width="1.2" stroke-dasharray="4 3"/>')
    p.append(LBL % (620, 146, 10, 'start', '0.9', 'barrier'))
    p.append(line(425, 74, 425, 138, accent=True))
    p.append(txt(433, 104, '!', 13))
    p.append(lbl(0, 214, 'the frame records the stack height its clause was entered at; '
                         '! assigns the top back to it', 10, op='0.8'))
    return svg(''.join(p), 700, 230,
               'Cut restores the choice point stack to the height recorded in the '
               'goal frame when its clause was entered.')

# --- Figure C: why one loop is constant space and the other is not
def fig_space():
    p = []
    # left: one reused mark
    p.append(lbl(0, 14, 'ONE CHOICE POINT, RETRIED IN PLACE'))
    p.append(lbl(40, 40, 'HEAP', 9))
    p.append('<rect x="40" y="150" width="54" height="46" fill="var(--accent-bg)" '
             'stroke="currentColor" stroke-width="1.2" opacity="0.9"/>')
    p.append('<rect x="40" y="126" width="54" height="24" fill="none" '
             'stroke="currentColor" stroke-width="1" stroke-dasharray="3 3" opacity="0.45"/>')
    p.append('<line x1="34" y1="150" x2="100" y2="150" stroke="var(--accent)" '
             'stroke-width="1.8"/>')
    p.append(lbl(106, 154, 'the one mark', 9))
    p.append(lbl(106, 134, 'one iteration', 9))
    p.append(line(196, 132, 130, 147, accent=True))
    p.append(lbl(200, 128, 'released', 9))
    p.append(lbl(200, 140, 'every retry', 9))
    p.append(lbl(0, 224, 'between/3, repeat/0, or backtracking into facts', 10, op='0.8'))
    p.append(lbl(0, 240, '1M iterations, 2.8 MB peak', 11, op='0.95'))
    # right: marks climbing
    p.append(lbl(380, 14, 'A GENERATOR WRITTEN AS A RECURSIVE PREDICATE'))
    p.append(lbl(420, 40, 'HEAP', 9))
    p.append('<rect x="420" y="76" width="54" height="120" fill="var(--accent-bg)" '
             'stroke="currentColor" stroke-width="1.2" opacity="0.9"/>')
    p.append('<rect x="420" y="52" width="54" height="24" fill="none" '
             'stroke="currentColor" stroke-width="1" stroke-dasharray="3 3" opacity="0.45"/>')
    for k, y in enumerate([166, 136, 106, 76]):
        p.append('<line x1="414" y1="%d" x2="480" y2="%d" stroke="var(--accent)" '
                 'stroke-width="1.4"/>' % (y, y))
        p.append(lbl(488, y + 4, 'mark %d' % (k + 1), 9))
    p.append(line(596, 58, 530, 68, accent=True))
    p.append(lbl(600, 54, 'released', 9))
    p.append(lbl(600, 66, 'every retry', 9))
    p.append(lbl(488, 196, 'kept: nothing below the', 9))
    p.append(lbl(488, 208, 'newest mark can go', 9))
    p.append(lbl(380, 224, 'each iteration leaves its mark higher up the heap', 10, op='0.8'))
    p.append(lbl(380, 240, '1M iterations, 754 MB peak', 11, op='0.95'))
    return svg(''.join(p), 700, 250,
               'A generator that retries one choice point reuses a single heap mark '
               'and runs in constant space; one written as a recursive predicate '
               'pushes the mark forward each iteration, so nothing older can be '
               'released.')

# --- Figure D: forwarding pointers keep sharing shared
def fig_gc():
    p = []
    p.append(lbl(0, 14, 'BEFORE'))
    p.append(box(0, 26, 250, 130))
    p.append(box(20, 44, 100, 30))
    p.append(txt(30, 63, 'f/2', 11))
    p.append(box(20, 106, 100, 30))
    p.append(txt(30, 125, 'g(1)', 11))
    p.append(line(60, 74, 60, 102))
    p.append(line(110, 74, 78, 102))
    p.append(lbl(130, 96, 'both arguments', 9))
    p.append(lbl(130, 108, 'point at one cell', 9))
    p.append(line(262, 96, 302, 96, accent=True))
    p.append(lbl(258, 84, 'copy', 9))
    p.append(lbl(330, 14, 'AFTER'))
    p.append(box(330, 26, 330, 130))
    for y in (44, 106):
        p.append('<rect x="350" y="%d" width="100" height="30" rx="3" fill="none" '
                 'stroke="currentColor" stroke-width="1" stroke-dasharray="3 3" '
                 'opacity="0.4"/>' % y)
        p.append(txt(360, y + 19, 'FWD', 11, op='0.55'))
    p.append(abox(530, 44, 100, 30))
    p.append(txt(540, 63, 'f/2', 11))
    p.append(abox(530, 106, 100, 30))
    p.append(txt(540, 125, 'g(1)', 11))
    p.append(line(452, 59, 526, 59, accent=True))
    p.append(line(452, 121, 526, 121, accent=True))
    p.append(line(570, 74, 570, 102, accent=True))
    p.append(line(618, 74, 588, 102, accent=True))
    p.append(lbl(350, 176, 'old cells, forwarded', 9))
    p.append(lbl(530, 176, 'the copy', 9))
    return svg(''.join(p), 700, 190,
               'Copying a term leaves a forwarding pointer in the old cell, so the '
               'second reference to a shared subterm finds the copy that already exists.')

# ---------------------------------------------------------------- sections

section('shape', 'The shape of the interpreter', ''.join([
    para("C Prolog resolves goals by copying structures, not by compiling to an "
         "abstract machine. There is no WAM, no register allocation and no clause "
         "compiler: a clause is stored as a term, and calling it copies that term with "
         "fresh variables. That costs some speed against a compiling system and buys "
         "an engine small enough to hold in your head — the whole solver is one "
         "606-line file."),
    para("Two decisions shape everything else. The solver is a flat loop over an "
         "explicit goal list rather than a recursive C function, so the depth of a "
         "Prolog computation costs heap rather than C stack. And memory is reclaimed "
         "primarily by backtracking rather than by collection, so a choice point "
         "records where the heap stood and failing rewinds to it."),
    table(['File', 'Lines', 'What lives there'], [
        ['src/prolog.h', '341', 'the shared declarations: terms, marks, frames, choice points'],
        ['src/term.c', '824', 'heap and arenas, atom table, unification, standard order, copying, the collector'],
        ['src/parser.c', '914', 'tokeniser, operator table, operator-precedence reader'],
        ['src/write.c', '328', 'the term writer'],
        ['src/arith.c', '401', 'arithmetic evaluation'],
        ['src/db.c', '148', 'predicate table, clause lists, first-argument indexing'],
        ['src/machine.c', '606', 'the solver: goal frames, choice points, cut, exceptions'],
        ['src/builtins.c', '2304', 'the builtin predicates and their dispatch table'],
        ['src/stream.c', '152', 'streams, including in-memory sinks'],
        ['src/consult.c', '227', 'loading programs, error messages'],
        ['src/main.c', '269', 'command line and the interactive toplevel'],
        ['lib/boot.pl', '633', 'the library written in Prolog, compiled into the binary'],
    ], 'mono1'),
    para("`lib/boot.pl` is turned into a C string by `tools/pl2c.awk` at build time and "
         "consulted at start-up, so predicates that are easier to write in Prolog — "
         "`bagof/3`, the list library, the grammar translator, `listing/1` — are "
         "written in Prolog."),
]))

section('terms', 'Terms in memory', ''.join([
    para("A term is a 24-byte cell: a one-byte tag and a union."),
    pre("""
struct Term {
    unsigned char tag;              /* VAR ATOM INT FLT STR FWD */
    union {
        struct { Term *ref; unsigned long serial; } v;
        int atom;                   /* index into the atom table */
        long long i;
        double f;
        struct { int functor; int arity; Term **args; } s;
    } u;
};
"""),
    para("A compound term is allocated as one block — the cell followed by its argument "
         "pointers — and `args` points just past the header, so reaching an argument is "
         "one indirection and a compound term is one allocation rather than two."),
    para("Atoms are interned in a hash table and a term holds the index, so comparing "
         "atoms is comparing integers; the text is only needed for printing and for the "
         "standard order. An unbound variable is a cell whose `ref` is null, and binding "
         "it writes that pointer. A variable also carries a serial number, which gives "
         "the standard order on variables a stable answer and lets unification always "
         "bind the younger variable to the older."),
    note('impl', 'Allocation granularity',
         "The heap rounds every allocation up to 8 bytes, which is the alignment of the "
         "widest member of the union on the platforms this targets, so a 24-byte cell "
         "occupies 24 and a two-argument compound 40. It rounded to 16 until 2026-09-12, "
         "when a 24-byte cell occupied 32; the change was one constant in two allocators "
         "and took a fifth off a list-heavy heap: 115 MB to 93 MB for a 200,000-element "
         "numlist, measured with the collector held off."),
]))

section('unify', 'Unification and the trail', ''.join([
    para("Unification is the ordinary recursive walk, with two details that matter."),
    para("It recurses into the first n-1 arguments and loops on the last, so a list — "
         "which is nested entirely in its tails — is unified iteratively. Without that, "
         "unifying two 100,000-element lists would need 100,000 C frames. Comparison and "
         "both copying routines use the same shape."),
    para("Every binding is pushed on the trail, an array of entries recording the "
         "variable that was bound. Undoing is a loop that walks the trail back to a mark, "
         "writing null into each variable. There is no attempt to avoid trailing bindings "
         "that could not need undoing — the check costs about as much as the push."),
    para("A trail entry can also record an integer slot and its old value. Exactly one "
         "thing uses that: the flag that marks a `catch/3` frame inactive once its goal "
         "has succeeded, which has to come back if the goal is re-entered on "
         "backtracking."),
    note('impl', 'No occurs check',
         "Unification binds without checking whether the variable occurs in the term, so "
         "`X = f(X)` builds a cycle. Copying and printing a cyclic term do not terminate. "
         "The collector, by contrast, is cycle-safe: it forwards a cell before it copies "
         "the children."),
]))

section('loop', 'The solver loop', ''.join([
    para("The continuation is a linked list of goal frames, each holding a goal, the "
         "next frame, and one integer — the cut barrier."),
    pre("struct Goal { Term *goal; Goal *next; size_t cutb; };"),
    para("The loop takes the first frame, executes its goal, and repeats. Executing a "
         "goal never calls the loop recursively; it rewrites the goal list instead. "
         "Conjunction pushes two frames, `call/1` pushes one with a fresh barrier, and a "
         "user predicate pushes the body of the clause it selected. A Prolog recursion a "
         "million deep is a million heap allocations and a C stack that never grows."),
    pre("""
for (;;) {
    if (!m_goals) return PL_OK;             /* nothing left to prove */
    rc = execute(deref(m_goals->goal), m_goals);
    if (rc == PL_FAIL  && !backtrack(base))   return PL_FAIL;
    if (rc == PL_ERROR && !handle_throw(base)) return PL_ERROR;
}
"""),
    para("`execute` dispatches in three steps. First the control constructs, which are "
         "recognised structurally — `,/2`, `;/2`, `->/2`, `*->/2`, `\\+/1`, `!`, "
         "`call/N`, `catch/3`, `throw/1` — because they have to manipulate the goal list "
         "and the choice point stack directly. Then the builtin table, a hash on functor "
         "and arity. Only then the predicate table, and if nothing is found, an existence "
         "error."),
    para("That order is also the precedence rule of the language: a control construct "
         "cannot be redefined, a builtin written in C cannot be redefined, and everything "
         "else can."),
    note('impl', 'Re-entering the solver',
         "`findall/3`, `forall/2` and `with_output_to/2` do call the loop again, from "
         "inside a builtin. A nesting counter records that, because a builtin holding C "
         "pointers into the heap must not have the collector run underneath it."),
]))

section('choice', 'Choice points and backtracking', ''.join([
    para("A choice point is 120 bytes recording everything needed to resume: the goal "
         "list to restore, the cut barrier to hand out, marks into the trail and the "
         "heap, and whatever the particular kind of alternative needs."),
    figure(fig_stacks(),
           "A choice point stores marks into the trail and the heap. Backtracking undoes "
           "the trail to its mark, releases the heap to its mark, restores the saved goal "
           "list, and resumes — so undoing a computation costs about what making it did."),
    table(['Kind', 'Created by', 'Retry does'], [
        ['CP_CLAUSES', 'a call with more than one matching clause',
         'try the next matching clause'],
        ['CP_ALT', 'disjunction, if-then-else, soft cut, negation',
         'run the stored alternative goal'],
        ['CP_ITER', 'clause/2 and retract/1', 'move to the next matching clause'],
        ['CP_REDO', 'between/3 and repeat/0',
         'produce the next solution from state held in the frame itself'],
        ['CP_CATCH', 'catch/3', 'nothing — it is a marker for the exception unwinder'],
    ], 'mono1'),
    para("The stack is an array that doubles as it grows, which is why choice points are "
         "referred to by index rather than by pointer: a cut is an assignment to the "
         "stack height, and an index survives the array being moved."),
    note('impl', 'Retrying in place',
         "`CP_REDO` is the one kind whose frame is updated rather than replaced. Its "
         "retry reads a counter out of the frame, writes the next one back, and returns "
         "to the same heap mark it took when it was created — which is what makes a "
         "generator cost nothing per iteration."),
]))

section('cut', 'Cut', ''.join([
    para("Cut is the part of Prolog that most often turns into a special case. Here it is "
         "one integer. Every goal frame carries the height of the choice point stack at "
         "the moment its clause was entered; `!` assigns that height back to the top."),
    figure(fig_cut(),
           "The barrier is recorded when the clause is entered and never recomputed, so "
           "cut is a single assignment no matter how many alternatives were created in "
           "between."),
    para("Because the barrier travels in the frame rather than in a global, cut lands "
         "correctly in nested control structures for free. The two branches of a "
         "disjunction are pushed with the enclosing clause's barrier, so a cut inside "
         "either one cuts the clause — cut is transparent to `;`. `call/1` pushes its "
         "goal with the current stack height instead, so a cut inside is local to the "
         "call — cut is opaque to `call/1`."),
    para("If-then-else, negation and soft cut are all assembled from a choice point and "
         "an internal goal. `(C -> T ; E)` pushes a `CP_ALT` holding `E`, then runs `C` "
         "with the continuation `'$cut'(N), T`, where N is the index of that choice "
         "point. If `C` succeeds, `'$cut'(N)` drops the alternative and everything `C` "
         "left behind; if it fails, backtracking finds the alternative and runs `E`. "
         "Negation is the same shape with `E = true` and a `fail` after the cut."),
    para("Soft cut differs by one line: instead of cutting back, `'$softcut'(N)` marks "
         "the alternative dead, so the alternatives inside `C` survive and `T` runs for "
         "each of them."),
    note('impl', 'A bug worth keeping in mind',
         "That mark must not be trailed. Trailing it looked right — it is a mutation, and "
         "mutations are undone on backtracking — but backtracking into the condition then "
         "restored the alternative, and `(member(X,[1,2]) *-> true ; none)` produced a "
         "third answer, `none`. Once the condition has succeeded the alternative is gone "
         "for good, including on re-entry."),
]))

section('exceptions', 'Exceptions', ''.join([
    para("`throw/1` has a lifetime problem: the ball is a term on the heap, and the "
         "unwinding that follows releases the heap the ball lives in. So the ball is "
         "copied out into an arena of its own before anything is unwound, and rebuilt on "
         "the heap once a catcher matches."),
    para("`catch/3` pushes a `CP_CATCH` frame and runs its goal with the continuation "
         "`'$exit_catch'(N)`. The unwinder walks the choice point stack downward, undoing "
         "the trail and releasing the heap at each frame, and stops at the first live "
         "`CP_CATCH` whose catcher unifies with the ball — bindings undone first, so the "
         "recovery goal starts from the state the catch was entered in."),
    para("`'$exit_catch'(N)` is what makes an exception thrown *after* the guarded goal "
         "succeeded pass over this frame instead of being caught by it. If the frame is "
         "on top it is simply popped; otherwise it is marked inactive, and that mark is "
         "trailed, because backtracking into the guarded goal has to make the frame live "
         "again. It is the one place in the system where a trail entry records something "
         "other than a variable binding."),
    pre("""
?- catch(( catch(true, e, true), throw(e2) ), e2, true).
true.                        % the inner catch is exited, so e2 passes it by
"""),
]))

section('clauses', 'Clauses and indexing', ''.join([
    para("A clause is stored in a form halfway to being compiled. Head and body are "
         "copied into a private arena with the variables replaced by cells whose serial "
         "number is an index — variable 0, variable 1, and so on — and the count is kept "
         "with the clause."),
    para("Calling it allocates an array of that many null pointers and rebuilds the term "
         "on the heap, filling variables in as it meets them. Head arguments are "
         "instantiated one at a time and unified as they are built, so a call that fails "
         "on the first argument never builds the rest of the head."),
    para("Freeing is the reason for the private arena: one `arena_free` releases the "
         "whole clause. `retract/1` unlinks the clause from the predicate but does not "
         "free it — a choice point may still hold a pointer to it — and puts it on a "
         "garbage list that is released when the predicate is abolished."),
    '<h3>First-argument indexing</h3>',
    para("Each clause records a tag and a key derived from the principal functor of its "
         "first head argument: the atom index for an atom, the value for an integer, the "
         "functor and arity packed together for a compound. A clause whose first argument "
         "is a variable or a float is not indexed and always matches."),
    para("The filter is deliberately approximate. Packing a functor and arity into one "
         "integer, or truncating a 64-bit value to fit, can make two different keys "
         "collide — but only ever in the direction of trying a clause that then fails to "
         "unify, never of skipping one that would have matched."),
    para("The real gain is not the skipping, it is the lookahead. The next matching "
         "clause is found *before* the current one is tried, so a call that matches only "
         "one clause pushes no choice point at all and the predicate is deterministic:"),
    pre("""
p(a).  p(b).  p(c).  p(d).

?- p(c).
true.                        % no choice point, no prompt for more solutions
"""),
    note('impl', 'The lookahead has to come first',
         "Both `clause/2` and `retract/1` originally looked for the next candidate after "
         "unifying the head. By then the head arguments were bound, so indexing rejected "
         "every remaining clause and both predicates silently returned only their first "
         "solution. Finding the next candidate while the arguments are still unbound is "
         "what makes them enumerate."),
]))

section('memory', 'Memory', ''.join([
    para("There are three kinds of storage, and which one a term lives in is decided by "
         "how long it needs to survive."),
    table(['Region', 'Holds', 'Released by'], [
        ['The heap', 'everything a computation builds',
         'backtracking, and the collector'],
        ['Arenas', 'clauses, global variables, exception balls, findall buffers',
         'one call, when the owner dies'],
        ['malloc', 'the atom table, the choice point stack, the trail',
         'never, or on resize'],
    ]),
    para("The heap is a list of chunks, at least 256 KB each. Allocation bumps a pointer; "
         "a mark is a chunk, an offset and an epoch; releasing sets the current chunk and "
         "offset back and leaves the chunks after it in place to be used again. Nothing "
         "is walked, so both marking and releasing are constant time."),
    para("This is what makes backtracking cheap, and it is also the limit of the scheme. "
         "The heap can only be released to a mark, and the only marks are the ones choice "
         "points hold. So the space a loop needs depends on where its newest choice point "
         "is."),
    figure(fig_space(),
           "Both loops run a million iterations and neither builds a lasting result. The "
           "difference is the generator: backtracking into a set of facts returns to the "
           "same mark every time, while a recursive generator leaves its newest mark "
           "further up the heap on every iteration, so everything below it has to stay."),
    para("The measured difference is stark. A million iterations driven by `between/3` "
         "peak at 2.8 MB. The same million iterations driven by a generator written as "
         "an ordinary recursive predicate peak at 754 MB — about a kilobyte an "
         "iteration, exactly linear — because each recursive call leaves its choice "
         "point, and therefore its heap mark, higher than the last."),
    para("The collector cannot help there either: it only runs when the choice point "
         "stack is empty, and a generator is a choice point."),
    para("This is why `between/3` and `repeat/0` are written in C rather than in the "
         "Prolog library, where both began. Each pushes one `CP_REDO` frame holding its "
         "own state — the next integer to try, and the bound — and the retry updates "
         "that state in place instead of calling anything. The heap mark the frame took "
         "when it was created is the mark every iteration returns to, so the loop runs "
         "flat. Rewriting them this way took a million-iteration loop from 1.0 GB to "
         "2.8 MB."),
    note('impl', 'The same trick for your own generator',
         "Anything that enumerates can be written this way: push a `CP_REDO` frame with "
         "`redo_push`, keep the cursor in the frame's two integer fields, and let the "
         "retry advance it. A generator written in Prolog cannot do this, because each "
         "recursive call necessarily leaves a new choice point behind."),
]))

section('gc', 'Garbage collection', ''.join([
    para("Backtracking reclaims nothing in a deterministic recursion, because there is "
         "nothing to backtrack to. Before the collector existed, a million iterations of "
         "`count(N) :- N1 is N-1, count(N1)` held 453 MB, and five million would not "
         "finish on a small machine. The collector is what makes ordinary recursive "
         "Prolog viable: the same five million iterations now peak at 25 MB."),
    '<h3>When it runs</h3>',
    para("The collector is a copying collector, and copying is only sound here if nothing "
         "outside the goal list can be holding a heap pointer. Three conditions have to "
         "hold, checked every 1024 inferences:"),
    ul([
        "The choice point stack is empty. A choice point holds a heap mark, and marks "
        "cannot survive the heap being rebuilt.",
        "No enclosing run of the solver is in progress, because a builtin that called "
        "back into the solver is holding C pointers into the heap.",
        "The heap in use exceeds the threshold — 16 MB, or three times what survived the "
        "last collection, whichever is larger.",
    ]),
    '<h3>What it does</h3>',
    para("A fresh chunk list is started, everything reachable is copied into it, and the "
         "old chunks are freed. The roots are the goal list and a small table of C "
         "variables that callers register — the toplevel registers the variable-name list "
         "it is about to print bindings from, and the loader registers the clause it is "
         "about to assert."),
    figure(fig_gc(),
           "Each copied cell is overwritten with a forwarding pointer to its copy, so a "
           "term reachable by two paths is copied once and stays shared. Forwarding "
           "before the children are copied is also what makes a cyclic term terminate."),
    para("A compound cell is forwarded by overwriting the tag and the union — which "
         "destroys the functor, the arity and the argument pointer, so those are read into "
         "locals first. The argument array itself sits after the header in the old chunk "
         "and is left alone until the whole copy is finished."),
    para("Two things then have to be admitted about the old world. The trail is emptied, "
         "which is sound because with no choice points there is nothing left to undo. And "
         "every outstanding heap mark now points into freed memory, which is what the "
         "epoch in a mark is for: the epoch counter moves on, and releasing a mark from an "
         "older epoch does nothing at all."),
    note('impl', 'How it is tested',
         "The environment variable `PROLOG_GC_THRESHOLD=1` makes the collector run at "
         "every opportunity — every 1024 inferences. `make test-gc` runs the whole suite "
         "that way, and `make test-asan` runs it again under the address and undefined "
         "behaviour sanitizers. A collector that only runs under memory pressure would "
         "otherwise be tested by almost nothing."),
]))

section('reader', 'Reader and writer', ''.join([
    para("The reader is a hand-written tokeniser and an operator-precedence parser. The "
         "parser is the standard two-part shape: read a primary term, then repeatedly "
         "look for an infix or postfix operator whose priority fits under the current "
         "maximum and whose left argument fits the associativity."),
    para("Two details do most of the work. The tokeniser marks whether layout preceded a "
         "token, which is what separates `f(a)` from `f (a)` and what makes `- 1` a "
         "prefix operator applied to 1 while `-1` is a negative literal. And a lone `.` "
         "ends a clause only when layout or end of file follows it, which is why "
         "`X = a.b` reads as one term but `X = a. b` does not."),
    para("The writer inverts the same table. It carries a maximum priority down the "
         "term, parenthesises any operator whose priority exceeds it, and remembers the "
         "last character it emitted so it can insert a space where two tokens would "
         "otherwise merge into one — which is what turns `1-(-1)` into `1- -1` rather "
         "than the unreadable `1--1`."),
    note('impl', 'Round-tripping is a test, not a hope',
         "The suite writes terms with `writeq/1`, reads them back with `atom_to_term/3` "
         "and requires the result to be a variant of the original. That is what caught "
         "the writer printing the atom `.` unquoted, which read back as an end of clause."),
]))

section('performance', 'Measured behaviour', ''.join([
    para("Measured on an Apple M-series laptop, clang -O2. The inference counter counts "
         "goal executions, so these figures are comparable with the usual LIPS numbers "
         "only loosely."),
    table(['Benchmark', 'Result'], [
        ['nrev on a 30-element list, 5000 times',
         '2,680,152 inferences in 183 ms, about 14.6M inferences/second'],
        ['All 92 solutions to 8 queens', '129,382 inferences in 9 ms'],
        ['The zebra puzzle', '1,917 inferences, under a millisecond'],
        ['Loading the bootstrap library', '3 ms'],
        ['5M iterations of a deterministic recursion', '0.40 s, peak 25 MB'],
        ['2M iterations of the same, collector disabled', 'peak 967 MB'],
        ['1M-iteration failure-driven loop over between/3', 'peak 2.8 MB'],
        ['1M iterations of a repeat/0 loop', 'peak 2.9 MB'],
        ['1M-iteration loop over facts', 'peak 13.1 MB'],
        ['1M-iteration loop over a recursive generator', 'peak 754 MB'],
    ]),
    para("Where the time goes is not mysterious: every call copies a clause. The "
         "instantiation of head and body dominates, and the first-argument lookahead is "
         "what keeps that from being paid on clauses that cannot match. A compiling "
         "system avoids the copy entirely, which is the factor of a few this design "
         "gives away."),
]))

section('bugs', 'Five bugs this design produced', ''.join([
    para("Every one of these was a mistake about lifetime or about when a value is read, "
         "which is what a structure-copying engine with manual memory is prone to. They "
         "are listed because the shape of the mistakes says more about the design than a "
         "clean description would."),
    table(['Symptom', 'Cause', 'What it says'], [
        ['A nested findall read freed memory',
         'Instantiating a clause shared the constant cells rather than copying them, and '
         'a findall buffer is freed while its results are still live.',
         'Sharing across two regions with different lifetimes is only safe if the shorter '
         'one is the reader. Copying constants cost about 10% and removed the whole class.'],
        ['clause/2 and retract/1 returned only their first solution',
         'The next candidate clause was chosen after head unification had bound the '
         'arguments, so indexing rejected everything that remained.',
         'Indexing reads state that unification is about to change. Anything derived from '
         'the call has to be derived before the call binds it.'],
        ['A soft cut produced an extra answer',
         'The flag marking the alternative dead was trailed, so backtracking into the '
         'condition brought the alternative back.',
         'Not every mutation should be undone on backtracking. Committing is exactly the '
         'operation that must survive it.'],
        ['Retrying a choice point read freed memory',
         'The alternative goal for if-then-else was built after the choice point took its '
         'heap mark, so retrying released the memory holding it.',
         'Anything a choice point refers to must be older than the mark it holds. The '
         'constants involved now live outside the heap entirely.'],
        ['write_canonical output would not read back',
         'The atom `.` was written unquoted, and atom_codes returned bytes rather than '
         'character codes.',
         'A writer is only correct against a reader. Round-tripping through both is the '
         'test that finds this; inspection does not.'],
    ]),
    para("One of the five was found by the address sanitizer, three by the test suite — "
         "a round-trip through the writer and the reader, a test that asked a predicate "
         "for all its solutions rather than its first, and a soft cut asked for both of "
         "its answers — and one by reading the code before it had ever run. None was "
         "found by using the interpreter, which is the argument for both the sanitizer "
         "run and for tests that ask for every solution rather than the first."),
]))

section('weaknesses', 'Where the design is weak', ''.join([
    para("In rough order of how much they would bother someone using it:"),
    ul([
        "A generator written in Prolog still grows the heap linearly. `between/3` and "
        "`repeat/0` no longer do, but a user-written one does, and there is no way to "
        "write a constant-space generator in Prolog alone.",
        "The collector runs only when the choice point stack is empty. A long computation "
        "that keeps one choice point open never collects at all.",
        "Retracted clauses are held until the predicate is abolished, so a long-running "
        "program that retracts millions of clauses from one predicate accumulates them.",
        "Integers are 64-bit with overflow raised as an error rather than promoted to "
        "bignums, and there are no modules, tabling or constraints.",
    ]),
    para("The first two are the same problem seen from two sides, and the second is the "
         "deep one: collecting with choice points live means keeping the "
         "segment-ordering that heap marks depend on, which is the point where this "
         "design would have to become a mark-and-slide collector over a cell heap — and "
         "at that point it is most of a WAM."),
]))

section('extending', 'Extending the interpreter', ''.join([
    '<h3>Adding a builtin predicate in C</h3>',
    para("A builtin takes the argument array, the continuation and the cut barrier, and "
         "returns success, failure or error. Arguments are not dereferenced for you."),
    pre("""
BI(bi_atom_reverse)                      /* atom_reverse(+Atom, -Reversed) */
{
    UNUSED;
    char *s;
    size_t n, i;
    int rc = get_text(A[0], &s, &n, "atom");

    if (rc != PL_OK) return rc;
    for (i = 0; i < n / 2; i++) {
        char c = s[i];
        s[i] = s[n - 1 - i];
        s[n - 1 - i] = c;
    }
    rc = unify(A[1], mk_atom(intern_n(s, n)));
    free(s);
    RET(rc);
}
"""),
    para("Then one line in the table in `src/builtins.c`, which is what makes it visible "
         "and also what makes it un-redefinable from Prolog:"),
    pre('{ "atom_reverse", 2, bi_atom_reverse },'),
    para("Two rules matter. Anything the builtin allocates on the heap is fine — the "
         "collector cannot run while a builtin is executing. But a builtin that calls "
         "back into the solver, through `solve_sub` or `solve_once`, must assume "
         "everything it holds may move, which is why `findall/3` copies its template "
         "into an arena rather than keeping a pointer."),
    '<h3>Adding a builtin that has more than one solution</h3>',
    para("A builtin that enumerates pushes a `CP_REDO` frame carrying its own state, and "
         "the retry in `backtrack` advances that state. `between/3` is the whole "
         "pattern: it binds the first value, and leaves behind a frame holding the next "
         "value and the bound."),
    pre("""
if (lo < hi) redo_push(REDO_BETWEEN, lo + 1, hi, x, cont, cutb);
RET(unify(A[2], mk_int(lo)));
"""),
    para("The frame is pushed before the first solution is bound, so backtracking undoes "
         "that binding; and because the frame is only ever updated, never replaced, "
         "every iteration returns to the same heap mark. A generator that instead "
         "recurses in Prolog cannot do either of those things."),
    '<h3>Adding an arithmetic function</h3>',
    para("Arithmetic is dispatched on name and arity in `src/arith.c`; a unary function "
         "is a clause in `eval_unary`, a binary one in `eval_binary`. Both receive "
         "already-evaluated operands tagged as integer or float, and set the same on the "
         "result."),
    '<h3>Adding a library predicate</h3>',
    para("If it can be written in Prolog, write it in `lib/boot.pl`. It is compiled into "
         "the binary at build time and consulted at start-up, and it can be redefined by "
         "a user program, which a builtin written in C cannot."),
    note('impl', 'After any change',
         "`make check` runs the suite normally and again with the collector firing every "
         "1024 inferences; `make test-asan` runs both under the sanitizers. A change to "
         "memory handling that passes only the first is not tested."),
]))

render(title='C Prolog Internals',
       prompt='?- engine design',
       subtitle="How the interpreter is built: terms in memory, the solver loop, choice "
                "points and cut, the three memory regions and the collector — and the "
                "places the design costs something.",
       outfile='internals.html')
