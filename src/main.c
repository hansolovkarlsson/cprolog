/* main.c -- command line handling and the interactive toplevel. */
#include "prolog.h"
#include <ctype.h>

#define VERSION "1.0"

static void banner(void)
{
    printf("C Prolog %s -- a Prolog interpreter in C\n", VERSION);
    printf("Type help. for help, halt. to quit.\n\n");
}

static void usage(const char *prog)
{
    printf("usage: %s [options] [file ...]\n\n", prog);
    printf("  -g, --goal GOAL   run GOAL after loading the files\n");
    printf("  -t, --top         enter the interactive toplevel even after -g\n");
    printf("  -q, --quiet       do not print the banner\n");
    printf("  -v, --version     print the version and exit\n");
    printf("  -h, --help        print this message\n\n");
    printf("With no -g option the interactive toplevel is entered.\n");
}

/* ------------------------------------------------------------------ */
/* Printing answers                                                   */
/* ------------------------------------------------------------------ */

/* Answers are printed with a depth limit, so that a binding to a huge term
   does not flood the terminal; use write/1 to see it in full. */
#define ANSWER_MAX_DEPTH 100

static void emit_stdout(void *ctx, const char *s, size_t n)
{
    (void)ctx;
    fwrite(s, 1, n, stdout);
}

static void write_answer(Term *t)
{
    Writer w;
    memset(&w, 0, sizeof(w));
    w.emit = emit_stdout;
    w.flags = WR_QUOTED | WR_NUMBERVARS;
    w.maxdepth = ANSWER_MAX_DEPTH;
    write_term(&w, t);
}

static int var_is_free(Term *v) { return deref(v)->tag == TAG_VAR; }

/* Is this variable shared with an earlier binding in the list? */
static int shared_with_earlier(Term *names, Term *upto, Term *var)
{
    Term *l = deref(names);
    while (l->tag == TAG_STR && FN(l) == a_dot && AR(l) == 2) {
        Term *p = deref(ARG(l, 0));
        if (p == upto) break;
        if (p->tag == TAG_STR && AR(p) == 2 && deref(ARG(p, 1)) == deref(var))
            return 1;
        l = deref(ARG(l, 1));
    }
    return 0;
}

static int print_bindings(Term *names)
{
    Term *l = deref(names);
    int printed = 0;

    while (l->tag == TAG_STR && FN(l) == a_dot && AR(l) == 2) {
        Term *p = deref(ARG(l, 0));
        if (p->tag == TAG_STR && AR(p) == 2) {
            Term *name = deref(ARG(p, 0));
            Term *val = deref(ARG(p, 1));
            /* A variable that is still free and not aliased says nothing. */
            if (!(var_is_free(val) && !shared_with_earlier(names, p, val))) {
                if (printed) printf(",\n");
                printf("%s = ", atom_name(AT(name)));
                write_answer(val);
                printed++;
            }
        }
        l = deref(ARG(l, 1));
    }
    return printed;
}

/* Reads the user's reply after a solution: 1 = more, 0 = stop. */
static int ask_more(void)
{
    int c;
    printf(" ");
    fflush(stdout);
    for (;;) {
        c = getchar();
        if (c == EOF) { printf("\n"); return 0; }
        if (c == '\n') return 0;
        if (c == ';' || c == ' ' || c == 'n') {
            while ((c = getchar()) != EOF && c != '\n') ;
            return 1;
        }
        if (c == '.' || c == 'c' || c == 'a') {
            while ((c = getchar()) != EOF && c != '\n') ;
            return 0;
        }
    }
}

static void report_error(void)
{
    Term **vars;
    Term *ball;
    int i;

    if (!m_ball) { fprintf(stderr, "ERROR: unknown error\n"); return; }
    vars = (Term **)heap_alloc((m_ball_nvars + 1) * sizeof(Term *));
    for (i = 0; i < m_ball_nvars; i++) vars[i] = NULL;
    ball = heap_instantiate(m_ball, vars, m_ball_nvars);
    fprintf(stderr, "ERROR: ");
    print_error_term(stderr, ball);
}

static void run_query(Term *goal, Term *names)
{
    size_t base = m_cp_top;
    size_t tm = trail_mark();
    int roots = gc_root_top();
    int rc;

    /* The answer bindings are printed after the run, so the collector must
       keep the variable names reachable. */
    gc_protect(&names);
    m_goals = goal_push(goal, NULL, base);
    rc = machine_run(base);
    for (;;) {
        if (rc == PL_OK) {
            if (print_bindings(names) == 0) printf("true");
            if (m_cp_top > base) {
                /* More solutions may exist, so wait for the reader. Their
                   newline is what ends the line -- printing a full stop after
                   it would leave one sitting on a line of its own. */
                if (ask_more()) { rc = machine_redo(base); continue; }
            } else {
                printf(".\n");
            }
            break;
        }
        if (rc == PL_FAIL) { printf("false.\n"); break; }
        if (rc == PL_ERROR) { report_error(); break; }
        break;                              /* PL_HALT */
    }
    m_cp_top = base;
    trail_undo(tm);
    gc_unprotect(roots);
    fflush(stdout);
}

static void toplevel(void)
{
    Reader r;
    reader_init_file(&r, stdin, "user_input");

    for (;;) {
        HeapMark hm;
        Term *goal, *names;
        int rc;

        if (m_halt) break;
        printf("?- ");
        fflush(stdout);
        hm = heap_mark();
        rc = read_term_from(&r, &goal, &names);
        if (rc == 0) { printf("\n"); break; }
        if (rc < 0) { report_error(); heap_release(hm); continue; }
        goal = deref(goal);
        if (goal->tag == TAG_ATOM && AT(goal) == a_end_of_file) break;
        run_query(goal, names);
        machine_reset();
        heap_release(hm);
    }
    if (m_halt) printf("\n");
}

/* Parses and runs a goal given on the command line. */
static int run_goal_string(const char *s)
{
    Reader r;
    Term *goal, *names;
    char *buf = (char *)malloc(strlen(s) + 4);
    int rc;

    sprintf(buf, "%s .", s);
    reader_init_string(&r, buf, strlen(buf));
    r.name = "goal";
    rc = read_term_from(&r, &goal, &names);
    free(buf);
    if (rc <= 0) { report_error(); return PL_ERROR; }
    rc = solve_once(goal);
    if (rc == PL_ERROR) report_error();
    else if (rc == PL_FAIL) {
        fprintf(stderr, "Warning: goal failed: %s\n", s);
        return PL_FAIL;
    }
    machine_reset();
    return rc;
}

int main(int argc, char **argv)
{
    const char *goals[64];
    const char *files[64];
    int ngoals = 0, nfiles = 0;
    int quiet = 0, force_top = 0, i, rc;

    for (i = 1; i < argc; i++) {
        const char *a = argv[i];
        if (!strcmp(a, "-h") || !strcmp(a, "--help")) { usage(argv[0]); return 0; }
        if (!strcmp(a, "-v") || !strcmp(a, "--version")) {
            printf("C Prolog %s\n", VERSION);
            return 0;
        }
        if (!strcmp(a, "-q") || !strcmp(a, "--quiet")) { quiet = 1; continue; }
        if (!strcmp(a, "-t") || !strcmp(a, "--top")) { force_top = 1; continue; }
        if (!strcmp(a, "-g") || !strcmp(a, "--goal")) {
            if (i + 1 >= argc) { fprintf(stderr, "%s: -g needs an argument\n", argv[0]); return 2; }
            if (ngoals < 64) goals[ngoals++] = argv[++i];
            continue;
        }
        if (a[0] == '-' && a[1]) {
            fprintf(stderr, "%s: unknown option %s\n", argv[0], a);
            return 2;
        }
        if (nfiles < 64) files[nfiles++] = a;
    }

    pl_init_atoms();
    op_init();
    db_init();
    stream_init();
    builtins_init();
    machine_init();

    rc = consult_string(boot_pl);
    if (rc == PL_HALT) return m_halt_code;

    for (i = 0; i < nfiles; i++) {
        if (consult_file(files[i]) == PL_FAIL) {
            fprintf(stderr, "ERROR: cannot open file %s\n", files[i]);
            return 1;
        }
        if (m_halt) return m_halt_code;
    }

    /* Goals registered with initialization/1 run once loading is done. */
    if (!m_halt) {
        run_goal_string("'$run_init_goals'");
        if (m_halt) return m_halt_code;
    }

    for (i = 0; i < ngoals && !m_halt; i++)
        if (run_goal_string(goals[i]) == PL_ERROR) { fflush(stdout); return 1; }
    if (m_halt) { fflush(stdout); return m_halt_code; }

    if (ngoals == 0 || force_top) {
        if (!quiet) banner();
        toplevel();
    }
    fflush(stdout);
    return m_halt_code;
}
