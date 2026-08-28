# -*- coding: utf-8 -*-
"""Generates docs/tutorial-2.html, the second tutorial.

    Run from the top of the source tree:  make doc

    Every query and every answer shown was run against the interpreter in this
    repository, loading tutorial/level2.pl. If you change that file, re-check
    the transcripts.
"""
from docpage import (esc, inline, para, ul, pre, table, note, section, figure,
                     render, ex, tasks, LEVELS)

# ---------------------------------------------------------------- figure

def fig_list():
    """A list as the chain of terms it really is."""
    p = []
    def node(x, y):
        return ('<circle cx="%d" cy="%d" r="18" fill="none" stroke="currentColor" '
                'stroke-width="1.2"/>'
                '<text x="%d" y="%d" font-family="IBM Plex Mono, monospace" '
                "font-size=\"12\" fill=\"currentColor\" text-anchor=\"middle\">'.'</text>"
                % (x, y, x, y + 4))
    def leaf(x, y, s, accent=False):
        return ('<rect x="%d" y="%d" width="48" height="28" rx="3" fill="%s" '
                'stroke="%s" stroke-width="1.2"/>'
                '<text x="%d" y="%d" font-family="IBM Plex Mono, monospace" '
                'font-size="12" fill="currentColor" text-anchor="middle">%s</text>'
                % (x - 24, y - 14, 'var(--accent-bg)' if accent else 'none',
                   'var(--accent)' if accent else 'currentColor', x, y + 4, esc(s)))
    def link(x1, y1, x2, y2):
        return ('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="currentColor" '
                'stroke-width="1.1" opacity="0.6"/>' % (x1, y1, x2, y2))
    def lbl(x, y, s, anchor='middle', op='0.6'):
        return ('<text x="%d" y="%d" font-family="IBM Plex Sans, sans-serif" '
                'font-size="9" fill="currentColor" text-anchor="%s" opacity="%s">%s'
                '</text>' % (x, y, anchor, op, esc(s)))

    xs = [80, 230, 380]
    for i, x in enumerate(xs):
        p.append(node(x, 60))
        p.append(link(x, 78, x, 104))                 # down to the element
        p.append(leaf(x, 118, ['a', 'b', 'c'][i]))
        p.append(lbl(x + 8, 96, 'head', 'start'))
        nxt = xs[i + 1] if i + 1 < len(xs) else 520
        p.append(link(x + 19, 60, nxt - 19, 60))       # along to the rest
        p.append(lbl((x + nxt) // 2, 50, 'tail'))
    p.append(leaf(544, 60, '[]', accent=True))
    p.append(lbl(544, 96, 'ends the list'))
    p.append(lbl(300, 160, "[a,b,c] is three '.'/2 terms, each holding one element "
                           "and the rest of the list"))
    return ('<div class="svg-frame"><svg viewBox="0 0 620 180" role="img" '
            'aria-label="The list [a,b,c] drawn as three nested terms, each with an '
            'element and the rest of the list, ending in the empty list." '
            'xmlns="http://www.w3.org/2000/svg">%s</svg></div>' % ''.join(p))

# ---------------------------------------------------------------- sections

section('start', 'Where we left off', ''.join([
    para("Level 1 covered the whole model: facts, rules, unification, and a "
         "search that backtracks. This page puts it to work on the structure "
         "Prolog programs are mostly made of — lists — and then answers the "
         "question Level 1 could not: how to ask about *all* the solutions at "
         "once."),
    pre("$ ./prolog tutorial/level2.pl"),
    note('impl', 'Why everything here is called my_something',
         "The library already defines `length/2`, `member/2` and `append/3`. If "
         "you define them again in your own file, your clauses are **added** to "
         "the library's rather than replacing them, and every answer comes back "
         "twice. So the versions we write are `my_length`, `my_member`, "
         "`my_append`. There is more on this below."),
]))

section('what', 'What a list actually is', ''.join([
    para("A list looks like special syntax, and it is — but only syntax. "
         "Underneath, `[a,b,c]` is an ordinary term built from two things you "
         "already know: the atom `[]`, and a two-argument term holding an "
         "element and the rest of the list."),
    pre("""
?- write_canonical([a,b,c]), nl.
'.'(a,'.'(b,'.'(c,[])))
true.
"""),
    figure(fig_list(),
           "Every list is this shape. The square brackets are a convenience the "
           "reader and the writer provide; unification sees the nested terms."),
    para("This matters because it explains the notation you will use constantly. "
         "`[H|T]` means a list whose first element is H and whose rest is T — "
         "the two arguments of that term. The bar separates the front from the "
         "rest."),
    pre("""
?- [a,b,c] = [H|T].
H = a,
T = [b,c].
"""),
    para("The rest is itself a list, all the way down to `[]`, which is where "
         "the structure stops. The empty list has no head and no tail, so it "
         "matches no `[H|T]` pattern at all:"),
    pre("""
?- [] = [X|Rest].
false.
"""),
    para("That failure is not a nuisance — it is how every list program knows "
         "when to stop."),
]))

section('apart', 'Taking a list apart', ''.join([
    para("Because `[H|T]` is just a term, you take a list apart by unifying it "
         "with a pattern. Ask for as many elements as you want by name:"),
    pre("""
?- [a,b,c] = [X,Y|Rest].
X = a,
Y = b,
Rest = [c].

?- [a] = [X|Rest].
X = a,
Rest = [].
"""),
    para("A pattern with no bar matches a list of exactly that length. "
         "`[X,Y,Z]` will match a three-element list and nothing else — useful "
         "when your data has a fixed shape."),
    note('try', 'Feel where it fails',
         "Try `[a,b] = [X,Y,Z]`, then `[a,b,c] = [X,Y]`, then "
         "`[a,b,c] = [a|T]`. The third one succeeds: patterns may contain "
         "constants as well as variables."),
]))

section('walking', 'Walking a list', ''.join([
    para("Almost every list predicate has the same two-clause shape: one clause "
         "for the empty list, one for a list with a head and a tail. The second "
         "does something with the head and calls itself on the tail."),
    pre("""
my_length([], 0).
my_length([_|T], N) :-
    my_length(T, N0),
    N is N0 + 1.
"""),
    para("Read the second clause as a claim rather than as instructions: the "
         "length of a list with a head is one more than the length of its tail. "
         "The recursion terminates because each call gets a shorter list, and "
         "`[]` matches the first clause."),
    pre("""
?- shopping(L), my_length(L, N).
L = [milk,bread,eggs,coffee],
N = 4.
"""),
    para("Summing works the same way, with the same shape:"),
    pre("""
total([], 0).
total([H|T], Sum) :-
    total(T, Rest),
    Sum is H + Rest.

?- primes(P), total(P, Sum).
P = [2,3,5,7,11],
Sum = 28.
"""),
    note('impl', 'Where the work happens',
         "Notice that `is` comes **after** the recursive call in both. Prolog "
         "walks all the way down to `[]` first, and the additions happen on the "
         "way back up. That is fine for ordinary lists; the section on "
         "accumulators below shows the other way round, and why you might want "
         "it."),
]))

section('building', 'Building a list', ''.join([
    para("So far the list was input. To produce one, put the pattern in the "
         "head of the rule and let unification build it:"),
    pre("""
double_all([], []).
double_all([H|T], [D|DT]) :-
    D is H * 2,
    double_all(T, DT).

?- primes(P), double_all(P, D).
P = [2,3,5,7,11],
D = [4,6,10,14,22].
"""),
    para("The second argument of the head, `[D|DT]`, is not a value being "
         "returned. It is a pattern the caller's variable unifies with, leaving "
         "`D` and `DT` to be filled in as the proof proceeds. Prolog builds the "
         "answer as it goes."),
    '<h3>Keeping only some elements</h3>',
    para("A filter needs a decision, and the plainest way to write one is two "
         "clauses whose bodies begin with the test that tells them apart:"),
    pre("""
only_even([], []).
only_even([H|T], [H|R]) :- 0 is H mod 2, only_even(T, R).
only_even([H|T], R)     :- 1 is H mod 2, only_even(T, R).

?- primes(P), only_even(P, E).
P = [2,3,5,7,11],
E = [2] ;
false.
"""),
    para("Clause two keeps the head; clause three drops it. The tests exclude "
         "each other, so exactly one clause applies to each element and there is "
         "exactly one answer."),
    para("But look at what happened when we asked for a second one. Prolog had "
         "to go and check: after clause two succeeded for an even element, "
         "clause three was still sitting there untried, and only failing it "
         "proved there was nothing more. The answer was never in doubt — the "
         "work of confirming it was."),
    para("The same filter written with if-then-else has no such loose ends:"),
    pre("""
only_even2([], []).
only_even2([H|T], Out) :-
    (   0 is H mod 2
    ->  Out = [H|Rest]
    ;   Out = Rest
    ),
    only_even2(T, Rest).
"""),
    pre("""
?- primes(P), only_even2(P, E).
P = [2,3,5,7,11],
E = [2].
"""),
    para("Same answer, and this time it ends in a full stop: nothing was left to "
         "reconsider. `( Condition -> Then ; Else )` proves Condition, and if it "
         "succeeds **commits** to that first solution and runs Then; otherwise it "
         "runs Else. Prolog will not go back and try the condition another way."),
    para("That is the first taste of controlling the search rather than only "
         "describing the problem, and it is the subject of Level 3. Both "
         "definitions are in the file, so you can compare them yourself."),
]))

section('member-append', 'The two that do the most work', ''.join([
    para("Two predicates turn up in nearly every Prolog program. Both are three "
         "lines, and both are more useful than they look because they run in "
         "several directions."),
    '<h3>member</h3>',
    pre("""
my_member(X, [X|_]).
my_member(X, [_|T]) :- my_member(X, T).
"""),
    para("X is a member of a list if it is the head, or if it is a member of the "
         "tail. With X bound it is a test; with X unbound it is a generator, "
         "handing out the elements one at a time on backtracking:"),
    pre("""
?- my_member(X, [a,b,c]).
X = a ;
X = b ;
X = c ;
false.
"""),
    '<h3>append</h3>',
    pre("""
my_append([], L, L).
my_append([H|T], L, [H|R]) :- my_append(T, L, R).
"""),
    para("Appending the empty list to L gives L; otherwise the head comes along "
         "for the ride and the tails are appended. Forwards it joins two lists:"),
    pre("""
?- my_append([1,2], [3], R).
R = [1,2,3].
"""),
    para("Backwards it takes a list apart — every way of splitting it in two, on "
         "backtracking. This is the relational pay-off, and it is worth staring "
         "at for a moment:"),
    pre("""
?- my_append(X, Y, [1,2]).
X = [],
Y = [1,2] ;
X = [1],
Y = [2] ;
X = [1,2],
Y = [] ;
false.
"""),
    para("With one argument fixed it answers a different question again — here, "
         "\"what comes before this ending?\":"),
    pre("""
?- my_append(X, [3], [1,2,3]).
X = [1,2] 
"""),
    note('try', 'One definition, four questions',
         "Join, split, take a prefix, take a suffix. You wrote none of those "
         "cases: they fall out of describing what appending *is* and letting the "
         "search do the rest."),
]))

section('accumulators', 'Accumulators', ''.join([
    para("Reversing a list is the classic example of why the shape of a "
         "recursion matters. The obvious version reverses the tail and puts the "
         "head on the end:"),
    pre("""
rev_naive([], []).
rev_naive([H|T], R) :-
    rev_naive(T, RT),
    my_append(RT, [H], R).
"""),
    para("It works, but `my_append` walks the whole reversed tail every time, so "
         "reversing an n-element list does about n²/2 steps. The alternative "
         "carries a second list along — an **accumulator** — that holds the "
         "answer so far:"),
    pre("""
rev(List, Reversed) :- rev_(List, [], Reversed).

rev_([], Acc, Acc).
rev_([H|T], Acc, R) :- rev_(T, [H|Acc], R).
"""),
    para("Each step moves one element from the front of the input to the front "
         "of the accumulator — which is exactly what reverses it. When the input "
         "runs out, the accumulator *is* the answer, and the first clause hands "
         "it back. One pass, n steps."),
    pre("""
?- rev([1,2,3], R).
R = [3,2,1].
"""),
    para("The pattern generalises. Summing with an accumulator adds on the way "
         "**down** rather than on the way back up:"),
    pre("""
total_acc(List, Sum) :- total_acc(List, 0, Sum).

total_acc([], Sum, Sum).
total_acc([H|T], Acc, Sum) :-
    Acc1 is Acc + H,
    total_acc(T, Acc1, Sum).

?- primes(P), total_acc(P, S).
P = [2,3,5,7,11],
S = 28.
"""),
    para("Two things are worth noticing. The helper takes one more argument than "
         "the predicate you call, which is why it has its own name and a wrapper "
         "that supplies the starting value. And the base clause `total_acc([], "
         "Sum, Sum)` says \"when there is nothing left, the answer is what I have "
         "accumulated\" — the same variable twice, which is unification doing the "
         "returning."),
]))

section('library', 'The library already has these', ''.join([
    para("Everything above is worth writing once, to see how it works. In real "
         "programs you use the versions that come with the system:"),
    table(['Predicate', 'What it does'], [
        ['length(?List, ?N)', 'Length, and it also builds a list of N fresh '
                              'variables when the list is unbound.'],
        ['member(?X, ?List)', 'As above, and `memberchk/2` for the first '
                              'solution only.'],
        ['append(?A, ?B, ?C)', 'As above, plus `append/2` to flatten a list of '
                               'lists.'],
        ['nth0/3, nth1/3, last/2', 'Index into a list, from 0 or from 1, and '
                                   'take the final element.'],
        ['reverse/2', 'With the accumulator already written.'],
        ['msort/2, sort/2', 'Sort; `sort/2` also removes duplicates.'],
        ['keysort/2', 'Sort a list of `Key-Value` pairs by key, keeping the '
                      'order of equal keys.'],
        ['sum_list/2, max_list/2, min_list/2', 'Arithmetic over a list of '
                                               'numbers.'],
        ['numlist(+L, +H, -List)', 'The list of integers from L to H.'],
        ['maplist(:G, ?L)', 'Call a goal on every element; also maplist/3 and /4 '
                            'for lists walked in step.'],
        ['exclude/3, include/3', 'Filter by a goal, without writing the '
                                 'recursion.'],
    ], 'mono1'),
    para("The library version of `length/2` is better than ours in a way worth "
         "seeing. Ask both for a list of a given length:"),
    pre("""
?- length(L, 3).
L = [_G703,_G702,_G701].

?- my_length(L, 3).
L = [_G696,_G700,_G704] 
"""),
    para("Both produce a three-element list of fresh variables. But the library "
         "one is finished — the full stop says so — while ours is still holding "
         "a choice open. Ask `my_length` for another answer and it will search "
         "for ever, because there is always a longer list to try."),
    '<h3>The trap with these names</h3>',
    para("If you define `member/2` in your own file, Prolog does not replace the "
         "library's definition. It appends your clauses to it, and you get every "
         "answer from both:"),
    pre("""
% in your own file
member(X, [X|_]).
member(X, [_|T]) :- member(X, T).

?- findall(X, member(X, [a,b]), L).
L = [a,b,b,a,b,b].
"""),
    para("Six answers where there should be two. Predicates written in C are "
         "protected and refuse outright — `atom_length(_, 42).` in a file gives "
         "`No permission to modify static_procedure`— but the library predicates "
         "written in Prolog are ordinary, and quietly accept the extra clauses. "
         "Give your own versions your own names."),
]))

section('collecting', 'Collecting all the answers', ''.join([
    para("Backtracking hands you solutions one at a time. Some questions are "
         "about the whole set of them: how many, which is largest, are they all "
         "such-and-such. Level 1's last exercise — the eldest child — got stuck "
         "exactly there."),
    para("`findall/3` runs a goal, collects one copy of a template per solution, "
         "and gives you the list:"),
    pre("""
?- findall(C, parent(esther, C), L).
L = [hannah,isaac].

?- findall(D, ancestor(esther, D), L).
L = [hannah,isaac,lars,maja,nils].
"""),
    para("The template can be any term, which is how you collect more than one "
         "thing per solution:"),
    pre("""
?- findall(Y-P, born(P, Y), L).
L = [1948-esther,1972-hannah,1975-isaac,1998-lars,2001-maja,2003-nils].
"""),
    para("`findall/3` always succeeds — with `[]` when the goal has no solutions "
         "at all — and it keeps duplicates and the original order."),
    '<h3>setof and bagof</h3>',
    para("`setof/3` sorts the results and removes duplicates:"),
    pre("""
?- setof(X, my_member(X, [c,a,b,a]), S).
S = [a,b,c].
"""),
    para("`bagof/3` and `setof/3` differ from `findall/3` in one further way: a "
         "variable in the goal that is not in the template is treated as a "
         "grouping key, and you get one answer per value of it, on "
         "backtracking:"),
    pre("""
?- bagof(C, parent(P, C), L).
P = esther,
L = [hannah,isaac] ;
P = hannah,
L = [lars,maja] ;
P = isaac,
L = [nils] 
"""),
    para("That is often exactly what you want — the children of each parent, "
         "grouped. When it is not, write `P^` in front of the goal to say the "
         "variable is not a key, or use `findall/3`, which never groups."),
    '<h3>Counting, summing, the largest</h3>',
    para("`aggregate_all/3` wraps the common cases so you do not have to collect "
         "a list and then walk it:"),
    pre("""
?- aggregate_all(count, parent(esther, _), N).
N = 2.

?- aggregate_all(sum(Y), born(_, Y), Total).
Total = 11897.

?- aggregate_all(min(Y), born(_, Y), Y0).
Y0 = 1948.
"""),
    '<h3>The eldest child, finally</h3>',
    para("Now the Level 1 problem can be stated directly: collect every child "
         "with their year of birth, sort by year, and take the first."),
    pre("""
eldest_child(P, C) :-
    findall(Y-K, (parent(P, K), born(K, Y)), Pairs),
    Pairs \\== [],
    keysort(Pairs, [_-C|_]).

?- eldest_child(hannah, C).
C = lars.

?- eldest_child(esther, C).
C = hannah.
"""),
    para("It is in `tutorial/level2.pl`, so you can try it as it stands. Three "
         "things are doing work here. The goal inside `findall/3` is a "
         "conjunction in brackets, so both parts run for each solution. "
         "`keysort/2` sorts `Key-Value` pairs by key, which is why the year "
         "comes first in the template. And the pattern `[_-C|_]` takes the value "
         "out of the first pair without any further predicate."),
    note('impl', 'findall gives you copies',
         "The solutions `findall/3` collects are copies, with fresh variables. "
         "If your template contains an unbound variable, each element of the "
         "list gets its own — they are not shared with anything in the goal, and "
         "not with each other."),
]))

section('errors', 'When list programs go wrong', ''.join([
    table(['Symptom', 'Usual cause'], [
        ['It runs for ever and eats memory',
         'A missing base case, or a recursive clause that does not make the list '
         'shorter. Check that `[]` is handled and that you recurse on the tail, '
         'not the whole list.'],
        ['Arguments are not sufficiently instantiated',
         '`is` reached an unbound variable — often because the recursion was '
         'written to compute on the way down while the value only arrives on the '
         'way back up.'],
        ['Answers come back twice',
         'Two clauses both match the same case. Filters written as guarded '
         'clauses need tests that exclude each other, as `only_even` does.'],
        ['false, when you expected an answer',
         'A pattern that does not match: `[X]` is a list of exactly one element, '
         'while `X` is anything at all, and `[X|Y]` needs at least one element.'],
    ]),
    note('try', 'The quickest way to find it',
         "Run the predicate on the smallest input that should work — `[]`, then "
         "`[a]`, then `[a,b]`. The first size that misbehaves tells you which "
         "clause is wrong."),
]))

section('exercises', 'Exercises', ''.join([
    para("All of these use `tutorial/level2.pl`. Write them with your own names, "
         "and remember that the library already has `last/2`, `nth0/3` and "
         "friends — the point is to write them once yourself."),
    tasks([
        para("`my_last(?List, ?X)`: X is the final element of List."),
        para("`count_of(@X, +List, -N)`: how many times X occurs in List."),
        para("`sum_evens(+List, -Sum)`: the sum of the even numbers in a list. "
             "You can do this in one line using what is already in the file."),
        para("`take(+N, +List, -Front)`: the first N elements, or the whole list "
             "if it is shorter. Write it without if-then-else."),
        para("`children_of(+P, -List)` and `ancestors_sorted(+D, -List)`: use "
             "`findall/3` for the first and `setof/3` for the second. What "
             "happens to the order?"),
        para("`youngest_child(+P, -C)`: the mirror of `eldest_child/2`. There is "
             "more than one way — try it with `keysort/2` and again with "
             "`aggregate_all/3`."),
        para("Predict the answers to `my_append(X, Y, [1,2,3])` and their order "
             "before running it. How many are there, and why that many?"),
    ]),
    ex("Solutions", ''.join([
        pre("""
% 1
my_last([X], X).
my_last([_|T], X) :- my_last(T, X).

% 2
count_of(_, [], 0).
count_of(X, [H|T], N) :-
    count_of(X, T, N0),
    ( X == H -> N is N0 + 1 ; N = N0 ).

% 3
sum_evens(L, S) :- only_even(L, E), total(E, S).

% 4
take(0, _, []).
take(N, [H|T], [H|R]) :- N > 0, N1 is N - 1, take(N1, T, R).
take(N, [], []) :- N > 0.

% 5
children_of(P, Cs) :- findall(C, parent(P, C), Cs).
ancestors_sorted(D, As) :- setof(A, ancestor(A, D), As).

% 6
youngest_child(P, C) :-
    findall(Y-K, (parent(P, K), born(K, Y)), Pairs),
    Pairs \\== [],
    keysort(Pairs, Sorted),
    my_last(Sorted, _-C).
"""),
        para("**2** uses `==` rather than `=`, because we are asking whether the "
             "element *is* X, not whether it can be made equal to it. With `=` "
             "an unbound element would be bound to X and counted."),
        para("**4** needs the third clause for the short-list case, and the "
             "`N > 0` guard keeps it from overlapping the first clause."),
        para("**5** `findall/3` gives `[lars,maja]` in file order; `setof/3` "
             "gives `[esther,hannah]` sorted and without duplicates — a "
             "different order from the search's."),
        para("**7** Four answers: the split can happen before the first element, "
             "between any two, or after the last. A list of n elements has n+1 "
             "places to cut it."),
    ])),
]))

section('next', 'Where this goes next', ''.join([
    para("You can now write most of what day-to-day Prolog consists of: walk a "
         "structure, build one, and ask about all the answers at once."),
    para("[Level 3](tutorial-3.html) turns to control — the parts that decide "
         "**which** proofs Prolog looks for:"),
    ul([
        "**Negation** — `\\\\+`, what \"not\" can and cannot mean when your "
        "program only knows what you told it.",
        "**The cut** — committing to a choice, what it saves, and the ways it "
        "changes a program's meaning behind your back.",
        "**Your own structures** — terms as records, and `op/3` for making them "
        "read like the problem instead of like data.",
        "**Grammars** — the `-->` notation, for taking apart sequences without "
        "writing the list plumbing by hand.",
    ]),
    para("The [language reference](reference.html) has every predicate this "
         "interpreter provides, and [Level 1](tutorial-1.html) is there if any "
         "of the groundwork needs another look."),
]))

render(title='Prolog Tutorial, Level 2',
       prompt='?- level 2',
       subtitle="Lists — what they really are, the patterns for walking and "
                "building them — and how to ask about every solution at once. "
                "Every query on this page was run against the interpreter here.",
       outfile='tutorial-2.html',
       levels=LEVELS)
