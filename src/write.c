/* write.c -- printing terms, operator aware. */
#include "prolog.h"
#include <ctype.h>
#include <math.h>

static int symbol_char(int c)
{
    return c && strchr("+-*/\\^<>=~:.?@#&$", c) != NULL;
}

static int alnum_char(int c) { return isalnum(c) || c == '_'; }

static void put(Writer *w, const char *s, size_t n)
{
    if (!n) return;
    /* Insert a space where two tokens would otherwise merge. */
    if ((symbol_char(w->lastc) && symbol_char((unsigned char)s[0])) ||
        (alnum_char(w->lastc) && alnum_char((unsigned char)s[0])))
        w->emit(w->ctx, " ", 1);
    w->emit(w->ctx, s, n);
    w->lastc = (unsigned char)s[n - 1];
}

static void puts_(Writer *w, const char *s) { put(w, s, strlen(s)); }

/* Raw output, bypassing the token separation logic. */
static void raw(Writer *w, const char *s)
{
    size_t n = strlen(s);
    if (!n) return;
    w->emit(w->ctx, s, n);
    w->lastc = (unsigned char)s[n - 1];
}

int atom_needs_quotes(const char *s, size_t n)
{
    size_t i;
    if (n == 0) return 1;
    if (!strcmp(s, "[]") || !strcmp(s, "{}") || !strcmp(s, "!") ||
        !strcmp(s, ";")) return 0;
    if (islower((unsigned char)s[0])) {
        for (i = 0; i < n; i++)
            if (!(isalnum((unsigned char)s[i]) || s[i] == '_')) return 1;
        return 0;
    }
    if (symbol_char((unsigned char)s[0])) {
        if (n == 1 && s[0] == '.') return 1;     /* a lone dot ends a clause */
        for (i = 0; i < n; i++)
            if (!symbol_char((unsigned char)s[i])) return 1;
        return 0;
    }
    return 1;
}

static void write_quoted_text(Writer *w, const char *s, size_t n, int q)
{
    char qs[2] = { (char)q, 0 };
    size_t i;
    raw(w, qs);
    for (i = 0; i < n; i++) {
        unsigned char c = (unsigned char)s[i];
        char buf[8];
        if (c == (unsigned char)q) { buf[0] = '\\'; buf[1] = (char)q; buf[2] = 0; }
        else switch (c) {
        case '\\': strcpy(buf, "\\\\"); break;
        case '\n': strcpy(buf, "\\n"); break;
        case '\t': strcpy(buf, "\\t"); break;
        case '\r': strcpy(buf, "\\r"); break;
        case '\a': strcpy(buf, "\\a"); break;
        case '\b': strcpy(buf, "\\b"); break;
        case '\f': strcpy(buf, "\\f"); break;
        case '\v': strcpy(buf, "\\v"); break;
        case 0:    strcpy(buf, "\\x0\\"); break;
        default:
            if (c < 32 || c == 127) snprintf(buf, sizeof(buf), "\\x%x\\", c);
            else { buf[0] = (char)c; buf[1] = 0; }
        }
        raw(w, buf);
    }
    raw(w, qs);
}

static void write_atom(Writer *w, int a)
{
    const char *s = atom_name(a);
    size_t n = atom_len(a);
    if ((w->flags & WR_QUOTED) && atom_needs_quotes(s, n)) {
        /* Quoted atoms are self-delimiting, but keep tokens apart anyway. */
        if (alnum_char(w->lastc) || symbol_char(w->lastc)) raw(w, " ");
        write_quoted_text(w, s, n, '\'');
    } else {
        put(w, s, n);
    }
}

void format_float(char *buf, size_t bufsz, double d)
{
    if (isinf(d)) { snprintf(buf, bufsz, d > 0 ? "inf" : "-inf"); return; }
    if (isnan(d)) { snprintf(buf, bufsz, "nan"); return; }
    snprintf(buf, bufsz, "%.15g", d);
    if (!strpbrk(buf, ".e")) {
        double rt;
        /* Make sure the result reads back as a float. */
        if (sscanf(buf, "%lf", &rt) == 1) strncat(buf, ".0", bufsz - strlen(buf) - 1);
    }
    /* %.15g may lose precision; fall back to a longer form if needed. */
    {
        double back = strtod(buf, NULL);
        if (back != d) {
            snprintf(buf, bufsz, "%.17g", d);
            if (!strpbrk(buf, ".e")) strncat(buf, ".0", bufsz - strlen(buf) - 1);
        }
    }
}

static void write_number(Writer *w, Term *t)
{
    char buf[64];
    if (t->tag == TAG_INT) snprintf(buf, sizeof(buf), "%lld", IV(t));
    else format_float(buf, sizeof(buf), FV(t));
    puts_(w, buf);
}

static void wr(Writer *w, Term *t, int maxprec, int depth);

static void write_args(Writer *w, Term *t, int from, int depth)
{
    int i;
    raw(w, "(");
    w->lastc = 0;
    for (i = from; i < AR(t); i++) {
        if (i > from) { raw(w, ","); w->lastc = 0; }
        wr(w, ARG(t, i), 999, depth + 1);
    }
    raw(w, ")");
}

static void write_list(Writer *w, Term *t, int depth)
{
    int n = 0;
    raw(w, "[");
    w->lastc = 0;
    for (;;) {
        wr(w, ARG(t, 0), 999, depth + 1);
        t = deref(ARG(t, 1));
        n++;
        if (t->tag == TAG_STR && FN(t) == a_dot && AR(t) == 2) {
            if (w->maxdepth && n >= w->maxdepth) { raw(w, "|..."); break; }
            raw(w, ",");
            w->lastc = 0;
            continue;
        }
        if (t->tag == TAG_ATOM && AT(t) == a_nil) break;
        raw(w, "|");
        w->lastc = 0;
        wr(w, t, 999, depth + 1);
        break;
    }
    raw(w, "]");
}

/* '$VAR'(N) printing: A, B, ... Z, A1, B1, ... */
static int write_numbervar(Writer *w, Term *t)
{
    Term *a;
    char buf[32];
    if (!(w->flags & WR_NUMBERVARS)) return 0;
    if (t->tag != TAG_STR || FN(t) != a_dollar_var || AR(t) != 1) return 0;
    a = deref(ARG(t, 0));
    if (a->tag == TAG_INT) {
        long long n = IV(a);
        if (n < 0) return 0;
        if (n / 26) snprintf(buf, sizeof(buf), "%c%lld", (int)('A' + n % 26), n / 26);
        else snprintf(buf, sizeof(buf), "%c", (int)('A' + n % 26));
        puts_(w, buf);
        return 1;
    }
    if (a->tag == TAG_ATOM) { puts_(w, atom_name(AT(a))); return 1; }
    return 0;
}

static void wr(Writer *w, Term *t, int maxprec, int depth)
{
    int prec, lp, rp;

    t = deref(t);
    if (w->maxdepth && depth > w->maxdepth) { puts_(w, "..."); return; }

    switch (t->tag) {
    case TAG_VAR: {
        char buf[32];
        snprintf(buf, sizeof(buf), "_G%lu", t->u.v.serial);
        puts_(w, buf);
        return;
    }
    case TAG_INT: case TAG_FLT:
        if ((t->tag == TAG_INT && IV(t) < 0) ||
            (t->tag == TAG_FLT && FV(t) < 0)) {
            /* A negative number is an operand of priority 200. */
            if (maxprec < 200) { raw(w, "("); w->lastc = 0; write_number(w, t); raw(w, ")"); return; }
        }
        write_number(w, t);
        return;
    case TAG_ATOM:
        if (op_is_op(AT(t)) && maxprec < 1201) {
            int p1, p2, a1, a2, a3;
            int p = 0;
            if (op_prefix(AT(t), &p1, &a1)) p = p1;
            if (op_infix(AT(t), &p2, &a2, &a3) && p2 > p) p = p2;
            if (op_postfix(AT(t), &p2, &a2) && p2 > p) p = p2;
            if (p > maxprec) {
                raw(w, "("); w->lastc = 0;
                write_atom(w, AT(t));
                raw(w, ")");
                return;
            }
        }
        write_atom(w, AT(t));
        return;
    }

    /* Compound terms. */
    if (write_numbervar(w, t)) return;

    if (!(w->flags & WR_IGNORE_OPS)) {
        if (FN(t) == a_dot && AR(t) == 2) { write_list(w, t, depth); return; }
        if (FN(t) == a_curly && AR(t) == 1) {
            raw(w, "{");
            w->lastc = 0;
            wr(w, ARG(t, 0), 1200, depth + 1);
            raw(w, "}");
            return;
        }
        if (AR(t) == 2 && op_infix(FN(t), &prec, &lp, &rp)) {
            int paren = prec > maxprec;
            if (paren) { raw(w, "("); w->lastc = 0; }
            wr(w, ARG(t, 0), lp, depth + 1);
            if (FN(t) == a_comma) { raw(w, ","); w->lastc = 0; }
            else {
                int alpha = isalpha((unsigned char)atom_name(FN(t))[0]);
                if (alpha) raw(w, " ");
                write_atom(w, FN(t));
                if (alpha) { raw(w, " "); w->lastc = 0; }
            }
            wr(w, ARG(t, 1), rp, depth + 1);
            if (paren) raw(w, ")");
            return;
        }
        if (AR(t) == 1 && op_prefix(FN(t), &prec, &lp)) {
            int paren = prec > maxprec;
            Term *arg = deref(ARG(t, 0));
            /* '-'(1) must not print as -1, which would read back as a number. */
            int spaced = isalpha((unsigned char)atom_name(FN(t))[0]);
            if (paren) { raw(w, "("); w->lastc = 0; }
            write_atom(w, FN(t));
            if (spaced) raw(w, " ");
            if (IS_NUM(arg) && (FN(t) == a_minus || FN(t) == a_plus)) raw(w, " ");
            wr(w, arg, lp, depth + 1);
            if (paren) raw(w, ")");
            return;
        }
        if (AR(t) == 1 && op_postfix(FN(t), &prec, &lp)) {
            int paren = prec > maxprec;
            if (paren) { raw(w, "("); w->lastc = 0; }
            wr(w, ARG(t, 0), lp, depth + 1);
            write_atom(w, FN(t));
            if (paren) raw(w, ")");
            return;
        }
    }

    write_atom(w, FN(t));
    write_args(w, t, 0, depth);
}

void write_term(Writer *w, Term *t)
{
    w->lastc = 0;
    wr(w, t, 1200, 0);
}

/* ---- convenience sinks ---- */

static void emit_file(void *ctx, const char *s, size_t n)
{
    fwrite(s, 1, n, (FILE *)ctx);
}

void write_to_stream(FILE *f, Term *t, int flags)
{
    Writer w;
    memset(&w, 0, sizeof(w));
    w.emit = emit_file;
    w.ctx = f;
    w.flags = flags;
    write_term(&w, t);
}

typedef struct { char *buf; size_t len, cap; } SBuf;

static void emit_sbuf(void *ctx, const char *s, size_t n)
{
    SBuf *b = (SBuf *)ctx;
    if (b->len + n + 1 > b->cap) {
        while (b->len + n + 1 > b->cap) b->cap = b->cap ? b->cap * 2 : 256;
        b->buf = (char *)realloc(b->buf, b->cap);
    }
    memcpy(b->buf + b->len, s, n);
    b->len += n;
    b->buf[b->len] = 0;
}

char *term_to_string(Term *t, int flags, size_t *len_out)
{
    Writer w;
    SBuf b;
    b.buf = (char *)malloc(256);
    b.len = 0;
    b.cap = 256;
    b.buf[0] = 0;
    memset(&w, 0, sizeof(w));
    w.emit = emit_sbuf;
    w.ctx = &b;
    w.flags = flags;
    write_term(&w, t);
    if (len_out) *len_out = b.len;
    return b.buf;
}
