/* db.c -- the clause database. */
#include "prolog.h"

#define PRED_BUCKETS 1024

static Pred *preds[PRED_BUCKETS];

static unsigned pred_hash(int functor, int arity)
{
    return ((unsigned)functor * 31u + (unsigned)arity) % PRED_BUCKETS;
}

void db_init(void)
{
    memset(preds, 0, sizeof(preds));
}

Pred *pred_lookup(int functor, int arity, int create)
{
    unsigned h = pred_hash(functor, arity);
    Pred *p;

    for (p = preds[h]; p; p = p->next)
        if (p->functor == functor && p->arity == arity) return p;
    if (!create) return NULL;
    p = (Pred *)calloc(1, sizeof(Pred));
    p->functor = functor;
    p->arity = arity;
    p->next = preds[h];
    preds[h] = p;
    return p;
}

int pred_enumerate(int i, Pred **out)
{
    int b, n = 0;
    Pred *p;
    for (b = 0; b < PRED_BUCKETS; b++)
        for (p = preds[b]; p; p = p->next)
            if (n++ == i) { *out = p; return 1; }
    return 0;
}

/* ---- first argument indexing ---- */

static void clause_index(Clause *c)
{
    Term *h = c->head, *a;

    c->first_arg_tag = -1;
    c->first_arg_key = 0;
    if (h->tag != TAG_STR || AR(h) == 0) return;
    a = ARG(h, 0);
    while (a->tag == TAG_VAR && a->u.v.ref) a = a->u.v.ref;
    switch (a->tag) {
    case TAG_ATOM: c->first_arg_tag = TAG_ATOM; c->first_arg_key = AT(a); break;
    case TAG_INT:  c->first_arg_tag = TAG_INT;  c->first_arg_key = (int)IV(a); break;
    case TAG_STR:  c->first_arg_tag = TAG_STR;
                   c->first_arg_key = FN(a) * 64 + AR(a); break;
    default: break;               /* variables and floats are not indexed */
    }
}

int clause_may_match(Clause *c, Term *goal)
{
    Term *a;
    int tag, key;

    if (!c->alive) return 0;
    if (c->first_arg_tag < 0) return 1;
    if (goal->tag != TAG_STR || AR(goal) == 0) return 1;
    a = deref(ARG(goal, 0));
    switch (a->tag) {
    case TAG_ATOM: tag = TAG_ATOM; key = AT(a); break;
    case TAG_INT:  tag = TAG_INT;  key = (int)IV(a); break;
    case TAG_STR:  tag = TAG_STR;  key = FN(a) * 64 + AR(a); break;
    default: return 1;
    }
    return tag == c->first_arg_tag && key == c->first_arg_key;
}

/* ---- clauses ---- */

Clause *clause_make(Term *head, Term *body)
{
    Arena *a = arena_new();
    Clause *c = (Clause *)calloc(1, sizeof(Clause));
    Term *pair = mk2(a_neck, head, body);
    Term *compiled;
    int nvars = 0;

    compiled = arena_compile(a, pair, &nvars);
    c->arena = a;
    c->head = ARG(compiled, 0);
    c->body = ARG(compiled, 1);
    c->nvars = nvars;
    c->alive = 1;
    clause_index(c);
    return c;
}

void pred_add_clause(Pred *p, Clause *c, int at_end)
{
    p->defined = 1;
    if (at_end) {
        c->next = NULL;
        if (p->last) p->last->next = c;
        else p->first = c;
        p->last = c;
    } else {
        c->next = p->first;
        p->first = c;
        if (!p->last) p->last = c;
    }
}

void clause_retract(Pred *p, Clause *c)
{
    Clause **link = &p->first, *prev = NULL;

    while (*link && *link != c) { prev = *link; link = &(*link)->next; }
    if (*link != c) return;
    *link = c->next;         /* c->next stays intact so iterators can go on */
    if (p->last == c) p->last = prev;
    c->alive = 0;
    /* The clause is not freed yet: choice points may still point at it.
       It is kept on the garbage list and released when the predicate is. */
    c->gnext = p->garbage;
    p->garbage = c;
}

void pred_abolish(Pred *p)
{
    Clause *c, *nx;
    for (c = p->first; c; c = nx) {
        nx = c->next;
        arena_free(c->arena);
        free(c);
    }
    for (c = p->garbage; c; c = nx) {
        nx = c->gnext;
        arena_free(c->arena);
        free(c);
    }
    p->first = p->last = NULL;
    p->garbage = NULL;
    p->defined = 0;
}
