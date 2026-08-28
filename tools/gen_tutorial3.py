# -*- coding: utf-8 -*-
"""Generates docs/tutorial-3.html, the third tutorial.

    Run from the top of the source tree:  make doc

    Every query and every answer shown was run against the interpreter in this
    repository, loading tutorial/level3.pl. If you change that file, re-check
    the transcripts.
"""
from docpage import (esc, inline, para, ul, pre, table, note, section, figure,
                     render, ex, tasks, LEVELS)

# ---------------------------------------------------------------- figure

def fig_cut():
    """The choice point stack, before and after a cut."""
    p = []

    def box(x, y, w, s, kind='plain'):
        fill = {'plain': 'none', 'keep': 'var(--accent-bg)',
                'gone': 'none'}[kind]
        stroke = {'plain': 'currentColor', 'keep': 'var(--accent)',
                  'gone': 'currentColor'}[kind]
        dash = ' stroke-dasharray="3 3"' if kind == 'gone' else ''
        op = ' opacity="0.35"' if kind == 'gone' else ''
        return ('<g%s><rect x="%d" y="%d" width="%d" height="32" rx="3" fill="%s" '
                'stroke="%s" stroke-width="1.2"%s/>'
                '<text x="%d" y="%d" font-family="IBM Plex Mono, monospace" '
                'font-size="11" fill="currentColor" text-anchor="middle">%s</text></g>'
                % (op, x, y, w, fill, stroke, dash,
                   x + w // 2, y + 20, esc(s)))

    def lbl(x, y, s, anchor='middle', size=9, op='0.6'):
        return ('<text x="%d" y="%d" font-family="IBM Plex Sans, sans-serif" '
                'font-size="%d" fill="currentColor" text-anchor="%s" opacity="%s">'
                '%s</text>' % (x, y, size, anchor, op, esc(s)))

    LX, RX, W = 40, 370, 210
    rows = [(70,  'b(X) left an alternative'),
            (110, 'a(X) left an alternative'),
            (150, 'clauses 2 and 3 of p/1'),
            (190, "the caller's choice point")]

    for i, (y, text) in enumerate(rows):
        last = (i == len(rows) - 1)
        p.append(box(LX, y, W, text, 'keep' if last else 'plain'))
        p.append(box(RX, y, W, text, 'keep' if last else 'gone'))

    p.append(lbl(LX + W // 2, 52, 'while proving the body of p/1'))
    p.append(lbl(RX + W // 2, 52, 'the instant ! is reached'))

    # the floor under each stack
    for x in (LX, RX):
        p.append('<line x1="%d" y1="234" x2="%d" y2="234" stroke="currentColor" '
                 'stroke-width="1.1" opacity="0.5"/>' % (x - 8, x + W + 8))
    p.append(lbl(LX + W // 2, 248, 'older, deeper in the stack'))
    p.append(lbl(RX + W // 2, 248, 'the only one left'))

    # the arrow
    p.append('<line x1="272" y1="135" x2="348" y2="135" stroke="var(--accent)" '
             'stroke-width="1.4" opacity="0.9"/>'
             '<path d="M348 135 l-8 -4 l0 8 z" fill="var(--accent)"/>')
    p.append('<text x="310" y="126" font-family="IBM Plex Mono, monospace" '
             'font-size="15" fill="var(--accent)" text-anchor="middle">!</text>')

    return ('<div class="svg-frame"><svg viewBox="0 0 620 262" role="img" '
            'aria-label="Two stacks of choice points side by side. On the left, '
            'four choice points while the body of a clause runs. On the right, '
            'after the cut, only the caller\'s choice point remains; the other '
            'three are gone." '
            'xmlns="http://www.w3.org/2000/svg">%s</svg></div>' % ''.join(p))

# ---------------------------------------------------------------- sections

section('start', 'Where we left off', ''.join([
    para("Levels 1 and 2 were about **describing** things: facts, rules, lists, "
         "and letting the search find whatever follows. Everything you wrote was "
         "true or false regardless of how Prolog went looking for it."),
    para("This level is about the other half. Real programs need to say \"stop "
         "here\", \"only the first one\", \"this is not the case\". Those are "
         "statements about the **search**, not about the world, and they behave "
         "differently: the order of your goals starts to matter, and a program "
         "can be correct read one way and wrong read the other. That trade is "
         "the subject of this page."),
    pre("$ ./prolog tutorial/level3.pl"),
]))

section('negation', 'Negation, and what it really means', ''.join([
    para("Prolog has no way to state that something is false. What it has is "
         "`\\+`, pronounced \"not provable\": `\\+ G` succeeds when the attempt "
         "to prove G **fails**, and fails when G succeeds."),
    pre("""
?- in_stock(rope).
true.

?- in_stock(tent).
false.

?- \\+ in_stock(tent).
true.
"""),
    para("That is enough for most of what you want. The stock room in the file "
         "has five items, one of them discontinued, two of them at zero:"),
    pre("""
item(hammer,      tools,   12).
item(screwdriver, tools,    0).
item(rope,        outdoor,  5).
item(tent,        outdoor,  0).
item(kettle,      kitchen,  3).

discontinued(tent).

in_stock(Item)      :- item(Item, _, N), N > 0.
out_of_stock(Item)  :- item(Item, _, _), \\+ in_stock(Item).
orderable(Item)     :- item(Item, _, _), \\+ discontinued(Item).
"""),
    pre("""
?- out_of_stock(X).
X = screwdriver ;
X = tent ;
false.
"""),
    '<h3>The closed world</h3>',
    para("`\\+ G` does not mean \"G is false\". It means \"I could not prove G "
         "from what I was told\". Prolog assumes that what it has been told is "
         "all there is — the **closed-world assumption** — so anything absent "
         "from the database counts as false."),
    para("Usually that is what you want: the stock room has five items and no "
         "others. It stops being what you want the moment your database is "
         "incomplete. \"Not provable that this flight is full\" is not the same "
         "claim as \"this flight has seats\", and a program that confuses them "
         "will sell you a seat that does not exist."),
    note('impl', 'An unknown predicate is not false',
         "Missing **clauses** are false; a missing **predicate** is an error, "
         "which is a deliberate distinction. `\\+ flies(pig)` raises "
         "`Unknown procedure: flies/1` rather than quietly succeeding, so a "
         "typo in a predicate name does not turn into a silent \"no\". See "
         "`unknown` in the [flags](reference.html) if you want the other "
         "behaviour."),
    '<h3>The order of goals now matters</h3>',
    para("This is the part that catches everyone. `\\+` is only safe when its "
         "goal has no unbound variables you care about. Compare:"),
    pre("""
?- item(X, _, _), \\+ in_stock(X).
X = screwdriver ;
X = tent ;
false.

?- \\+ in_stock(X), item(X, _, _).
false.
"""),
    para("Same two goals, opposite results. In the first, `item/3` binds X to one "
         "item at a time, and `\\+ in_stock(X)` asks a question about **that** "
         "item. In the second, X is still unbound, so `in_stock(X)` asks \"is "
         "anything in stock?\" — it succeeds, and the negation of a success is "
         "failure. The whole query dies before `item/3` is even reached."),
    para("The rule to carry around: **generate first, negate second**. Put the "
         "goals that bind the variables before the `\\+` that tests them."),
    '<h3>It never binds anything</h3>',
    para("A goal inside `\\+` is proved and then thrown away, bindings and all. "
         "That is inherent — if it had succeeded there would be nothing to "
         "report, and it did not succeed, so there is nothing to report either:"),
    pre("""
?- \\+ \\+ (X = hammer), write(X), nl.
_G1938
true.
"""),
    para("The doubled `\\+ \\+` is the idiom for \"does this goal have a "
         "solution?\" when you deliberately want the bindings discarded — it is "
         "how you test a goal without letting it change anything."),
    '<h3>Negation inside negation</h3>',
    para("`\\+` composes, and the nested form is how you say \"for all\". The "
         "orders in the file are lists of `N of Item`, and an order is fillable "
         "when there is no line whose item is out of stock:"),
    pre("""
order(alice, [3 of hammer, 2 of rope]).
order(bob,   [1 of kettle]).
order(cara,  [2 of tent, 1 of rope]).

fillable(Customer) :-
    order(Customer, Lines),
    \\+ ( member(_ of Item, Lines), \\+ in_stock(Item) ).
"""),
    pre("""
?- fillable(C).
C = alice ;
C = bob ;
false.
"""),
    para("Read the inner part as \"there is a line that is not in stock\", and "
         "the outer `\\+` as \"there is no such line\". Cara's order asks for a "
         "tent, so she is not in the list. This shape — `\\+ (Generate, \\+ "
         "Test)` — is common enough to have a name of its own, `forall/2`:"),
    pre("""
?- forall(item(_, _, N), N >= 0).
true.

?- forall(item(I, _, _), orderable(I)).
false.
"""),
    note('impl', 'What this interpreter does not have',
         "Serious Prolog systems offer `dif/2`, which *delays* an inequality "
         "until the variables are bound instead of guessing now. This "
         "interpreter has no constraint store, so it has no `dif/2` — "
         "constraints are on the project's roadmap. Until then, bind before "
         "you test."),
]))

section('cut', 'The cut', ''.join([
    para("The cut, written `!`, is a goal that always succeeds and, in "
         "succeeding, throws away choice points. It is the most powerful and "
         "the most misused thing in the language, so it is worth being exact "
         "about what it discards."),
    para("When `!` is reached in the body of a clause of `p/1`, two sets of "
         "choice points go away: the **remaining clauses** of `p/1`, and any "
         "alternatives left behind by the goals **to the left of the cut in that "
         "same body**. Everything older — in particular anything the caller was "
         "holding — is untouched."),
    figure(fig_cut(),
           "The cut is a stack height. Everything piled up since p/1 was entered "
           "is dropped; the caller's choice points survive, which is why a cut "
           "can never make the predicate that called you deterministic."),
    para("That last point is worth a demonstration. `first_in_stock/1` cuts after "
         "its first success:"),
    pre("""
first_in_stock(Item) :- item(Item, _, N), N > 0, !.

?- member(X, [a,b]), first_in_stock(I).
X = a,
I = hammer ;
X = b,
I = hammer ;
false.
"""),
    para("`member/2` still backtracked twice. The cut made `first_in_stock/1` "
         "give one answer instead of three; it did not reach out and freeze the "
         "goal that called it."),
    '<h3>A cut that only saves work</h3>',
    para("Here is a classification written the honest way, with tests that "
         "exclude one another:"),
    pre("""
level(N, low)    :- N < 5.
level(N, medium) :- N >= 5, N < 20.
level(N, high)   :- N >= 20.
"""),
    pre("""
?- level(3, L).
L = low ;
false.
"""),
    para("Correct, but the `;` shows the cost: after answering `low`, Prolog "
         "still had to enter the other two clauses and fail their tests to prove "
         "there was nothing more. The cut says \"do not bother\":"),
    pre("""
level_cut(N, low)    :- N < 5, !.
level_cut(N, medium) :- N < 20, !.
level_cut(_, high).
"""),
    pre("""
?- level_cut(3, L).
L = low.

?- level_cut(10, L).
L = medium.
"""),
    para("Notice that the second clause no longer needs `N >= 5`. It cannot be "
         "reached unless the first clause's test failed, so `N >= 5` is already "
         "known. That is the real economy of the cut: it lets later clauses "
         "assume the earlier ones did not apply."),
    para("A cut that only removes work Prolog was going to waste, without "
         "changing which answers come out, is traditionally called a **green "
         "cut**. Remove it and the program still means the same thing; it is "
         "just slower."),
    '<h3>A cut that changes the answer</h3>',
    para("The trouble is that the same technique, applied where the answer might "
         "arrive as an input, silently breaks. The classic case is a maximum:"),
    pre("""
max_of(X, Y, X) :- X >= Y, !.
max_of(_, Y, Y).
"""),
    pre("""
?- max_of(7, 3, M).
M = 7.

?- max_of(3, 7, M).
M = 7.
"""),
    para("Both right. Now ask it a question instead of asking it to compute — "
         "check a claim that is plainly false:"),
    pre("""
?- max_of(7, 3, 3).
true.
"""),
    para("The first clause's head is `max_of(X, Y, X)`, and unifying `X` with "
         "both 7 and 3 is impossible, so that clause is rejected **before its "
         "test and its cut are ever reached**. The second clause has no test at "
         "all — it relied entirely on the cut in the first one to protect it — "
         "so it happily agrees that the maximum of 7 and 3 is 3."),
    para("This is a **red cut**: take it out and the program changes meaning. "
         "The failure mode is nasty because the predicate looks fine under every "
         "test you are likely to write, and only misbehaves when someone uses it "
         "in a direction you did not have in mind. `level_cut/2` above has "
         "exactly the same flaw — `level_cut(3, high)` succeeds."),
    note('try', 'See it for yourself',
         "Try `level_cut(3, high).` and then `level(3, high).` The version "
         "without cuts answers correctly; the version with them does not."),
    '<h3>Say it with if-then-else instead</h3>',
    para("Almost every red cut is a `( Cond -> Then ; Else )` that has not been "
         "written out. Level 2 met this form already; here is why it is safer. "
         "The condition is a test, the branches are separate, and nothing "
         "depends on the head having failed to unify:"),
    pre("""
max_safe(X, Y, M) :- ( X >= Y -> M = X ; M = Y ).
"""),
    pre("""
?- max_safe(3, 7, M).
M = 7.

?- max_safe(7, 3, 3).
false.
"""),
    para("Same determinism, same speed, and it now answers the checking question "
         "correctly. The output variable `M` is bound in the branch rather than "
         "in the head, so there is no way to smuggle a wrong answer in through "
         "an argument."),
    note('impl', 'When a cut is genuinely the right tool',
         "Keep the cut for the cases if-then-else cannot express: committing "
         "after a goal that is a **generator** rather than a test "
         "(`item(I,_,N), N > 0, !`), and the base clause of a recursion that "
         "must not be retried. Elsewhere, prefer the arrow — a reader can see "
         "its scope without reconstructing which clauses could still match."),
]))

section('packaged', 'The cut, already wrapped up for you', ''.join([
    para("Four predicates you will use constantly are all cuts underneath. "
         "Reaching for them instead of writing `!` keeps the commitment visible "
         "and confined to one goal."),
    table(['Predicate', 'Means', 'Roughly'], [
        ['once(:G)', 'Prove G, keep the first solution only.', '`G, !`'],
        ['\\+ :G', 'G has no solution.', '`( G -> fail ; true )`'],
        ['ignore(:G)', 'Prove G if you can; succeed either way.',
         '`( G -> true ; true )`'],
        ['forall(:C, :A)', 'A holds for every solution of C.',
         '`\\+ ( C, \\+ A )`'],
    ], 'mono1'),
    pre("""
?- once(item(X, _, _)).
X = hammer.

?- ignore(item(unicorn, _, _)).
true.
"""),
    para("`once/1` is the one to reach for when a goal has several solutions but "
         "you only need the existence of one — a lookup, a first match, a "
         "witness. Unlike a cut written into the predicate, it commits at the "
         "**call site**, so the predicate itself stays usable by callers who do "
         "want every answer."),
    note('impl', 'Cuts are local to the goal they are in',
         "A cut inside `findall/3`, `\\+`, `once/1` or the condition of an "
         "if-then-else is confined to that goal — it cannot prune anything "
         "outside. `findall(X, (member(X,[1,2,3]), !), L)` gives `L = [1]`, not "
         "an empty list and not a pruned outer query."),
]))

section('structures', 'Terms as records', ''.join([
    para("You have been using compound terms all along — `parent(esther, "
         "hannah)` is one. The same terms make perfectly good records, and "
         "Prolog can take them apart without you writing an accessor for every "
         "field."),
    table(['Predicate', 'What it does'], [
        ['functor(?T, ?Name, ?Arity)',
         'The name and argument count of a term, or builds one with fresh '
         'arguments when T is unbound.'],
        ['arg(?N, +T, ?A)', 'The Nth argument, counting from 1. Backtracks over '
                            'N when N is unbound.'],
        ['?T =.. ?List', 'Term to list and back: `[Name|Args]`. Pronounced '
                         '"univ".'],
        ['copy_term(+T, -Copy)', 'A copy with fresh variables.'],
    ], 'mono1'),
    pre("""
?- functor(3 of hammer, F, A).
F = of,
A = 2.

?- arg(2, 3 of hammer, X).
X = hammer.

?- 3 of hammer =.. L.
L = [of,3,hammer].

?- T =.. [costs, rope, 12].
T = rope costs 12.
"""),
    para("`=..` is how you write code that works on terms it was not told about "
         "in advance — a printer, a term rewriter, a translator. Reach for "
         "`arg/3` and `functor/3` first when you know the shape and only want a "
         "field; they do not build an intermediate list."),
    note('impl', 'Prefer plain patterns where you can',
         "`line_total(N of Item, Total)` picks both fields apart in the head, "
         "with no accessor call at all. Unification is the fastest and clearest "
         "way to reach into a term whose shape you know; `=..` is for when you "
         "do not."),
]))

section('operators', 'Your own notation', ''.join([
    para("`3 of hammer` and `rope costs 12` are not built into anything. They "
         "are ordinary two-argument terms that the reader was taught to accept "
         "in infix position, by two directives at the top of the file:"),
    pre("""
:- op(700, xfx, costs).
:- op(400, xfx, of).

hammer      costs 24.
screwdriver costs  9.
rope        costs 12.
tent        costs 95.
kettle      costs 15.
"""),
    para("`op(Priority, Type, Name)` declares Name as an operator. Priority runs "
         "from 1 to 1200, and **lower binds tighter**. Type says where the "
         "operator sits and how it associates:"),
    table(['Type', 'Shape', 'Example'], [
        ['xfx', 'infix, neither side may contain an operator of equal priority',
         '`=`, `is`, `costs`'],
        ['xfy', 'infix, right associative', '`,`, `;`, `->`'],
        ['yfx', 'infix, left associative', '`+`, `-`, `*`'],
        ['fy',  'prefix, argument may equal the priority', '`\\+`, unary `-`'],
        ['fx',  'prefix, argument must be lower', '`:-`, `?-`'],
        ['xf, yf', 'postfix', '— none predefined'],
    ], 'mono1'),
    para("The priorities in the file are chosen so that `of` binds tighter than "
         "`costs`. That is not decoration; it decides how a term is read:"),
    pre("""
?- write_canonical(2 of hammer costs 5), nl.
costs(of(2,hammer),5)
true.
"""),
    para("Had `of` been given the larger priority, the same characters would have "
         "read as `of(2, costs(hammer, 5))` — a different term, and a bug you "
         "would have to find at run time."),
    '<h3>Only the syntax changes</h3>',
    para("An operator declaration affects the reader and the writer, nothing "
         "else. The term underneath is exactly what it always was:"),
    pre("""
?- X = (hammer costs 24), write_canonical(X), nl.
costs(hammer,24)
X = hammer costs 24.
"""),
    para("Which means everything still works the way it did. `costs/2` is a "
         "predicate with five clauses; you can call it, index it, and run it "
         "backwards:"),
    pre("""
?- hammer costs P.
P = 24.

?- Item costs 15.
Item = kettle.
"""),
    para("And rules can be written in the notation too, which is where it starts "
         "to pay for itself:"),
    pre("""
line_total(N of Item, Total) :-
    Item costs Price,
    Total is N * Price.

order_total([], 0).
order_total([L|Ls], Total) :-
    line_total(L, T),
    order_total(Ls, Rest),
    Total is T + Rest.
"""),
    pre("""
?- order_total([3 of hammer, 2 of rope], T).
T = 96.

?- order(C, Ls), order_total(Ls, Total).
C = alice,
Ls = [3 of hammer,2 of rope],
Total = 96 ;
C = bob,
Ls = [1 of kettle],
Total = 15 ;
C = cara,
Ls = [2 of tent,1 of rope],
Total = 202.
"""),
    note('impl', 'Operators are global, and take effect while the file is read',
         "`op/3` is a side effect on the reader, so a declaration must appear "
         "**before** the clauses that use it — that is why it is written as a "
         "`:-` directive at the top of the file. It also stays in force for "
         "everything read afterwards, including the toplevel. Declare few, "
         "declare them at the top, and check `current_op/3` before you take a "
         "name."),
    pre("""
?- current_op(P, T, of).
P = 400,
T = xfx ;
false.
"""),
]))

section('dcg', 'Grammars', ''.join([
    para("Sequences — words in a sentence, characters in a line, tokens in a "
         "file — are lists, and everything you wrote in Level 2 works on them. "
         "But writing a parser that way means threading \"the list I have left\" "
         "through every rule by hand, and it buries the grammar under plumbing."),
    para("Prolog has a notation that writes the plumbing for you. A rule with "
         "`-->` instead of `:-` is a **definite clause grammar** rule:"),
    pre("""
sentence    --> noun_phrase, verb_phrase.

noun_phrase --> determiner, noun.
verb_phrase --> verb, noun_phrase.

determiner --> [the].
determiner --> [a].

noun --> [dog].
noun --> [cat].

verb --> [sees].
verb --> [chases].
"""),
    para("A list on the right-hand side is a **terminal** — the literal tokens to "
         "consume. Anything else is another grammar rule. `phrase/2` runs a "
         "grammar against a list and demands that the whole list be consumed:"),
    pre("""
?- phrase(sentence, [the,dog,sees,a,cat]).
true ;
false.

?- phrase(sentence, [the,dog,sees]).
false.
"""),
    para("The `;` in the first answer is the grammar being honest: after "
         "matching `[the]`, the rule `determiner --> [a]` was still untried, so "
         "a choice point remained until we asked. Nothing was wrong — there was "
         "simply no second parse."),
    '<h3>What the arrow actually does</h3>',
    para("There is no new machinery here. `-->` is read by the same reader as "
         "everything else, and a rule written with it is translated into an "
         "ordinary clause with two extra arguments: the list coming in and the "
         "list left over. You can look at the result:"),
    pre("""
?- listing(noun_phrase/2).
noun_phrase(A,B) :-
    determiner(A,C),
    noun(C,B).

true.
"""),
    para("`determiner` takes the whole list A and leaves C; `noun` takes C and "
         "leaves B. The rest of the list flows from one non-terminal to the "
         "next, which is precisely the bookkeeping you would otherwise write by "
         "hand. A grammar of *n* rules is *n* ordinary predicates of arity two."),
    para("Because they are ordinary predicates, they run in both directions. "
         "Give `phrase/2` an unbound list and the grammar becomes a generator:"),
    pre("""
?- phrase(noun_phrase, NP).
NP = [the,dog] ;
NP = [the,cat] ;
NP = [a,dog] ;
NP = [a,cat].

?- aggregate_all(count, phrase(sentence, _), N).
N = 32.
"""),
    '<h3>Arguments and side conditions</h3>',
    para("A grammar that only says yes or no is rarely enough; you want the "
         "thing it parsed. Non-terminals take arguments like any predicate, and "
         "a goal in braces `{ }` is an ordinary Prolog goal run at that point in "
         "the parse, consuming nothing."),
    para("Here is the order grammar from the file. It turns text into the "
         "`N of Item` structures the rest of the program already understands:"),
    pre("""
lines([L|Ls]) --> line(L), more(Ls).

more(Ls) --> ",", blanks, lines(Ls).
more([])  --> blanks.

line(N of Item) --> count(N), blanks, word(Cs), { atom_codes(Item, Cs) }.

count(N) --> digits(Ds), { Ds \\== [], number_codes(N, Ds) }.

digits([D|Ds]) --> [D], { D >= 0'0, D =< 0'9 }, !, digits(Ds).
digits([])     --> [].

word([C|Cs]) --> [C], { C >= 0'a, C =< 0'z }, !, word(Cs).
word([])     --> [].

blanks --> " ", !, blanks.
blanks --> [].
"""),
    pre("""
?- phrase(lines(L), "3 hammer, 2 rope").
L = [3 of hammer,2 of rope] ;
false.

?- parse_order("3 hammer, 2 rope", L), order_total(L, T).
L = [3 of hammer,2 of rope],
T = 96.
"""),
    para("Three things in there are worth naming. A double-quoted string is a "
         "list of character codes in this system, so `\",\"` is a terminal like "
         "any other list. `0'0` is the code of the character `0`, which is how "
         "you write a character in a numeric comparison. And the `!` in `digits` "
         "and `word` is a cut inside a grammar rule — it means the same thing it "
         "always did, and it is there to stop the parser from also offering the "
         "shorter matches."),
    note('try', 'Take the cuts out',
         "Delete the `!` from `digits//1`, reload, and ask "
         "`phrase(lines(L), \"12 kettle\").` again. You will get "
         "`[12 of kettle]`, then `[1 of ...]` — the grammar will happily stop "
         "reading digits early. The cut is what makes it greedy."),
    '<h3>Leftovers</h3>',
    para("`phrase/3` takes a third argument for what is left unconsumed, which "
         "is how you use a grammar as one stage of something larger:"),
    pre("""
?- phrase(digits(D), "42x", Rest).
D = [52,50],
Rest = [120].
"""),
    para("`[52,50]` is `\"42\"` and `[120]` is `\"x\"` — codes, printed as the "
         "numbers they are. Wrap them with `number_codes/2` or `atom_codes/2` "
         "when you want something readable, as `count//1` does."),
    note('impl', 'The whole translation',
         "`-->` handles conjunction, disjunction, if-then-else, `\\+`, `!`, "
         "`{ }` goals, terminals, `[]`, `call//N` and pushback lists. The "
         "translator is `'$dcg_translate'/2` in `lib/boot.pl` — about forty "
         "lines of Prolog, readable in one sitting, and a good example of the "
         "language being extended in itself."),
]))

section('errors', 'When control goes wrong', ''.join([
    table(['Symptom', 'Usual cause'], [
        ['A negated goal always fails',
         'Its variables were still unbound, so it asked \"is there any\" rather '
         'than \"is this one\". Move the generator before the `\\+`.'],
        ['A predicate gives the right answer but the wrong one when checked',
         'A red cut. The clause after the cut has no test of its own and is '
         'reached whenever the head above it failed to unify. Rewrite as '
         '`( Cond -> Then ; Else )`.'],
        ['Adding a cut made a caller lose answers',
         'It did not — the cut is confined to its own predicate. Something else '
         'changed; check whether you also removed a test the cut had made look '
         'redundant.'],
        ['A term reads as a different shape than you meant',
         'Operator priorities. Check with `write_canonical/1`, and remember '
         'lower priority binds tighter.'],
        ['Operator not recognised while loading a file',
         'The `:- op(...)` directive comes after the clauses that use it. It '
         'must be read first.'],
        ['A grammar loops or returns too many parses',
         'Left recursion (`xs --> xs, x`), or a rule that can match the empty '
         'list in a position where the parser can retry it for ever.'],
    ]),
    note('try', 'The test that catches red cuts',
         "For every predicate with a cut, call it with the output argument "
         "already bound to a wrong value. `max_of(7, 3, 3)` should fail. If it "
         "succeeds, the cut is doing work the clause heads should have done."),
]))

section('exercises', 'Exercises', ''.join([
    para("All of these use `tutorial/level3.pl`. Several have more than one "
         "reasonable answer; the point of the first few is to notice when `\\+` "
         "is safe."),
    tasks([
        para("`unavailable(?Item)`: items that cannot be shipped — out of stock "
             "**or** discontinued — with each item appearing once."),
        para("`unordered(?Item)`: items in the catalogue that appear on nobody's "
             "order. You will need a `\\+` around a conjunction."),
        para("`cheapest(?Item)`: the item no other item undercuts. Write it with "
             "`\\+` and no sorting at all."),
        para("Fix `max_of/3` so that `max_of(7, 3, 3)` fails, **without** using "
             "if-then-else. What did you have to add, and to which clause?"),
        para("`discount(+Total, -Final)`: nothing under 50, 5% off from 50 to "
             "199, 10% off from 200. Write it twice — once with cuts, once with "
             "if-then-else — and decide which you would keep."),
        para("`by_value(-Sorted)`: every customer's order total, sorted "
             "cheapest first. `setof/3` and a `Key-Value` pair will do it in one "
             "line."),
        para("Give the sentence grammar an optional adjective, so that "
             "`[the,big,dog,sees,a,cat]` parses. How many sentences does it "
             "generate now, and why that many?"),
        para("`total_of_text(+Text, -Total)`: parse an order written as text and "
             "price it, in one predicate."),
    ]),
    ex("Solutions", ''.join([
        pre("""
% 1
unavailable(I) :- item(I, _, _), \\+ ( in_stock(I), \\+ discontinued(I) ).

% 2
unordered(I) :- item(I, _, _), \\+ ( order(_, Ls), member(_ of I, Ls) ).

% 3
cheapest(I) :- I costs P, \\+ ( _ costs Q, Q < P ).

% 4
max_fixed(X, Y, X) :- X >= Y, !.
max_fixed(X, Y, Y) :- X <  Y.

% 5
discount(T, F) :- T <  50, !, F = T.
discount(T, F) :- T < 200, !, F is T * 95 // 100.
discount(T, F) :- F is T * 90 // 100.

discount2(T, F) :-
    (   T <  50 ->  F = T
    ;   T < 200 ->  F is T * 95 // 100
    ;               F is T * 90 // 100
    ).

% 6
order_value(C, T) :- order(C, Ls), order_total(Ls, T).
by_value(Sorted)  :- setof(T-C, order_value(C, T), Sorted).

% 7
noun_phrase --> determiner, adjective, noun.
noun_phrase --> determiner, noun.
adjective   --> [big].
adjective   --> [small].

% 8
total_of_text(Text, Total) :-
    parse_order(Text, Lines),
    order_total(Lines, Total).
"""),
        pre("""
?- findall(I, unavailable(I), L).
L = [screwdriver,tent].

?- findall(I, unordered(I), L).
L = [screwdriver].

?- findall(I, cheapest(I), L).
L = [screwdriver].

?- by_value(S).
S = [15-bob,96-alice,202-cara].

?- total_of_text("3 hammer, 2 rope", T).
T = 96.
"""),
        para("**1** The single `\\+` around a conjunction gives one solution per "
             "item, which is what keeps the duplicates away. Writing it as "
             "`out_of_stock(I) ; discontinued(I)` would report the tent twice."),
        para("**3** \"No item costs less\" is a `\\+` over a generator, and it "
             "is safe because `I costs P` bound `P` first. Swap the two goals "
             "and it fails for everything."),
        para("**4** The second clause needs its own test, `X < Y`. Once it has "
             "one, the cut in the first clause is only saving work — it has "
             "become green, and you could delete it without changing a single "
             "answer."),
        para("**5** Both give `30-30`, `96-91` and `202-181`. The cut version is "
             "shorter; the arrow version says out loud that the three cases are "
             "alternatives, and cannot be broken by someone calling it with "
             "`Final` already bound. Most people keep the second."),
        para("**7** 288. A noun phrase is now `2 determiners × (2 adjectives + "
             "nothing) × 2 nouns = 12`, and a sentence is two noun phrases with "
             "a verb between them: `12 × 2 × 12`."),
    ])),
]))

section('next', 'Where this goes next', ''.join([
    para("Between the three levels you now have the whole working language: "
         "facts and rules, unification and backtracking, lists and aggregation, "
         "and — as of this page — control over which proofs get attempted and "
         "notation of your own for the data."),
    para("[Level 4](tutorial-4.html) turns that into a program. It covers the "
         "parts that reach outside the proof: exceptions with `catch/3` and "
         "`throw/1`, the database predicates `assertz/1` and `retract/1`, "
         "`format/2`, and reading and writing files."),
    para("If you would rather know how any of this works underneath, the "
         "[engine internals](internals.html) page describes the machine that "
         "runs it — and the cut in particular turns out to be exactly what the "
         "figure above suggests: one integer, remembered per goal, holding the "
         "height the choice point stack must be cut back to."),
    ul([
        "Level 1 — [facts, rules and the search](tutorial-1.html).",
        "Level 2 — [lists and collecting answers](tutorial-2.html).",
        "Level 4 — [exceptions, the database and I/O](tutorial-4.html).",
        "The examples in `examples/` are worth reading too: the eight queens, "
        "the zebra puzzle and a calculator built on the grammar notation from "
        "this page.",
    ]),
]))

render(title='Prolog Tutorial, Level 3',
       prompt='?- level 3',
       subtitle="Negation, the cut, terms and operators of your own, and the "
                "grammar notation — the parts of Prolog that control the search "
                "rather than describe the problem. Every query on this page was "
                "run against the interpreter here.",
       outfile='tutorial-3.html',
       levels=LEVELS)
