/*  Level 3 -- controlling the search.

    Load it and follow along:

        ./prolog tutorial/level3.pl

    Every query in the tutorial works against this file.
*/

/* ---- a stock room, for negation ---- */

item(hammer,      tools,   12).
item(screwdriver, tools,    0).
item(rope,        outdoor,  5).
item(tent,        outdoor,  0).
item(kettle,      kitchen,  3).

discontinued(tent).

in_stock(Item) :- item(Item, _, N), N > 0.

out_of_stock(Item) :- item(Item, _, _), \+ in_stock(Item).

orderable(Item) :- item(Item, _, _), \+ discontinued(Item).

/* ---- classification, with and without the cut ---- */

level(N, low)    :- N < 5.
level(N, medium) :- N >= 5, N < 20.
level(N, high)   :- N >= 20.

level_cut(N, low)    :- N < 5, !.
level_cut(N, medium) :- N < 20, !.
level_cut(_, high).

/* ---- the cut that quietly changes the meaning ---- */

/*  max_of/3 is wrong on purpose: max_of(7, 3, 3) succeeds, because the first
    clause is rejected on its head before its cut is ever reached, and the
    second has no test of its own. It is here to be compared with max_safe/3,
    not to be copied. level_cut/2 above is wrong the same way.
*/

max_of(X, Y, X) :- X >= Y, !.
max_of(_, Y, Y).

max_safe(X, Y, M) :- ( X >= Y -> M = X ; M = Y ).

first_in_stock(Item) :- item(Item, _, N), N > 0, !.

/* ---- your own notation ---- */

:- op(700, xfx, costs).
:- op(400, xfx, of).

hammer      costs 24.
screwdriver costs  9.
rope        costs 12.
tent        costs 95.
kettle      costs 15.

line_total(N of Item, Total) :-
    Item costs Price,
    Total is N * Price.

order_total([], 0).
order_total([L|Ls], Total) :-
    line_total(L, T),
    order_total(Ls, Rest),
    Total is T + Rest.

order(alice, [3 of hammer, 2 of rope]).
order(bob,   [1 of kettle]).
order(cara,  [2 of tent, 1 of rope]).

fillable(Customer) :-
    order(Customer, Lines),
    \+ ( member(_ of Item, Lines), \+ in_stock(Item) ).

/* ---- a grammar for orders written as text ---- */

lines([L|Ls]) --> line(L), more(Ls).

more(Ls) --> ",", blanks, lines(Ls).
more([])  --> blanks.

line(N of Item) --> count(N), blanks, word(Cs), { atom_codes(Item, Cs) }.

count(N) --> digits(Ds), { Ds \== [], number_codes(N, Ds) }.

digits([D|Ds]) --> [D], { D >= 0'0, D =< 0'9 }, !, digits(Ds).
digits([])     --> [].

word([C|Cs]) --> [C], { C >= 0'a, C =< 0'z }, !, word(Cs).
word([])     --> [].

blanks --> " ", !, blanks.
blanks --> [].

parse_order(Text, Lines) :- phrase(lines(Lines), Text).

/* ---- a grammar over words, for the two directions ---- */

sentence    --> noun_phrase, verb_phrase.

noun_phrase --> determiner, noun.
verb_phrase --> verb, noun_phrase.

determiner --> [the].
determiner --> [a].

noun --> [dog].
noun --> [cat].

verb --> [sees].
verb --> [chases].
