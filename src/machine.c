/* machine.c -- the resolution engine: goals, choice points, cut, exceptions. */
#include "prolog.h"

Goal        *m_goals;
ChoicePoint *m_cps;
size_t       m_cp_top;
static size_t m_cp_cap;
int          m_halt, m_halt_code;
Term        *m_ball;
Arena       *m_ball_arena;
int          m_ball_nvars;
int          m_flag_unknown_error = 1;
static int   m_nesting;            /* depth of re-entrant machine runs */
static size_t gc_min = 16 * 1024 * 1024;
static size_t gc_threshold = 16 * 1024 * 1024;
int          m_flag_double_quotes = DQ_CODES;
long long    m_inferences;

static int a_dollar_cut, a_dollar_softcut, a_dollar_exit_catch, a_throw;
static int a_not_provable, a_call_n, a_curly_call;

/* Constants stored outside the backtrackable heap: they are referenced by
   choice points, which outlive the heap segment they were created in. */
static Term *K_true, *K_fail;

static Term *permanent_atom(int a)
{
    Term *t = (Term *)malloc(sizeof(Term));
    t->tag = TAG_ATOM;
    t->u.atom = a;
    return t;
}

void machine_init(void)
{
    a_dollar_cut = intern("$cut");
    a_dollar_softcut = intern("$softcut");
    a_dollar_exit_catch = intern("$exit_catch");
    a_throw = intern("throw");
    a_not_provable = intern("\\+");
    a_call_n = intern("call");
    a_curly_call = intern("{}");
    {   /* PROLOG_GC_THRESHOLD makes the collector run early; it exists so
           that the test suite can exercise it on every code path. */
        const char *e = getenv("PROLOG_GC_THRESHOLD");
        if (e) {
            long v = atol(e);
            if (v > 0) gc_min = gc_threshold = (size_t)v;
        }
    }
    K_true = permanent_atom(a_true);
    K_fail = permanent_atom(a_fail);
    m_cp_cap = 1024;
    m_cps = (ChoicePoint *)malloc(m_cp_cap * sizeof(ChoicePoint));
    m_cp_top = 0;
    m_goals = NULL;
}

Goal *goal_push(Term *t, Goal *next, size_t cutb)
{
    Goal *g = (Goal *)heap_alloc(sizeof(Goal));
    g->goal = t;
    g->next = next;
    g->cutb = cutb;
    return g;
}

static ChoicePoint *cp_push(int kind, Goal *cont, size_t cutb)
{
    ChoicePoint *cp;
    if (m_cp_top == m_cp_cap) {
        m_cp_cap *= 2;
        m_cps = (ChoicePoint *)realloc(m_cps, m_cp_cap * sizeof(ChoicePoint));
        if (!m_cps) { fprintf(stderr, "prolog: choice point stack exhausted\n"); exit(1); }
    }
    cp = &m_cps[m_cp_top++];
    memset(cp, 0, sizeof(*cp));
    cp->kind = (unsigned char)kind;
    cp->active = 1;
    cp->goals = cont;
    cp->cutb = cutb;
    cp->trail = trail_mark();
    cp->heap = heap_mark();
    return cp;
}

/* ------------------------------------------------------------------ */
/* Exceptions                                                         */
/* ------------------------------------------------------------------ */

int pl_throw_ball(Term *ball)
{
    if (m_ball_arena) arena_free(m_ball_arena);
    m_ball_arena = arena_new();
    m_ball = arena_compile(m_ball_arena, ball, &m_ball_nvars);
    return PL_ERROR;
}

int pl_throw(Term *formal)
{
    /* Wraps a formal error description as error(Formal, Context). */
    return pl_throw_ball(mk2(a_error, formal, mk_var()));
}

int type_error(const char *type, Term *culprit)
{
    return pl_throw(mk2(intern("type_error"), mk_atom_str(type), culprit));
}

int domain_error(const char *dom, Term *culprit)
{
    return pl_throw(mk2(intern("domain_error"), mk_atom_str(dom), culprit));
}

int instantiation_error(void)
{
    return pl_throw(mk_atom_str("instantiation_error"));
}

int existence_error(const char *kind, Term *what)
{
    return pl_throw(mk2(intern("existence_error"), mk_atom_str(kind), what));
}

int evaluation_error(const char *what)
{
    return pl_throw(mk1(intern("evaluation_error"), mk_atom_str(what)));
}

int representation_error(const char *what)
{
    return pl_throw(mk1(intern("representation_error"), mk_atom_str(what)));
}

int permission_error(const char *op, const char *type, Term *what)
{
    return pl_throw(mk3(intern("permission_error"), mk_atom_str(op),
                        mk_atom_str(type), what));
}

static Term *ball_to_heap(void)
{
    Term **vars;
    int i;
    if (!m_ball) return mk_atom_str("unknown_error");
    vars = (Term **)heap_alloc((m_ball_nvars + 1) * sizeof(Term *));
    for (i = 0; i < m_ball_nvars; i++) vars[i] = NULL;
    return heap_instantiate(m_ball, vars, m_ball_nvars);
}

/* ------------------------------------------------------------------ */
/* Clause resolution                                                  */
/* ------------------------------------------------------------------ */

static Clause *next_match(Clause *c, Term *goal)
{
    while (c && !clause_may_match(c, goal)) c = c->next;
    return c;
}

/* Tries clause `c` for `goal`.  Returns 1 if the head unified (and the
   machine state has been advanced), 0 otherwise. */
static int try_clause(Clause *c, Term *goal, Goal *cont, size_t barrier)
{
    Term **vars;
    Term *head = c->head;
    int i;

    vars = (Term **)heap_alloc((c->nvars + 1) * sizeof(Term *));
    for (i = 0; i < c->nvars; i++) vars[i] = NULL;

    if (head->tag == TAG_STR) {
        for (i = 0; i < AR(head); i++) {
            Term *ha = heap_instantiate(ARG(head, i), vars, c->nvars);
            if (!unify(ARG(goal, i), ha)) return 0;
        }
    }
    if (c->body->tag == TAG_ATOM && AT(c->body) == a_true)
        m_goals = cont;
    else
        m_goals = goal_push(heap_instantiate(c->body, vars, c->nvars),
                            cont, barrier);
    return 1;
}

/* ------------------------------------------------------------------ */
/* clause/2 and retract/1 iteration                                   */
/* ------------------------------------------------------------------ */

static int iter_try(Pred *p, Clause *start, Term *head, Term *body,
                    int kind, Goal *cont, int have_cp, size_t cpidx)
{
    Clause *c = start;

    for (;;) {
        Term **vars;
        Term *h, *b;
        Clause *nx;
        size_t tm;
        int i;

        while (c && !clause_may_match(c, head)) c = c->next;
        if (!c) {
            if (have_cp) m_cp_top = cpidx;       /* drop our choice point */
            return 0;
        }
        /* The next candidate has to be picked while the head arguments are
           still unbound, otherwise indexing would rule out every clause that
           this attempt is about to bind. */
        nx = next_match(c->next, head);
        tm = trail_mark();
        vars = (Term **)heap_alloc((c->nvars + 1) * sizeof(Term *));
        for (i = 0; i < c->nvars; i++) vars[i] = NULL;
        h = heap_instantiate(c->head, vars, c->nvars);
        b = heap_instantiate(c->body, vars, c->nvars);
        if (unify(head, h) && unify(body, b)) {
            if (have_cp) {
                if (nx) m_cps[cpidx].clause = nx;
                else m_cp_top = cpidx;           /* last solution */
            }
            if (kind == ITER_RETRACT) clause_retract(p, c);
            m_goals = cont;
            return 1;
        }
        trail_undo(tm);
        c = nx;
    }
}

/* ------------------------------------------------------------------ */
/* Backtracking                                                       */
/* ------------------------------------------------------------------ */

int backtrack(size_t base)
{
    while (m_cp_top > base) {
        ChoicePoint *cp = &m_cps[m_cp_top - 1];
        size_t idx = m_cp_top - 1;

        trail_undo(cp->trail);

        switch (cp->kind) {
        case CP_CLAUSES: {
            Term *call = cp->call;
            Goal *cont = cp->goals;
            Clause *c = next_match(cp->clause, call);
            Clause *nx;

            if (!c) { m_cp_top--; continue; }
            heap_release(cp->heap);
            nx = next_match(c->next, call);
            if (nx) m_cps[idx].clause = nx;
            else m_cp_top--;                    /* last clause: pop */
            if (try_clause(c, call, cont, idx)) return 1;
            continue;                           /* head did not unify */
        }
        case CP_ALT: {
            Term *alt = cp->alt;
            Goal *cont = cp->goals;
            size_t cutb = cp->cutb;
            int active = cp->active;
            m_cp_top--;
            if (!active) continue;              /* disabled by a soft cut */
            heap_release(cp->heap);
            m_goals = goal_push(alt, cont, cutb);
            return 1;
        }
        case CP_ITER: {
            Term *head = cp->iter_a, *body = cp->iter_b;
            Goal *cont = cp->goals;
            Pred *p = cp->pred;
            int kind = cp->iter_kind;
            Clause *c = cp->clause;
            heap_release(cp->heap);
            if (iter_try(p, c, head, body, kind, cont, 1, idx))
                return 1;
            continue;
        }
        case CP_REDO: {
            Goal     *cont = cp->goals;
            Term     *var = cp->iter_a;
            long long cur = cp->redo_a, high = cp->redo_b;
            int       kind = cp->iter_kind;

            heap_release(cp->heap);
            if (kind == REDO_REPEAT) {       /* an endless supply of solutions */
                m_goals = cont;
                return 1;
            }
            if (cur > high) { m_cp_top--; continue; }
            if (cur == high) m_cp_top--;     /* the last one: leave nothing behind */
            else m_cps[idx].redo_a = cur + 1;
            if (!unify(var, mk_int(cur))) continue;
            m_goals = cont;
            return 1;
        }
        case CP_CATCH:
        default:
            heap_release(cp->heap);
            m_cp_top--;
            continue;
        }
    }
    return 0;
}

static int handle_throw(size_t base)
{
    while (m_cp_top > base) {
        ChoicePoint *cp = &m_cps[m_cp_top - 1];

        trail_undo(cp->trail);
        heap_release(cp->heap);
        m_cp_top--;
        if (cp->kind == CP_CATCH && cp->active) {
            size_t tm = trail_mark();
            Term *ball = ball_to_heap();
            if (unify(cp->alt, ball)) {
                m_goals = goal_push(cp->recovery, cp->goals, cp->cutb);
                return 1;
            }
            trail_undo(tm);
        }
    }
    return 0;
}

/* ------------------------------------------------------------------ */
/* Goal execution                                                     */
/* ------------------------------------------------------------------ */

/* Builds call(G, Extra...) style goals. */
static Term *add_args(Term *g, Term **extra, int n)
{
    Term *t;
    int i, base;

    g = deref(g);
    if (n == 0) return g;
    base = g->tag == TAG_STR ? AR(g) : 0;
    t = mk_str(g->tag == TAG_STR ? FN(g) : AT(g), base + n);
    for (i = 0; i < base; i++) ARG(t, i) = ARG(g, i);
    for (i = 0; i < n; i++) ARG(t, base + i) = extra[i];
    return t;
}

static int check_callable(Term *g)
{
    g = deref(g);
    if (g->tag == TAG_VAR) return instantiation_error();
    if (!IS_CALLABLE(g)) return type_error("callable", g);
    return PL_OK;
}

static int execute(Term *t, Goal *frame)
{
    Goal *cont = frame->next;
    size_t cutb = frame->cutb;
    int f, n;
    BiFn bi;
    Pred *p;
    Clause *c, *nx;
    size_t barrier;

    if (t->tag == TAG_VAR) return instantiation_error();
    if (!IS_CALLABLE(t)) return type_error("callable", t);

    if (t->tag == TAG_ATOM) { f = AT(t); n = 0; }
    else { f = FN(t); n = AR(t); }

    /* ---- control constructs ---- */
    if (n == 0) {
        if (f == a_true) { m_goals = cont; return PL_OK; }
        if (f == a_fail || f == a_false) return PL_FAIL;
        if (f == a_cut) { m_cp_top = cutb; m_goals = cont; return PL_OK; }
    } else if (n == 2 && f == a_comma) {
        m_goals = goal_push(ARG(t, 0), goal_push(ARG(t, 1), cont, cutb), cutb);
        return PL_OK;
    } else if (n == 2 && (f == a_semicolon || f == a_bar)) {
        Term *l = deref(ARG(t, 0));
        if (l->tag == TAG_STR && AR(l) == 2 &&
            (FN(l) == a_arrow || FN(l) == a_softarrow)) {
            int soft = FN(l) == a_softarrow;
            ChoicePoint *cp = cp_push(CP_ALT, cont, cutb);
            size_t idx = m_cp_top - 1;
            Goal *g;
            cp->alt = ARG(t, 1);
            g = goal_push(ARG(l, 1), cont, cutb);
            g = goal_push(mk1(soft ? a_dollar_softcut : a_dollar_cut,
                              mk_int((long long)idx)), g, cutb);
            m_goals = goal_push(ARG(l, 0), g, m_cp_top);
            return PL_OK;
        } else {
            ChoicePoint *cp = cp_push(CP_ALT, cont, cutb);
            cp->alt = ARG(t, 1);
            m_goals = goal_push(ARG(t, 0), cont, cutb);
            return PL_OK;
        }
    } else if (n == 2 && (f == a_arrow || f == a_softarrow)) {
        int soft = f == a_softarrow;
        ChoicePoint *cp = cp_push(CP_ALT, cont, cutb);
        size_t idx = m_cp_top - 1;
        Goal *g;
        cp->alt = K_fail;
        g = goal_push(ARG(t, 1), cont, cutb);
        g = goal_push(mk1(soft ? a_dollar_softcut : a_dollar_cut,
                          mk_int((long long)idx)), g, cutb);
        m_goals = goal_push(ARG(t, 0), g, m_cp_top);
        return PL_OK;
    } else if (n == 1 && (f == a_not_provable || f == a_not)) {
        /* \+ G  ==  (G -> fail ; true) */
        ChoicePoint *cp = cp_push(CP_ALT, cont, cutb);
        size_t idx = m_cp_top - 1;
        Goal *g;
        cp->alt = K_true;
        g = goal_push(K_fail, cont, cutb);
        g = goal_push(mk1(a_dollar_cut, mk_int((long long)idx)), g, cutb);
        m_goals = goal_push(ARG(t, 0), g, m_cp_top);
        return PL_OK;
    } else if (n == 1 && f == a_dollar_cut) {
        Term *a = deref(ARG(t, 0));
        m_cp_top = (size_t)IV(a);
        m_goals = cont;
        return PL_OK;
    } else if (n == 1 && f == a_dollar_softcut) {
        Term *a = deref(ARG(t, 0));
        size_t idx = (size_t)IV(a);
        /* Not trailed: once the condition has succeeded the alternative is
           gone for good, including when the condition is re-entered. */
        if (idx < m_cp_top && m_cps[idx].kind == CP_ALT)
            m_cps[idx].active = 0;
        m_goals = cont;
        return PL_OK;
    } else if (n == 1 && f == a_dollar_exit_catch) {
        Term *a = deref(ARG(t, 0));
        size_t idx = (size_t)IV(a);
        if (idx < m_cp_top && m_cps[idx].kind == CP_CATCH) {
            if (idx == m_cp_top - 1) m_cp_top--;        /* nothing left to undo */
            else { trail_flag(&m_cps[idx].active); m_cps[idx].active = 0; }
        }
        m_goals = cont;
        return PL_OK;
    } else if (f == a_call_n && n >= 1) {
        Term *g;
        int rc;
        g = add_args(ARG(t, 0), &ARG(t, 1), n - 1);
        if ((rc = check_callable(g)) != PL_OK) return rc;
        m_goals = goal_push(g, cont, m_cp_top);     /* cut is local to call/N */
        return PL_OK;
    } else if (n == 3 && f == a_catch) {
        ChoicePoint *cp = cp_push(CP_CATCH, cont, cutb);
        size_t idx = m_cp_top - 1;
        Goal *g;
        cp->alt = ARG(t, 1);
        cp->recovery = ARG(t, 2);
        g = goal_push(mk1(a_dollar_exit_catch, mk_int((long long)idx)),
                      cont, cutb);
        m_goals = goal_push(ARG(t, 0), g, m_cp_top);
        return PL_OK;
    } else if (n == 1 && f == a_throw) {
        Term *b = deref(ARG(t, 0));
        if (b->tag == TAG_VAR) return instantiation_error();
        return pl_throw_ball(b);
    } else if (n == 1 && f == a_curly_call) {
        /* {}/1 is only callable in DCG bodies; treat it as its argument. */
        m_goals = goal_push(ARG(t, 0), cont, cutb);
        return PL_OK;
    }

    /* ---- builtins ---- */
    bi = builtin_lookup(f, n);
    if (bi) {
        Goal *saved = m_goals;
        int rc;
        m_goals = cont;
        rc = bi(t->tag == TAG_STR ? t->u.s.args : NULL, cont, cutb);
        if (rc == PL_FAIL) m_goals = saved;
        return rc;
    }

    /* ---- user predicates ---- */
    p = pred_lookup(f, n, 0);
    if (!p || (!p->defined && !p->dynamic)) {
        if (m_flag_unknown_error)
            return existence_error("procedure",
                                   mk2(a_slash, mk_atom(f), mk_int(n)));
        return PL_FAIL;
    }
    c = next_match(p->first, t);
    if (!c) return PL_FAIL;
    barrier = m_cp_top;
    nx = next_match(c->next, t);
    if (nx) {
        ChoicePoint *cp = cp_push(CP_CLAUSES, cont, cutb);
        cp->call = t;
        cp->clause = nx;
        cp->pred = p;
    }
    if (try_clause(c, t, cont, barrier)) return PL_OK;
    return PL_FAIL;
}

/* ------------------------------------------------------------------ */
/* Running                                                            */
/* ------------------------------------------------------------------ */

int machine_run(size_t base)
{
    for (;;) {
        int rc;
        Goal *g;

        if (m_halt) return PL_HALT;
        g = m_goals;
        if (!g) return PL_OK;
        m_inferences++;
        /* Collect when the computation is deterministic: with no choice
           points and no enclosing run, the goal stack and the registered C
           roots are the only things that can still be reached. */
        if ((m_inferences & 0x3FF) == 0 && m_cp_top == 0 && m_nesting == 0 &&
            heap_in_use() > gc_threshold) {
            size_t live;
            heap_gc(&m_goals);
            g = m_goals;
            live = heap_in_use();
            gc_threshold = live * 3 > gc_min ? live * 3 : gc_min;
        }
        rc = execute(deref(g->goal), g);
        if (rc == PL_OK) continue;
        if (rc == PL_FAIL) {
            if (!backtrack(base)) return PL_FAIL;
        } else if (rc == PL_ERROR) {
            if (!handle_throw(base)) return PL_ERROR;
        } else {
            return rc;                  /* PL_HALT */
        }
    }
}

int machine_redo(size_t base)
{
    if (!backtrack(base)) return PL_FAIL;
    return machine_run(base);
}

/* Creates a choice point that a builtin retries in place.  The heap mark it
   takes is the one every retry returns to, so a loop over such a builtin runs
   in constant space. */
void redo_push(int kind, long long a, long long b, Term *var,
               Goal *cont, size_t cutb)
{
    ChoicePoint *cp = cp_push(CP_REDO, cont, cutb);
    cp->iter_kind = kind;
    cp->redo_a = a;
    cp->redo_b = b;
    cp->iter_a = var;
}

/* Starts an iterated clause/2 or retract/1 search.  Used by builtins. */
int clause_iter_start(Pred *p, Term *head, Term *body, int kind,
                      Goal *cont, size_t cutb)
{
    Clause *first = next_match(p->first, head);
    Clause *nx;
    size_t idx;

    if (!first) return PL_FAIL;
    nx = next_match(first->next, head);
    idx = m_cp_top;
    if (nx) {
        ChoicePoint *cp = cp_push(CP_ITER, cont, cutb);
        cp->iter_a = head;
        cp->iter_b = body;
        cp->pred = p;
        cp->clause = first;
        cp->iter_kind = kind;
        /* The retry path re-examines `first` as well, so start there. */
        return iter_try(p, first, head, body, kind, cont, 1, idx)
               ? PL_OK : PL_FAIL;
    }
    (void)cutb;
    return iter_try(p, first, head, body, kind, cont, 0, idx)
           ? PL_OK : PL_FAIL;
}

int solve_sub(Term *goal, int (*on_solution)(void *), void *ctx)
{
    Goal    *saved = m_goals;
    int      saved_nesting = m_nesting;
    size_t   base = m_cp_top;
    size_t   tm = trail_mark();
    HeapMark hm = heap_mark();
    int      rc;

    m_goals = goal_push(goal, NULL, base);
    /* The caller holds C pointers into the heap, so no collection here. */
    m_nesting++;
    rc = machine_run(base);
    while (rc == PL_OK) {
        if (on_solution && !on_solution(ctx)) break;
        rc = machine_redo(base);
    }
    m_nesting = saved_nesting;
    m_cp_top = base;
    trail_undo(tm);
    heap_release(hm);
    m_goals = saved;
    if (rc == PL_ERROR) return PL_ERROR;
    if (rc == PL_HALT) return PL_HALT;
    return PL_OK;
}

/* Runs a goal to its first solution, keeping the bindings it made. */
int solve_once(Term *goal)
{
    Goal  *saved = m_goals;
    size_t base = m_cp_top;
    int    saved_nesting = m_nesting;
    int    rc;

    /* Re-entrant calls (a builtin running a goal) keep C pointers into the
       heap alive; only an outermost call may collect. */
    if (saved) m_nesting++;
    m_goals = goal_push(goal, NULL, base);
    rc = machine_run(base);
    m_nesting = saved_nesting;
    m_cp_top = base;
    m_goals = saved;
    return rc;
}

void machine_reset(void)
{
    m_cp_top = 0;
    m_goals = NULL;
}
