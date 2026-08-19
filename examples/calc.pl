/*  A calculator: a grammar that reads an arithmetic expression from a list
    of character codes and evaluates it as it goes.

    ?- calc("2 + 3 * (4 - 1)", X).
    X = 11.
*/

calc(Text, Value) :-
    phrase(expr(Value), Text).

expr(V)         --> term(V0), expr_rest(V0, V).
expr_rest(A, V) --> ws, "+", !, term(B), { C is A + B }, expr_rest(C, V).
expr_rest(A, V) --> ws, "-", !, term(B), { C is A - B }, expr_rest(C, V).
expr_rest(V, V) --> [].

term(V)         --> factor(V0), term_rest(V0, V).
term_rest(A, V) --> ws, "*", !, factor(B), { C is A * B }, term_rest(C, V).
term_rest(A, V) --> ws, "/", !, factor(B), { C is A / B }, term_rest(C, V).
term_rest(V, V) --> [].

factor(V)       --> ws, "(", !, expr(V), ws, ")".
factor(V)       --> ws, "-", !, factor(V0), { V is -V0 }.
factor(V)       --> ws, digits(Ds), { number_codes(V, Ds) }.

digits([D|T])   --> digit(D), digits_rest(T).
digits_rest([D|T]) --> digit(D), !, digits_rest(T).
digits_rest([])    --> [].
digit(D)        --> [D], { D >= 0'0, D =< 0'9 }.

ws --> [C], { C =< 0'\s }, !, ws.
ws --> [].
