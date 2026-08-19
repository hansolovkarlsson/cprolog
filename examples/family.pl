/*  A first Prolog program: facts, rules and queries.

    ?- ancestor(esther, X).
    ?- forall(sibling(A, B), format("~w and ~w are siblings~n", [A, B])).
*/

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

mother(M, C) :- parent(M, C), female(M).
father(F, C) :- parent(F, C), male(F).

sibling(A, B) :- parent(P, A), parent(P, B), A \== B.

ancestor(A, D) :- parent(A, D).
ancestor(A, D) :- parent(A, X), ancestor(X, D).

descendants(A, Ds) :- setof(D, ancestor(A, D), Ds).
