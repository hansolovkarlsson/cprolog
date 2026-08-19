/*  The N queens problem.

    ?- queens(8, Qs), print_board(Qs).
    ?- aggregate_all(count, queens(8, _), N).    % 92 solutions
*/

queens(N, Queens) :-
    numlist(1, N, Ns),
    place(Ns, [], Queens).

/* Places the queens one at a time, checking each against those already
   placed, which prunes far earlier than generating whole permutations. */
place([], Placed, Placed).
place(Unplaced, Placed, Queens) :-
    select(Q, Unplaced, Rest),
    safe(Placed, Q, 1),
    place(Rest, [Q|Placed], Queens).

safe([], _, _).
safe([Q|Qs], Queen, Distance) :-
    Queen =\= Q + Distance,
    Queen =\= Q - Distance,
    D1 is Distance + 1,
    safe(Qs, Queen, D1).

print_board(Queens) :-
    length(Queens, N),
    forall(member(Q, Queens), print_row(Q, N)).

print_row(Q, N) :-
    forall(between(1, N, C),
           (   C =:= Q
           ->  write('Q ')
           ;   write('. ')
           )),
    nl.
