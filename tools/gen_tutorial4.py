# -*- coding: utf-8 -*-
"""Generates docs/tutorial-4.html, the fourth tutorial.

    Run from the top of the source tree:  make doc

    Every query and every answer shown was run against the interpreter in this
    repository, loading tutorial/level4.pl. If you change that file, re-check
    the transcripts.
"""
from docpage import (esc, inline, para, ul, pre, table, note, section, figure,
                     render, ex, tasks, LEVELS)

# ---------------------------------------------------------------- figure

def fig_throw():
    """A ball rising past the frames that cannot catch it."""
    p = []

    def box(y, text, kind='plain'):
        fill = {'plain': 'none', 'catch': 'var(--accent-bg)', 'gone': 'none'}[kind]
        stroke = {'plain': 'currentColor', 'catch': 'var(--accent)',
                  'gone': 'currentColor'}[kind]
        dash = ' stroke-dasharray="3 3"' if kind == 'gone' else ''
        op = ' opacity="0.4"' if kind == 'gone' else ''
        return ('<g%s><rect x="30" y="%d" width="300" height="34" rx="3" fill="%s" '
                'stroke="%s" stroke-width="1.2"%s/>'
                '<text x="46" y="%d" font-family="IBM Plex Mono, monospace" '
                'font-size="10.5" fill="currentColor">%s</text></g>'
                % (op, y, fill, stroke, dash, y + 22, esc(text)))

    def side(y, text, colour=None):
        c = colour or 'currentColor'
        o = '1' if colour else '0.6'
        return ('<text x="366" y="%d" font-family="IBM Plex Sans, sans-serif" '
                'font-size="9" fill="%s" opacity="%s">%s</text>'
                % (y + 21, c, o, esc(text)))

    rows = [
        (30,  '?- fill_orders.',                          'plain', 'never hears about it', None),
        (74,  'catch(_, network_error(E), retry)',        'plain', 'wrong shape \u2014 not this one', None),
        (118, 'catch(_, short_of_stock(I,W,H), explain)', 'catch', 'unifies \u2014 the ball lands here', 'var(--accent)'),
        (162, 'sell/2',                                   'gone',  'unwound, bindings undone', None),
        (206, "throw(short_of_stock(tent,1,0))",          'gone',  'the ball is thrown', None),
    ]
    for y, text, kind, note_text, colour in rows:
        p.append(box(y, text, kind))
        p.append(side(y, note_text, colour))

    # the ball's path, up the gap between the frames and their labels
    p.append('<line x1="348" y1="223" x2="348" y2="140" stroke="var(--accent)" '
             'stroke-width="1.4"/>'
             '<path d="M348 133 l-4 8 l8 0 z" fill="var(--accent)"/>')

    p.append('<text x="310" y="272" font-family="IBM Plex Sans, sans-serif" '
             'font-size="9" fill="currentColor" text-anchor="middle" opacity="0.6">'
             'older frames above, newer below</text>')

    return ('<div class="svg-frame"><svg viewBox="0 0 620 288" role="img" '
            'aria-label="Five stacked frames. A ball thrown in the innermost '
            'frame travels up past the frame that raised it and past a catch '
            'whose catcher does not unify, and is caught by the catch whose '
            'catcher does." '
            'xmlns="http://www.w3.org/2000/svg">%s</svg></div>' % ''.join(p))

# ---------------------------------------------------------------- sections

section('start', 'Where we left off', ''.join([
    para("The first three levels built up the language: facts and rules, "
         "lists and aggregation, control and notation. Everything so far has "
         "been a pure question — you asked, Prolog answered, and nothing "
         "outside the query changed."),
    para("Real programs are not like that. They read files, write reports, "
         "keep a record of what has happened, and have to cope when something "
         "goes wrong. This level is about the parts of Prolog that reach "
         "outside the proof: **exceptions**, the **database**, and **input and "
         "output**."),
    para("The running example is the stock room from Level 3, turned into "
         "something that runs. It has stock that goes down when you sell, "
         "errors that are raised and caught, and a report it can write to a "
         "file."),
    pre("$ ./prolog tutorial/level4.pl"),
    note('impl', 'Two files, not one',
         "`tutorial/level4.pl` is the program; `tutorial/orders.txt` is a "
         "handful of orders for it to read, including three that fail on "
         "purpose. Both are in the repository."),
]))

section('exceptions', 'Raising and catching', ''.join([
    para("A goal in Prolog has had two possible outcomes so far: it succeeds, "
         "or it fails. There is a third. `throw/1` abandons the computation "
         "and hands a term — traditionally called the **ball** — to the nearest "
         "enclosing `catch/3` whose catcher unifies with it."),
    pre("""
?- throw(too_hot).
ERROR: Unhandled exception: too_hot

?- catch(throw(too_hot), Ball, format("caught ~q~n", [Ball])).
caught too_hot
Ball = too_hot.
"""),
    para("`catch(Goal, Catcher, Recovery)` runs Goal. If Goal throws a ball "
         "that unifies with Catcher, everything Goal did is undone, the "
         "bindings are rolled back, and Recovery runs instead. A ball that does "
         "not unify keeps going outward."),
    figure(fig_throw(),
           "The ball rises until it finds a catcher that unifies with it. "
           "Frames it passes are unwound; frames above the one that catches it "
           "never learn that anything happened."),
    para("The rollback is worth seeing directly. Here `X` is bound and then the "
         "goal throws; by the time Recovery runs, the binding is gone:"),
    pre("""
?- catch((X = 1, throw(oops)), E, true), var(X).
E = oops.
"""),
    '<h3>The shape of an error</h3>',
    para("Anything can be a ball, but errors raised by the system all have the "
         "same two-argument shape, `error(Formal, Context)`. The first argument "
         "says what went wrong in a form a program can match on; the second is "
         "left for context, and in this interpreter is always an unbound "
         "variable."),
    pre("""
?- catch(X is 1/0, E, true).
E = error(evaluation_error(zero_divisor),_G726).

?- catch(atom_length(f(x), _), error(Formal, _), true).
Formal = type_error(atom,f(x)).
"""),
    para("The [language reference](reference.html) lists every formal term the "
         "interpreter raises. The ones you will meet most are:"),
    table(['Formal', 'Means'], [
        ['type_error(Type, Culprit)', 'Culprit is the wrong kind of thing '
                                      'altogether.'],
        ['domain_error(Domain, Culprit)', 'Right kind, wrong value — an option '
                                          'that does not exist, say.'],
        ['instantiation_error', 'A variable was unbound where a value was '
                                'needed.'],
        ['existence_error(Kind, What)', 'It is not there: an undefined '
                                        'predicate, a missing file.'],
        ['evaluation_error(What)', 'Arithmetic could not produce an answer.'],
        ['permission_error(Op, Kind, What)', 'Not allowed — modifying a builtin, '
                                             'writing to a read stream.'],
    ], 'mono1'),
    para("Following the convention costs nothing and buys a lot: a caller can "
         "match on `error(type_error(_, _), _)` and treat every type error the "
         "same way, whether it came from your code or from the system's."),
    '<h3>Throwing your own</h3>',
    para("`sell/2` in the file raises three different things. Two of them use "
         "the standard shape because they are standard kinds of mistake; the "
         "third is a fact about the stock room, so it gets a term of its own:"),
    pre("""
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
    ...
"""),
    pre("""
?- sell(tent, 1).
ERROR: Unhandled exception: short_of_stock(tent,1,0)

?- catch(sell(tent, 1), Err, true).
Err = short_of_stock(tent,1,0).
"""),
    '<h3>Catch only what you understand</h3>',
    para("The catcher is a pattern, and choosing it carelessly is the most "
         "common way to turn a loud bug into a silent one. `_` catches "
         "everything, including the mistakes you have not made yet:"),
    pre("""
?- catch(sell(hammr, 3), _, true).
true.
"""),
    para("The item was misspelled, `sell/2` raised an existence error to say "
         "so, and the query answered `true` — the typo has been converted into "
         "a success. Name the ball you expect and let the rest through:"),
    pre("""
?- catch(sell(tent, 1), error(_, _), true).
ERROR: Unhandled exception: short_of_stock(tent,1,0)
"""),
    para("That catcher only matches system errors, so the stock-room ball "
         "sailed past it, exactly as it should. The version in the file catches "
         "everything but **reports** everything it did not expect, which is the "
         "other acceptable answer:"),
    pre("""
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
"""),
    pre("""
?- try_sell(tent, 1).
cannot sell 1 tent: only 0 left
false.

?- try_sell(unicorn, 1).
no such item: unicorn
false.

?- try_sell(hammer, -1).
-1 is not a positive_integer
false.
"""),
    '<h3>Failure or an exception?</h3>',
    para("Both stop a goal. The line between them is about whose problem it is:"),
    ul([
        "**Fail** when the answer is a legitimate no. `in_stock(tent)` failing "
        "is not an error; it is the answer.",
        "**Throw** when the question itself was wrong, or when the caller "
        "cannot possibly have meant this. `sell(unicorn, 1)` is not a no — "
        "there is no such item, and silently failing would hide a typo.",
    ]),
    note('impl', 'A recovery that fails does not rethrow',
         "If Recovery fails, `catch/3` fails and the ball is gone — it is "
         "**not** passed on to the next catcher out. To handle some balls and "
         "let the others through, test the ball and `throw/1` it again "
         "yourself: `( mine(E) -> handle(E) ; throw(E) )`. Exercise 6 is this."),
    note('impl', 'assertion/1 for the things that cannot happen',
         "`assertion(Goal)` succeeds quietly when Goal does and throws "
         "`assertion_failed(Goal)` when it does not. It is for invariants you "
         "believe rather than input you are checking — the failure is a bug "
         "report, not an error message."),
]))

section('database', 'Changing the database', ''.join([
    para("Everything in Levels 1 to 3 was written in a file and stayed there. "
         "Prolog also lets a program add and remove clauses while it runs, "
         "which is how it holds on to anything at all between goals."),
    table(['Predicate', 'What it does'], [
        ['assertz(+Clause)', 'Add Clause at the end. `assert/1` is a synonym.'],
        ['asserta(+Clause)', 'Add it at the front.'],
        ['retract(+Clause)', 'Remove the first clause that unifies; on '
                             'backtracking, the next.'],
        ['retractall(+Head)', 'Remove every clause whose head unifies, and make '
                              'the predicate known.'],
        ['abolish(+Name/+Arity)', 'Remove the predicate entirely.'],
        ['clause(+Head, ?Body)', 'Enumerate the clauses; a fact has the body '
                                 '`true`.'],
    ], 'mono1'),
    pre("""
?- assertz(counter(1)), assertz(counter(2)).
true.

?- findall(X, counter(X), L).
L = [1,2].

?- asserta(counter(0)), findall(X, counter(X), L).
L = [0,1,2].

?- retract(counter(0)), findall(X, counter(X), L).
L = [1,2].

?- retractall(counter(_)), findall(X, counter(X), L).
L = [].
"""),
    para("Clauses, not just facts. The argument is a whole clause, so a rule "
         "needs the extra brackets that keep `:-` inside one argument:"),
    pre("""
?- assertz((double(X, Y) :- Y is X * 2)), double(21, D).
D = 42.

?- listing(double/2).
double(A,B) :-
    B is A*2.

true.
"""),
    '<h3>Declaring what changes</h3>',
    para("Calling a predicate that has never been defined is an error, not a "
         "failure — which is the behaviour you want, because it catches typos. "
         "A predicate that starts empty and gets filled in later therefore has "
         "to be declared:"),
    pre("""
:- dynamic(stock/2).
:- dynamic(sale/2).
"""),
    pre("""
?- counter(X).
ERROR: Unknown procedure: counter/1
"""),
    note('impl', 'dynamic is a predicate here, not an operator',
         "Write `:- dynamic(stock/2).` with the brackets. Systems that declare "
         "`dynamic` as a prefix operator accept `:- dynamic stock/2.` as well; "
         "this one does not, and the bracketed form is what every system reads."),
    '<h3>The clause is copied</h3>',
    para("`assertz/1` stores a copy of its argument with fresh variables. "
         "Nothing you do to the original afterwards reaches the stored clause:"),
    pre("""
?- assertz(note(X)), X = bound, note(Y), var(Y).
X = bound.
"""),
    para("`Y` came back unbound: the clause in the database is `note(_)` with a "
         "variable of its own, and binding `X` afterwards had no effect on it. "
         "This is why `assertz/1` is a way of **saving a value**, not of "
         "sharing one."),
    '<h3>What a running goal sees</h3>',
    para("If you change a predicate while a goal is still backtracking through "
         "it, what does that goal see? The ISO answer is the **logical update "
         "view**: a call sees the clauses that existed when it started, and "
         "nothing later. This interpreter does not do that — it walks the live "
         "clause list, so changes are visible immediately:"),
    pre("""
?- assertz(c(1)), assertz(c(2)),
   findall(X, ( c(X), ( X < 6 -> Y is X + 10, assertz(c(Y)) ; true ) ), Visited).
Visited = [1,2,11,12].
"""),
    para("Under the logical view that would be `[1,2]`. Here the goal went on "
         "to visit the clauses it had just created, and only the `X < 6` guard "
         "stopped it running for ever. Removing a clause the goal has not "
         "reached yet makes it disappear from under the walk in the same way:"),
    pre("""
?- retractall(c(_)),
   assertz(c(1)), assertz(c(2)), assertz(c(3)), assertz(c(4)),
   findall(X, ( c(X), ( X =:= 1 -> retract(c(3)) ; true ) ), Visited).
Visited = [1,2,4].
"""),
    note('impl', 'What to do about it',
         "Do not modify a predicate you are backtracking through. Collect first "
         "with `findall/3` and change the database afterwards, or write the "
         "loop over a `forall/2` whose generator is a list rather than the "
         "predicate itself. `retract/1` on the clause you are **currently** on "
         "is safe and is the normal idiom."),
    '<h3>Bindings are undone; the database is not</h3>',
    para("Backtracking and exceptions both roll back bindings. Neither rolls "
         "back the database. This is the single most important thing to know "
         "about `assertz/1`, and it is easy to see:"),
    pre("""
?- stock(kettle, N).
N = 3.

?- catch(( retract(stock(kettle, 3)),
           assertz(stock(kettle, 2)),
           throw(oops) ), E, true).
E = oops.

?- stock(kettle, N).
N = 2.
"""),
    para("The goal was abandoned and the stock stayed changed. A predicate that "
         "asserts halfway through and then throws leaves the world in the state "
         "it reached, which is why `sell/2` does all of its checking **before** "
         "the first `retract/1`. Get the failures out of the way while failing "
         "is still free."),
    '<h3>Remembering an answer</h3>',
    para("The other everyday use of the database is memoisation: work out a "
         "value once, store it, and look it up ever after. Fibonacci is the "
         "usual illustration because the naive version recomputes so much:"),
    pre("""
fib_slow(0, 0).
fib_slow(1, 1).
fib_slow(N, F) :-
    N > 1,
    A is N - 1, B is N - 2,
    fib_slow(A, FA), fib_slow(B, FB),
    F is FA + FB.

fib(N, F) :- fib_known(N, F), !.
fib(0, 0).
fib(1, 1).
fib(N, F) :-
    N > 1,
    A is N - 1, B is N - 2,
    fib(A, FA), fib(B, FB),
    F is FA + FB,
    assertz(fib_known(N, F)).
"""),
    para("One extra first clause looks the answer up and cuts; one extra last "
         "goal records it. `count_inferences/2` in the file wraps "
         "`statistics(inferences, N)` around a goal so the difference is "
         "visible:"),
    pre("""
?- count_inferences(fib_slow(24, _), N).
N = 825273.

?- count_inferences(fib(24, _), N).
N = 423.

?- count_inferences(fib(24, _), N).
N = 12.

?- aggregate_all(count, fib_known(_, _), N).
N = 23.
"""),
    para("Two thousand times fewer inferences the first time, and seventy "
         "thousand times fewer after that, for two lines and twenty-three "
         "stored facts. The cut in the first clause matters: without it the "
         "later clauses would be tried as well and you would get the "
         "recomputation back, alongside the stored answer."),
    note('impl', 'Where the database is the wrong tool',
         "A value that only one predicate needs and only for the length of one "
         "call belongs in an argument, not in the database — an accumulator, as "
         "in Level 2. Reach for `assertz/1` when something must outlive the "
         "goal that computed it. `nb_setval/2` and `nb_getval/2` are there for "
         "a single global value where a whole predicate would be overkill."),
]))

section('writing', 'Writing terms, and format', ''.join([
    para("There are five ways to write a term, and they differ in how much "
         "they care about being read back:"),
    pre("""
?- write('a b'), nl.
a b
true.

?- writeq('a b'), nl.
'a b'
true.

?- print(f('a b', [1,2])), nl.
f('a b',[1,2])
true.

?- write_canonical([1,2]), nl.
'.'(1,'.'(2,[]))
true.
"""),
    table(['Predicate', 'Quotes', 'Operators', 'For'], [
        ['write/1', 'no', 'yes', 'People. What you want in a message.'],
        ['print/1', 'yes', 'yes', 'The toplevel\'s own format.'],
        ['writeq/1', 'yes', 'yes', 'Anything that must be readable again.'],
        ['write_canonical/1', 'yes', 'no', 'Seeing what a term really is.'],
        ['portray_clause/1', 'yes', 'yes', 'A clause, laid out and with a full '
                                           'stop.'],
    ], 'mono1'),
    pre("""
?- portray_clause((greet(X) :- format("hi ~w~n", [X]))).
greet(A) :-
    format([104,105,32,126,119,126,110],[A]).
true.
"""),
    note('impl', 'Why the format string came out as numbers',
         "The `double_quotes` flag is `codes`, so `\"hi ~w~n\"` **is** a list of "
         "character codes — `portray_clause/1` printed the term it was given, "
         "faithfully. `format/2` accepts either a code list or an atom, so "
         "writing `format('hi ~w~n', [X])` with single quotes gives the same "
         "output and a clause that reads back the way you wrote it."),
    '<h3>format</h3>',
    para("`format/2` takes a control string and a list of arguments, and is "
         "what you will actually use. A directive begins with `~`:"),
    pre("""
?- format("~w and ~q~n", ['a b', 'a b']).
a b and 'a b'
true.

?- format("~a|~d|~2f|~e~n", [x, 42, 3.14159, 1.5]).
x|42|3.14|1.500000e+00
true.

?- format("~D~n", [1234567]).
1,234,567
true.

?- format("~s~n", ["codes as text"]).
codes as text
true.
"""),
    table(['Directive', 'Effect'], [
        ['~w  ~q  ~p', 'Write the next argument, as `write/1`, `writeq/1` or '
                       '`print/1`.'],
        ['~a', 'An atomic argument as text, unquoted.'],
        ['~d  ~D', 'An integer; `~D` groups the digits with commas.'],
        ['~Nf  ~e  ~g', 'A float: fixed with N digits, exponential, shortest.'],
        ['~s', 'A code or character list, as text.'],
        ['~n  ~Nn', 'A newline, or N of them.'],
        ['~~', 'A literal tilde.'],
    ], 'mono1'),
    para("The [reference](reference.html) has the rest. The two that repay "
         "learning are `~t` and `~N|`, which are how you get columns: `~N|` "
         "says \"pad to column N\", and `~t` marks where the padding goes."),
    pre("""
?- format("[~w~t~10|]~n", [left]).
[left     ]
true.

?- format("[~t~w~10|]~n", [right]).
[    right]
true.

?- format("~`-t~24|~n").
------------------------
true.
"""),
    para("The last one sets the fill character to a dash rather than a space, "
         "which is how you draw a rule: a back-quote inside the directive names "
         "the character to pad with. Put the three together and that is the "
         "whole report:"),
    pre("""
report :-
    format("~w~t~14|~w~t~22|~w~t~30|~w~n", ['ITEM', 'PRICE', 'LEFT', 'SOLD']),
    forall(item(Item, _, Price),
           ( stock(Item, Left),
             ( sale(Item, Sold) -> true ; Sold = 0 ),
             format("~w~t~14|~d~t~22|~d~t~30|~d~n", [Item, Price, Left, Sold]) )),
    revenue(Total),
    format("~t~22|~w~t~30|~d~n", [revenue, Total]).
"""),
    '<h3>Output that does not go anywhere</h3>',
    para("`format/3` takes a sink as its first argument, which may be a stream "
         "or a request to capture the text instead of printing it. "
         "`with_output_to/2` does the same for a whole goal:"),
    pre("""
?- format(atom(A), "~w-~w", [a, b]).
A = 'a-b'.

?- with_output_to(atom(A), (write(x), write(y))).
A = xy.
"""),
    para("Both accept `atom(A)`, `string(A)`, `codes(C)` and `chars(C)`. This "
         "is the tidy way to build a piece of text out of things that only know "
         "how to print themselves."),
]))

section('files', 'Streams and files', ''.join([
    para("A stream is opened with `open/3`, used by the stream versions of the "
         "reading and writing predicates, and closed with `close/1`."),
    pre("""
?- open('tutorial/orders.txt', read, S), read(S, First), read(S, Second), close(S).
S = '$stream'(3),
First = sell(hammer,3),
Second = sell(rope,2).
"""),
    para("Note what came back: not lines, but **terms**. `read/1` and `read/2` "
         "run the same reader that loads your programs, so an input file is a "
         "sequence of Prolog terms each ended by a full stop. That is why "
         "`tutorial/orders.txt` looks the way it does:"),
    pre("""
sell(hammer, 3).
sell(rope, 2).
sell(tent, 1).
sell(unicorn, 1).
sell(kettle, 99).
sell(screwdriver, 2).
"""),
    para("Reading stops at the end of the file, which arrives as the atom "
         "`end_of_file`. There is no `at_end_of_stream/0` in this interpreter, "
         "so that atom is the test:"),
    pre("""
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
"""),
    note('impl', 'A file of terms is not a file of text',
         "There are no character-reading predicates here — no `get_char/1`, no "
         "line reading — so a file this interpreter reads has to be Prolog "
         "terms. "
         "For text with its own shape, read it as one term (a quoted atom, or a "
         "code list) and take it apart with a grammar, exactly as Level 3 did "
         "with the order text."),
    '<h3>Closing the stream whatever happens</h3>',
    para("A stream must be closed even when the goal using it throws. Most "
         "systems have `setup_call_cleanup/3` for this; this one does not:"),
    pre("""
?- setup_call_cleanup(true, true, true).
ERROR: Unknown procedure: setup_call_cleanup/3
"""),
    para("So you write it out. Catch the ball, clean up, then re-throw it — the "
         "shape is the same every time:"),
    pre("""
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
"""),
    para("`catch/3` with `true` as the recovery consumes the ball like any "
         "other, but it also leaves it in `Error`, which is what makes this "
         "work: the cleanup runs, and then the last line throws the ball again "
         "so the caller still hears about it. `var(Error)` is the test for "
         "\"nothing went wrong\". `save_report/1` is the same shape around "
         "`current_output/1` and `set_output/1`."),
    note('try', 'The one thing to check',
         "The idiom above is only correct because nothing between `set_input/1` "
         "and `close/1` can throw outside the `catch/3`. If you add a goal "
         "there, put it inside."),
]))

section('program', 'The whole thing', ''.join([
    para("With those pieces the stock room is a program. Load the orders, and "
         "the three that cannot be filled report themselves and are skipped:"),
    pre("""
?- load_orders('tutorial/orders.txt').
cannot sell 1 tent: only 0 left
no such item: unicorn
cannot sell 99 kettle: only 3 left
true.

?- report.
ITEM          PRICE   LEFT    SOLD
hammer        24      9       3
screwdriver   9       2       2
rope          12      3       2
tent          95      0       0
kettle        15      3       0
                      revenue 114
true.

?- save_report('/tmp/report.txt').
true.
"""),
    para("`tutorial/restock.pl` is the same thing as a script. A directive runs "
         "as the file is read, which is too early to do any work; "
         "`initialization/1` defers a goal until everything named on the "
         "command line has been loaded, and that is where a program's `main` "
         "goes:"),
    pre("""
:- ['tutorial/level4'].

:- initialization(main).

orders_file('tutorial/orders.txt').
report_file('/tmp/stock-report.txt').

main :-
    orders_file(Orders),
    report_file(Report),
    catch(( load_orders(Orders),
            save_report(Report),
            report,
            format("~nwritten to ~w~n", [Report])
          ),
          Error,
          ( print_message(error, Error), halt(1) )),
    halt.
"""),
    pre("""
$ ./prolog -q tutorial/restock.pl
cannot sell 1 tent: only 0 left
no such item: unicorn
cannot sell 99 kettle: only 3 left
ITEM          PRICE   LEFT    SOLD
hammer        24      9       3
screwdriver   9       2       2
rope          12      3       2
tent          95      0       0
kettle        15      3       0
                      revenue 114

written to /tmp/stock-report.txt
"""),
    para("Three details make it a program rather than a query. `halt/0` at the "
         "end stops it dropping into the toplevel. `halt(1)` in the recovery "
         "gives the shell a non-zero status, so a script that calls this one can "
         "tell that it failed. And `print_message(error, Error)` prints the ball "
         "the way the toplevel would, on standard error, rather than inventing a "
         "message of its own:"),
    pre("""
$ ./prolog -q tutorial/restock.pl        # with the orders file renamed away
ERROR: Unknown source_sink: 'tutorial/orders.txt'
$ echo $?
1
"""),
    note('impl', 'There is no argv',
         "This interpreter has no `argv` flag, so a script cannot take a file "
         "name from the command line. Name the files in the program, as "
         "`restock.pl` does, or pass them in with a second `-g` goal."),
]))

section('errors', 'When this goes wrong', ''.join([
    table(['Symptom', 'Usual cause'], [
        ['A typo behaves like a failure instead of an error',
         'A `catch/3` with `_` as the catcher somewhere above it. Name the '
         'balls you expect.'],
        ['Half the change happened and then it threw',
         'The database is not rolled back by an exception. Do the checking '
         'before the first `assertz/1` or `retract/1`.'],
        ['A loop over a dynamic predicate never ends',
         'It is asserting to the predicate it is walking, and this interpreter '
         'shows the new clauses to the running goal. Collect with `findall/3` '
         'first.'],
        ['Unknown procedure for a predicate that starts empty',
         'It needs `:- dynamic(name/arity).` — with the brackets.'],
        ['assertz stored a variable instead of the value',
         'The clause is copied at the moment you assert it. Bind first, assert '
         'second.'],
        ['A file of text will not read',
         '`read/1` reads terms, not lines, and needs a full stop after each. '
         'A report written by `format/2` cannot be read back by `read/1`.'],
        ['The stream is still open after an error',
         'The goal threw past the `close/1`. Use the catch-clean-rethrow shape.'],
    ]),
    note('try', 'The quickest way to see the database',
         "`listing/1` writes a predicate the way it would be read back, "
         "clauses, rules and all. `listing(stock/2).` after a few sales shows "
         "exactly what the program has done."),
]))

section('exercises', 'Exercises', ''.join([
    para("All of these use `tutorial/level4.pl`. `reset/0` puts the stock back "
         "to its opening values whenever you want to start again."),
    tasks([
        para("`restock(+Item, +Count)`: the opposite of `sell/2`. Raise the same "
             "errors for an unknown item and a count that is not a positive "
             "integer."),
        para("`sell_all(+Lines)`: sell a list of `Count-Item` pairs, all or "
             "nothing — if any line cannot be filled, none of them happen. Why "
             "can you not simply wrap the whole thing in `catch/3`?"),
        para("`with_stock_restored(:Goal)`: run Goal and then put the stock "
             "back where it was, whether Goal succeeds, fails or throws. This "
             "is `setup_call_cleanup/3` for one particular case."),
        para("`department_report/0`: total units in stock per department, in "
             "columns. `setof/3` from Level 2 and `~t~N|` from this page."),
        para("`save_stock(+File)` and `load_stock(+File)`: write the current "
             "stock as terms and read it back. Check that a round trip through "
             "the file changes nothing."),
        para("Make `try_sell/2` catch only the three balls `explain/1` "
             "understands, and let anything else through. What do you have to "
             "write, and what happens now if `sell/2` has a bug in it?"),
        para("Memoise something of your own. The Collatz sequence length is a "
             "good target: `collatz(N, Steps)` where even N halves, odd N goes "
             "to `3N + 1`, and `collatz(1, 0)`."),
    ]),
    ex("Solutions", ''.join([
        pre("""
% 1
restock(Item, Count) :-
    (   item(Item, _, _) -> true
    ;   throw(error(existence_error(item, Item), restock/2))
    ),
    (   integer(Count), Count > 0 -> true
    ;   throw(error(type_error(positive_integer, Count), restock/2))
    ),
    retract(stock(Item, Have)),
    Left is Have + Count,
    assertz(stock(Item, Left)).

% 2  check everything first, then do it
sell_all(Lines) :-
    forall(member(Count-Item, Lines),
           ( item(Item, _, _), stock(Item, Have), Have >= Count )),
    forall(member(Count-Item, Lines), sell(Item, Count)).

% 3
with_stock_restored(Goal) :-
    findall(Item-N, stock(Item, N), Saved),
    (   catch(Goal, Error, true) -> Outcome = true ; Outcome = fail ),
    retractall(stock(_, _)),
    forall(member(Item-N, Saved), assertz(stock(Item, N))),
    (   nonvar(Error) -> throw(Error) ; Outcome == true ).

% 4
department_report :-
    setof(D, I^P^item(I, D, P), Ds),
    forall(member(D, Ds),
           ( aggregate_all(sum(N), (item(I, D, _), stock(I, N)), Units),
             format("~w~t~14|~d~n", [D, Units]) )).

% 5
save_stock(File) :-
    open(File, write, S),
    forall(stock(I, N), ( writeq(S, stock(I, N)), write(S, '.'), nl(S) )),
    close(S).

load_stock(File) :-
    retractall(stock(_, _)),
    open(File, read, S),
    read_all(S),
    close(S).

read_all(S) :-
    read(S, T),
    ( T == end_of_file -> true ; assertz(T), read_all(S) ).

% 6
try_sell(Item, Count) :-
    catch(sell(Item, Count), Error,
          (   known(Error)
          ->  explain(Error), fail
          ;   throw(Error)
          )).

known(short_of_stock(_, _, _)).
known(error(existence_error(item, _), _)).
known(error(type_error(positive_integer, _), _)).

% 7
:- dynamic(collatz_known/2).

collatz(N, S) :- collatz_known(N, S), !.
collatz(1, 0) :- !.
collatz(N, S) :-
    (   0 is N mod 2 -> M is N // 2 ; M is 3 * N + 1 ),
    collatz(M, S0),
    S is S0 + 1,
    assertz(collatz_known(N, S)).
"""),
        para("**2** `catch/3` cannot undo it, because the database is not part "
             "of what an exception rolls back. By the time the third line "
             "throws, the first two have already been sold. Checking every line "
             "before touching anything is the only way to get the all-or-nothing "
             "behaviour — or you undo it by hand, which is exercise 3."),
        para("**3** Two things are easy to get wrong. Writing "
             "`catch(Goal, Error, true)` as a plain goal handles success and "
             "an exception but **not** failure — a failing Goal makes `catch/3` "
             "fail, so the restore never runs. Wrapping it in `( ... -> ... ; "
             "... )` catches the failure and records it, so the cleanup happens "
             "either way and the final line reproduces the outcome. And the "
             "explicit `throw(Error)` is what makes this a cleanup rather than "
             "a swallow."),
        para("**5** The round trip works because `writeq/1` quotes whatever "
             "needs it and the full stop makes each line a term. Writing with "
             "`write/1` instead would produce a file that `read/1` cannot always "
             "read back."),
        para("**6** The explicit `throw(Error)` in the else branch is the "
             "whole point. Letting the recovery just fail would **not** put the "
             "ball back — a recovery that fails makes `catch/3` fail, and the "
             "exception is gone. With the rethrow, a bug inside `sell/2` — an "
             "unbound variable reaching `atom_length/2`, say — comes back as "
             "`error(instantiation_error, _)` and tells you about itself, "
             "instead of being printed as \"unexpected\" and turned into a "
             "quiet `false`."),
    ])),
]))

section('next', 'Where this goes next', ''.join([
    para("That is the language. Across four levels: facts and rules and the "
         "search; lists and collecting answers; negation, the cut, your own "
         "notation and grammars; and now exceptions, the database and I/O. "
         "There is no fifth thing you need before writing real programs in it."),
    para("What is worth doing next is reading and writing rather than learning:"),
    ul([
        "The programs in `examples/` — the eight queens, the zebra puzzle, "
        "Hanoi, a calculator, a family tree. They are short, and each is one "
        "idea from these four levels used properly.",
        "The [language reference](reference.html) for everything this page "
        "skipped: every builtin, the full `format/2` table, arithmetic, flags, "
        "and the deviations from ISO.",
        "The [engine internals](internals.html) if you would rather know why "
        "any of it behaves as it does. The choice point for a call with more "
        "than one matching clause holds a pointer to the next clause in the "
        "live list, which is the whole reason the update view above is "
        "immediate rather than logical.",
    ]),
    para("And the levels are here if you want to go back over any of it: "
         "[Level 1](tutorial-1.html), [Level 2](tutorial-2.html), "
         "[Level 3](tutorial-3.html)."),
]))

render(title='Prolog Tutorial, Level 4',
       prompt='?- level 4',
       subtitle="Exceptions, the database, and input and output — the parts of "
                "Prolog that reach outside the proof, and what it takes to turn "
                "a set of rules into a program. Every query on this page was run "
                "against the interpreter here.",
       outfile='tutorial-4.html',
       levels=LEVELS)
