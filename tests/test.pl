/*  test.pl -- the regression test suite.

    Run with:  make test      (or ./prolog -q tests/test.pl -g run_tests)

    Every test/2 fact names a goal that must succeed.  Goals that must fail
    are written with \+, and goals that must raise are wrapped in catch/3.
*/

:- dynamic(tmp/1).
:- dynamic(cnt/1).

/* ---------------- unification and comparison ---------------- */

test(unify_atom,      a = a).
test(unify_var,       (X = f(Y), Y = 1, X == f(1))).
test(unify_list,      [1,2,3] = [1|[2,3]]).
test(unify_fail,      \+ f(a) = f(b)).
test(unify_arity,     \+ f(a) = f(a,b)).
test(unify_occurs,    \+ unify_with_occurs_check(X, f(X))).
test(unify_cyclic_ok, (X = f(X), X = f(_))).
test(not_unify,       a \= b).
test(eq_var,          (X = Y, X == Y)).
test(neq_var,         X \== _Y).
test(order_std,       (compare(<, 1, a), compare(<, a, f(x)), compare(<, _V, 1))).
test(order_num,       (compare(<, 1, 1.5), compare(>, 2, 1.5))).
test(order_float_int, compare(<, 1.0, 1)).
test(sort_order,      msort([b, 1, f(x), "s", 2.0, a], [1,2.0,a,b,f(x),[115]])).

/* ---------------- types ---------------- */

test(type_var,        (var(_), \+ var(a))).
test(type_atom,       (atom(a), atom([]), \+ atom("x"), \+ atom(1))).
test(type_number,     (number(1), number(1.0), \+ number(a))).
test(type_integer,    (integer(3), \+ integer(3.0))).
test(type_float,      (float(3.0), \+ float(3))).
test(type_atomic,     (atomic(a), atomic(1), \+ atomic(f(x)), \+ atomic(_))).
test(type_compound,   (compound(f(x)), compound([a]), \+ compound(a))).
test(type_callable,   (callable(a), callable(f(x)), \+ callable(1))).
test(type_is_list,    (is_list([]), is_list([a,b]), \+ is_list([a|_]))).
test(type_ground,     (ground(f(a)), \+ ground(f(_)))).

/* ---------------- arithmetic ---------------- */

test(ar_add,          X is 2 + 3, X =:= 5).
test(ar_prec,         X is 2 + 3 * 4, X =:= 14).
test(ar_float,        X is 7 / 2, X =:= 3.5).
test(ar_intdiv,       X is 6 / 3, integer(X), X =:= 2).
test(ar_idiv,         X is 7 // 2, X =:= 3).
test(ar_negdiv,       X is -7 // 2, X =:= -3).
test(ar_div_floor,    X is -7 div 2, X =:= -4).
test(ar_mod,          (X is -7 mod 2, X =:= 1)).
test(ar_rem,          (X is -7 rem 2, X =:= -1)).
test(ar_pow_int,      X is 2 ** 10, X =:= 1024).
test(ar_pow_caret,    X is 2 ^ 10, X =:= 1024).
test(ar_pow_float,    X is 2.0 ** 0.5, abs(X - 1.4142135) < 0.001).
test(ar_min_max,      (X is min(3, 5), Y is max(3, 5), X =:= 3, Y =:= 5)).
test(ar_abs_sign,     (X is abs(-3), Y is sign(-3), X =:= 3, Y =:= -1)).
test(ar_bits,         (X is 5 /\ 3, Y is 5 \/ 3, Z is 5 xor 3, W is \ 5,
                       X =:= 1, Y =:= 7, Z =:= 6, W =:= -6)).
test(ar_shift,        (X is 1 << 10, Y is 1024 >> 3, X =:= 1024, Y =:= 128)).
test(ar_shift_neg,    (X is -1 << 2, Y is -8 >> 1, X =:= -4, Y =:= -4)).
test(ar_shift_range,  (catch(_ is 1 << 64, error(evaluation_error(undefined),_), true),
                       catch(_ is 1 << -1, error(evaluation_error(undefined),_), true))).
test(ar_gcd,          X is gcd(12, 18), X =:= 6).
test(ar_trig,         (X is cos(0.0), X =:= 1.0)).
test(ar_sqrt,         X is sqrt(16.0), X =:= 4.0).
test(ar_round,        (A is round(2.5), B is truncate(2.7), C is ceiling(2.1),
                       D is floor(-2.1), A =:= 3, B =:= 2, C =:= 3, D =:= -3)).
test(ar_float_parts,  (X is float_integer_part(3.7), Y is float_fractional_part(3.5),
                       X =:= 3.0, Y =:= 0.5)).
test(ar_compare,      (1 < 2, 2 =< 2, 3 > 2, 3 >= 3, 1 =:= 1.0, 1 =\= 2)).
test(ar_pi,           (X is pi, X > 3.14, X < 3.15)).
test(ar_eval_list,    X is "a", X =:= 97).
test(ar_succ,         (succ(3, X), succ(Y, 4), X =:= 4, Y =:= 3)).
test(ar_plus,         (plus(1, 2, X), plus(1, Y, 3), X =:= 3, Y =:= 2)).
test(ar_zero_div,     catch(_ is 1 // 0, error(evaluation_error(zero_divisor), _), true)).
test(ar_inst_err,     catch(_ is _ + 1, error(instantiation_error, _), true)).
test(ar_type_err,     catch(_ is foo + 1, error(type_error(evaluable, foo/0), _), true)).
test(ar_overflow,     catch(_ is 9223372036854775807 + 1,
                            error(evaluation_error(int_overflow), _), true)).

/* ---------------- control ---------------- */

test(ctl_true,        true).
test(ctl_fail,        \+ fail).
test(ctl_conj,        (true, true)).
test(ctl_disj,        (fail ; true)).
test(ctl_ite_then,    (1 < 2 -> true ; fail)).
test(ctl_ite_else,    (1 > 2 -> fail ; true)).
test(ctl_ite_nested,  (X = 2, (X =:= 1 -> R = a ; X =:= 2 -> R = b ; R = c), R == b)).
test(ctl_cut,         (findall(X, cut_first(X), [1]))).
test(ctl_cut_local,   (findall(X, cut_in_call(X), [1,2,3]))).
test(ctl_softcut,     (findall(X, (member(X,[1,2]) *-> true ; X = none), [1,2]))).
test(ctl_softcut_else,(findall(X, (fail *-> true ; X = none), [none]))).
test(ctl_neg,         (\+ fail, \+ \+ true)).
test(ctl_call_n,      (call(plus(1), 2, X), X =:= 3)).
test(ctl_call_cut,    (findall(X, (member(X,[1,2,3]), call((!, true))), [1,2,3]))).
test(ctl_once,        (findall(X, once(member(X,[a,b])), [a]))).
test(ctl_ignore,      (ignore(fail), ignore(true))).
test(ctl_forall,      (forall(member(X,[1,2,3]), X > 0), \+ forall(member(X,[1,-2]), X > 0))).
test(ctl_between,     (findall(X, between(1,5,X), [1,2,3,4,5]))).
test(ctl_between_det, (between(1, 10, 5), \+ between(1, 3, 7))).
test(ctl_between_one, (findall(X, between(3,3,X), [3]))).
test(ctl_between_none,(findall(X, between(5,1,X), []))).
test(ctl_between_inf, (findall(X, (between(1,inf,X), X >= 3, !), [3]))).
test(ctl_between_err, (catch(between(a,2,_), error(type_error(integer,a),_), true),
                       catch(between(1,_,_), error(instantiation_error,_), true),
                       catch(between(1,2,a), error(type_error(integer,a),_), true))).
test(ctl_repeat,      (nb_setval(rc, 0),
                       (   repeat,
                           nb_getval(rc, C), C1 is C + 1, nb_setval(rc, C1),
                           C1 >= 5, !
                       ),
                       nb_getval(rc, 5))).
test(ctl_repeat_cut,  (findall(x, (repeat, !), [x]))).

/*  Both generators must reuse one choice point: the heap is sampled on the
    last iteration, so a version that leaves a choice point per solution shows
    up as growth here rather than only as a slow test. */
test(space_between,   (statistics(memory, [M0,_]),
                       (   between(1, 200000, I),
                           ( I =:= 200000 -> statistics(memory, [M1,_]),
                                             nb_setval(peak, M1) ; true ),
                           fail
                       ;   true
                       ),
                       nb_getval(peak, Peak),
                       Growth is Peak - M0,
                       Growth < 2000000)).
test(space_repeat,    (statistics(memory, [M0,_]),
                       nb_setval(rc2, 0),
                       (   repeat,
                           nb_getval(rc2, C), C1 is C + 1, nb_setval(rc2, C1),
                           ( C1 >= 100000 -> statistics(memory, [M1,_]),
                                             nb_setval(peak2, M1) ; true ),
                           C1 >= 100000, !
                       ),
                       nb_getval(peak2, Peak),
                       Growth is Peak - M0,
                       Growth < 2000000)).

cut_first(X) :- member(X, [1,2,3]), !.
cut_in_call(X) :- member(X, [1,2,3]).

/* ---------------- exceptions ---------------- */

test(exc_catch,       catch(throw(oops), oops, true)).
test(exc_rethrow,     catch(catch(throw(a), b, true), a, true)).
test(exc_recovery,    (catch(throw(x), x, R = caught), R == caught)).
test(exc_no_catch,    (catch(true, _, fail))).
test(exc_backtrack,   (findall(X, catch(member(X,[1,2]), _, fail), [1,2]))).
test(exc_unknown,     catch(no_such_predicate_here, error(existence_error(procedure, _), _), true)).
test(exc_after_exit,  (catch(( catch(true, e, true), throw(e2)), e2, true))).
test(exc_type,        catch(atom_length(1, _), _, true)).
test(exc_cut_in_catch,(catch((member(X,[1,2]), !), _, true), X == 1)).

/* ---------------- findall, bagof, setof ---------------- */

test(fa_basic,        findall(X, member(X,[a,b,c]), [a,b,c])).
test(fa_empty,        findall(X, (member(X,[a]), fail), [])).
test(fa_expr,         findall(Y, (member(X,[1,2,3]), Y is X*X), [1,4,9])).
test(fa_tail,         (findall(X, member(X,[a]), L, [z]), L == [a,z])).
test(fa_nested,       findall(X-L, (member(X,[1,2]), findall(Y, member(Y,[X,X]), L)),
                              [1-[1,1], 2-[2,2]])).
test(bagof_simple,    bagof(X, member(X,[3,1,2]), [3,1,2])).
test(bagof_fails,     \+ bagof(X, member(X,[]), _)).
test(bagof_free,      (findall(K-B, bagof(V, p(K,V), B), [1-[a,b], 2-[c]]))).
test(bagof_caret,     (bagof(V, K^p(K,V), Vs), msort(Vs, [a,b,c]))).
test(setof_sorts,     setof(X, member(X,[c,a,b,a]), [a,b,c])).
test(setof_pairs,     setof(K-V, p(K,V), [1-a,1-b,2-c])).
test(agg_count,       aggregate_all(count, member(_,[a,b,c]), 3)).
test(agg_sum,         aggregate_all(sum(X), member(X,[1,2,3]), 6)).
test(agg_max,         aggregate_all(max(X), member(X,[1,5,3]), 5)).
test(agg_bag_set,     (aggregate_all(bag(X), member(X,[b,a,b]), [b,a,b]),
                       aggregate_all(set(X), member(X,[b,a,b]), [a,b]))).

p(1, a).
p(1, b).
p(2, c).

/* ---------------- terms ---------------- */

test(tm_functor,      (functor(f(a,b), N, A), N == f, A =:= 2)).
test(tm_functor_atom, (functor(foo, N, A), N == foo, A =:= 0)).
test(tm_functor_make, (functor(T, point, 2), T = point(_,_))).
test(tm_arg,          (arg(1, f(a,b), X), arg(2, f(a,b), Y), X == a, Y == b)).
test(tm_arg_fail,     \+ arg(3, f(a,b), _)).
test(tm_univ,         (f(a,b) =.. L, L == [f,a,b])).
test(tm_univ_make,    (T =.. [g,1,2], T == g(1,2))).
test(tm_univ_atom,    (foo =.. L, L == [foo])).
test(tm_copy,         (copy_term(f(X,Y,X), C), C = f(A,B,A2), A == A2, A \== B, X == X, Y == Y)).
test(tm_vars,         (term_variables(f(X,g(Y),X), Vs), Vs == [X,Y])).
test(tm_numbervars,   (T = f(_,_), numbervars(T, 0, E), E =:= 2,
                       with_output_to(atom(A), write(T)), A == 'f(A,B)')).
test(tm_setarg,       (T = f(a), setarg(1, T, b), T == f(b))).

/*  The arity limit is one number, MAX_ARITY in src/prolog.h, and the reader,
    =../2 and functor/3 all stop at the same place. current_prolog_flag/2
    reports it, so these tests are written against the flag rather than
    against a literal 256.
*/
test(tm_max_arity_flag,
     (current_prolog_flag(max_arity, N), integer(N), N > 0)).
test(tm_max_arity_functor,
     (current_prolog_flag(max_arity, N),
      functor(T, f, N), functor(T, f, A), A =:= N)).
test(tm_max_arity_functor_over,
     (current_prolog_flag(max_arity, N), N1 is N + 1,
      catch(functor(_, f, N1), error(E, _), true),
      E == representation_error(max_arity))).
test(tm_max_arity_univ,
     (current_prolog_flag(max_arity, N),
      length(L, N), T =.. [f|L], functor(T, f, A), A =:= N)).
test(tm_max_arity_univ_over,
     (current_prolog_flag(max_arity, N), N1 is N + 1,
      length(L, N1),
      catch(_ =.. [f|L], error(E, _), true),
      E == representation_error(max_arity))).
test(tm_max_arity_reader,
     (current_prolog_flag(max_arity, N),
      numlist(1, N, Ns), atomic_list_concat(Ns, ',', Args),
      atomic_list_concat(['f(', Args, ')'], Text),
      atom_to_term(Text, T, _), functor(T, f, A), A =:= N)).

/* ---------------- atoms and text ---------------- */

test(at_length,       atom_length(hello, 5)).
test(at_length_num,   atom_length(123, 3)).
test(at_codes,        (atom_codes(abc, C), C == [97,98,99])).
test(at_codes_back,   (atom_codes(A, [97,98]), A == ab)).
test(at_chars,        (atom_chars(abc, C), C == [a,b,c])).
test(at_chars_back,   (atom_chars(A, [a,b]), A == ab)).
test(at_char_code,    (char_code(a, X), X =:= 97, char_code(C, 98), C == b)).
test(at_number_codes, (number_codes(N, "42"), N =:= 42)).
test(at_number_chars, (number_chars(N, ['4','2']), N =:= 42)).
test(at_number_float, (number_codes(N, "3.25"), N =:= 3.25)).
test(at_atom_number,  (atom_number('42', N), N =:= 42, \+ atom_number(foo, _))).
test(at_concat,       (atom_concat(foo, bar, X), X == foobar)).
test(at_concat_split, (findall(A-B, atom_concat(A,B,ab), [''-ab, a-b, ab-'']))).
test(at_sub_atom,     (sub_atom(abcde, 1, 3, A, S), S == bcd, A =:= 1)).
test(at_sub_find,     (sub_atom(hello_world, B, _, _, world), B =:= 6)).
test(at_sub_all,      (findall(S, sub_atom(abc, _, 1, _, S), [a,b,c]))).
test(at_upcase,       (upcase_atom(hello, X), X == 'HELLO')).
test(at_downcase,     (downcase_atom('HELLO', X), X == hello)).
test(at_list_concat,  (atomic_list_concat([a,b,c], X), X == abc)).
test(at_list_sep,     (atomic_list_concat([a,b,c], '-', X), X == 'a-b-c')).
test(at_list_split,   (atomic_list_concat(L, '-', 'x-y-z'), L == [x,y,z])).
test(at_term_to_atom, (term_to_atom(f(a,'b c'), A), A == 'f(a,\'b c\')')).
test(at_atom_to_term, (atom_to_term('foo(X, Y)', T, Bs), T = foo(A,B),
                       Bs = ['X'=A2, 'Y'=B2], A == A2, B == B2)).
test(at_unicode,      (atom_length('héllo', 5), atom_codes('é', [233]))).

/* ---------------- sorting ---------------- */

test(so_sort,         sort([c,a,b,a], [a,b,c])).
test(so_msort,        msort([c,a,b,a], [a,a,b,c])).
test(so_sort4_dup,    sort(0, @=<, [c,a,b,a], [a,a,b,c])).
test(so_sort4_desc,   sort(0, @>=, [1,3,2], [3,2,1])).
test(so_sort4_key,    sort(1, @<, [f(2,a), f(1,b), f(2,c)], [f(1,b), f(2,a)])).
test(so_keysort,      keysort([b-1, a-2, b-3], [a-2, b-1, b-3])).
test(so_keysort_stable, (keysort([b-1,a-2,b-3,a-4], L), L == [a-2,a-4,b-1,b-3])).
test(so_predsort,     (predsort(cmp_len, [[1,2],[1],[1,2,3]], S),
                       S == [[1],[1,2],[1,2,3]])).

cmp_len(O, A, B) :- length(A, LA), length(B, LB), compare(O, LA, LB).

/* ---------------- lists ---------------- */

test(li_append,       append([1,2],[3],[1,2,3])).
test(li_append_split, (findall(A-B, append(A,B,[1,2]), [[]-[1,2], [1]-[2], [1,2]-[]]))).
test(li_member,       (member(b,[a,b,c]), \+ member(z,[a,b]))).
test(li_memberchk,    (memberchk(b,[a,b,b]), \+ memberchk(z,[a]))).
test(li_length,       (length([a,b,c], 3), length(L, 2), L = [_,_])).
test(li_length_var,   (findall(N, (length(L, N), N >= 2, !), [2]))).
test(li_reverse,      reverse([1,2,3],[3,2,1])).
test(li_nth0,         (nth0(0,[a,b],a), nth0(1,[a,b],b), nth0(I,[a,b],b), I =:= 1)).
test(li_nth1,         (nth1(1,[a,b],a), nth1(2,[a,b],b))).
test(li_last,         last([1,2,3],3)).
test(li_select,       (select(b,[a,b,c],R), R == [a,c])).
test(li_subtract,     subtract([1,2,3],[2],[1,3])).
test(li_intersection, intersection([1,2,3],[2,3,4],[2,3])).
test(li_union,        union([1,2],[2,3],[1,2,3])).
test(li_delete,       delete([1,2,1,3],1,[2,3])).
test(li_include,      (include(integer, [1,a,2], [1,2]))).
test(li_exclude2,     (exclude(integer, [1,a,2], [a]))).
test(li_partition,    (partition(integer, [1,a,2], I, E), I == [1,2], E == [a])).
test(li_maplist2,     maplist(integer, [1,2,3])).
test(li_maplist3,     (maplist(succ, [1,2,3], L), L == [2,3,4])).
test(li_maplist4,     (maplist(plus, [1,2], [10,20], L), L == [11,22])).
test(li_foldl,        (foldl(add3, [1,2,3], 0, S), S =:= 6)).
test(li_sum,          (sum_list([1,2,3], S), S =:= 6)).
test(li_max_min,      (max_list([1,5,3], 5), min_list([1,5,3], 1))).
test(li_max_member,   (max_member(M, [a,c,b]), M == c)).
test(li_numlist,      numlist(1,5,[1,2,3,4,5])).
test(li_permutation,  (findall(P, permutation([1,2],P), [[1,2],[2,1]]))).
test(li_flatten,      (flatten([1,[2,[3,4]],5], F), F == [1,2,3,4,5])).
test(li_list_to_set,  (list_to_set([a,b,a,c,b], S), S == [a,b,c])).
test(li_pairs,        (pairs_keys_values(P, [a,b], [1,2]), P == [a-1,b-2])).
test(li_append_lol,   (append([[1,2],[3]], L), L == [1,2,3])).

add3(X, A, B) :- B is A + X.

/* ---------------- database ---------------- */

test(db_assert,       (assertz(tmp(1)), tmp(1), retract(tmp(1)), \+ tmp(_))).
test(db_asserta,      (assertz(tmp(2)), asserta(tmp(1)),
                       findall(X, tmp(X), [1,2]), retractall(tmp(_)))).
test(db_retract_bt,   (assertz(tmp(a)), assertz(tmp(b)),
                       findall(X, retract(tmp(X)), [a,b]), \+ tmp(_))).
test(db_retractall,   (assertz(tmp(1)), assertz(tmp(2)), retractall(tmp(_)),
                       \+ tmp(_))).
test(db_clause,       (assertz((tmp_rule(X) :- X > 1)),
                       clause(tmp_rule(_), Body), Body = (_ > 1),
                       retractall(tmp_rule(_)))).
test(db_dynamic_fail, (dynamic(undefined_thing/1), \+ undefined_thing(_))).
test(db_assert_rule,  (assertz((dbl(X,Y) :- Y is X*2)), dbl(3,R), R =:= 6)).
test(db_counter,      (retractall(cnt(_)), assertz(cnt(0)),
                       forall(between(1,10,_),
                              (retract(cnt(C)), C1 is C+1, assertz(cnt(C1)))),
                       cnt(10))).
test(db_protect,      catch(assertz(atom(x)), error(permission_error(_,_,_), _), true)).
test(db_clause_bt,    (retractall(tmp(_)),
                       assertz(tmp(1)), assertz(tmp(2)), assertz(tmp(3)),
                       findall(X, clause(tmp(X), true), [1,2,3]),
                       retractall(tmp(_)))).
test(db_retract_one,  (retractall(tmp(_)), assertz(tmp(a)), assertz(tmp(b)),
                       retract(tmp(a)), findall(X, tmp(X), [b]),
                       retractall(tmp(_)))).
test(db_indexed_bt,   (retractall(tmp(_)),
                       forall(between(1,20,N), assertz(tmp(N))),
                       findall(N, retract(tmp(N)), L), length(L, 20),
                       \+ tmp(_))).
test(db_current_pred, (current_predicate(p/2))).

/* ---------------- parsing and writing ---------------- */

:- op(700, xfx, ===).

test(rw_ops,          (X = (1 + 2 * 3), X = +(1, *(2,3)))).
test(rw_ops_left,     (X = (1 - 2 - 3), X = -(-(1,2),3))).
test(rw_ops_right,    (X = (a , b , c), X = ','(a, ','(b,c)))).
test(rw_neg_number,   (X = -1, integer(X), X =:= -1)).
test(rw_neg_term,     (X = -(1), X = -(1), \+ integer(X))).
test(rw_curly,        (X = {a,b}, X = {}((a,b)))).
test(rw_string_codes, (X = "ab", X == [97,98])).
test(rw_char_code,    (X = 0'a, X =:= 97)).
test(rw_escape,       (atom_codes(A, "a\nb"), atom_length(A, 3))).
test(rw_hex,          (X is 0x1f + 0o17 + 0b101, X =:= 31 + 15 + 5)).
test(rw_write,        (with_output_to(atom(A), write(f(-1, 'a b', [1,2]))),
                       A == 'f(-1,a b,[1,2])')).
test(rw_writeq,       (with_output_to(atom(A), writeq('a b')), A == '\'a b\'')).
test(rw_write_op,     (with_output_to(atom(A), write(1+2*3)), A == '1+2*3')).
test(rw_write_paren,  (with_output_to(atom(A), write((1+2)*3)), A == '(1+2)*3')).
test(rw_write_neg,    (with_output_to(atom(A), write(1 - (-1))), A == '1- -1')).
test(rw_write_clause, (with_output_to(atom(A), writeq((a :- b, c))), A == 'a:-b,c')).
test(rw_write_list,   (with_output_to(atom(A), write([a,b|c])), A == '[a,b|c]')).
test(rw_canonical,    (with_output_to(atom(A), write_canonical([1,2])),
                       A == '\'.\'(1,\'.\'(2,[]))')).
test(rw_op_define,    (X = (a === b), X = ===(a,b))).
test(rw_current_op,   (current_op(P, yfx, +), P =:= 500)).
test(rw_read_term,    (atom_to_term('foo(A,B)', T, _), functor(T, foo, 2))).
test(rw_roundtrip,    (T0 = f('A b', [1,-2.5], "x", {y}, (p:-q)),
                       with_output_to(atom(A), writeq(T0)),
                       atom_to_term(A, T1, _),
                       T0 =@= T1)).
test(rw_syntax_err,   catch(atom_to_term('foo(', _, _), error(syntax_error(_), _), true)).

/* ---------------- format ---------------- */

test(fmt_w,           (format(atom(A), "~w", [f(x)]), A == 'f(x)')).
test(fmt_q,           (format(atom(A), "~q", ['a b']), A == '\'a b\'')).
test(fmt_a,           (format(atom(A), "~a", ['a b']), A == 'a b')).
test(fmt_d,           (format(atom(A), "~d", [42]), A == '42')).
test(fmt_d_dec,       (format(atom(A), "~2d", [314]), A == '3.14')).
test(fmt_D,           (format(atom(A), "~D", [1234567]), A == '1,234,567')).
test(fmt_f,           (format(atom(A), "~2f", [3.14159]), A == '3.14')).
test(fmt_e,           (format(atom(A), "~e", [1.0]), atom_length(A, _))).
test(fmt_s,           (format(atom(A), "~s", [[104,105]]), A == hi)).
test(fmt_n,           (format(atom(A), "a~nb", []), atom_length(A, 3))).
test(fmt_c,           (format(atom(A), "~3c", [0'x]), A == xxx)).
test(fmt_r,           (format(atom(A), "~16r", [255]), A == ff)).
test(fmt_tilde,       (format(atom(A), "~~", []), A == '~')).
test(fmt_column,      (format(atom(A), "~w~10|~w", [ab, cd]), A == 'ab        cd')).
test(fmt_fill,        (format(atom(A), "~t~w~10|", [ab]), A == '        ab')).
test(fmt_codes,       (format(codes(C), "hi", []), C == [104,105])).
test(fmt_star,        (format(atom(A), "~*c", [3, 0'z]), A == zzz)).
test(fmt_nonlist_arg, (format(atom(A), "~w", hello), A == hello)).

/* ---------------- DCG ---------------- */

digits([D|T]) --> digit(D), digits(T).
digits([D]) --> digit(D).
digit(D) --> [D], { code_type_digit(D) }.
code_type_digit(D) :- D >= 0'0, D =< 0'9.

greeting --> [hello], subject.
subject --> [world].
subject --> [prolog].

abc --> "abc".

count_ab(N) --> [a], count_ab(N0), { N is N0 + 1 }.
count_ab(0) --> [].

test(dcg_simple,      phrase(greeting, [hello, world])).
test(dcg_alt,         (findall(L, phrase(greeting, L), [[hello,world],[hello,prolog]]))).
test(dcg_rest,        phrase(subject, [world, extra], [extra])).
test(dcg_string,      phrase(abc, "abc")).
test(dcg_digits,      (phrase(digits(Ds), "123"), Ds == [0'1,0'2,0'3])).
test(dcg_count,       (phrase(count_ab(N), [a,a,a]), N =:= 3)).
test(dcg_pushback,    (phrase(digits(_), "42"))).

/* ---------------- streams and I/O ---------------- */

test(io_write_read,   (tmp_file(F),
                       open(F, write, S), writeq(S, foo(bar, "x")), write(S, '.'), nl(S),
                       close(S),
                       open(F, read, S2), read(S2, T), close(S2),
                       T = foo(bar, _))).
test(io_read_eof,     (tmp_file(F), open(F, write, S), close(S),
                       open(F, read, S2), read(S2, T), close(S2), T == end_of_file)).
test(io_with_output,  (with_output_to(atom(A), (write(a), write(b))), A == ab)).
test(io_format_stream,(tmp_file(F), open(F, write, S), format(S, "~w.~n", [42]),
                       close(S), open(F, read, S2), read_term(S2, T, []), close(S2),
                       T =:= 42)).

tmp_file('/tmp/cprolog_test_tmp.pl').

/* ---------------- flags and misc ---------------- */

test(flag_bounded,    current_prolog_flag(bounded, true)).
test(flag_max_int,    (current_prolog_flag(max_integer, M), M > 0)).
test(flag_dq,         (set_prolog_flag(double_quotes, codes),
                       current_prolog_flag(double_quotes, codes))).
test(misc_statistics, (statistics(inferences, I), integer(I))).
test(misc_nb,         (nb_setval(k, f(1)), nb_getval(k, V), V == f(1))).
test(misc_ground,     (ground(f(a,b)), \+ ground(f(a,_)))).
test(misc_tab,        (with_output_to(atom(A), tab(3)), A == '   ')).

/* ---------------- deep recursion / GC stress ---------------- */

build(0, []) :- !.
build(N, [N|T]) :- N1 is N-1, build(N1, T).

sum_to(0, 0) :- !.
sum_to(N, S) :- N1 is N-1, sum_to(N1, S1), S is S1 + N.

loop_det(0) :- !.
loop_det(N) :- X = f(N, [a,b,c]), X = f(_, _), N1 is N-1, loop_det(N1).

test(deep_build,      (build(20000, L), length(L, 20000))).
test(deep_sum,        (sum_to(10000, S), S =:= 50005000)).
test(deep_det_loop,   loop_det(200000)).
test(deep_findall,    (numlist(1, 20000, L), findall(X, member(X, L), L2),
                       length(L2, 20000))).
test(deep_atoms,      (numlist(1, 2000, L), maplist(mk_atom_, L, As), length(As, 2000))).
test(gc_holds_term,   (build(5000, L), loop_det(20000), length(L, 5000),
                       last(L, 1))).
test(gc_in_findall,   (findall(S, (between(1, 50, _), sum_to(200, S)), Ss),
                       length(Ss, 50), Ss = [S1|_], S1 =:= 20100)).
test(gc_with_assert,  (retractall(tmp(_)),
                       forall(between(1, 200, N), (X is N*N, assertz(tmp(X)))),
                       loop_det(20000),
                       aggregate_all(count, tmp(_), 200),
                       retractall(tmp(_)))).
test(gc_exception,    (loop_det(5000),
                       catch((loop_det(5000), throw(ball(deep))), ball(W), true),
                       W == deep)).

mk_atom_(N, A) :- atom_concat(item_, N, A).

/* ---------------- the harness ---------------- */

run_tests :-
    nb_setval(passed, 0),
    nb_setval(failed, 0),
    forall(test(Name, Goal), run_one(Name, Goal)),
    nb_getval(passed, P),
    nb_getval(failed, F),
    Total is P + F,
    format("~n~d tests, ~d passed, ~d failed~n", [Total, P, F]),
    (   F =:= 0
    ->  format("ALL TESTS PASSED~n")
    ;   halt(1)
    ).

run_one(Name, Goal) :-
    (   catch(Goal, E, (format("ERROR ~w: ~q~n", [Name, E]), fail))
    ->  bump(passed)
    ;   format("FAIL  ~w~n", [Name]),
        bump(failed)
    ).

bump(Key) :-
    nb_getval(Key, V),
    V1 is V + 1,
    nb_setval(Key, V1).
