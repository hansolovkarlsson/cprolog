/*  The towers of Hanoi.

    ?- hanoi(4).
    ?- hanoi_moves(20, N).     % how many moves for 20 discs
*/

hanoi(N) :-
    move(N, left, right, middle).

move(0, _, _, _) :- !.
move(N, From, To, Via) :-
    N > 0,
    N1 is N - 1,
    move(N1, From, Via, To),
    format("move a disc from ~w to ~w~n", [From, To]),
    move(N1, Via, To, From).

/* Counting the moves only, which is 2^N - 1. */
hanoi_moves(N, Moves) :-
    count_moves(N, 0, Moves).

count_moves(0, M, M) :- !.
count_moves(N, M0, M) :-
    N1 is N - 1,
    count_moves(N1, M0, M1),
    M2 is M1 + 1,
    count_moves(N1, M2, M).
