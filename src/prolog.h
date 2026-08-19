/* prolog.h -- shared declarations for the C Prolog interpreter. */
#ifndef PROLOG_H
#define PROLOG_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stddef.h>
#include <limits.h>

/* ------------------------------------------------------------------ */
/* Terms                                                              */
/* ------------------------------------------------------------------ */

enum { TAG_VAR = 0, TAG_ATOM, TAG_INT, TAG_FLT, TAG_STR, TAG_FWD };

typedef struct Term Term;
struct Term {
    unsigned char tag;
    union {
        struct { Term *ref; unsigned long serial; } v;
        int atom;
        long long i;
        double f;
        struct { int functor; int arity; Term **args; } s;
    } u;
};

#define ARG(t, i)  ((t)->u.s.args[i])
#define FN(t)      ((t)->u.s.functor)
#define AR(t)      ((t)->u.s.arity)
#define AT(t)      ((t)->u.atom)
#define IV(t)      ((t)->u.i)
#define FV(t)      ((t)->u.f)

/* A term is "callable" if it is an atom or a compound term. */
#define IS_CALLABLE(t) ((t)->tag == TAG_ATOM || (t)->tag == TAG_STR)
#define IS_NUM(t)      ((t)->tag == TAG_INT || (t)->tag == TAG_FLT)

Term *deref(Term *t);

/* ------------------------------------------------------------------ */
/* Atom table                                                         */
/* ------------------------------------------------------------------ */

int         intern(const char *s);
int         intern_n(const char *s, size_t n);
const char *atom_name(int a);
size_t      atom_len(int a);

/* Frequently used atoms, initialised by pl_init_atoms(). */
extern int a_nil, a_dot, a_true, a_fail, a_false, a_comma, a_semicolon;
extern int a_arrow, a_softarrow, a_cut, a_curly, a_minus, a_plus, a_error;
extern int a_call, a_catch, a_end_of_file, a_eq, a_clause, a_dcg, a_var_prefix;
extern int a_empty, a_star, a_slash, a_colon, a_bar, a_neck, a_not, a_dollar_var;

void pl_init_atoms(void);

/* ------------------------------------------------------------------ */
/* Backtrackable heap (chunked arena with mark/release)               */
/* ------------------------------------------------------------------ */

typedef struct HeapChunk HeapChunk;
struct HeapChunk { HeapChunk *next; size_t size, used; char *data; };

typedef struct { HeapChunk *chunk; size_t used; unsigned epoch; } HeapMark;

char    *pl_strdup(const char *s);
void    *heap_alloc(size_t n);
HeapMark heap_mark(void);
void     heap_release(HeapMark m);
size_t   heap_in_use(void);

/* Garbage collection.  The collector copies everything reachable from the
   goal stack (plus the protected C roots) into a fresh heap.  It is only
   safe with an empty choice point stack, which the machine checks. */
struct Goal;
void   heap_gc(struct Goal **goals_root);
void   gc_protect(Term **slot);
void   gc_unprotect(int n);
int    gc_root_top(void);
extern long long m_gc_count;

/* Non-backtrackable arenas, used for clauses, exception balls and
   findall/3 style solution buffers. */
typedef struct Arena Arena;
Arena *arena_new(void);
void  *arena_alloc(Arena *a, size_t n);
void   arena_free(Arena *a);

/* ------------------------------------------------------------------ */
/* Term construction                                                  */
/* ------------------------------------------------------------------ */

Term *mk_var(void);
Term *mk_atom(int a);
Term *mk_int(long long i);
Term *mk_float(double f);
Term *mk_str(int functor, int arity);       /* args left uninitialised */
Term *mk1(int f, Term *a);
Term *mk2(int f, Term *a, Term *b);
Term *mk3(int f, Term *a, Term *b, Term *c);
Term *mk4(int f, Term *a, Term *b, Term *c, Term *d);
Term *mk_cons(Term *head, Term *tail);
Term *mk_atom_str(const char *s);
Term  *mk_codes(const char *s, size_t n);    /* code list */
long   utf8_decode(const char *s, size_t n, size_t *i);
size_t utf8_encode(long code, char *buf);
Term *mk_chars(const char *s, size_t n);    /* one-char-atom list */

/* ------------------------------------------------------------------ */
/* Bindings, trail and unification                                    */
/* ------------------------------------------------------------------ */

void   bind(Term *var, Term *val);
void   trail_flag(int *slot);               /* record an int for undo */
size_t trail_mark(void);
void   trail_undo(size_t mark);

int  unify(Term *a, Term *b);
int  compare_terms(Term *a, Term *b);       /* standard order: -1/0/1 */
int  term_variables(Term *t, Term **buf, int max, int n);

/* Copying.  A "compiled" term stores its variables as TAG_VAR cells whose
   serial number is an index in 0..nvars-1; instantiate rebuilds it with
   fresh heap variables. */
Term *heap_copy(Term *t);
Term *arena_compile(Arena *a, Term *t, int *nvars);
Term *heap_instantiate(Term *t, Term **vars, int nvars);

/* List helpers. */
int   list_length(Term *t);                 /* -1 if not a proper list */
Term *list_from_array(Term **items, int n);

/* ------------------------------------------------------------------ */
/* Operator table                                                     */
/* ------------------------------------------------------------------ */

enum { OP_XFX = 1, OP_XFY, OP_YFX, OP_FY, OP_FX, OP_XF, OP_YF };

void op_define(int prec, int type, int atom);
int  op_prefix(int atom, int *prec, int *argp);
int  op_infix(int atom, int *prec, int *lp, int *rp);
int  op_postfix(int atom, int *prec, int *lp);
int  op_is_op(int atom);
void op_init(void);
int  op_enumerate(int i, int *prec, int *type, int *atom); /* for current_op/3 */
const char *op_type_name(int type);

/* ------------------------------------------------------------------ */
/* Reader                                                             */
/* ------------------------------------------------------------------ */

typedef struct {
    const char *str;      /* string source, or NULL */
    size_t      pos, len;
    FILE       *file;     /* file source, or NULL */
    int         pushback[8];
    int         npush;
    int         line;
    const char *name;     /* for error messages */
} Reader;

void  reader_init_string(Reader *r, const char *s, size_t len);
void  reader_init_file(Reader *r, FILE *f, const char *name);

/* Reads one clause terminated by '.'.  Returns:
     1 on success (*out set),
     0 at end of file,
    -1 on a syntax error (exception raised). */
int read_term_from(Reader *r, Term **out, Term **varnames);

/* ------------------------------------------------------------------ */
/* Writer                                                             */
/* ------------------------------------------------------------------ */

enum { WR_QUOTED = 1, WR_IGNORE_OPS = 2, WR_NUMBERVARS = 4 };

typedef struct {
    void (*emit)(void *ctx, const char *s, size_t n);
    void *ctx;
    int   flags;
    int   maxdepth;
    int   lastc;          /* internal: last character emitted */
} Writer;

void write_term(Writer *w, Term *t);
void write_to_stream(FILE *f, Term *t, int flags);
char *term_to_string(Term *t, int flags, size_t *len_out); /* malloc'd */
int  atom_needs_quotes(const char *s, size_t n);
void format_float(char *buf, size_t bufsz, double d);

/* ------------------------------------------------------------------ */
/* Database                                                           */
/* ------------------------------------------------------------------ */

typedef struct Clause Clause;
struct Clause {
    Clause *next;
    Clause *gnext;           /* link in the predicate's garbage list */
    Arena  *arena;
    Term   *head, *body;     /* compiled form */
    int     nvars;
    int     alive;
    int     first_arg_tag;   /* -1 = variable/any */
    int     first_arg_key;
};

typedef struct Pred Pred;
struct Pred {
    Pred   *next;
    int     functor, arity;
    Clause *first, *last;
    int     dynamic;
    int     defined;
    int     discontiguous;
    Clause *garbage;         /* retracted clauses, freed on abolish */
};

Pred   *pred_lookup(int functor, int arity, int create);
Clause *clause_make(Term *head, Term *body);
void    pred_add_clause(Pred *p, Clause *c, int at_end);
void    clause_retract(Pred *p, Clause *c);
void    pred_abolish(Pred *p);
int     pred_enumerate(int i, Pred **out);
int     clause_may_match(Clause *c, Term *goal);
void    db_init(void);

/* ------------------------------------------------------------------ */
/* Machine                                                            */
/* ------------------------------------------------------------------ */

typedef struct Goal Goal;
struct Goal { Term *goal; Goal *next; size_t cutb; };

Goal *goal_push(Term *t, Goal *next, size_t cutb);

enum { CP_CLAUSES = 1, CP_ALT, CP_CATCH, CP_ITER, CP_REDO };

typedef struct {
    unsigned char kind;
    int      active;
    Goal    *goals;
    size_t   trail;
    HeapMark heap;
    size_t   cutb;
    Term    *call;         /* CP_CLAUSES: the calling goal            */
    Clause  *clause;       /* CP_CLAUSES/CP_ITER: next clause to try  */
    Pred    *pred;
    Term    *alt;          /* CP_ALT: alternative goal, CP_CATCH: catcher */
    Term    *recovery;     /* CP_CATCH                                */
    Term    *iter_a, *iter_b;
    int      iter_kind;
    long long redo_a, redo_b;   /* CP_REDO: the state of a retried builtin */
} ChoicePoint;

extern Goal        *m_goals;
extern ChoicePoint *m_cps;
extern size_t       m_cp_top;
extern int          m_halt, m_halt_code;
extern Term        *m_ball;        /* compiled exception term */
extern Arena       *m_ball_arena;
extern int          m_ball_nvars;
extern int          m_flag_unknown_error;
extern int          m_flag_double_quotes;   /* 0=codes 1=chars 2=atom */
extern long long    m_inferences;

enum { DQ_CODES = 0, DQ_CHARS, DQ_ATOM };

/* Result codes for builtins and for the solver. */
enum { PL_FAIL = 0, PL_OK = 1, PL_ERROR = -1, PL_HALT = -2 };

int  pl_throw(Term *t);
int  pl_throw_ball(Term *ball);                 /* already a plain term */
int  type_error(const char *type, Term *culprit);
int  domain_error(const char *dom, Term *culprit);
int  instantiation_error(void);
int  existence_error(const char *kind, Term *what);
int  evaluation_error(const char *what);
int  representation_error(const char *what);
int  permission_error(const char *op, const char *type, Term *what);

void machine_init(void);
int  machine_run(size_t base);      /* 1 = solution, 0 = exhausted, -1 = error */
int  machine_redo(size_t base);
int  solve_once(Term *goal);        /* run a goal to its first solution */
int  solve_sub(Term *goal, int (*on_solution)(void *), void *ctx);
void machine_reset(void);
int  backtrack(size_t base);

/* Consulting. */
int  consult_reader(Reader *r);
int  consult_file(const char *path);
int  consult_string(const char *s);
int  run_directive(Term *goal);

/* Builtins. */
typedef int (*BiFn)(Term **args, Goal *cont, size_t cutb);
void builtins_init(void);
BiFn builtin_lookup(int functor, int arity);
int  builtin_exists(int functor, int arity);

/* Arithmetic. */
int  arith_eval(Term *expr, Term **result);
int  arith_compare(Term *a, Term *b, int *cmp);

/* Text helpers shared by builtins. */
int   text_of(Term *t, char **buf, size_t *len);  /* atom/number/string -> text */
Term *parse_number_str(const char *s, size_t n);  /* NULL if not a number */

/* Clause iteration shared by clause/2 and retract/1. */
enum { ITER_CLAUSE = 1, ITER_RETRACT };

/* Builtins that produce a sequence of solutions from one choice point that is
   retried in place, so that a loop over them runs in constant space. */
enum { REDO_BETWEEN = 1, REDO_REPEAT };
void redo_push(int kind, long long a, long long b, Term *var,
               Goal *cont, size_t cutb);
int clause_iter_start(Pred *p, Term *head, Term *body, int kind,
                      Goal *cont, size_t cutb);

/* Streams. */
typedef struct PStream PStream;
PStream    *stream_of(Term *t);
FILE       *stream_file(PStream *s);
PStream    *stream_current_output(void);
PStream    *stream_current_input(void);
void        stream_set_output(PStream *s);
void        stream_set_input(PStream *s);
void        stream_init(void);
void        stream_write(PStream *s, const char *buf, size_t n);
int         stream_index(PStream *s);
PStream    *stream_by_index(int i);
Term       *stream_term(PStream *s);
PStream    *stream_open(const char *path, const char *mode, int is_input);
PStream    *stream_open_sink(void);
const char *stream_sink_text(PStream *s, size_t *len);
int         stream_close(PStream *s);
int         stream_getc(PStream *s);
int         stream_is_input(PStream *s);
Reader     *stream_reader(PStream *s);

/* Error reporting used by the toplevel and by consult. */
void print_error_term(FILE *f, Term *ball);

/* The bootstrap library (generated from lib/boot.pl). */
extern const char boot_pl[];

#endif /* PROLOG_H */
