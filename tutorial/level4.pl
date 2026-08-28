/*  Level 4 -- programs that do things.

    Load it and follow along:

        ./prolog tutorial/level4.pl

    Every query in the tutorial works against this file. It picks up the
    stock room from Level 3 and turns it into something that runs: stock
    that changes, errors that are raised and caught, and a report written
    to a file.
*/

/* ---- the catalogue: ordinary facts, which never change ---- */

item(hammer,      tools,   24).
item(screwdriver, tools,    9).
item(rope,        outdoor, 12).
item(tent,        outdoor, 95).
item(kettle,      kitchen, 15).

opening(hammer,      12).
opening(screwdriver,  4).
opening(rope,         5).
opening(tent,         0).
opening(kettle,       3).

/* ---- what changes while the program runs ---- */

:- dynamic(stock/2).
:- dynamic(sale/2).

reset :-
    retractall(stock(_, _)),
    retractall(sale(_, _)),
    forall(opening(Item, N), assertz(stock(Item, N))).

:- initialization(reset).

/* ---- raising errors ---- */

sell(Item, Count) :-
    (   item(Item, _, _)
    ->  true
    ;   throw(error(existence_error(item, Item), sell/2))
    ),
    (   integer(Count), Count > 0
    ->  true
    ;   throw(error(type_error(positive_integer, Count), sell/2))
    ),
    stock(Item, Have),
    (   Have >= Count
    ->  true
    ;   throw(short_of_stock(Item, Count, Have))
    ),
    Left is Have - Count,
    retract(stock(Item, Have)),
    assertz(stock(Item, Left)),
    record_sale(Item, Count).

record_sale(Item, Count) :-
    (   retract(sale(Item, Sold))
    ->  true
    ;   Sold = 0
    ),
    Total is Sold + Count,
    assertz(sale(Item, Total)).

/* ---- catching them ---- */

try_sell(Item, Count) :-
    catch(sell(Item, Count), Error, (explain(Error), fail)).

explain(short_of_stock(Item, Want, Have)) :- !,
    format("cannot sell ~w ~w: only ~w left~n", [Want, Item, Have]).
explain(error(existence_error(item, Item), _)) :- !,
    format("no such item: ~w~n", [Item]).
explain(error(type_error(Type, Value), _)) :- !,
    format("~q is not a ~w~n", [Value, Type]).
explain(Error) :-
    format("unexpected: ~q~n", [Error]).

/* ---- remembering an answer: the other use of the database ---- */

:- dynamic(fib_known/2).

fib_slow(0, 0).
fib_slow(1, 1).
fib_slow(N, F) :-
    N > 1,
    A is N - 1,
    B is N - 2,
    fib_slow(A, FA),
    fib_slow(B, FB),
    F is FA + FB.

fib(N, F) :- fib_known(N, F), !.
fib(0, 0).
fib(1, 1).
fib(N, F) :-
    N > 1,
    A is N - 1,
    B is N - 2,
    fib(A, FA),
    fib(B, FB),
    F is FA + FB,
    assertz(fib_known(N, F)).

/*  A small measuring tape, used in the tutorial. The goal is run once and
    its success or failure ignored; what we want is the difference.
*/
count_inferences(Goal, N) :-
    statistics(inferences, Before),
    ignore(Goal),
    statistics(inferences, After),
    N is After - Before.

/* ---- the report ---- */

report :-
    format("~w~t~14|~w~t~22|~w~t~30|~w~n", ['ITEM', 'PRICE', 'LEFT', 'SOLD']),
    forall(item(Item, _, Price),
           ( stock(Item, Left),
             ( sale(Item, Sold) -> true ; Sold = 0 ),
             format("~w~t~14|~d~t~22|~d~t~30|~d~n", [Item, Price, Left, Sold]) )),
    revenue(Total),
    format("~t~22|~w~t~30|~d~n", [revenue, Total]).

revenue(Total) :-
    aggregate_all(sum(V),
                  ( sale(Item, N), item(Item, _, Price), V is N * Price ),
                  Total).

/* ---- writing it to a file ---- */

save_report(File) :-
    open(File, write, Stream),
    current_output(Old),
    set_output(Stream),
    catch(report, Error, true),
    set_output(Old),
    close(Stream),
    (   var(Error)
    ->  true
    ;   throw(Error)
    ).

/* ---- reading orders from a file ---- */

load_orders(File) :-
    open(File, read, Stream),
    current_input(Old),
    set_input(Stream),
    catch(read_orders, Error, true),
    set_input(Old),
    close(Stream),
    (   var(Error)
    ->  true
    ;   throw(Error)
    ).

read_orders :-
    read(Term),
    (   Term == end_of_file
    ->  true
    ;   apply_order(Term),
        read_orders
    ).

apply_order(sell(Item, Count)) :- !,
    ignore(try_sell(Item, Count)).
apply_order(Other) :-
    format("not an order, ignored: ~q~n", [Other]).
