/*  Level 2 -- lists, and collecting answers.

    Load it and follow along:

        ./prolog tutorial/level2.pl

    Every query in the tutorial works against this file.

    The predicates here are named my_length, my_member and so on because the
    library already defines length/2, member/2 and append/3. Defining them
    again would add clauses to the library's, not replace them, and you would
    get every answer twice.
*/

/* ---- some lists to work with ---- */

shopping([milk, bread, eggs, coffee]).
primes([2, 3, 5, 7, 11]).

/* ---- walking a list ---- */

my_length([], 0).
my_length([_|T], N) :-
    my_length(T, N0),
    N is N0 + 1.

total([], 0).
total([H|T], Sum) :-
    total(T, Rest),
    Sum is H + Rest.

/* ---- building a list ---- */

double_all([], []).
double_all([H|T], [D|DT]) :-
    D is H * 2,
    double_all(T, DT).

% two guarded clauses: one keeps the head, one drops it
only_even([], []).
only_even([H|T], [H|R]) :- 0 is H mod 2, only_even(T, R).
only_even([H|T], R)     :- 1 is H mod 2, only_even(T, R).

% the same thing written with if-then-else
only_even2([], []).
only_even2([H|T], Out) :-
    (   0 is H mod 2
    ->  Out = [H|Rest]
    ;   Out = Rest
    ),
    only_even2(T, Rest).

/* ---- the two that do the most work ---- */

my_member(X, [X|_]).
my_member(X, [_|T]) :- my_member(X, T).

my_append([], L, L).
my_append([H|T], L, [H|R]) :- my_append(T, L, R).

/* ---- accumulators ---- */

rev_naive([], []).
rev_naive([H|T], R) :-
    rev_naive(T, RT),
    my_append(RT, [H], R).

rev(List, Reversed) :- rev_(List, [], Reversed).

rev_([], Acc, Acc).
rev_([H|T], Acc, R) :- rev_(T, [H|Acc], R).

total_acc(List, Sum) :- total_acc(List, 0, Sum).

total_acc([], Sum, Sum).
total_acc([H|T], Acc, Sum) :-
    Acc1 is Acc + H,
    total_acc(T, Acc1, Sum).

/* ---- the family from Level 1, for the collecting section ---- */

parent(esther, hannah).
parent(esther, isaac).
parent(hannah, lars).
parent(hannah, maja).
parent(isaac, nils).

born(esther, 1948).
born(hannah, 1972).
born(isaac, 1975).
born(lars, 1998).
born(maja, 2001).
born(nils, 2003).

ancestor(A, D) :- parent(A, D).
ancestor(A, D) :- parent(A, X), ancestor(X, D).

/* ---- the Level 1 exercise, finally answerable ---- */

eldest_child(P, C) :-
    findall(Y-K, (parent(P, K), born(K, Y)), Pairs),
    Pairs \== [],
    keysort(Pairs, [_-C|_]).
