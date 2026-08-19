/* consult.c -- loading programs and reporting uncaught errors. */
#include "prolog.h"

static int a_dcg_translate;

static void init_local(void)
{
    if (!a_dcg_translate) a_dcg_translate = intern("$dcg_translate");
}

/* ------------------------------------------------------------------ */
/* Error messages                                                     */
/* ------------------------------------------------------------------ */

static void wr(FILE *f, Term *t)
{
    write_to_stream(f, t, WR_QUOTED | WR_NUMBERVARS);
}

void print_error_term(FILE *f, Term *ball)
{
    Term *formal;

    ball = deref(ball);
    if (!(ball->tag == TAG_STR && FN(ball) == a_error && AR(ball) == 2)) {
        fprintf(f, "Unhandled exception: ");
        wr(f, ball);
        fprintf(f, "\n");
        return;
    }
    formal = deref(ARG(ball, 0));
    if (formal->tag == TAG_ATOM &&
        !strcmp(atom_name(AT(formal)), "instantiation_error")) {
        fprintf(f, "Arguments are not sufficiently instantiated\n");
        return;
    }
    if (formal->tag == TAG_STR) {
        const char *k = atom_name(FN(formal));
        if (!strcmp(k, "type_error") && AR(formal) == 2) {
            fprintf(f, "Type error: `");
            wr(f, ARG(formal, 0));
            fprintf(f, "' expected, found `");
            wr(f, ARG(formal, 1));
            fprintf(f, "'\n");
            return;
        }
        if (!strcmp(k, "domain_error") && AR(formal) == 2) {
            fprintf(f, "Domain error: `");
            wr(f, ARG(formal, 0));
            fprintf(f, "' expected, found `");
            wr(f, ARG(formal, 1));
            fprintf(f, "'\n");
            return;
        }
        if (!strcmp(k, "existence_error") && AR(formal) == 2) {
            fprintf(f, "Unknown ");
            wr(f, ARG(formal, 0));
            fprintf(f, ": ");
            wr(f, ARG(formal, 1));
            fprintf(f, "\n");
            return;
        }
        if (!strcmp(k, "evaluation_error") && AR(formal) == 1) {
            fprintf(f, "Arithmetic: evaluation error: `");
            wr(f, ARG(formal, 0));
            fprintf(f, "'\n");
            return;
        }
        if (!strcmp(k, "permission_error") && AR(formal) == 3) {
            fprintf(f, "No permission to ");
            wr(f, ARG(formal, 0));
            fprintf(f, " ");
            wr(f, ARG(formal, 1));
            fprintf(f, " `");
            wr(f, ARG(formal, 2));
            fprintf(f, "'\n");
            return;
        }
        if (!strcmp(k, "representation_error") && AR(formal) == 1) {
            fprintf(f, "Cannot represent due to `");
            wr(f, ARG(formal, 0));
            fprintf(f, "'\n");
            return;
        }
        if (!strcmp(k, "syntax_error") && AR(formal) == 1) {
            Term *m = deref(ARG(formal, 0));
            if (m->tag == TAG_ATOM) fprintf(f, "Syntax error: %s\n", atom_name(AT(m)));
            else { fprintf(f, "Syntax error: "); wr(f, m); fprintf(f, "\n"); }
            return;
        }
    }
    fprintf(f, "Unhandled exception: ");
    wr(f, ball);
    fprintf(f, "\n");
}

static void print_current_error(void)
{
    Term **vars;
    Term *ball;
    int i;

    if (!m_ball) { fprintf(stderr, "Unknown error\n"); return; }
    vars = (Term **)heap_alloc((m_ball_nvars + 1) * sizeof(Term *));
    for (i = 0; i < m_ball_nvars; i++) vars[i] = NULL;
    ball = heap_instantiate(m_ball, vars, m_ball_nvars);
    fprintf(stderr, "ERROR: ");
    print_error_term(stderr, ball);
}

/* ------------------------------------------------------------------ */
/* Loading clauses                                                    */
/* ------------------------------------------------------------------ */

int run_directive(Term *goal)
{
    int rc = solve_once(goal);
    if (rc == PL_ERROR) {
        print_current_error();
        return PL_OK;
    }
    if (rc == PL_FAIL) {
        fprintf(stderr, "Warning: Goal (directive) failed: ");
        write_to_stream(stderr, goal, WR_QUOTED);
        fprintf(stderr, "\n");
        return PL_OK;
    }
    return rc;
}

static int add_clause(Term *t)
{
    Term *head, *body;
    Pred *p;
    int f, n;

    t = deref(t);
    if (t->tag == TAG_STR && FN(t) == a_neck && AR(t) == 2) {
        head = deref(ARG(t, 0));
        body = deref(ARG(t, 1));
    } else {
        head = t;
        body = mk_atom(a_true);
    }
    if (head->tag == TAG_VAR) { instantiation_error(); return PL_ERROR; }
    if (!IS_CALLABLE(head)) { type_error("callable", head); return PL_ERROR; }
    if (head->tag == TAG_ATOM) { f = AT(head); n = 0; }
    else { f = FN(head); n = AR(head); }
    if (builtin_exists(f, n)) {
        permission_error("modify", "static_procedure",
                         mk2(a_slash, mk_atom(f), mk_int(n)));
        return PL_ERROR;
    }
    p = pred_lookup(f, n, 1);
    pred_add_clause(p, clause_make(head, body), 1);
    return PL_OK;
}

int consult_reader(Reader *r)
{
    init_local();
    for (;;) {
        HeapMark hm = heap_mark();
        size_t tm = trail_mark();
        Term *t, *names;
        int rc = read_term_from(r, &t, &names);

        if (rc == 0) { heap_release(hm); break; }         /* end of file */
        if (rc < 0) {                                     /* syntax error */
            print_current_error();
            trail_undo(tm);
            heap_release(hm);
            continue;
        }
        t = deref(t);
        if (t->tag == TAG_STR && AR(t) == 1 &&
            (FN(t) == a_neck || FN(t) == intern("?-"))) {
            rc = run_directive(deref(ARG(t, 0)));
            if (rc == PL_HALT) { trail_undo(tm); heap_release(hm); return PL_HALT; }
        } else if (t->tag == TAG_STR && FN(t) == a_dcg && AR(t) == 2) {
            Term *out = mk_var();
            Term *goal = mk2(a_dcg_translate, t, out);
            int roots = gc_root_top();
            gc_protect(&out);
            rc = solve_once(goal);
            gc_unprotect(roots);
            if (rc == PL_ERROR) print_current_error();
            else if (rc == PL_FAIL)
                fprintf(stderr, "Warning: cannot translate grammar rule\n");
            else if (add_clause(out) != PL_OK) print_current_error();
        } else {
            if (add_clause(t) != PL_OK) print_current_error();
        }
        trail_undo(tm);
        heap_release(hm);
        if (m_halt) return PL_HALT;
    }
    return PL_OK;
}

int consult_file(const char *path)
{
    FILE *f = fopen(path, "r");
    Reader r;
    int rc;
    char alt[1024];

    if (!f) {
        /* Try adding the conventional .pl extension. */
        snprintf(alt, sizeof(alt), "%s.pl", path);
        f = fopen(alt, "r");
        if (!f) return PL_FAIL;
        path = alt;
    }
    reader_init_file(&r, f, path);
    rc = consult_reader(&r);
    fclose(f);
    return rc;
}

int consult_string(const char *s)
{
    Reader r;
    reader_init_string(&r, s, strlen(s));
    r.name = "boot";
    return consult_reader(&r);
}
