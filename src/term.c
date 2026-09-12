/* term.c -- memory management, atom table, terms, unification. */
#include "prolog.h"

/* ------------------------------------------------------------------ */
/* Backtrackable heap                                                 */
/* ------------------------------------------------------------------ */

#define HEAP_CHUNK_MIN (256 * 1024)

static HeapChunk *heap_head, *heap_cur;
static size_t heap_total;
static unsigned heap_epoch = 1;
long long m_gc_count;

static HeapChunk *chunk_new(size_t size)
{
    HeapChunk *c = (HeapChunk *)malloc(sizeof(HeapChunk));
    if (!c) { fprintf(stderr, "prolog: out of memory\n"); exit(1); }
    if (size < HEAP_CHUNK_MIN) size = HEAP_CHUNK_MIN;
    c->data = (char *)malloc(size);
    if (!c->data) { fprintf(stderr, "prolog: out of memory\n"); exit(1); }
    c->size = size;
    c->used = 0;
    c->next = NULL;
    heap_total += size;
    return c;
}

static void heap_init(void)
{
    heap_head = heap_cur = chunk_new(HEAP_CHUNK_MIN);
}

/* strdup is POSIX, not C99, and is hidden by glibc under -std=c99: calling it
   there truncates the returned pointer to an int. */
char *pl_strdup(const char *s)
{
    size_t n = strlen(s) + 1;
    char *p = (char *)malloc(n);
    if (!p) { fprintf(stderr, "prolog: out of memory\n"); exit(1); }
    memcpy(p, s, n);
    return p;
}

void *heap_alloc(size_t n)
{
    HeapChunk *c;
    void *p;

    n = (n + 7) & ~(size_t)7;               /* 8 is enough for every member of Term */
    if (!heap_cur) heap_init();
    if (heap_cur->used + n <= heap_cur->size) {
        p = heap_cur->data + heap_cur->used;
        heap_cur->used += n;
        return p;
    }
    /* Re-use a following chunk if one is large enough, else splice a new
       chunk in after the current one (keeping the rest of the list). */
    if (heap_cur->next && heap_cur->next->size >= n) {
        heap_cur = heap_cur->next;
        heap_cur->used = n;
        return heap_cur->data;
    }
    c = chunk_new(n);
    c->next = heap_cur->next;
    heap_cur->next = c;
    heap_cur = c;
    heap_cur->used = n;
    return heap_cur->data;
}

HeapMark heap_mark(void)
{
    HeapMark m;
    if (!heap_cur) heap_init();
    m.chunk = heap_cur;
    m.used = heap_cur->used;
    m.epoch = heap_epoch;
    return m;
}

void heap_release(HeapMark m)
{
    HeapChunk *c;
    if (!m.chunk) return;
    /* A mark taken before a garbage collection no longer describes a
       position in the current heap; the collector has already reclaimed it. */
    if (m.epoch != heap_epoch) return;
    /* Chunks after the mark stay allocated but become free space again. */
    for (c = m.chunk->next; c; c = c->next) c->used = 0;
    heap_cur = m.chunk;
    heap_cur->used = m.used;
}

size_t heap_in_use(void)
{
    HeapChunk *c;
    size_t n = 0;
    for (c = heap_head; c; c = c->next) {
        n += c->used;
        if (c == heap_cur) break;
    }
    return n;
}

/* ------------------------------------------------------------------ */
/* Permanent arenas                                                   */
/* ------------------------------------------------------------------ */

typedef struct ABlock ABlock;
struct ABlock { ABlock *next; size_t size, used; char data[1]; };

struct Arena { ABlock *block; };

#define ARENA_BLOCK 4096

Arena *arena_new(void)
{
    Arena *a = (Arena *)malloc(sizeof(Arena));
    if (!a) { fprintf(stderr, "prolog: out of memory\n"); exit(1); }
    a->block = NULL;
    return a;
}

void *arena_alloc(Arena *a, size_t n)
{
    ABlock *b;
    void *p;

    n = (n + 7) & ~(size_t)7;
    if (a->block && a->block->used + n <= a->block->size) {
        p = a->block->data + a->block->used;
        a->block->used += n;
        return p;
    }
    {
        size_t size = n > ARENA_BLOCK ? n : ARENA_BLOCK;
        b = (ABlock *)malloc(sizeof(ABlock) + size);
        if (!b) { fprintf(stderr, "prolog: out of memory\n"); exit(1); }
        b->size = size;
        b->used = n;
        b->next = a->block;
        a->block = b;
        return b->data;
    }
}

void arena_free(Arena *a)
{
    ABlock *b, *nx;
    if (!a) return;
    for (b = a->block; b; b = nx) { nx = b->next; free(b); }
    free(a);
}

/* ------------------------------------------------------------------ */
/* Atom table                                                         */
/* ------------------------------------------------------------------ */

typedef struct { char *name; size_t len; } AtomEntry;

static AtomEntry *atoms;
static int natoms, atoms_cap;
static int *atom_hash;            /* open addressing, holds index+1 */
static int atom_hash_cap;

static unsigned long hash_bytes(const char *s, size_t n)
{
    unsigned long h = 5381;
    size_t i;
    for (i = 0; i < n; i++) h = ((h << 5) + h) ^ (unsigned char)s[i];
    return h;
}

static void atom_rehash(int newcap)
{
    int i;
    free(atom_hash);
    atom_hash = (int *)calloc(newcap, sizeof(int));
    if (!atom_hash) { fprintf(stderr, "prolog: out of memory\n"); exit(1); }
    atom_hash_cap = newcap;
    for (i = 0; i < natoms; i++) {
        unsigned long h = hash_bytes(atoms[i].name, atoms[i].len) % newcap;
        while (atom_hash[h]) h = (h + 1) % newcap;
        atom_hash[h] = i + 1;
    }
}

int intern_n(const char *s, size_t n)
{
    unsigned long h;
    int idx;

    if (!atom_hash) atom_rehash(1024);
    h = hash_bytes(s, n) % atom_hash_cap;
    while ((idx = atom_hash[h])) {
        AtomEntry *e = &atoms[idx - 1];
        if (e->len == n && memcmp(e->name, s, n) == 0) return idx - 1;
        h = (h + 1) % atom_hash_cap;
    }
    if (natoms == atoms_cap) {
        atoms_cap = atoms_cap ? atoms_cap * 2 : 512;
        atoms = (AtomEntry *)realloc(atoms, atoms_cap * sizeof(AtomEntry));
        if (!atoms) { fprintf(stderr, "prolog: out of memory\n"); exit(1); }
    }
    atoms[natoms].name = (char *)malloc(n + 1);
    memcpy(atoms[natoms].name, s, n);
    atoms[natoms].name[n] = 0;
    atoms[natoms].len = n;
    natoms++;
    atom_hash[h] = natoms;
    if (natoms * 2 > atom_hash_cap) atom_rehash(atom_hash_cap * 2);
    return natoms - 1;
}

int intern(const char *s) { return intern_n(s, strlen(s)); }

const char *atom_name(int a) { return atoms[a].name; }
size_t atom_len(int a) { return atoms[a].len; }

int a_nil, a_dot, a_true, a_fail, a_false, a_comma, a_semicolon;
int a_arrow, a_softarrow, a_cut, a_curly, a_minus, a_plus, a_error;
int a_call, a_catch, a_end_of_file, a_eq, a_clause, a_dcg, a_var_prefix;
int a_empty, a_star, a_slash, a_colon, a_bar, a_neck, a_not, a_dollar_var;

void pl_init_atoms(void)
{
    a_nil = intern("[]");
    a_dot = intern(".");
    a_true = intern("true");
    a_fail = intern("fail");
    a_false = intern("false");
    a_comma = intern(",");
    a_semicolon = intern(";");
    a_arrow = intern("->");
    a_softarrow = intern("*->");
    a_cut = intern("!");
    a_curly = intern("{}");
    a_minus = intern("-");
    a_plus = intern("+");
    a_error = intern("error");
    a_call = intern("call");
    a_catch = intern("catch");
    a_end_of_file = intern("end_of_file");
    a_eq = intern("=");
    a_clause = intern(":-");
    a_dcg = intern("-->");
    a_empty = intern("");
    a_star = intern("*");
    a_slash = intern("/");
    a_colon = intern(":");
    a_bar = intern("|");
    a_neck = intern(":-");
    a_not = intern("\\+");
    a_dollar_var = intern("$VAR");
    a_var_prefix = intern("_G");
}

/* ------------------------------------------------------------------ */
/* Term construction                                                  */
/* ------------------------------------------------------------------ */

static unsigned long var_serial;

Term *mk_var(void)
{
    Term *t = (Term *)heap_alloc(sizeof(Term));
    t->tag = TAG_VAR;
    t->u.v.ref = NULL;
    t->u.v.serial = ++var_serial;
    return t;
}

Term *mk_atom(int a)
{
    Term *t = (Term *)heap_alloc(sizeof(Term));
    t->tag = TAG_ATOM;
    t->u.atom = a;
    return t;
}

Term *mk_atom_str(const char *s) { return mk_atom(intern(s)); }

Term *mk_int(long long i)
{
    Term *t = (Term *)heap_alloc(sizeof(Term));
    t->tag = TAG_INT;
    t->u.i = i;
    return t;
}

Term *mk_float(double f)
{
    Term *t = (Term *)heap_alloc(sizeof(Term));
    t->tag = TAG_FLT;
    t->u.f = f;
    return t;
}

Term *mk_str(int functor, int arity)
{
    Term *t = (Term *)heap_alloc(sizeof(Term) + arity * sizeof(Term *));
    t->tag = TAG_STR;
    t->u.s.functor = functor;
    t->u.s.arity = arity;
    t->u.s.args = (Term **)((char *)t + sizeof(Term));
    return t;
}

Term *mk1(int f, Term *a)
{
    Term *t = mk_str(f, 1);
    ARG(t, 0) = a;
    return t;
}

Term *mk2(int f, Term *a, Term *b)
{
    Term *t = mk_str(f, 2);
    ARG(t, 0) = a; ARG(t, 1) = b;
    return t;
}

Term *mk3(int f, Term *a, Term *b, Term *c)
{
    Term *t = mk_str(f, 3);
    ARG(t, 0) = a; ARG(t, 1) = b; ARG(t, 2) = c;
    return t;
}

Term *mk4(int f, Term *a, Term *b, Term *c, Term *d)
{
    Term *t = mk_str(f, 4);
    ARG(t, 0) = a; ARG(t, 1) = b; ARG(t, 2) = c; ARG(t, 3) = d;
    return t;
}

Term *mk_cons(Term *head, Term *tail) { return mk2(a_dot, head, tail); }

/* Decodes one UTF-8 character starting at s[i], advancing i. */
long utf8_decode(const char *s, size_t n, size_t *i)
{
    unsigned char c = (unsigned char)s[*i];
    int extra, k;
    long code;

    if (c < 0x80) { (*i)++; return c; }
    extra = c >= 0xF0 ? 3 : c >= 0xE0 ? 2 : 1;
    code = c & (0x3F >> extra);
    (*i)++;
    for (k = 0; k < extra && *i < n; k++, (*i)++) {
        unsigned char d = (unsigned char)s[*i];
        if ((d & 0xC0) != 0x80) break;
        code = (code << 6) | (d & 0x3F);
    }
    return code;
}

size_t utf8_encode(long code, char *buf)
{
    if (code < 0) code = 0xFFFD;
    if (code < 0x80) { buf[0] = (char)code; return 1; }
    if (code < 0x800) {
        buf[0] = (char)(0xC0 | (code >> 6));
        buf[1] = (char)(0x80 | (code & 0x3F));
        return 2;
    }
    if (code < 0x10000) {
        buf[0] = (char)(0xE0 | (code >> 12));
        buf[1] = (char)(0x80 | ((code >> 6) & 0x3F));
        buf[2] = (char)(0x80 | (code & 0x3F));
        return 3;
    }
    buf[0] = (char)(0xF0 | (code >> 18));
    buf[1] = (char)(0x80 | ((code >> 12) & 0x3F));
    buf[2] = (char)(0x80 | ((code >> 6) & 0x3F));
    buf[3] = (char)(0x80 | (code & 0x3F));
    return 4;
}

Term *mk_codes(const char *s, size_t n)
{
    Term *list = mk_atom(a_nil);
    long *codes;
    size_t i = 0, k = 0;

    codes = (long *)malloc((n + 1) * sizeof(long));
    while (i < n) codes[k++] = utf8_decode(s, n, &i);
    while (k > 0) list = mk_cons(mk_int(codes[--k]), list);
    free(codes);
    return list;
}

Term *mk_chars(const char *s, size_t n)
{
    Term *list = mk_atom(a_nil);
    size_t *starts;
    size_t i = 0, k = 0;

    starts = (size_t *)malloc((n + 2) * sizeof(size_t));
    while (i < n) { starts[k++] = i; utf8_decode(s, n, &i); }
    starts[k] = n;
    while (k > 0) {
        k--;
        list = mk_cons(mk_atom(intern_n(s + starts[k], starts[k + 1] - starts[k])),
                       list);
    }
    free(starts);
    return list;
}

Term *list_from_array(Term **items, int n)
{
    Term *list = mk_atom(a_nil);
    int i;
    for (i = n - 1; i >= 0; i--) list = mk_cons(items[i], list);
    return list;
}

int list_length(Term *t)
{
    int n = 0;
    t = deref(t);
    while (t->tag == TAG_STR && FN(t) == a_dot && AR(t) == 2) {
        n++;
        t = deref(ARG(t, 1));
    }
    return (t->tag == TAG_ATOM && AT(t) == a_nil) ? n : -1;
}

/* ------------------------------------------------------------------ */
/* Dereferencing, trail and binding                                   */
/* ------------------------------------------------------------------ */

Term *deref(Term *t)
{
    while (t->tag == TAG_VAR && t->u.v.ref) t = t->u.v.ref;
    return t;
}

enum { TR_BIND, TR_FLAG };

typedef struct {
    unsigned char kind;
    union { Term *var; int *slot; } p;
    int old;
} TrailEntry;

static TrailEntry *trail;
static size_t tr_top, tr_cap;

static void trail_grow(void)
{
    tr_cap = tr_cap ? tr_cap * 2 : 4096;
    trail = (TrailEntry *)realloc(trail, tr_cap * sizeof(TrailEntry));
    if (!trail) { fprintf(stderr, "prolog: out of memory\n"); exit(1); }
}

void bind(Term *var, Term *val)
{
    var->u.v.ref = val;
    if (tr_top == tr_cap) trail_grow();
    trail[tr_top].kind = TR_BIND;
    trail[tr_top].p.var = var;
    tr_top++;
}

void trail_flag(int *slot)
{
    if (tr_top == tr_cap) trail_grow();
    trail[tr_top].kind = TR_FLAG;
    trail[tr_top].p.slot = slot;
    trail[tr_top].old = *slot;
    tr_top++;
}

size_t trail_mark(void) { return tr_top; }

void trail_undo(size_t mark)
{
    while (tr_top > mark) {
        tr_top--;
        if (trail[tr_top].kind == TR_BIND)
            trail[tr_top].p.var->u.v.ref = NULL;
        else
            *trail[tr_top].p.slot = trail[tr_top].old;
    }
}

/* ------------------------------------------------------------------ */
/* Garbage collection                                                 */
/* ------------------------------------------------------------------ */

/* Roots held in C variables across a call into the machine.  Anything the
   caller still needs after machine_run() returns must be registered here. */
#define MAX_GC_ROOTS 32
static Term **gc_roots[MAX_GC_ROOTS];
static int gc_nroots;

void gc_protect(Term **slot)
{
    if (gc_nroots < MAX_GC_ROOTS) gc_roots[gc_nroots++] = slot;
}

int  gc_root_top(void) { return gc_nroots; }
void gc_unprotect(int n) { gc_nroots = n; }

/* Copies one term into the new heap, leaving a forwarding pointer behind so
   that shared (and cyclic) structure is copied exactly once. */
static Term *gc_copy(Term *t)
{
    Term *result = NULL, *c;
    Term **slot = &result;
    int i;

tail:
    while (t->tag == TAG_VAR && t->u.v.ref) t = t->u.v.ref;
    if (t->tag == TAG_FWD) { *slot = t->u.v.ref; return result; }

    switch (t->tag) {
    case TAG_VAR:
        c = (Term *)heap_alloc(sizeof(Term));
        c->tag = TAG_VAR;
        c->u.v.ref = NULL;
        c->u.v.serial = t->u.v.serial;      /* keep the standard order stable */
        t->tag = TAG_FWD;
        t->u.v.ref = c;
        *slot = c;
        return result;
    case TAG_ATOM: case TAG_INT: case TAG_FLT:
        c = (Term *)heap_alloc(sizeof(Term));
        *c = *t;
        *slot = c;
        return result;
    default: {
        int f = FN(t), n = AR(t);
        Term **args = t->u.s.args;          /* saved: forwarding clobbers it */
        c = mk_str(f, n);
        t->tag = TAG_FWD;
        t->u.v.ref = c;
        *slot = c;
        if (n == 0) return result;
        for (i = 0; i < n - 1; i++) ARG(c, i) = gc_copy(args[i]);
        slot = &ARG(c, n - 1);
        t = args[n - 1];
        goto tail;
    }
    }
}

void heap_gc(Goal **goals_root)
{
    HeapChunk *old_head = heap_head, *c, *nx;
    Goal *g, **link;
    int i;

    /* Start a fresh heap; everything reachable is copied into it. */
    heap_head = heap_cur = chunk_new(HEAP_CHUNK_MIN);

    for (g = *goals_root, link = goals_root; g; g = g->next) {
        Goal *ng = (Goal *)heap_alloc(sizeof(Goal));
        ng->cutb = g->cutb;
        ng->next = NULL;
        ng->goal = gc_copy(g->goal);
        *link = ng;
        link = &ng->next;
    }
    for (i = 0; i < gc_nroots; i++)
        if (*gc_roots[i]) *gc_roots[i] = gc_copy(*gc_roots[i]);

    /* With no choice points there is nothing left to undo. */
    tr_top = 0;
    heap_epoch++;
    m_gc_count++;

    for (c = old_head; c; c = nx) {
        nx = c->next;
        heap_total -= c->size;
        free(c->data);
        free(c);
    }
}

/* ------------------------------------------------------------------ */
/* Unification                                                        */
/* ------------------------------------------------------------------ */

int unify(Term *a, Term *b)
{
    int i;

tail:
    a = deref(a);
    b = deref(b);
    if (a == b) return 1;

    if (a->tag == TAG_VAR) {
        if (b->tag == TAG_VAR) {
            /* Bind the younger variable to the older one. */
            if (a->u.v.serial < b->u.v.serial) { bind(b, a); return 1; }
        }
        bind(a, b);
        return 1;
    }
    if (b->tag == TAG_VAR) { bind(b, a); return 1; }
    if (a->tag != b->tag) return 0;

    switch (a->tag) {
    case TAG_ATOM: return AT(a) == AT(b);
    case TAG_INT:  return IV(a) == IV(b);
    case TAG_FLT:  return FV(a) == FV(b);
    case TAG_STR:
        if (FN(a) != FN(b) || AR(a) != AR(b)) return 0;
        if (AR(a) == 0) return 1;
        for (i = 0; i < AR(a) - 1; i++)
            if (!unify(ARG(a, i), ARG(b, i))) return 0;
        /* Recurse iteratively on the last argument, so that long lists do
           not grow the C stack. */
        b = ARG(b, i);
        a = ARG(a, i);
        goto tail;
    }
    return 0;
}

/* ------------------------------------------------------------------ */
/* Standard order of terms                                            */
/* ------------------------------------------------------------------ */

static int type_rank(Term *t)
{
    switch (t->tag) {
    case TAG_VAR:  return 0;
    case TAG_FLT:  return 1;
    case TAG_INT:  return 1;   /* numbers compare by value, float first */
    case TAG_ATOM: return 3;
    default:       return 4;
    }
}

static int cmp_ll(long long a, long long b) { return a < b ? -1 : a > b ? 1 : 0; }
static int cmp_d(double a, double b) { return a < b ? -1 : a > b ? 1 : 0; }

int compare_terms(Term *a, Term *b)
{
    int ra, rb, c, i;

tail:
    a = deref(a);
    b = deref(b);
    if (a == b) return 0;
    ra = type_rank(a);
    rb = type_rank(b);
    if (ra != rb) return ra < rb ? -1 : 1;

    switch (a->tag) {
    case TAG_VAR:
        return a->u.v.serial < b->u.v.serial ? -1 :
               a->u.v.serial > b->u.v.serial ? 1 : 0;
    case TAG_INT:
        if (b->tag == TAG_INT) return cmp_ll(IV(a), IV(b));
        c = cmp_d((double)IV(a), FV(b));
        return c ? c : 1;                       /* Float < Int if equal */
    case TAG_FLT:
        if (b->tag == TAG_FLT) return cmp_d(FV(a), FV(b));
        c = cmp_d(FV(a), (double)IV(b));
        return c ? c : -1;
    case TAG_ATOM:
        c = strcmp(atom_name(AT(a)), atom_name(AT(b)));
        return c < 0 ? -1 : c > 0 ? 1 : 0;
    default:
        if (AR(a) != AR(b)) return AR(a) < AR(b) ? -1 : 1;
        c = strcmp(atom_name(FN(a)), atom_name(FN(b)));
        if (c) return c < 0 ? -1 : 1;
        if (AR(a) == 0) return 0;
        for (i = 0; i < AR(a) - 1; i++) {
            c = compare_terms(ARG(a, i), ARG(b, i));
            if (c) return c;
        }
        b = ARG(b, i);
        a = ARG(a, i);
        goto tail;
    }
}

/* ------------------------------------------------------------------ */
/* Copying                                                            */
/* ------------------------------------------------------------------ */

typedef struct {
    Term **from;
    Term **to;
    int n, cap;
} VarMap;

static Term *vmap_get(VarMap *m, Term *v)
{
    int i;
    for (i = 0; i < m->n; i++) if (m->from[i] == v) return m->to[i];
    return NULL;
}

static void vmap_put(VarMap *m, Term *from, Term *to)
{
    if (m->n == m->cap) {
        m->cap = m->cap ? m->cap * 2 : 32;
        m->from = (Term **)realloc(m->from, m->cap * sizeof(Term *));
        m->to = (Term **)realloc(m->to, m->cap * sizeof(Term *));
    }
    m->from[m->n] = from;
    m->to[m->n] = to;
    m->n++;
}

static Term *copy_rec(Term *t, VarMap *m, Arena *a, int compile)
{
    Term *c, *r, *result = NULL;
    Term **slot = &result;
    int i;

tail:
    t = deref(t);
    switch (t->tag) {
    case TAG_VAR:
        r = vmap_get(m, t);
        if (!r) {
            if (a) {
                r = (Term *)arena_alloc(a, sizeof(Term));
                r->tag = TAG_VAR;
                r->u.v.ref = NULL;
                r->u.v.serial = compile ? (unsigned long)m->n : 0;
            } else {
                r = mk_var();
            }
            vmap_put(m, t, r);
        }
        *slot = r;
        return result;
    case TAG_ATOM:
    case TAG_INT:
    case TAG_FLT:
        if (!a) { *slot = t; return result; } /* constants can be shared */
        c = (Term *)arena_alloc(a, sizeof(Term));
        *c = *t;
        *slot = c;
        return result;
    default:
        if (a) {
            c = (Term *)arena_alloc(a, sizeof(Term) + AR(t) * sizeof(Term *));
            c->tag = TAG_STR;
            c->u.s.functor = FN(t);
            c->u.s.arity = AR(t);
            c->u.s.args = (Term **)((char *)c + sizeof(Term));
        } else {
            c = mk_str(FN(t), AR(t));
        }
        *slot = c;
        if (AR(t) == 0) return result;
        for (i = 0; i < AR(t) - 1; i++)
            ARG(c, i) = copy_rec(ARG(t, i), m, a, compile);
        slot = &ARG(c, i);
        t = ARG(t, i);
        goto tail;
    }
}

static void vmap_done(VarMap *m) { free(m->from); free(m->to); }

Term *heap_copy(Term *t)
{
    VarMap m = { NULL, NULL, 0, 0 };
    Term *r = copy_rec(t, &m, NULL, 0);
    vmap_done(&m);
    return r;
}

Term *arena_compile(Arena *a, Term *t, int *nvars)
{
    VarMap m = { NULL, NULL, 0, 0 };
    Term *r = copy_rec(t, &m, a, 1);
    if (nvars) *nvars = m.n;
    vmap_done(&m);
    return r;
}

Term *heap_instantiate(Term *t, Term **vars, int nvars)
{
    Term *c, *result = NULL;
    Term **slot = &result;
    int i;

tail:
    switch (t->tag) {
    case TAG_VAR: {
        unsigned long idx = t->u.v.serial;
        if ((int)idx >= nvars) { *slot = mk_var(); return result; }
        if (!vars[idx]) vars[idx] = mk_var();
        *slot = vars[idx];
        return result;
    }
    case TAG_ATOM:
    case TAG_INT:
    case TAG_FLT:
        /* Constants are copied rather than shared: the source term may live
           in an arena (a clause, a findall buffer, an exception ball) that is
           released long before the instantiated copy dies. */
        c = (Term *)heap_alloc(sizeof(Term));
        *c = *t;
        *slot = c;
        return result;
    default:
        c = mk_str(FN(t), AR(t));
        *slot = c;
        if (AR(t) == 0) return result;
        for (i = 0; i < AR(t) - 1; i++)
            ARG(c, i) = heap_instantiate(ARG(t, i), vars, nvars);
        slot = &ARG(c, i);
        t = ARG(t, i);
        goto tail;
    }
}

int term_variables(Term *t, Term **buf, int max, int n)
{
    int i;
    t = deref(t);
    if (t->tag == TAG_VAR) {
        for (i = 0; i < n; i++) if (buf[i] == t) return n;
        if (n < max) buf[n++] = t;
        return n;
    }
    if (t->tag == TAG_STR)
        for (i = 0; i < AR(t); i++) n = term_variables(ARG(t, i), buf, max, n);
    return n;
}
