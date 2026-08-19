/*  Level 1 -- facts, rules and the search.

    Load it and follow along:

        ./prolog tutorial/level1.pl

    Every query in the tutorial works against this file.
*/

/* ---- facts: things that are simply true ---- */

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

/* ---- rules: things that are true when something else is ---- */

mother(M, C) :- parent(M, C), female(M).
father(F, C) :- parent(F, C), male(F).

grandparent(G, C) :- parent(G, P), parent(P, C).

sibling(A, B) :- parent(P, A), parent(P, B), A \== B.

/* ---- recursion: a rule that uses itself ---- */

ancestor(A, D) :- parent(A, D).
ancestor(A, D) :- parent(A, X), ancestor(X, D).

/* ---- arithmetic ---- */

born(esther, 1948).
born(hannah, 1972).
born(isaac, 1975).
born(lars, 1998).
born(maja, 2001).
born(nils, 2003).

age_in(Person, Year, Age) :-
    born(Person, Born),
    Age is Year - Born.

older(A, B) :-
    born(A, YearA),
    born(B, YearB),
    YearA < YearB.
