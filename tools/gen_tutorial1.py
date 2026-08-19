# -*- coding: utf-8 -*-
"""Generates docs/tutorial-1.html, the first tutorial.

    Run from the top of the source tree:  make doc

    Every query and every answer shown on the page was run against the
    interpreter in this repository, loading tutorial/level1.pl. If you change
    that file, re-check the transcripts.
"""
from docpage import (esc, inline, para, ul, pre, table, note, section, figure,
                     render)

def ex(title, body):
    """An exercise with its solution folded away."""
    return ('<details class="ex"><summary>%s</summary><div class="ex-body">%s</div>'
            '</details>' % (esc(title), body))

def tasks(items):
    return '<ol class="task">%s</ol>' % ''.join('<li>%s</li>' % i for i in items)

# ---------------------------------------------------------------- figure

def fig_search():
    """The search tree for grandparent(esther, C)."""
    W, H = 700, 300
    p = []
    def box(x, y, w, h, accent=False):
        return ('<rect x="%d" y="%d" width="%d" height="%d" rx="3" fill="%s" '
                'stroke="%s" stroke-width="1.2"/>'
                % (x, y, w, h, 'var(--accent-bg)' if accent else 'none',
                   'var(--accent)' if accent else 'currentColor'))
    def txt(x, y, s, size=11, anchor='middle', op='0.95'):
        return ('<text x="%d" y="%d" font-family="IBM Plex Mono, monospace" '
                'font-size="%d" fill="currentColor" text-anchor="%s" opacity="%s">%s'
                '</text>' % (x, y, size, anchor, op, esc(s)))
    def lbl(x, y, s, size=9, anchor='middle', op='0.6'):
        return ('<text x="%d" y="%d" font-family="IBM Plex Sans, sans-serif" '
                'font-size="%d" fill="currentColor" text-anchor="%s" opacity="%s">%s'
                '</text>' % (x, y, size, anchor, op, esc(s)))
    def arrow(x1, y1, x2, y2):
        return ('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="currentColor" '
                'stroke-width="1.1" opacity="0.55" marker-end="url(#t-ar)"/>'
                % (x1, y1, x2, y2))

    p.append('<defs><marker id="t-ar" viewBox="0 0 10 10" refX="9" refY="5" '
             'markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
             '<path d="M0,0 L10,5 L0,10 z" fill="currentColor" opacity="0.55"/>'
             '</marker></defs>')

    p.append(box(240, 10, 220, 30))
    p.append(txt(350, 30, 'grandparent(esther, C)'))
    p.append(arrow(350, 40, 350, 66))
    p.append(lbl(362, 60, 'the only rule turns it into two goals', 9, anchor='start'))

    p.append(box(215, 70, 270, 30))
    p.append(txt(350, 90, 'parent(esther, P), parent(P, C)'))

    p.append(arrow(300, 100, 150, 136))
    p.append(arrow(400, 100, 545, 136))
    p.append(lbl(196, 112, 'P = hannah'))
    p.append(lbl(504, 112, 'P = isaac'))

    p.append(box(60, 140, 180, 30))
    p.append(txt(150, 160, 'parent(hannah, C)'))
    p.append(box(460, 140, 170, 30))
    p.append(txt(545, 160, 'parent(isaac, C)'))

    p.append(arrow(120, 170, 90, 206))
    p.append(arrow(180, 170, 215, 206))
    p.append(arrow(545, 170, 545, 206))

    for x, name in ((90, 'C = lars'), (215, 'C = maja'), (545, 'C = nils')):
        p.append(box(x - 55, 210, 110, 28, accent=True))
        p.append(txt(x, 229, name))

    p.append(lbl(350, 268, 'Prolog walks this tree left to right, top to bottom, '
                           'and reports each leaf as an answer', 10, op='0.7'))
    return ('<div class="svg-frame"><svg viewBox="0 0 %d %d" role="img" '
            'aria-label="The search tree for grandparent(esther, C): the rule '
            'produces two goals, the first has two solutions for P, and the '
            'second yields three answers in all." '
            'xmlns="http://www.w3.org/2000/svg">%s</svg></div>' % (W, H, ''.join(p)))

# ---------------------------------------------------------------- sections

section('start', 'Before you begin', ''.join([
    para("This tutorial teaches the basics of Prolog using the interpreter in "
         "this repository. Everything shown here was run against it, so if a "
         "transcript says the answer is `X = 7`, that is what you will see."),
    para("Build it and start the toplevel:"),
    pre("""
$ make
$ ./prolog
C Prolog 1.0 -- a Prolog interpreter in C
Type help. for help, halt. to quit.

?-
"""),
    para("The `?-` is the prompt: it is Prolog asking you for a question. Type "
         "`halt.` to leave — including the full stop, which is how Prolog knows "
         "you have finished a sentence."),
    para("The programs in this tutorial are in `tutorial/level1.pl`. Load the "
         "file when you start:"),
    pre("$ ./prolog tutorial/level1.pl"),
    note('try', 'Follow along',
         "Read this page with a terminal open beside it. Prolog is quick to try "
         "things in, and the point of the language is hard to feel without "
         "watching it answer."),
]))

section('idea', 'The idea in one page', ''.join([
    para("Most languages are built from instructions: do this, then do that, "
         "return a value. Prolog is built from two other things — facts you "
         "state, and questions you ask. You describe what is true, and the "
         "system searches for a way to prove what you ask about."),
    para("A program is a set of relations. `parent(esther, hannah)` says that "
         "esther and hannah stand in the parent relation. It is not a function "
         "call and it returns nothing; it is a statement that this is so."),
    para("The consequence takes some getting used to: a relation can be used in "
         "any direction. One definition of `parent/2` answers all of these:"),
    ul([
        "Is esther a parent of hannah? — ask `parent(esther, hannah)`",
        "Who are esther's children? — ask `parent(esther, Child)`",
        "Whose parent is hannah? — ask `parent(Who, lars)`",
        "Which parent-child pairs exist at all? — ask `parent(P, C)`",
    ]),
    para("You never wrote three functions for that. You wrote facts, and asked "
         "different questions about them."),
]))

section('facts', 'Facts', ''.join([
    para("A fact is a relation name and its arguments, ended by a full stop. "
         "Here is the start of `tutorial/level1.pl`:"),
    pre("""
parent(esther, hannah).
parent(esther, isaac).
parent(hannah, lars).
parent(hannah, maja).
parent(isaac, nils).

female(esther).
female(hannah).
female(maja).

male(isaac).
male(lars).
male(nils).
"""),
    para("Three rules of spelling matter from the start:"),
    table(['Written as', 'Means'], [
        ['esther, hannah, parent', 'An **atom**: a name that stands for itself. '
                                   'It begins with a lower-case letter.'],
        ['Child, Who, X', 'A **variable**: a blank to be filled in. It begins '
                          'with a capital letter or an underscore.'],
        ['parent(esther, hannah)', 'A relation applied to arguments. No space '
                                   'before the bracket.'],
        ['.', 'Ends every fact, rule and question. Forgetting it is the most '
              'common beginner error.'],
    ]),
    para("`parent/2` is how a relation is named when you talk about it: the "
         "name, then how many arguments it takes. `parent/2` and `parent/3` "
         "would be different relations entirely."),
    note('impl', 'Order matters, and it is the order you wrote',
         "Prolog tries facts and rules from the top of the file downwards. That "
         "is not an implementation detail you can ignore — it decides the order "
         "of answers, and sometimes whether you get any."),
]))

section('asking', 'Asking questions', ''.join([
    para("With the file loaded, ask whether something is true. A question with "
         "no variables gets a yes or no:"),
    pre("""
?- parent(hannah, lars).
true 

?- parent(hannah, esther).
false.
"""),
    para("`true` means Prolog proved it from what you gave it. `false` means it "
         "could not — which is not quite the same as \"this is false in the "
         "world\". Prolog only knows what is in the file. Nothing there says "
         "hannah is a parent of esther, so the answer is no."),
    para("Notice the space after the first `true`, where the second answer ends "
         "in a full stop. The space means Prolog is waiting: it has found one "
         "proof but there may be more, and it wants to know whether to look. "
         "Press return to stop, or `;` and return to search on."),
    para("That is more interesting with a variable in the question. A variable "
         "asks Prolog to find values that make the question true:"),
    pre("""
?- parent(esther, C).
C = hannah ;
C = isaac.
"""),
    para("The first answer came back with a space after it; typing `;` asked for "
         "another; after `C = isaac` there was a full stop, because Prolog could "
         "see there were no more clauses left to try."),
    para("Keep asking past the last answer and you get `false` — meaning \"no "
         "further proof\", not \"the previous answers were wrong\":"),
    pre("""
?- parent(X, lars).
X = hannah ;
false.
"""),
    note('try', 'Try these',
         "`parent(P, C)` on its own — every pair in the database, one `;` at a "
         "time. Then `male(X)`, then `female(esther)`."),
    para("A variable you do not care about can be written `_`, the anonymous "
         "variable. `parent(esther, _)` asks whether esther has any child at all "
         "without asking who."),
]))

section('unification', 'Variables and unification', ''.join([
    para("The single most important thing to understand about Prolog is what "
         "`=` does, because it is not assignment. `X = hannah` does not store "
         "hannah in X. It asks: can these two things be made the same?"),
    pre("""
?- X = hannah.
X = hannah.
"""),
    para("They can, by letting X stand for hannah. That is **unification**: "
         "matching two terms, filling in variables as needed to make them "
         "identical. It works on structure, in both directions at once:"),
    pre("""
?- f(a, B) = f(A, b).
B = b,
A = a.
"""),
    para("Prolog lined the two terms up: same name `f`, same number of "
         "arguments, then argument by argument. `a` had to match `A`, so A "
         "stands for a; `B` had to match `b`, so B stands for b."),
    para("When two terms cannot be made the same, unification simply fails:"),
    pre("""
?- f(a) = g(a).
false.

?- f(a, b) = f(a).
false.
"""),
    para("This is why a variable in a question works the way it does. Asking "
         "`parent(esther, C)` means: find a fact that unifies with this "
         "pattern. `parent(esther, hannah)` does, with C standing for hannah."),
    note('impl', 'A variable is filled in once, but only until Prolog backtracks',
         "Within one proof a variable that has been given a value keeps it — "
         "there is no reassignment. When Prolog gives up on a line of reasoning "
         "and tries another, the values it filled in along the way are undone. "
         "That undoing is what lets the next answer be found."),
]))

section('rules', 'Rules', ''.join([
    para("A rule says that something is true **if** something else is. The "
         "`:-` is the \"if\", and the comma is \"and\":"),
    pre("""
mother(M, C) :- parent(M, C), female(M).
"""),
    para("Read it aloud: M is the mother of C if M is a parent of C, and M is "
         "female. The part before `:-` is the head, the part after is the body."),
    pre("""
?- mother(M, lars).
M = hannah 
"""),
    para("Rules may use other rules, and may use themselves — which comes later "
         "on this page. A grandparent is a parent of a parent:"),
    pre("""
grandparent(G, C) :- parent(G, P), parent(P, C).
"""),
    para("The variable `P` appears twice in the body and nowhere in the head. "
         "That is what ties the two goals together: the same person must be both "
         "esther's child and lars's parent. A variable that appears only inside "
         "the body is local to the rule."),
    pre("""
?- grandparent(G, lars).
G = esther 

?- grandparent(esther, C).
C = lars ;
C = maja ;
C = nils.
"""),
    para("One more, which needs a way of saying \"different\":"),
    pre("""
sibling(A, B) :- parent(P, A), parent(P, B), A \\== B.
"""),
    para("`A \\== B` succeeds when A and B are not the same term. Without it, "
         "everybody would be their own sibling, since `parent(hannah, lars)` "
         "matches both goals at once."),
    tasks([
        para("Write `grandmother/2` using `grandparent/2` and `female/1`."),
        para("Write `father_of_a_son/1`: someone who is the father of a male "
             "child."),
    ]) + ex("Solutions", ''.join([
        pre("""
grandmother(G, C) :- grandparent(G, C), female(G).

father_of_a_son(F) :- father(F, C), male(C).
"""),
        para("Test them with `grandmother(G, lars).` and "
             "`father_of_a_son(X).` — the second answers `X = isaac`."),
    ])),
]))

section('search', 'How Prolog answers', ''.join([
    para("It is worth being precise about what happens when you ask a question, "
         "because everything else follows from it. Take `grandparent(esther, C)`."),
    figure(fig_search(),
           "Prolog works through this tree from the left. Each branch is a "
           "choice it can come back to, and each leaf it reaches is one answer."),
    para("Step by step:"),
    tasks([
        para("The question `grandparent(esther, C)` matches the head of the "
             "rule, so it is replaced by the rule's body: "
             "`parent(esther, P), parent(P, C)`."),
        para("Prolog takes the leftmost goal first. `parent(esther, P)` matches "
             "the first fact about esther, so P stands for hannah. It remembers "
             "that another fact could have matched."),
        para("Now the second goal, with P filled in: `parent(hannah, C)`. That "
             "matches, C stands for lars, and there are no goals left — so "
             "`C = lars` is an answer."),
        para("Asked for more, Prolog goes back to its most recent choice. "
             "`parent(hannah, C)` had another match: `C = maja`."),
        para("Out of matches there, it goes further back, to the choice it left "
             "at `parent(esther, P)`: P stands for isaac instead. The undoing "
             "matters here — C is a blank again before the search continues."),
        para("`parent(isaac, C)` gives `C = nils`. Nothing is left to try "
             "anywhere, so the next request for an answer would be `false`."),
    ]),
    para("That is the whole engine: try goals left to right, try clauses top to "
         "bottom, and on failure go back to the most recent choice and take the "
         "next option. It is called **backtracking**, and it is doing the work "
         "that loops and conditionals do in other languages."),
]))

section('recursion', 'Recursion', ''.join([
    para("`grandparent/2` reaches exactly two generations. For any distance, a "
         "rule has to refer to itself. The pattern is always the same: one "
         "clause that stops, and one that takes a step and recurses."),
    pre("""
ancestor(A, D) :- parent(A, D).
ancestor(A, D) :- parent(A, X), ancestor(X, D).
"""),
    para("The first clause is the base case: a parent is an ancestor. The second "
         "says A is an ancestor of D if A is a parent of somebody who is an "
         "ancestor of D."),
    pre("""
?- ancestor(esther, D).
D = hannah ;
D = isaac ;
D = lars ;
D = maja ;
D = nils 
"""),
    para("The order is worth reading twice. Both of esther's children come "
         "first, because the base-case clause is tried before the recursive "
         "one. Only when those are exhausted does Prolog take a step down and "
         "start again."),
    '<h3>The mistake everybody makes once</h3>',
    para("Write the recursive call first and you get a program that never "
         "answers:"),
    pre("""
ancestor(A, D) :- ancestor(A, X), parent(X, D).   % do not do this
ancestor(A, D) :- parent(A, D).
"""),
    para("To prove `ancestor(esther, D)`, Prolog must first prove "
         "`ancestor(esther, X)` — which sends it to the same clause, which asks "
         "the same thing again. It never reaches a fact. The interpreter will "
         "sit there consuming memory until you interrupt it with Ctrl-C."),
    para("The cure is the discipline above: **make progress before you "
         "recurse**. In the working version the recursive clause consumes a "
         "`parent` step first, so each call is asked about someone further down "
         "the tree, and the questions eventually run out."),
    tasks([
        para("Using `ancestor/2`, ask who all of lars's ancestors are. Which "
             "direction of the relation is that?"),
        para("Write `descendant/2` in terms of `ancestor/2`."),
    ]) + ex("Solutions", ''.join([
        pre("""
?- ancestor(A, lars).
A = hannah ;
A = esther 

descendant(D, A) :- ancestor(A, D).
"""),
        para("The first is the same relation read the other way round — no new "
             "code needed, which is the pay-off for describing relations rather "
             "than writing functions."),
    ])),
]))

section('arithmetic', 'Arithmetic', ''.join([
    para("Numbers need one special word, because of what `=` really means. "
         "Unification matches structure, so this succeeds without computing "
         "anything:"),
    pre("""
?- X = 3 + 4.
X = 3+4.
"""),
    para("X now stands for the term `3+4` — a compound term with two arguments, "
         "exactly like `parent(esther, hannah)` has two. To evaluate it, ask for "
         "that specifically with `is`:"),
    pre("""
?- X is 3 + 4.
X = 7.
"""),
    para("`is` evaluates the expression on its right and unifies the result with "
         "the left. Everything in the expression must already have a value:"),
    pre("""
?- X is Y + 1.
ERROR: Arguments are not sufficiently instantiated
"""),
    para("This is the one place where Prolog stops being able to run in several "
         "directions: `is` computes forwards only. Comparisons work the same "
         "way, evaluating both sides:"),
    table(['Written', 'True when'], [
        ['X =:= Y', 'the two expressions have equal values (`2 + 2 =:= 4`)'],
        ['X =\\= Y', 'their values differ'],
        ['X < Y', 'less than; also `>`, `=<`, `>=`'],
        ['X = Y', 'the two terms unify — no arithmetic at all'],
        ['X == Y', 'the two terms are already identical, without unifying them'],
    ], 'mono1'),
    para("Note `=<` for \"less than or equal\", not `<=`. In the tutorial file:"),
    pre("""
age_in(Person, Year, Age) :-
    born(Person, Born),
    Age is Year - Born.

?- age_in(hannah, 2026, A).
A = 54.
"""),
    tasks([
        para("Write `age_gap/3`, true when the gap between two people's birth "
             "years is a given number of years. Which arguments have to be bound "
             "when you call it?"),
    ]) + ex("Solution", ''.join([
        pre("""
age_gap(A, B, Gap) :-
    born(A, YearA),
    born(B, YearB),
    Gap is YearB - YearA.

?- age_gap(hannah, lars, G).
G = 26.
"""),
        para("A and B must be bound to people, because `is` needs both years "
             "before it can subtract. `Gap` is the one argument that may be a "
             "variable."),
    ])),
]))

section('errors', 'When things go wrong', ''.join([
    para("Four messages account for most of what a beginner sees."),
    table(['Message', 'What happened'], [
        ['Unknown procedure: parnet/2',
         'A name Prolog has never heard of — nearly always a typo, or a file '
         'that was not loaded. Check the spelling and the argument count.'],
        ['Arguments are not sufficiently instantiated',
         'Something needed a value and got a blank. Usually `is` with an '
         'unbound variable on the right.'],
        ['Syntax error: operator expected',
         'Most often a missing full stop at the end of a line, or an unclosed '
         'bracket or quote.'],
        ['false.',
         'Not an error at all: Prolog could not prove what you asked. Check '
         'your facts, and check the argument order — `parent(lars, hannah)` is '
         'a different claim from `parent(hannah, lars)`.'],
    ]),
    note('try', 'A useful habit',
         "When a query surprises you, ask a simpler one. If "
         "`grandparent(esther, C)` gives nothing, try `parent(esther, P)` and "
         "then `parent(hannah, C)` by hand. The goal that fails first is where "
         "the mistake is."),
]))

section('exercises', 'Exercises', ''.join([
    para("These use `tutorial/level1.pl` and nothing beyond this page. Try them "
         "in the toplevel before opening the solutions."),
    tasks([
        para("How many children does esther have? Ask a question that shows "
             "them, one at a time."),
        para("Write `parent_of_two/1`: someone with at least two different "
             "children."),
        para("Write `aunt_or_uncle/2`, true when the first person is a sibling "
             "of the second person's parent."),
        para("Write `same_generation/2` for people who share a parent, then say "
             "why this is not the same relation as `sibling/2`."),
        para("Without running it, predict the answers to `sibling(X, Y)` and "
             "their order. Then check."),
        para("Write `eldest_child/2`: a child of a given person who was born "
             "before all their other children. This one is harder than it "
             "looks — say what makes it awkward with only what you know so far."),
    ]),
    ex("Solutions", ''.join([
        para("**1.** `parent(esther, C).` and press `;` — two children, hannah "
             "and isaac."),
        pre("""
% 2.
parent_of_two(P) :- parent(P, A), parent(P, B), A \\== B.

% 3.
aunt_or_uncle(A, C) :- parent(P, C), sibling(A, P).

% 4.
same_generation(A, B) :- parent(P, A), parent(P, B).
"""),
        para("**2.** answers `esther` twice and `hannah` twice, for the same "
             "reason as exercise 5: the two children can be picked in either "
             "order. Getting each answer once needs `setof/3`, in Level 2."),
        para("**4.** `same_generation/2` has no `A \\== B`, so it also says "
             "everybody shares a generation with themselves. `sibling/2` "
             "excludes that."),
        para("**5.** Four answers, in this order:"),
        pre("""
?- sibling(X, Y).
X = hannah,
Y = isaac ;
X = isaac,
Y = hannah ;
X = lars,
Y = maja ;
X = maja,
Y = lars 
"""),
        para("Each answer binds two variables, and the toplevel prints one "
             "binding per line."),
        para("Two things to notice. Esther's children are siblings too, which "
             "is easy to forget when you are thinking about the younger pair. "
             "And every pair comes out twice, once in each order, because the "
             "rule's two goals can match the two children either way round — "
             "nothing says the first argument has to come first in the file."),
        para("**6.** The awkward part is \"before all their other children\": "
             "that is a claim about every other child, and so far you can only "
             "state claims about particular ones. It needs negation or a way of "
             "gathering all the answers at once — both of which are Level 2. A "
             "half-answer with what you have:"),
        pre("""
% true when C is a child of P and no *known* younger sibling was found first --
% correct only if you check every candidate yourself
older_child(P, C, Other) :-
    parent(P, C), parent(P, Other), C \\== Other,
    born(C, Y1), born(Other, Y2), Y1 < Y2.
"""),
    ])),
]))

section('next', 'Where this goes next', ''.join([
    para("You now have the whole model: facts, rules, unification, and a search "
         "that backtracks. Everything else in Prolog is built from those four "
         "things."),
    para("Level 2 takes on the parts that make it practical:"),
    ul([
        "**Lists** — the workhorse structure, and the recursion patterns that go "
        "with them.",
        "**Collecting answers** — `findall/3` and friends, for the questions "
        "that ask about *all* the solutions at once, like the eldest-child "
        "exercise above.",
        "**Controlling the search** — `\\\\+` for negation, and the cut for "
        "committing to a choice.",
        "**Building your own data** — terms as structures, and the operators "
        "that make them readable.",
    ]),
    para("Until then, the [language reference](reference.html) lists every "
         "predicate this interpreter provides, with the modes each argument "
         "takes."),
]))

render(title='Prolog Tutorial, Level 1',
       prompt='?- level 1',
       subtitle="Facts, rules, unification and the search — the whole model, "
                "using the interpreter in this repository. Every query on this "
                "page was run against it.",
       outfile='tutorial-1.html')
