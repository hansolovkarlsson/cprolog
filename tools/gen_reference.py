# -*- coding: utf-8 -*-
"""Generates doc/reference.html, the language reference.

    Run from the top of the source tree:  make doc

    The HTML is generated, so edit the content here rather than in
    doc/reference.html, which is overwritten. Everything documented was
    checked against the running interpreter; when the language changes,
    update the tables below to match.
"""
import re
from docpage import (esc, lit, inline, para, ul, pre, table, note, preds,
                     section, render, SECTIONS, GROUPS)

# ---------------------------------------------------------------- sections

# ---- 1. reading this manual
section('notation', 'Reading this manual', ''.join([
    para("This is the reference for C Prolog, a Prolog interpreter written in C99. "
         "It describes the language the interpreter actually implements: every "
         "predicate, operator, arithmetic function and directive listed here was "
         "checked against the running system, and anything the interpreter does not "
         "provide is listed under Deviations and limits at the end."),
    para("Predicate entries give the argument modes in the usual notation:"),
    table(['Mode', 'Meaning'], [
        ['+Arg', 'Input. Must be instantiated when the predicate is called.'],
        ['-Arg', 'Output. Normally unbound at call time; the predicate binds it.'],
        ['?Arg', 'Either. May be bound or unbound, and the predicate works both ways.'],
        ['@Arg', 'Input that is inspected but never bound.'],
        [':Goal', 'A goal, called by the predicate.'],
    ], 'mono1'),
    para("Predicates whose name begins with `$` are interpreter internals used by the "
         "bootstrap library. They are not part of the language and may change."),
]))

# ---- 2. running
section('running', 'Running the interpreter', ''.join([
    para("The interpreter is a single executable. Given files, it loads them; given "
         "`-g`, it runs a goal and exits; given neither, it starts the interactive "
         "toplevel."),
    pre("""
prolog [options] [file ...]

  -g, --goal GOAL   run GOAL after loading the files
  -t, --top         enter the toplevel even after -g
  -q, --quiet       do not print the banner
  -v, --version     print the version and exit
  -h, --help        print the usage message
"""),
    para("Several `-g` options may be given; they run in order. A file name may omit "
         "the `.pl` extension, and may be written in path notation, so "
         "`[examples/family]` and `consult('examples/family.pl')` load the same file."),
    '<h3>The toplevel</h3>',
    para("The toplevel reads a goal terminated by a full stop and prints the bindings "
         "of the named variables in the query, or `true.` when there are none and "
         "`false.` when the goal has no solution."),
    pre("""
?- append(X, Y, [a,b]).
X = [],
Y = [a,b] ;
X = [a],
Y = [b] ;
X = [a,b],
Y = [] ;
false.
"""),
    table(['Key', 'Effect'], [
        [';  or  space', 'Ask for the next solution.'],
        ['return', 'Accept this solution and return to the prompt.'],
        ['.  or  a', 'Stop enumerating.'],
        ['Ctrl-D', 'Leave the interpreter, like halt.'],
    ]),
    para("Answers are written with `quoted(true)` and a depth limit of 100, so a "
         "binding to a very large term prints as a truncated term ending in `|...`. "
         "Use `write/1` or `print/1` inside the goal to see it in full."),
    '<h3>Loading programs</h3>',
    para("A file is a sequence of clauses and directives. A directive `:- Goal.` is "
         "run as soon as it is read, which is how operators and flags take effect for "
         "the rest of the file. Clauses for a predicate need not be contiguous, and "
         "loading a file again adds its clauses to those already there rather than "
         "replacing them."),
    para("`initialization(Goal)` defers `Goal` until every file named on the command "
         "line has been loaded, which is the usual way to write a script:"),
    pre("""
:- initialization(main).

main :-
    format("hello~n"),
    halt.
"""),
    '<h3>Exit status</h3>',
    table(['Situation', 'Status'], [
        ['Normal exit, or halt/0', '0'],
        ['halt(N)', 'N'],
        ['A -g goal raised an uncaught exception', '1'],
        ['A file named on the command line could not be opened', '1'],
        ['A -g goal failed', '0, with a warning on standard error'],
    ]),
]))

# ---- 3. syntax
ESCAPES = [
    ['\\a', 'alert (7)'], ['\\b', 'backspace (8)'], ['\\f', 'form feed (12)'],
    ['\\n', 'newline (10)'], ['\\r', 'return (13)'], ['\\t', 'tab (9)'],
    ['\\v', 'vertical tab (11)'], ['\\e', 'escape (27)'], ['\\s', 'space (32)'],
    ['\\0', 'null; \\NNN\\ is any octal code'],
    ['\\xHH\\', 'hexadecimal character code'],
    [lit("\\\\  \\'  \\\"  \\`"), 'the character itself'],
    ['\\ at end of line', 'line continuation, produces nothing'],
]

section('syntax', 'Syntax', ''.join([
    '<h3>Terms</h3>',
    para("Every piece of Prolog data is a term: a variable, an atom, an integer, a "
         "float, or a compound term. Lists and strings are compound terms in disguise."),
    table(['Term', 'Written as'], [
        ['Variable', 'X, Value, _rest, or _ for an anonymous variable'],
        ['Atom', "foo, [], !, ;, +, the empty atom '', or any quoted text"],
        ['Integer', "42, -7, 0x1f, 0o17, 0b1011, 0'a, 1_000_000"],
        ['Float', '3.14, -0.5, 6.02e23, 1.0e-9'],
        ['Compound', 'point(1,2), a+b, [H|T], {a,b}'],
    ], 'mono2'),
    '<h3>Atoms</h3>',
    para("An atom is written as a lowercase letter followed by letters, digits and "
         "underscores; as a sequence of the symbol characters "
         "`+ - * / \\\\ ^ < > = ~ : . ? @ # & $`; as one of the solo atoms `[] {} ! ;`; "
         "or as any text in single quotes. Inside quotes, a doubled quote `''` stands "
         "for one quote and the escape sequences below apply."),
    table(['Escape', 'Meaning'], ESCAPES, 'mono1'),
    '<h3>Numbers</h3>',
    para("Integers are 64-bit and signed. Besides decimal, they may be written in "
         "hexadecimal (`0x`), octal (`0o`) or binary (`0b`), and underscores may "
         "separate digit groups. The form `0'c` is the character code of `c`, so "
         "`0'a` is 97; escape sequences work there too, and `0'''` is the quote "
         "character."),
    para("A float needs a digit on both sides of the point: `1.0`, not `1.` — and "
         "`X = 1.` reads as the integer 1 followed by the end of the clause. An "
         "exponent may follow, as in `1.5e10`."),
    '<h3>Strings</h3>',
    para("Text in double quotes is read according to the `double_quotes` flag, whose "
         "default is `codes`. There is no separate string type."),
    table(['Flag value', '\"ab\" reads as'], [
        ['codes (default)', '[97,98], a list of character codes'],
        ['chars', "[a,b], a list of one-character atoms"],
        ['atom', "the atom 'ab'"],
    ], 'mono1'),
    para("Text in back quotes is always a code list, whatever the flag says. Because "
         "the flag is consulted while reading, changing it affects the clauses that "
         "follow the directive, not the one it appears in."),
    '<h3>Lists and curly terms</h3>',
    para("`[a,b,c]` is shorthand for `'.'(a,'.'(b,'.'(c,[])))`, and `[H|T]` is "
         "`'.'(H,T)`. The empty list `[]` is an atom, not a compound term. `{a,b}` is "
         "shorthand for `{}((a,b))` and is mostly used in grammar rules."),
    '<h3>Comments</h3>',
    para("`%` starts a comment that runs to the end of the line; `/*` and `*/` bracket "
         "a comment that may span lines. Comments count as layout, so they may appear "
         "anywhere between tokens."),
    '<h3>Clauses and directives</h3>',
    para("A clause is `Head :- Body.` or, for a fact, `Head.`; a directive is "
         "`:- Goal.` or `?- Goal.`; a grammar rule is `Head --> Body.`. Every one ends "
         "with a full stop: a `.` followed by layout or end of file. That is why "
         "`foo. bar.` on one line is two clauses but `X = a.b` is not — there the dot "
         "is an ordinary symbol character."),
    note('impl', 'Reading errors',
         "A clause with a syntax error is reported on standard error and skipped; "
         "loading continues with the next clause, so one bad clause does not stop a "
         "file from loading."),
]))

# ---- 4. operators
OPS = [
    ['1200', 'xfx', ':-   -->'],
    ['1200', 'fx',  ':-   ?-'],
    ['1100', 'xfy', ';    |'],
    ['1050', 'xfy', '->   *->'],
    ['1000', 'xfy', ','],
    ['990',  'xfx', ':='],
    ['900',  'fy',  '\\+'],
    ['700',  'xfx', '=   \\=   ==   \\==   =@=   \\=@=   @<   @>   @=<   @>=   '
                    '=..   is   =:=   =\\=   <   >   =<   >=   as   >:<   :<'],
    ['600',  'xfy', ':'],
    ['500',  'yfx', '+   -   /\\   \\/   xor'],
    ['400',  'yfx', '*   /   //   rem   mod   div   divmod   <<   >>'],
    ['200',  'xfx', '**'],
    ['200',  'xfy', '^'],
    ['200',  'fy',  '-   +   \\'],
    ['100',  'yfx', '.'],
    ['1',    'fx',  '$'],
]

section('operators', 'Operators', ''.join([
    para("An operator lets a compound term be written in infix, prefix or postfix "
         "position. It has a priority from 1 to 1200 — lower binds tighter — and a "
         "type that says where the arguments sit and how they associate: `f` marks the "
         "operator, `x` an argument of strictly lower priority, `y` an argument of the "
         "same priority or lower."),
    table(['Priority', 'Type', 'Operators'], OPS, 'ops'),
    para("So `a-b-c` is `(a-b)-c` because `-` is `yfx`, while `a^b^c` is `a^(b^c)` "
         "because `^` is `xfy`, and `a = b = c` is a syntax error because `=` is `xfx`. "
         "An argument of a compound term or an element of a list has a maximum "
         "priority of 999, which is why a term containing `,` must be parenthesised "
         "there: `f((a,b))`."),
    para("`|` used as an infix operator in a body is read as `;`. Operators are "
         "ordinary atoms, so `X = (+)` and `Y = -(1,2)` are both fine."),
    preds([
        ('op(+Priority, +Type, +Name)',
         "Defines Name as an operator, or a list of names in one call. Priority 0 "
         "removes the definition. Type is one of xfx, xfy, yfx, fy, fx, xf, yf. "
         "Redefining `,` is not allowed."),
        ('current_op(?Priority, ?Type, ?Name)',
         "Enumerates the operators currently defined, on backtracking."),
    ]),
    note('impl', 'Directives run while reading',
         "op/3 takes effect for the clauses read after it, so an operator used in a "
         "file must be declared by a directive earlier in that file."),
]))

# ---- 5. terms and standard order
section('terms', 'Terms and the standard order', ''.join([
    para("Terms are ordered by a total order used by the comparison predicates, by "
         "`sort/2` and `msort/2`, and by `setof/3`:"),
    pre("Var  <  Number  <  Atom  <  Compound"),
    ul([
        "Variables come first, ordered by age — the order is stable within a run but "
        "carries no other meaning.",
        "Numbers compare by value, so `1 @< 1.5 @< 2`. When an integer and a float are "
        "equal in value the float comes first, so `1.0 @< 1`.",
        "Atoms compare alphabetically by their text.",
        "Compound terms compare first by arity, then by name, then by their arguments "
        "left to right. Because a list is a compound term, `f(x) @< [a]` — arity 1 "
        "before arity 2.",
    ]),
    para("Two terms are identical (`==`) when they have the same structure and the "
         "same variables in the same places; they are variants (`=@=`) when they are "
         "the same up to a consistent renaming of variables, so `f(A,B) =@= f(X,Y)` "
         "holds but `f(A,A) =@= f(X,Y)` does not."),
    note('impl', 'Cyclic terms',
         "Unification does not do an occurs check, so `X = f(X)` succeeds and builds a "
         "cyclic term. Comparing, copying or printing one will not terminate. Use "
         "unify_with_occurs_check/2 where that matters."),
]))

# ---- 6. control
section('control', 'Control constructs', ''.join([
    para("These are recognised by the solver itself rather than being ordinary "
         "predicates, which is what lets cut and exceptions work across them."),
    preds([
        ('true', "Succeeds once."),
        ('fail', "Fails. `false` is the same."),
        ('(:Goal1, :Goal2)', "Conjunction: both goals must succeed."),
        ('(:Goal1 ; :Goal2)',
         "Disjunction: tries Goal1, and on backtracking Goal2."),
        ('(:Cond -> :Then ; :Else)',
         "If-then-else. If Cond has a solution, its first one is committed to and "
         "Then runs; otherwise Else runs. Without an else branch, `(Cond -> Then)` "
         "fails when Cond fails."),
        ('(:Cond *-> :Then ; :Else)',
         "Soft cut. Runs Then for every solution of Cond; runs Else only if Cond has "
         "no solution at all."),
        ('\\+ :Goal',
         "True when Goal has no solution. Bindings made while proving Goal are undone. "
         "`not/1` is a synonym."),
        ('!', "Cut: commits to the clause and to every choice made since the parent "
              "goal was called."),
        ('call(:Goal)',
         "Calls Goal. A cut inside is local to the call."),
        ('call(:Goal, +Extra, ...)',
         "Appends the extra arguments to Goal and calls it, so "
         "`call(plus(1), 2, X)` calls `plus(1,2,X)`. The standard defines call/2 to "
         "call/8; any number of arguments is accepted here."),
        ('catch(:Goal, ?Catcher, :Recovery)',
         "Runs Goal; if it throws a ball that unifies with Catcher, undoes the "
         "bindings and runs Recovery instead. Other balls pass through."),
        ('throw(+Ball)',
         "Throws Ball to the nearest matching catch/3. The ball is copied, so it "
         "survives the unwinding."),
    ]),
    '<h3>How cut behaves</h3>',
    para("A cut removes the choice points created since its clause was entered, "
         "including the clause alternatives of the predicate it appears in. It is "
         "transparent to `,` `;` `->` — a cut in either branch of a disjunction cuts "
         "the enclosing clause — and opaque to `call/1`, `\\+/1`, `findall/3` and the "
         "other predicates that call a goal, where it only cuts inside that goal."),
    pre("""
first(X) :- member(X, [1,2,3]), !.     % one solution: X = 1
all(X)   :- member(X, [1,2,3]).        % three solutions

?- findall(X, (member(X,[1,2,3]), call(!)), L).
L = [1,2,3].                            % the cut is local to call/1
"""),
    note('impl', 'Cut in a condition',
         "A cut in the condition of if-then-else is local to the condition, as the "
         "condition is already committed to its first solution."),
]))

# ---- 7. arithmetic
UNARY = [
    ['-X   +X   abs(X)', 'Negation, identity, absolute value.'],
    ['sign(X)', 'Sign as -1, 0 or 1; a float argument gives a float.'],
    ['min(X,Y)   max(X,Y)', 'Smaller or larger of two numbers; returns one argument '
                            'unchanged, and the first when they compare equal.'],
    ['sqrt(X)   exp(X)   log(X)   log2(X)', 'Float results; log of a non-positive '
                                            'number is an evaluation error.'],
    ['sin cos tan asin acos atan', 'Trigonometry in radians, float results.'],
    ['sinh cosh tanh asinh acosh atanh', 'Hyperbolic functions.'],
    ['float(X)', 'X as a float.'],
    ['integer(X)', 'X rounded to the nearest integer.'],
    ['float_integer_part(X)   float_fractional_part(X)',
     'The two halves of a float, both floats.'],
    ['truncate(X)   round(X)   ceiling(X)   floor(X)',
     'Float to integer: toward zero, to nearest (halves away from zero), up, down.'],
    ['\\ X', 'Bitwise complement.'],
    ['msb(X)', 'Position of the most significant bit of a positive integer.'],
    ['succ(X)', 'X + 1, for integers.'],
    ['random(X)', 'A random integer in 0 .. X-1.'],
    ['random_float', 'A random float in 0.0 .. 1.0.'],
]
BINARY = [
    ['X + Y   X - Y   X * Y', 'Integer when both arguments are integers, else float. '
                              'Integer overflow raises an evaluation error.'],
    ['X / Y', 'Integer division when both are integers and the division is exact, '
              'otherwise float division. Dividing by zero raises an evaluation error.'],
    ['X // Y', 'Integer division truncating toward zero.'],
    ['X div Y', 'Integer division truncating toward negative infinity.'],
    ['X mod Y', 'Remainder with the sign of the divisor: `-7 mod 2` is 1.'],
    ['X rem Y', 'Remainder with the sign of the dividend: `-7 rem 2` is -1.'],
    ['X ** Y', 'Power. Integer when both are integers and Y is not negative, '
               'otherwise float.'],
    ['X ^ Y', 'Power, integers only when both are integers: a negative exponent on an '
              'integer base other than 1 or -1 is a type error.'],
    ['X >> Y   X << Y', 'Arithmetic shift, integers only.'],
    ['X /\\ Y   X \\/ Y   xor(X,Y)', 'Bitwise and, or, exclusive or.'],
    ['gcd(X,Y)', 'Greatest common divisor.'],
    ['atan2(Y,X)   atan(Y,X)', 'Angle of the point (X,Y) in radians.'],
    ['copysign(X,Y)', 'Magnitude of X with the sign of Y.'],
    ['log(X,Y)', 'Logarithm of Y in base X.'],
    ['min(X,Y)   max(X,Y)', 'As above.'],
]
CONSTS = [
    ['pi   e   epsilon', 'The usual constants as floats.'],
    ['inf   infinite   nan', 'Float infinity and not-a-number.'],
    ['max_tagged_integer   min_tagged_integer', 'The largest and smallest integer.'],
    ['random', 'A random float in 0.0 .. 1.0.'],
    ['cputime', 'Processor time used, in seconds, as a float.'],
    ['realtime', 'Wall clock time as an integer, in seconds since the epoch.'],
    ['[c]', 'A one-element code list evaluates to that character code, so '
            '`X is "a"` gives 97.'],
]

section('arithmetic', 'Arithmetic', ''.join([
    para("Arithmetic happens only where a predicate asks for it: `is/2`, the "
         "arithmetic comparisons, and a few library predicates. Elsewhere `2+3` is "
         "just a term. Evaluation is recursive over the expression, and an unbound "
         "variable or an unknown function raises an error rather than failing."),
    preds([
        ('-Number is +Expr', "Evaluates Expr and unifies the result with Number."),
        ('+Expr1 =:= +Expr2', "The two expressions evaluate to equal numbers."),
        ('+Expr1 =\\= +Expr2', "They evaluate to different numbers."),
        ('+Expr1 < +Expr2', "Less than; also `>`, `=<`, `>=`."),
    ]),
    para("Integers are 64-bit; mixing an integer and a float in an operation gives a "
         "float. Comparisons convert as needed, so `1 =:= 1.0` is true even though "
         "`1 == 1.0` is false."),
    '<h3>Functions of one argument</h3>',
    table(['Function', 'Result'], UNARY, 'mono1'),
    '<h3>Functions of two arguments</h3>',
    table(['Function', 'Result'], BINARY, 'mono1'),
    '<h3>Constants</h3>',
    table(['Constant', 'Value'], CONSTS, 'mono1'),
    note('impl', 'No bignums',
         "Integer results that do not fit in 64 bits raise "
         "`evaluation_error(int_overflow)` rather than growing, and there are no "
         "rational numbers."),
]))

# ---- 8. builtin predicates
BUILTINS = [
    ('##', 'Testing the type of a term'),
    ('var(@Term)', "Term is an unbound variable."),
    ('nonvar(@Term)', "Term is not an unbound variable."),
    ('atom(@Term)', "Term is an atom, including [] and {}."),
    ('number(@Term)', "Term is an integer or a float."),
    ('integer(@Term)', "Term is an integer."),
    ('float(@Term)', "Term is a float."),
    ('atomic(@Term)', "Term is an atom or a number."),
    ('compound(@Term)', "Term has a functor and at least one argument."),
    ('callable(@Term)', "Term is an atom or a compound term."),
    ('is_list(@Term)', "Term is a proper list, ending in []."),
    ('ground(@Term)', "Term contains no unbound variables."),
    ('must_be(+Type, @Term)',
     "Succeeds if Term is of Type, otherwise raises a type or instantiation error. "
     "Types: integer, nonneg, positive_integer, float, number, atom, atomic, "
     "callable, var, nonvar, boolean, list."),

    ('##', 'Unification and comparison'),
    ('?Term1 = ?Term2', "Unifies the two terms. No occurs check."),
    ('?Term1 \\= ?Term2', "The terms do not unify; makes no bindings."),
    ('unify_with_occurs_check(?T1, ?T2)',
     "Unifies with an occurs check, so no cyclic term can be built."),
    ('@Term1 == @Term2', "The terms are identical, without unifying anything."),
    ('@Term1 \\== @Term2', "The terms are not identical."),
    ('@Term1 =@= @Term2', "The terms are variants: identical up to variable renaming."),
    ('@Term1 \\=@= @Term2', "The terms are not variants."),
    ('@Term1 @< @Term2',
     "Term1 comes before Term2 in the standard order; also `@>`, `@=<`, `@>=`."),
    ('compare(?Order, @T1, @T2)',
     "Order is one of `<`, `=`, `>`, according to the standard order."),

    ('##', 'Constructing and inspecting terms'),
    ('functor(?Term, ?Name, ?Arity)',
     "Relates a term to its name and arity. With Term unbound, builds a term with "
     "fresh arguments; an arity of 0 gives the atom Name."),
    ('arg(+N, +Term, ?Arg)',
     "Arg is the Nth argument of Term, counting from 1. Fails if N is out of range."),
    ('?Term =.. ?List',
     "List is Term's name followed by its arguments, so `f(a,b) =.. [f,a,b]`. "
     "An atomic term gives a one-element list."),
    ('copy_term(+Term, -Copy)',
     "Copy is Term with all its variables replaced by fresh ones."),
    ('term_variables(+Term, -Vars)',
     "Vars are the variables of Term, in the order they first appear."),
    ('numbervars(+Term, +Start, -End)',
     "Binds each variable in Term to `'$VAR'(N)`, numbering from Start. Such terms "
     "print as A, B, ... under write/1 and print/1."),
    ('setarg(+N, +Term, +Value)',
     "Replaces the Nth argument of Term with Value. The change is undone on "
     "backtracking."),

    ('##', 'Atoms, numbers and text'),
    ('atom_length(+Atomic, ?Length)',
     "Length is the number of characters in Atomic, which may be an atom or a number. "
     "Counts characters, not bytes."),
    ('atom_codes(?Atom, ?Codes)',
     "Relates an atom or number to a list of character codes."),
    ('atom_chars(?Atom, ?Chars)',
     "Relates an atom or number to a list of one-character atoms."),
    ('char_code(?Char, ?Code)',
     "Relates a one-character atom to its character code."),
    ('number_codes(?Number, ?Codes)',
     "Relates a number to its text as codes; raises a syntax error if the text is not "
     "a number."),
    ('number_chars(?Number, ?Chars)', "The same, with one-character atoms."),
    ('atom_number(?Atom, ?Number)',
     "Converts between an atom and a number, and fails quietly if the atom is not a "
     "number."),
    ('atom_concat(?A, ?B, ?C)',
     "C is the concatenation of A and B. With C bound and either A or B unbound, "
     "enumerates every split of C on backtracking."),
    ('sub_atom(+Atom, ?Before, ?Len, ?After, ?Sub)',
     "Sub is the substring of Atom with Before characters before it, Len characters "
     "long and After characters after. Enumerates all substrings when unbound, and "
     "finds occurrences when Sub is given."),
    ('sub_string(+S, ?B, ?L, ?A, ?Sub)', "A synonym for sub_atom/5."),
    ('upcase_atom(+Atom, -Upper)', "Upper is Atom with ASCII letters upper-cased."),
    ('downcase_atom(+Atom, -Lower)', "Lower is Atom with ASCII letters lower-cased."),
    ('atomic_list_concat(+List, -Atom)', "Concatenates a list of atomics into Atom."),
    ('atomic_list_concat(?List, +Sep, ?Atom)',
     "Joins List with Sep between the parts. With List unbound, splits Atom on Sep "
     "instead."),
    ('concat_atom(?List, ?Atom)', "A synonym for atomic_list_concat/2, also with /3."),
    ('term_to_atom(?Term, ?Atom)',
     "Writes Term to Atom with quoting, or reads Atom as a term when Term is unbound."),
    ('term_string(?Term, ?Atom)', "A synonym for term_to_atom/2."),
    ('atom_to_term(+Atom, -Term, -Bindings)',
     "Reads Atom as a term; Bindings is a list of `Name=Var` for the named variables."),

    ('##', 'Finding all solutions'),
    ('findall(?Template, :Goal, -Bag)',
     "Bag holds a copy of Template for every solution of Goal, in order. Succeeds with "
     "[] when there is none."),
    ('findall(?Template, :Goal, -Bag, +Tail)',
     "As findall/3, but the list ends in Tail rather than []."),
    ('findnsols(+N, ?Template, :Goal, -Bag)',
     "As findall/3, but stops after N solutions."),
    ('bagof(?Template, :Goal, -Bag)',
     "Like findall/3, but fails when there is no solution, and backtracks over the "
     "bindings of the free variables of Goal, which group the results. `V^Goal` marks "
     "V as not free."),
    ('setof(?Template, :Goal, -Set)',
     "As bagof/3, with the result sorted and duplicates removed."),
    ('aggregate_all(+Spec, :Goal, -Result)',
     "Aggregates over all solutions. Spec is count, count(T), sum(E), max(E), min(E), "
     "bag(T) or set(T); max and min fail when there is no solution."),
    ('forall(:Cond, :Action)',
     "Action succeeds for every solution of Cond. Makes no bindings."),
    ('^(?Var, :Goal)',
     "Outside bagof/3 and setof/3, simply calls Goal."),

    ('##', 'Sorting'),
    ('sort(+List, -Sorted)',
     "Sorts into the standard order and removes duplicates."),
    ('msort(+List, -Sorted)', "Sorts into the standard order, keeping duplicates."),
    ('sort(+Key, +Order, +List, -Sorted)',
     "Sorts on argument Key of each element — 0 means the whole element — with Order "
     "one of `@<`, `@=<`, `@>`, `@>=`. The strict orders remove duplicate keys. "
     "The sort is stable."),
    ('keysort(+Pairs, -Sorted)',
     "Sorts a list of `Key-Value` pairs by key only, keeping the original order of "
     "equal keys."),
    ('predsort(:Pred, +List, -Sorted)',
     "Sorts using `call(Pred, Order, A, B)`, which must bind Order to `<`, `=` or `>`. "
     "Elements compared `=` are dropped."),

    ('##', 'Lists'),
    ('append(?A, ?B, ?C)',
     "C is A followed by B. With C bound, enumerates every way of splitting it."),
    ('append(+ListOfLists, -List)', "Concatenates a list of lists."),
    ('member(?Elem, ?List)', "Elem is a member of List; enumerates on backtracking."),
    ('memberchk(?Elem, +List)', "As member/2, but only the first solution."),
    ('length(?List, ?Length)',
     "Length is the number of elements of List. Builds a list of fresh variables when "
     "List is unbound, and enumerates lengths when both are unbound."),
    ('reverse(+List, -Reversed)', "Reversed has the elements of List in reverse order."),
    ('nth0(?Index, ?List, ?Elem)',
     "Elem is the Index-th element counting from 0; enumerates when Index is unbound."),
    ('nth1(?Index, ?List, ?Elem)', "As nth0/3, counting from 1."),
    ('last(+List, -Last)', "Last is the last element of List."),
    ('select(?Elem, ?List, ?Rest)',
     "Rest is List with one occurrence of Elem removed."),
    ('select(?X, ?Xs, ?Y, ?Ys)', "Ys is Xs with one X replaced by Y."),
    ('selectchk(?Elem, +List, -Rest)', "As select/3, committed to the first solution."),
    ('subtract(+Set, +Delete, -Result)',
     "Result holds the elements of Set that are not in Delete."),
    ('intersection(+A, +B, -C)', "C holds the elements of A that also occur in B."),
    ('union(+A, +B, -C)', "C holds the elements of A not in B, followed by B."),
    ('delete(+List, @Elem, -Rest)',
     "Rest is List without the elements that unify with Elem."),
    ('exclude(:Pred, +List, -Rest)', "Rest holds the elements for which Pred fails."),
    ('include(:Pred, +List, -Rest)', "Rest holds the elements for which Pred succeeds."),
    ('partition(:Pred, +List, -Incl, -Excl)', "Both of the above in one pass."),
    ('maplist(:Goal, ?List)',
     "Calls Goal on each element. Also maplist/3, /4 and /5 for two, three and four "
     "lists walked in step."),
    ('foldl(:Goal, +List, +V0, -V)',
     "Threads an accumulator through the list with `call(Goal, Elem, Acc0, Acc)`. "
     "foldl/5 walks two lists."),
    ('sum_list(+List, -Sum)', "Sum of a list of numbers; `sumlist/2` is a synonym."),
    ('max_list(+List, -Max)', "Largest number in the list; also min_list/2."),
    ('max_member(-Max, +List)',
     "Largest element in the standard order; also min_member/2."),
    ('numlist(+Low, +High, -List)', "List is [Low, Low+1, ..., High]."),
    ('permutation(?List, ?Perm)', "Perm is a permutation of List."),
    ('flatten(+Nested, -Flat)', "Flattens nested lists into one list."),
    ('list_to_set(+List, -Set)',
     "Removes duplicates, keeping the first occurrence of each element."),
    ('pairs_keys_values(?Pairs, ?Keys, ?Values)',
     "Relates a list of `Key-Value` pairs to its keys and values; also pairs_keys/2 "
     "and pairs_values/2."),
    ('between(+Low, +High, ?X)',
     "X is an integer from Low to High. Enumerates when X is unbound, tests when it is "
     "bound. High may be `inf` or `infinite`. The enumeration runs from a single choice "
     "point, so a failure-driven loop over it uses constant space."),
    ('succ(?Int1, ?Int2)',
     "Int2 is Int1 + 1, for non-negative integers; works in either direction."),
    ('plus(?Int1, ?Int2, ?Int3)',
     "Int3 is Int1 + Int2, with any one of the three unbound."),
    ('apply(:Goal, +ExtraArgs)', "Calls Goal with the extra arguments appended."),

    ('##', 'Control (library)'),
    ('once(:Goal)', "Calls Goal and commits to its first solution."),
    ('ignore(:Goal)', "Calls Goal once; succeeds even when Goal fails."),
    ('not(:Goal)', "A synonym for `\\+`."),
    ('repeat',
     "Succeeds, and succeeds again every time it is backtracked into. Like between/3 it "
     "runs from a single choice point, so a `repeat, ..., !` loop uses constant space. "
     "A cut or an exception is the only way out."),
    ('assertion(:Goal)',
     "Succeeds if Goal succeeds, otherwise throws `assertion_failed(Goal)`."),

    ('##', 'The database'),
    ('assertz(+Clause)',
     "Adds Clause at the end of its predicate. The clause is copied, so later bindings "
     "do not affect it. `assert/1` is a synonym."),
    ('asserta(+Clause)', "Adds Clause at the front of its predicate."),
    ('retract(+Clause)',
     "Removes the first clause that unifies with Clause; on backtracking, removes the "
     "next one."),
    ('retractall(+Head)',
     "Removes every clause whose head unifies with Head, and makes the predicate known "
     "and dynamic so that later calls fail rather than raise an error."),
    ('abolish(+Name/+Arity)', "Removes all clauses of a predicate."),
    ('clause(+Head, ?Body)',
     "Enumerates the clauses of a predicate; a fact has the body `true`."),
    ('dynamic(+Spec)',
     "Declares predicates dynamic, so calling them fails instead of raising an "
     "existence error. Spec is a `Name/Arity`, a comma sequence, or a list."),
    ('discontiguous(+Spec)', "Accepted and recorded; clauses may be spread out anyway."),
    ('current_predicate(?Name/?Arity)',
     "Enumerates the predicates that have been defined."),
    ('predicate_property(+Head, ?Prop)', "Currently only the property `defined`."),
    ('nb_setval(+Key, +Value)',
     "Stores a copy of Value under the atom Key, outside the database."),
    ('nb_getval(+Key, -Value)', "Retrieves the value stored under Key."),
    ('b_setval(+Key, +Value)',
     "Accepted as a synonym of nb_setval/2; the assignment is not undone on "
     "backtracking. Also b_getval/2."),

    ('##', 'Writing terms'),
    ('write(?Term)',
     "Writes Term without quoting, honouring operators and `'$VAR'(N)` names."),
    ('print(?Term)', "Writes Term with quoting, like writeq/1."),
    ('writeq(?Term)', "Writes Term with quotes where they would be needed to read it "
                      "back."),
    ('write_canonical(?Term)',
     "Writes Term quoted and without operator notation, so lists print as "
     "`'.'(1,'.'(2,[]))`."),
    ('write_term(?Term, +Options)',
     "Writes Term under Options: `quoted(Bool)`, `ignore_ops(Bool)`, "
     "`numbervars(Bool)`, `max_depth(N)`."),
    ('writeln(?Term)', "Writes Term and a newline."),
    ('portray_clause(+Clause)',
     "Writes a clause as it would be listed, with numbered variables, indented body "
     "goals and a closing full stop."),
    ('nl', "Writes a newline."),
    ('tab(+N)', "Writes N spaces."),
    ('put_char(+Char)', "Writes a one-character atom."),
    ('print_message(+Kind, +Message)',
     "Prints an error term on standard error the way the toplevel does."),

    ('##', 'Formatted output'),
    ('format(+Format)', "Writes Format, which may be an atom or a code list."),
    ('format(+Format, +Args)',
     "Writes Format, taking arguments from the list Args. A single non-list argument "
     "is taken as a one-element list."),
    ('format(+Sink, +Format, +Args)',
     "Writes to a stream, or captures the output when Sink is `atom(A)`, `string(A)`, "
     "`codes(C)` or `chars(C)`."),

    ('##', 'Reading terms and streams'),
    ('read(?Term)',
     "Reads a term from the current input; gives `end_of_file` at the end."),
    ('read_term(?Term, +Options)',
     "As read/1, with `variable_names(L)`, `variables(L)` or `singletons(L)`."),
    ('open(+File, +Mode, -Stream)',
     "Opens File in mode `read`, `write` or `append`. open/4 takes an options list, "
     "which is accepted and ignored."),
    ('close(+Stream)', "Closes a stream."),
    ('current_input(-Stream)', "The stream read/1 uses; also current_output/1."),
    ('set_input(+Stream)', "Makes Stream the current input; also set_output/1."),
    ('with_output_to(+Sink, :Goal)',
     "Calls Goal once with the output captured into Sink, which is `atom(A)`, "
     "`string(A)`, `codes(C)` or `chars(C)`."),
    ('flush_output', "Flushes the current output stream."),
    ('write(+Stream, ?Term)',
     "The stream versions of the writing predicates: write/2, print/2, writeq/2, "
     "write_canonical/2, write_term/3, writeln/2, nl/1, tab/2, read/2, read_term/3."),

    ('##', 'Loading, flags and the system'),
    ('consult(+File)',
     "Loads a file, adding its clauses to the database. `[file]` and "
     "`ensure_loaded/1` do the same; the `.pl` extension may be left off."),
    ('initialization(:Goal)',
     "Runs Goal once all the files named on the command line have been loaded."),
    ('listing', "Writes every user predicate; listing/1 takes a Name or Name/Arity."),
    ('halt', "Leaves the interpreter; halt/1 sets the exit status."),
    ('statistics(+Key, -Value)',
     "Key is runtime, cputime, process_cputime or walltime, giving "
     "`[Total, SinceLast]` in milliseconds; inferences, giving a count; or memory, "
     "giving `[InUse, 0]` in bytes."),
    ('set_prolog_flag(+Flag, +Value)', "Sets `double_quotes` or `unknown`."),
    ('current_prolog_flag(?Flag, ?Value)', "Reads a flag; enumerates when unbound."),
    ('garbage_collect', "Accepted; collection is automatic, so this does nothing."),
    ('help', "Prints a short summary at the toplevel."),
]

FORMAT_DIRECTIVES = [
    ['~w', 'Write the next argument, unquoted.'],
    ['~p', 'Write it quoted, like print/1.'],
    ['~q', 'Write it quoted, like writeq/1.'],
    ['~a', 'Write an atomic argument as text, without quotes.'],
    ['~s', 'Write a code or character list as text.'],
    ['~d', 'Write an integer. `~Nd` inserts a decimal point N digits from the right.'],
    ['~D', 'Write an integer with a comma between each group of three digits.'],
    ['~f  ~e  ~g', 'Write a float in fixed, exponential or shortest form. `~Nf` sets '
                   'the number of digits, six by default.'],
    ['~c', 'Write the character whose code is the argument; `~Nc` repeats it N times.'],
    ['~r  ~R', 'Write an integer in base N (`~16r`), in lower or upper case.'],
    ['~n', 'Write a newline; `~Nn` writes N of them.'],
    ['~i', 'Skip an argument.'],
    ['~t', 'Mark a fill point for the next column stop.'],
    ['~N|', 'Pad to column N, distributing the padding over the fill points, or at the '
            'end of the segment when there are none.'],
    ['~N+', 'Pad to N columns past the previous column stop.'],
    ['~*c', 'Take the count from the argument list, as in `format("~*c", [3, 0\'x])`.'],
    [lit('~`Xt'), 'Use X as the fill character rather than a space.'],
    ['~~', 'Write a tilde.'],
]

section('builtins', 'Builtin predicates', ''.join([
    para("The predicates below are always available. Those defined in C and those "
         "written in the bootstrap library are not distinguished here, because they "
         "behave the same way; both can be shadowed only by the library ones, since "
         "redefining a built-in predicate written in C raises a permission error."),
    '<div class="filter">'
    '<label class="visually-hidden" for="pfilter">Filter predicates</label>'
    '<input id="pfilter" type="search" placeholder="Filter predicates: try sort, atom_, findall" '
    'autocomplete="off" spellcheck="false">'
    '<span class="filter-count" id="pcount"></span></div>',
    preds(BUILTINS),
    '<h3 id="format-directives">Format directives</h3>',
    para("These are understood by format/1,2,3. A directive may take a numeric "
         "argument, written between the tilde and the letter."),
    table(['Directive', 'Effect'], FORMAT_DIRECTIVES, 'mono1'),
    pre("""
?- format("~w and ~q~n", ['a b', 'a b']).
a b and 'a b'

?- format("~a~t~15|~2f~n", [total, 12.5]).
total          12.50
"""),
]))

# ---- 9. DCG
DCG_RULES = [
    ['Variable', 'phrase(Var, S0, S)'],
    ['(A, B)', "A then B, threading the list through"],
    ['(A ; B)', 'either branch, both spanning the same part of the list'],
    ['(A -> B)', 'if-then, threading the list through'],
    ['\\+ A', "(\\+ A', S = S0) — matches nothing"],
    ['!', '(!, S = S0)'],
    ['{Goal}', '(Goal, S = S0) — an ordinary goal, consuming nothing'],
    ['[]', 'S = S0'],
    ['[a,b,c]', 'matches those items at the front of the list'],
    ['"abc"', 'the same, for the codes or chars the flag produces'],
    ['call(G)', 'call(G, S0, S)'],
    ['Other callable', 'the same goal with two extra arguments'],
]

section('dcg', 'Grammars', ''.join([
    para("A grammar rule `Head --> Body` is translated into an ordinary clause when "
         "the file is loaded, by adding two arguments that thread the input list "
         "through the body: the list before, and the list after."),
    pre("""
greeting --> [hello], subject.
subject  --> [world].
subject  --> [prolog].

?- phrase(greeting, [hello, prolog]).
true.
"""),
    para("A rule may also carry a pushback list, written `Head, PushBack --> Body`, "
         "which puts items back onto the input after the body has run."),
    '<h3>How bodies translate</h3>',
    table(['In the body', 'Becomes'], DCG_RULES, 'mono1 mono2'),
    '<h3>Calling a grammar</h3>',
    preds([
        ('phrase(:Rule, ?List)', "List matches Rule exactly."),
        ('phrase(:Rule, ?List, ?Rest)',
         "Rule matches a prefix of List, leaving Rest. Rule may be any grammar body, "
         "not just a non-terminal."),
    ]),
    pre("""
digits([D|T]) --> digit(D), digits(T).
digits([D])   --> digit(D).
digit(D)      --> [D], { D >= 0'0, D =< 0'9 }.

?- phrase(digits(Ds), "42", Rest).
Ds = [52,50],
Rest = [].
"""),
]))

# ---- 10. errors
ERRORS = [
    ['instantiation_error',
     'An argument was an unbound variable where a value was needed.'],
    ['type_error(Type, Culprit)',
     'Culprit is not of the expected Type, as in `atom_length(1.0e10, X)` asking for '
     'an integer.'],
    ['domain_error(Domain, Culprit)',
     'Culprit has the right type but a value outside the allowed set, such as an '
     'unknown option or sort order.'],
    ['existence_error(procedure, Name/Arity)',
     'An undefined predicate was called, unless the unknown flag says fail.'],
    ['existence_error(source_sink, File)', 'A file could not be opened.'],
    ['evaluation_error(zero_divisor)', 'Division or remainder by zero.'],
    ['evaluation_error(int_overflow)', 'An integer result does not fit in 64 bits.'],
    ['evaluation_error(undefined)',
     'An arithmetic function has no value there, such as sqrt of a negative number.'],
    ['representation_error(max_arity)', 'A term of more than 256 arguments.'],
    ['representation_error(character_code)', 'A character code outside Unicode.'],
    ['permission_error(modify, static_procedure, PI)',
     'An attempt to assert to, retract from or inspect a predicate written in C.'],
    ['syntax_error(Message)',
     'The reader could not parse the text. Message names the file and line.'],
]

section('errors', 'Exceptions and errors', ''.join([
    para("Builtin predicates report problems by throwing a term of the form "
         "`error(Formal, Context)`, where Formal describes what went wrong and Context "
         "is currently an unbound variable. Programs may throw anything at all with "
         "`throw/1`."),
    table(['Formal', 'Raised when'], ERRORS, 'mono1'),
    pre("""
?- catch(X is foo + 1, error(type_error(T, C), _), true).
T = evaluable,
C = foo/0.
"""),
    para("An exception that no `catch/3` handles unwinds to the toplevel, which prints "
         "it as a readable message on standard error and abandons the query. In a "
         "directive it is printed the same way and loading continues with the next "
         "clause; from a `-g` goal it is printed and the interpreter exits with "
         "status 1."),
    note('impl', 'Errors and backtracking',
         "The ball is copied before the stack is unwound, so it keeps its bindings "
         "even though the bindings made inside the goal are undone before Recovery "
         "runs."),
]))

# ---- 11. flags
FLAGS = [
    ['bounded', 'true', 'read-only', 'Integers are bounded — there are no bignums.'],
    ['max_integer', '9223372036854775807', 'read-only', 'The largest integer.'],
    ['min_integer', '-9223372036854775808', 'read-only', 'The smallest integer.'],
    ['double_quotes', 'codes', 'settable',
     'How "text" is read: codes, chars or atom.'],
    ['unknown', 'error', 'settable',
     'What calling an undefined predicate does: error or fail.'],
    ['dialect', 'cprolog', 'read-only', 'Identifies this implementation.'],
    ['version', '10000', 'read-only', 'Version as a single integer.'],
    ['max_arity', 'unbounded', 'read-only',
     'Reported as unbounded; the reader stops at 256 arguments.'],
]

section('flags', 'Flags', ''.join([
    para("Flags are read with `current_prolog_flag/2` and changed, where they are "
         "settable, with `set_prolog_flag/2`."),
    table(['Flag', 'Default', 'Access', 'Meaning'], FLAGS, 'mono1 mono2'),
]))

# ---- 12. deviations
section('limits', 'Deviations and limits', ''.join([
    para("This is a compact interpreter, and the following are the places where it "
         "knowingly differs from a full ISO system. Each is a deliberate omission "
         "rather than an oversight."),
    '<h3>Numbers</h3>',
    ul([
        "Integers are 64-bit; overflow raises `evaluation_error(int_overflow)` instead "
        "of growing without bound. There are no rationals.",
        "`2 ** 3` gives the integer 8 rather than a float, matching common practice "
        "rather than the ISO standard.",
    ]),
    '<h3>Terms and text</h3>',
    ul([
        "There is no distinct string type; double-quoted text is a code list, a char "
        "list or an atom according to the `double_quotes` flag, and `sub_string/5` and "
        "`term_string/2` are synonyms of their atom counterparts.",
        "The maximum arity of a term is 256.",
        "Unification has no occurs check by default, so a cyclic term can be built; "
        "printing or copying one will not terminate.",
    ]),
    '<h3>Predicates that are absent</h3>',
    ul([
        "No modules, tabling, constraints, attributed variables, coroutining or "
        "threads.",
        "No yall lambdas, so `maplist([X]>>Goal, L)` is not available — write a named "
        "helper predicate instead.",
        "The character predicates `get_char/1,2`, `peek_char/1,2` and "
        "`at_end_of_stream/0,1` are not implemented, and `put_char/2` exists only in "
        "its one-argument form.",
        "`read_term/2,3` accepts `singletons(L)` but always reports `[]`.",
        "`open/4` accepts an options list and ignores it.",
        "`discontiguous/1` is recorded but never enforced; clauses may be spread "
        "through a file regardless.",
    ]),
    '<h3>Behaviour worth knowing</h3>',
    ul([
        "After `abolish/1` a predicate that was dynamic stays known, so calls to it "
        "fail rather than raising an existence error.",
        "A retracted clause is held until its predicate is abolished, so a program "
        "that retracts millions of clauses from one predicate keeps them in memory.",
        "A `-g` goal that fails prints a warning but still exits with status 0; only "
        "an uncaught exception exits with 1.",
        "Memory is reclaimed on backtracking, and otherwise by a collector that can "
        "only run when the computation is deterministic. The heap is released to the "
        "newest choice point's mark, so a loop driven by `between/3`, `repeat/0` or "
        "backtracking into facts runs in constant space, while one driven by a "
        "generator written as a recursive predicate costs about a kilobyte an "
        "iteration: a million iterations peak at 754 MB against 2.8 MB for the same "
        "loop over `between/3`. Writing such a generator as a builtin in C is the way "
        "round it.",
    ]),
]))


render(title='C Prolog Reference',
       prompt='?- version 1.0',
       subtitle="The language as this interpreter implements it: syntax, control, "
                "arithmetic, every builtin predicate, grammars, errors, and the "
                "places it parts company with the ISO standard.",
       outfile='reference.html',
       sub_under='builtins')
