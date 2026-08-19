/* arith.c -- evaluation of arithmetic expressions. */
#include "prolog.h"
#include <math.h>
#include <time.h>

typedef struct { int isf; long long i; double f; } Num;

#define NF(n) ((n)->isf ? (n)->f : (double)(n)->i)

static int eval(Term *t, Num *n);

static int evaluable_error(Term *t)
{
    Term *ind;
    t = deref(t);
    if (t->tag == TAG_STR)
        ind = mk2(a_slash, mk_atom(FN(t)), mk_int(AR(t)));
    else if (t->tag == TAG_ATOM)
        ind = mk2(a_slash, mk_atom(AT(t)), mk_int(0));
    else
        return type_error("evaluable", t);
    return type_error("evaluable", ind);
}

static int need_int(Num *n, Term *culprit)
{
    if (n->isf) return type_error("integer", culprit ? culprit : mk_float(n->f));
    return PL_OK;
}

static int add_ovf(long long a, long long b, long long *r)
{
#if defined(__GNUC__) || defined(__clang__)
    return __builtin_add_overflow(a, b, r);
#else
    *r = a + b; return 0;
#endif
}
static int sub_ovf(long long a, long long b, long long *r)
{
#if defined(__GNUC__) || defined(__clang__)
    return __builtin_sub_overflow(a, b, r);
#else
    *r = a - b; return 0;
#endif
}
static int mul_ovf(long long a, long long b, long long *r)
{
#if defined(__GNUC__) || defined(__clang__)
    return __builtin_mul_overflow(a, b, r);
#else
    *r = a * b; return 0;
#endif
}

static long long ipow(long long base, long long e, int *ovf)
{
    long long r = 1;
    *ovf = 0;
    while (e > 0) {
        if (e & 1) { if (mul_ovf(r, base, &r)) { *ovf = 1; return 0; } }
        e >>= 1;
        if (e) { if (mul_ovf(base, base, &base)) { *ovf = 1; return 0; } }
    }
    return r;
}

static int eval_unary(int f, Term *expr, Num *a, Num *out)
{
    const char *name = atom_name(f);

    out->isf = 0;
    if (!strcmp(name, "-")) {
        if (a->isf) { out->isf = 1; out->f = -a->f; }
        else if (sub_ovf(0, a->i, &out->i)) return evaluation_error("int_overflow");
        return PL_OK;
    }
    if (!strcmp(name, "+")) { *out = *a; return PL_OK; }
    if (!strcmp(name, "abs")) {
        if (a->isf) { out->isf = 1; out->f = fabs(a->f); }
        else if (a->i == LLONG_MIN) return evaluation_error("int_overflow");
        else out->i = a->i < 0 ? -a->i : a->i;
        return PL_OK;
    }
    if (!strcmp(name, "sign")) {
        if (a->isf) { out->isf = 1; out->f = a->f > 0 ? 1.0 : a->f < 0 ? -1.0 : 0.0; }
        else out->i = a->i > 0 ? 1 : a->i < 0 ? -1 : 0;
        return PL_OK;
    }
    if (!strcmp(name, "min") || !strcmp(name, "max")) return evaluable_error(expr);

    if (!strcmp(name, "sqrt")) {
        double v = NF(a);
        if (v < 0) return evaluation_error("undefined");
        out->isf = 1; out->f = sqrt(v); return PL_OK;
    }
#define UNARY_F(nm, expr_)  \
    if (!strcmp(name, nm)) { double x = NF(a); out->isf = 1; out->f = (expr_); return PL_OK; }
    UNARY_F("sin", sin(x))
    UNARY_F("cos", cos(x))
    UNARY_F("tan", tan(x))
    UNARY_F("asin", asin(x))
    UNARY_F("acos", acos(x))
    UNARY_F("atan", atan(x))
    UNARY_F("sinh", sinh(x))
    UNARY_F("cosh", cosh(x))
    UNARY_F("tanh", tanh(x))
    UNARY_F("asinh", asinh(x))
    UNARY_F("acosh", acosh(x))
    UNARY_F("atanh", atanh(x))
    UNARY_F("exp", exp(x))
    UNARY_F("float", x)
#undef UNARY_F
    if (!strcmp(name, "log")) {
        double x = NF(a);
        if (x <= 0) return evaluation_error(x == 0 ? "zero_divisor" : "undefined");
        out->isf = 1; out->f = log(x); return PL_OK;
    }
    if (!strcmp(name, "log2")) {
        double x = NF(a);
        if (x <= 0) return evaluation_error("undefined");
        out->isf = 1; out->f = log(x) / log(2.0); return PL_OK;
    }
    if (!strcmp(name, "integer")) {
        if (!a->isf) { *out = *a; return PL_OK; }
        out->i = (long long)llround(a->f);
        return PL_OK;
    }
    if (!strcmp(name, "float_integer_part")) {
        out->isf = 1; out->f = trunc(NF(a)); return PL_OK;
    }
    if (!strcmp(name, "float_fractional_part")) {
        double x = NF(a);
        out->isf = 1; out->f = x - trunc(x); return PL_OK;
    }
    if (!strcmp(name, "truncate")) {
        if (!a->isf) { *out = *a; return PL_OK; }
        out->i = (long long)trunc(a->f); return PL_OK;
    }
    if (!strcmp(name, "round")) {
        if (!a->isf) { *out = *a; return PL_OK; }
        out->i = (long long)llround(a->f); return PL_OK;
    }
    if (!strcmp(name, "ceiling")) {
        if (!a->isf) { *out = *a; return PL_OK; }
        out->i = (long long)ceil(a->f); return PL_OK;
    }
    if (!strcmp(name, "floor")) {
        if (!a->isf) { *out = *a; return PL_OK; }
        out->i = (long long)floor(a->f); return PL_OK;
    }
    if (!strcmp(name, "\\")) {
        if (need_int(a, NULL) != PL_OK) return PL_ERROR;
        out->i = ~a->i; return PL_OK;
    }
    if (!strcmp(name, "msb")) {
        int b = -1;
        unsigned long long v;
        if (need_int(a, NULL) != PL_OK) return PL_ERROR;
        if (a->i <= 0) return type_error("positive_integer", mk_int(a->i));
        for (v = (unsigned long long)a->i; v; v >>= 1) b++;
        out->i = b; return PL_OK;
    }
    if (!strcmp(name, "succ")) {
        if (need_int(a, NULL) != PL_OK) return PL_ERROR;
        if (add_ovf(a->i, 1, &out->i)) return evaluation_error("int_overflow");
        return PL_OK;
    }
    if (!strcmp(name, "random")) {
        if (need_int(a, NULL) != PL_OK) return PL_ERROR;
        if (a->i <= 0) return evaluation_error("undefined");
        out->i = (long long)(rand() % a->i);
        return PL_OK;
    }
    if (!strcmp(name, "random_float")) {
        out->isf = 1; out->f = (double)rand() / ((double)RAND_MAX + 1.0);
        return PL_OK;
    }
    return evaluable_error(expr);
}

static int eval_binary(int f, Term *expr, Num *a, Num *b, Num *out)
{
    const char *name = atom_name(f);
    int both_int = !a->isf && !b->isf;

    out->isf = 0;
    if (!strcmp(name, "+")) {
        if (both_int) {
            if (add_ovf(a->i, b->i, &out->i)) return evaluation_error("int_overflow");
        } else { out->isf = 1; out->f = NF(a) + NF(b); }
        return PL_OK;
    }
    if (!strcmp(name, "-")) {
        if (both_int) {
            if (sub_ovf(a->i, b->i, &out->i)) return evaluation_error("int_overflow");
        } else { out->isf = 1; out->f = NF(a) - NF(b); }
        return PL_OK;
    }
    if (!strcmp(name, "*")) {
        if (both_int) {
            if (mul_ovf(a->i, b->i, &out->i)) return evaluation_error("int_overflow");
        } else { out->isf = 1; out->f = NF(a) * NF(b); }
        return PL_OK;
    }
    if (!strcmp(name, "/")) {
        if (both_int) {
            if (b->i == 0) return evaluation_error("zero_divisor");
            if (a->i % b->i == 0 && !(a->i == LLONG_MIN && b->i == -1))
                { out->i = a->i / b->i; return PL_OK; }
            out->isf = 1; out->f = (double)a->i / (double)b->i;
            return PL_OK;
        }
        if (NF(b) == 0.0) return evaluation_error("zero_divisor");
        out->isf = 1; out->f = NF(a) / NF(b);
        return PL_OK;
    }
    if (!strcmp(name, "//")) {
        if (!both_int) return type_error("integer", a->isf ? mk_float(a->f) : mk_float(b->f));
        if (b->i == 0) return evaluation_error("zero_divisor");
        if (a->i == LLONG_MIN && b->i == -1) return evaluation_error("int_overflow");
        out->i = a->i / b->i;
        return PL_OK;
    }
    if (!strcmp(name, "div")) {
        long long q;
        if (!both_int) return type_error("integer", a->isf ? mk_float(a->f) : mk_float(b->f));
        if (b->i == 0) return evaluation_error("zero_divisor");
        if (a->i == LLONG_MIN && b->i == -1) return evaluation_error("int_overflow");
        q = a->i / b->i;
        if ((a->i % b->i != 0) && ((a->i < 0) != (b->i < 0))) q--;
        out->i = q;
        return PL_OK;
    }
    if (!strcmp(name, "mod")) {
        long long m;
        if (!both_int) return type_error("integer", a->isf ? mk_float(a->f) : mk_float(b->f));
        if (b->i == 0) return evaluation_error("zero_divisor");
        if (a->i == LLONG_MIN && b->i == -1) { out->i = 0; return PL_OK; }
        m = a->i % b->i;
        if (m != 0 && ((m < 0) != (b->i < 0))) m += b->i;
        out->i = m;
        return PL_OK;
    }
    if (!strcmp(name, "rem")) {
        if (!both_int) return type_error("integer", a->isf ? mk_float(a->f) : mk_float(b->f));
        if (b->i == 0) return evaluation_error("zero_divisor");
        if (a->i == LLONG_MIN && b->i == -1) { out->i = 0; return PL_OK; }
        out->i = a->i % b->i;
        return PL_OK;
    }
    if (!strcmp(name, "min")) {
        int cmp = NF(a) < NF(b) ? -1 : NF(a) > NF(b) ? 1 : 0;
        *out = cmp <= 0 ? *a : *b;
        return PL_OK;
    }
    if (!strcmp(name, "max")) {
        int cmp = NF(a) < NF(b) ? -1 : NF(a) > NF(b) ? 1 : 0;
        *out = cmp >= 0 ? *a : *b;
        return PL_OK;
    }
    if (!strcmp(name, "**") || !strcmp(name, "^")) {
        int iso_pow = name[0] == '^';
        if (both_int) {
            if (b->i >= 0) {
                int ovf;
                out->i = ipow(a->i, b->i, &ovf);
                if (ovf) return evaluation_error("int_overflow");
                return PL_OK;
            }
            if (iso_pow) {
                if (a->i == 1) { out->i = 1; return PL_OK; }
                if (a->i == -1) { out->i = (b->i % 2 == 0) ? 1 : -1; return PL_OK; }
                if (a->i == 0) return evaluation_error("zero_divisor");
                return type_error("float", mk_int(a->i));
            }
            out->isf = 1; out->f = pow((double)a->i, (double)b->i);
            return PL_OK;
        }
        out->isf = 1;
        out->f = pow(NF(a), NF(b));
        if (isnan(out->f) && !isnan(NF(a)) && !isnan(NF(b)))
            return evaluation_error("undefined");
        return PL_OK;
    }
    if (!strcmp(name, "atan2") || !strcmp(name, "atan")) {
        out->isf = 1; out->f = atan2(NF(a), NF(b)); return PL_OK;
    }
    if (!strcmp(name, "copysign")) {
        out->isf = 1; out->f = copysign(NF(a), NF(b)); return PL_OK;
    }
    if (!strcmp(name, "log")) {
        double x = NF(a), y = NF(b);
        if (x <= 0 || y <= 0) return evaluation_error("undefined");
        out->isf = 1; out->f = log(y) / log(x); return PL_OK;
    }
    if (!strcmp(name, "truncate")) return evaluable_error(expr);

    /* Integer-only operations. */
    if (!strcmp(name, ">>") || !strcmp(name, "<<") || !strcmp(name, "/\\") ||
        !strcmp(name, "\\/") || !strcmp(name, "xor") || !strcmp(name, "gcd")) {
        if (!both_int)
            return type_error("integer", a->isf ? mk_float(a->f) : mk_float(b->f));
        if (!strcmp(name, ">>")) {
            if (b->i < 0 || b->i > 63) return evaluation_error("undefined");
            out->i = a->i >> b->i;
        } else if (!strcmp(name, "<<")) {
            if (b->i < 0 || b->i > 63) return evaluation_error("undefined");
            out->i = a->i << b->i;
        } else if (!strcmp(name, "/\\")) out->i = a->i & b->i;
        else if (!strcmp(name, "\\/")) out->i = a->i | b->i;
        else if (!strcmp(name, "xor")) out->i = a->i ^ b->i;
        else {
            long long x = a->i < 0 ? -a->i : a->i, y = b->i < 0 ? -b->i : b->i;
            while (y) { long long t = x % y; x = y; y = t; }
            out->i = x;
        }
        return PL_OK;
    }
    return evaluable_error(expr);
}

static int eval_atom(Term *t, Num *n)
{
    const char *name = atom_name(AT(t));
    n->isf = 1;
    if (!strcmp(name, "pi")) { n->f = 3.14159265358979323846; return PL_OK; }
    if (!strcmp(name, "e")) { n->f = 2.71828182845904523536; return PL_OK; }
    if (!strcmp(name, "inf") || !strcmp(name, "infinite")) { n->f = HUGE_VAL; return PL_OK; }
    if (!strcmp(name, "nan")) { n->f = NAN; return PL_OK; }
    if (!strcmp(name, "epsilon")) { n->f = 2.2204460492503131e-16; return PL_OK; }
    if (!strcmp(name, "max_tagged_integer")) { n->isf = 0; n->i = LLONG_MAX; return PL_OK; }
    if (!strcmp(name, "min_tagged_integer")) { n->isf = 0; n->i = LLONG_MIN; return PL_OK; }
    if (!strcmp(name, "random")) {
        n->f = (double)rand() / ((double)RAND_MAX + 1.0);
        return PL_OK;
    }
    if (!strcmp(name, "cputime")) {
        n->f = (double)clock() / (double)CLOCKS_PER_SEC;
        return PL_OK;
    }
    if (!strcmp(name, "realtime")) { n->isf = 0; n->i = (long long)time(NULL); return PL_OK; }
    if (!strcmp(name, "[]")) return type_error("evaluable", t);
    return evaluable_error(t);
}

static int eval(Term *t, Num *n)
{
    t = deref(t);
    switch (t->tag) {
    case TAG_VAR:
        return instantiation_error();
    case TAG_INT:
        n->isf = 0; n->i = IV(t); return PL_OK;
    case TAG_FLT:
        n->isf = 1; n->f = FV(t); return PL_OK;
    case TAG_ATOM:
        return eval_atom(t, n);
    default:
        /* A one-element code or char list evaluates to the character code. */
        if (FN(t) == a_dot && AR(t) == 2) {
            Term *h = deref(ARG(t, 0)), *tl = deref(ARG(t, 1));
            if (tl->tag == TAG_ATOM && AT(tl) == a_nil) return eval(h, n);
            return type_error("evaluable", t);
        }
        if (AR(t) == 1) {
            Num a;
            if (eval(ARG(t, 0), &a) != PL_OK) return PL_ERROR;
            return eval_unary(FN(t), t, &a, n);
        }
        if (AR(t) == 2) {
            Num a, b;
            if (eval(ARG(t, 0), &a) != PL_OK) return PL_ERROR;
            if (eval(ARG(t, 1), &b) != PL_OK) return PL_ERROR;
            return eval_binary(FN(t), t, &a, &b, n);
        }
        return evaluable_error(t);
    }
}

int arith_eval(Term *expr, Term **result)
{
    Num n;
    if (eval(expr, &n) != PL_OK) return PL_ERROR;
    *result = n.isf ? mk_float(n.f) : mk_int(n.i);
    return PL_OK;
}

int arith_compare(Term *a, Term *b, int *cmp)
{
    Num x, y;
    if (eval(a, &x) != PL_OK) return PL_ERROR;
    if (eval(b, &y) != PL_OK) return PL_ERROR;
    if (!x.isf && !y.isf)
        *cmp = x.i < y.i ? -1 : x.i > y.i ? 1 : 0;
    else {
        double u = NF(&x), v = NF(&y);
        *cmp = u < v ? -1 : u > v ? 1 : 0;
    }
    return PL_OK;
}
