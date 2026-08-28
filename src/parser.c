/* parser.c -- tokeniser, operator table and operator-precedence reader. */
#include "prolog.h"
#include <ctype.h>
#include <math.h>
#include <errno.h>

/* ------------------------------------------------------------------ */
/* Operator table                                                     */
/* ------------------------------------------------------------------ */

typedef struct {
    int atom;
    int pre_prec, pre_type;
    int in_prec, in_type;
    int post_prec, post_type;
} OpEntry;

static OpEntry *ops;
static int nops, ops_cap;

static OpEntry *op_find(int atom, int create)
{
    int i;
    for (i = 0; i < nops; i++) if (ops[i].atom == atom) return &ops[i];
    if (!create) return NULL;
    if (nops == ops_cap) {
        ops_cap = ops_cap ? ops_cap * 2 : 64;
        ops = (OpEntry *)realloc(ops, ops_cap * sizeof(OpEntry));
    }
    memset(&ops[nops], 0, sizeof(OpEntry));
    ops[nops].atom = atom;
    return &ops[nops++];
}

void op_define(int prec, int type, int atom)
{
    OpEntry *e = op_find(atom, 1);
    switch (type) {
    case OP_FX: case OP_FY:
        e->pre_prec = prec; e->pre_type = type; break;
    case OP_XFX: case OP_XFY: case OP_YFX:
        e->in_prec = prec; e->in_type = type; break;
    default:
        e->post_prec = prec; e->post_type = type; break;
    }
}

int op_prefix(int atom, int *prec, int *argp)
{
    OpEntry *e = op_find(atom, 0);
    if (!e || !e->pre_prec) return 0;
    *prec = e->pre_prec;
    *argp = e->pre_type == OP_FY ? e->pre_prec : e->pre_prec - 1;
    return 1;
}

int op_infix(int atom, int *prec, int *lp, int *rp)
{
    OpEntry *e = op_find(atom, 0);
    if (!e || !e->in_prec) return 0;
    *prec = e->in_prec;
    *lp = e->in_type == OP_YFX ? e->in_prec : e->in_prec - 1;
    *rp = e->in_type == OP_XFY ? e->in_prec : e->in_prec - 1;
    return 1;
}

int op_postfix(int atom, int *prec, int *lp)
{
    OpEntry *e = op_find(atom, 0);
    if (!e || !e->post_prec) return 0;
    *prec = e->post_prec;
    *lp = e->post_type == OP_YF ? e->post_prec : e->post_prec - 1;
    return 1;
}

int op_is_op(int atom)
{
    OpEntry *e = op_find(atom, 0);
    return e && (e->pre_prec || e->in_prec || e->post_prec);
}

int op_enumerate(int i, int *prec, int *type, int *atom)
{
    /* Flattens the table into a sequence of (prec, type, atom) triples. */
    int idx = i / 3, slot = i % 3;
    if (idx >= nops) return 0;
    *atom = ops[idx].atom;
    switch (slot) {
    case 0: *prec = ops[idx].pre_prec;  *type = ops[idx].pre_type;  break;
    case 1: *prec = ops[idx].in_prec;   *type = ops[idx].in_type;   break;
    default:*prec = ops[idx].post_prec; *type = ops[idx].post_type; break;
    }
    return 1;
}

const char *op_type_name(int type)
{
    switch (type) {
    case OP_XFX: return "xfx";
    case OP_XFY: return "xfy";
    case OP_YFX: return "yfx";
    case OP_FY:  return "fy";
    case OP_FX:  return "fx";
    case OP_XF:  return "xf";
    default:     return "yf";
    }
}

void op_init(void)
{
    static const struct { int prec; int type; const char *name; } tbl[] = {
        { 1200, OP_XFX, ":-" },  { 1200, OP_XFX, "-->" },
        { 1200, OP_FX,  ":-" },  { 1200, OP_FX,  "?-" },
        { 1100, OP_XFY, ";" },   { 1100, OP_XFY, "|" },
        { 1050, OP_XFY, "->" },  { 1050, OP_XFY, "*->" },
        { 1000, OP_XFY, "," },
        { 990,  OP_XFX, ":=" },
        { 900,  OP_FY,  "\\+" },
        { 700,  OP_XFX, "=" },   { 700,  OP_XFX, "\\=" },
        { 700,  OP_XFX, "==" },  { 700,  OP_XFX, "\\==" },
        { 700,  OP_XFX, "@<" },  { 700,  OP_XFX, "@>" },
        { 700,  OP_XFX, "@=<" }, { 700,  OP_XFX, "@>=" },
        { 700,  OP_XFX, "=.." }, { 700,  OP_XFX, "is" },
        { 700,  OP_XFX, "=:=" }, { 700,  OP_XFX, "=\\=" },
        { 700,  OP_XFX, "<" },   { 700,  OP_XFX, ">" },
        { 700,  OP_XFX, "=<" },  { 700,  OP_XFX, ">=" },
        { 700,  OP_XFX, "=@=" }, { 700,  OP_XFX, "\\=@=" },
        { 700,  OP_XFX, "as" },  { 700,  OP_XFX, ">:<" },
        { 700,  OP_XFX, ":<" },
        { 600,  OP_XFY, ":" },
        { 500,  OP_YFX, "+" },   { 500,  OP_YFX, "-" },
        { 500,  OP_YFX, "/\\" }, { 500,  OP_YFX, "\\/" },
        { 500,  OP_YFX, "xor" },
        { 400,  OP_YFX, "*" },   { 400,  OP_YFX, "/" },
        { 400,  OP_YFX, "//" },  { 400,  OP_YFX, "rem" },
        { 400,  OP_YFX, "mod" }, { 400,  OP_YFX, "div" },
        { 400,  OP_YFX, "<<" },  { 400,  OP_YFX, ">>" },
        { 400,  OP_YFX, "divmod" },
        { 200,  OP_XFX, "**" },  { 200,  OP_XFY, "^" },
        { 200,  OP_FY,  "-" },   { 200,  OP_FY,  "+" },
        { 200,  OP_FY,  "\\" },
        { 100,  OP_YFX, "." },
        { 1,    OP_FX,  "$" },
        { 0, 0, NULL }
    };
    int i;
    for (i = 0; tbl[i].name; i++)
        op_define(tbl[i].prec, tbl[i].type, intern(tbl[i].name));
}

/* ------------------------------------------------------------------ */
/* Character input                                                    */
/* ------------------------------------------------------------------ */

void reader_init_string(Reader *r, const char *s, size_t len)
{
    memset(r, 0, sizeof(*r));
    r->str = s;
    r->len = len;
    r->line = 1;
    r->name = "string";
}

void reader_init_file(Reader *r, FILE *f, const char *name)
{
    memset(r, 0, sizeof(*r));
    r->file = f;
    r->line = 1;
    r->name = name ? name : "stream";
}

static int rd_getc(Reader *r)
{
    int c;
    if (r->npush) { c = r->pushback[--r->npush]; }
    else if (r->file) { c = fgetc(r->file); }
    else c = (r->pos < r->len) ? (unsigned char)r->str[r->pos++] : EOF;
    if (c == '\n') r->line++;
    return c;
}

static void rd_ungetc(Reader *r, int c)
{
    if (c == EOF) return;
    if (c == '\n') r->line--;
    r->pushback[r->npush++] = c;
}

/* ------------------------------------------------------------------ */
/* Tokeniser                                                          */
/* ------------------------------------------------------------------ */

enum { TK_ATOM, TK_VAR, TK_INT, TK_FLT, TK_STR, TK_BQ, TK_PUNCT, TK_END, TK_EOF };

typedef struct {
    int   kind;
    int   atom;          /* TK_ATOM/TK_VAR: name; TK_PUNCT: the character */
    long long ival;
    double fval;
    char *text;          /* TK_STR/TK_BQ payload */
    size_t tlen;
    int   quoted;
    int   layout;        /* layout seen before this token */
    int   func;          /* immediately followed by '(' */
} Token;

typedef struct {
    Reader *r;
    Token   tok;
    struct { int name; Term *var; int count; } *vars;
    int     nvars, cvars;
    char   *buf;
    size_t  buflen, bufcap;
    char    err[256];
    int     errline;
} Parser;

static void buf_reset(Parser *p) { p->buflen = 0; }

static void buf_put(Parser *p, int c)
{
    if (p->buflen + 2 > p->bufcap) {
        p->bufcap = p->bufcap ? p->bufcap * 2 : 128;
        p->buf = (char *)realloc(p->buf, p->bufcap);
    }
    p->buf[p->buflen++] = (char)c;
    p->buf[p->buflen] = 0;
}

static void buf_put_utf8(Parser *p, long code)
{
    if (code < 0x80) buf_put(p, (int)code);
    else if (code < 0x800) {
        buf_put(p, 0xC0 | (int)(code >> 6));
        buf_put(p, 0x80 | (int)(code & 0x3F));
    } else if (code < 0x10000) {
        buf_put(p, 0xE0 | (int)(code >> 12));
        buf_put(p, 0x80 | (int)((code >> 6) & 0x3F));
        buf_put(p, 0x80 | (int)(code & 0x3F));
    } else {
        buf_put(p, 0xF0 | (int)(code >> 18));
        buf_put(p, 0x80 | (int)((code >> 12) & 0x3F));
        buf_put(p, 0x80 | (int)((code >> 6) & 0x3F));
        buf_put(p, 0x80 | (int)(code & 0x3F));
    }
}

static int syntax_err(Parser *p, const char *msg)
{
    snprintf(p->err, sizeof(p->err), "%s", msg);
    p->errline = p->r->line;
    return -1;
}

static int is_symbol_char(int c)
{
    return c != EOF && c != 0 && strchr("+-*/\\^<>=~:.?@#&$", c) != NULL;
}

static int is_alpha_char(int c)
{
    return c != EOF && (isalnum(c) || c == '_' || c >= 0x80);
}

/* Skips layout and comments.  Returns 1 if any layout was skipped. */
static int skip_layout(Parser *p)
{
    Reader *r = p->r;
    int c, seen = 0;
    for (;;) {
        c = rd_getc(r);
        if (c == EOF) return seen;
        if (isspace(c)) { seen = 1; continue; }
        if (c == '%') {
            seen = 1;
            while ((c = rd_getc(r)) != EOF && c != '\n') ;
            continue;
        }
        if (c == '/') {
            int d = rd_getc(r);
            if (d == '*') {
                int prev = 0;
                seen = 1;
                for (;;) {
                    c = rd_getc(r);
                    if (c == EOF) return seen;
                    if (prev == '*' && c == '/') break;
                    prev = c;
                }
                continue;
            }
            rd_ungetc(r, d);
            rd_ungetc(r, c);
            return seen;
        }
        rd_ungetc(r, c);
        return seen;
    }
}

/* Reads one escape sequence after a backslash.  Returns the character
   code, -2 for "produced nothing" (line continuation) or -1 on error. */
static long read_escape(Parser *p)
{
    Reader *r = p->r;
    int c = rd_getc(r);
    long v = 0;

    switch (c) {
    case 'a': return 7;
    case 'b': return 8;
    case 'f': return 12;
    case 'n': return 10;
    case 'r': return 13;
    case 't': return 9;
    case 'v': return 11;
    case 'e': return 27;
    case 's': return ' ';
    case '0': case '1': case '2': case '3':
    case '4': case '5': case '6': case '7':
        v = c - '0';
        for (;;) {
            c = rd_getc(r);
            if (c >= '0' && c <= '7') v = v * 8 + (c - '0');
            else break;
        }
        if (c != '\\') rd_ungetc(r, c);
        return v;
    case 'x':
        for (;;) {
            c = rd_getc(r);
            if (isdigit(c)) v = v * 16 + (c - '0');
            else if (c >= 'a' && c <= 'f') v = v * 16 + (c - 'a' + 10);
            else if (c >= 'A' && c <= 'F') v = v * 16 + (c - 'A' + 10);
            else break;
        }
        if (c != '\\') rd_ungetc(r, c);
        return v;
    case '\\': return '\\';
    case '\'': return '\'';
    case '"':  return '"';
    case '`':  return '`';
    case '\n': return -2;
    case EOF:  syntax_err(p, "unexpected end of file in escape"); return -1;
    default:
        syntax_err(p, "undefined escape sequence");
        return -1;
    }
}

/* Reads the body of a quoted item; `q` is the closing quote. */
static int read_quoted(Parser *p, int q)
{
    Reader *r = p->r;
    int c;
    buf_reset(p);
    for (;;) {
        c = rd_getc(r);
        if (c == EOF) return syntax_err(p, "unterminated quoted text");
        if (c == q) {
            int d = rd_getc(r);
            if (d == q) { buf_put(p, q); continue; }
            rd_ungetc(r, d);
            return 0;
        }
        if (c == '\\') {
            long v = read_escape(p);
            if (v == -1) return -1;
            if (v == -2) continue;
            buf_put_utf8(p, v);
            continue;
        }
        buf_put(p, c);
    }
}

static int read_number(Parser *p, Token *t, int first)
{
    Reader *r = p->r;
    int c;
    long long v = 0;

    if (first == '0') {
        c = rd_getc(r);
        if (c == '\'') {
            int d = rd_getc(r);
            if (d == '\\') {
                long e = read_escape(p);
                if (e == -1) return -1;
                if (e == -2) return syntax_err(p, "bad character code");
                t->kind = TK_INT; t->ival = e;
                return 0;
            }
            if (d == '\'') {
                int e = rd_getc(r);
                if (e != '\'') rd_ungetc(r, e);
                t->kind = TK_INT; t->ival = '\'';
                return 0;
            }
            if (d == EOF) return syntax_err(p, "bad character code");
            /* Decode a UTF-8 sequence into one code point. */
            if (d >= 0xC0) {
                int extra = d >= 0xF0 ? 3 : d >= 0xE0 ? 2 : 1;
                long code = d & (0x3F >> extra);
                int i;
                for (i = 0; i < extra; i++) {
                    int e = rd_getc(r);
                    if (e == EOF) break;
                    code = (code << 6) | (e & 0x3F);
                }
                t->kind = TK_INT; t->ival = code;
                return 0;
            }
            t->kind = TK_INT; t->ival = d;
            return 0;
        }
        if (c == 'x' || c == 'o' || c == 'b') {
            int base = c == 'x' ? 16 : c == 'o' ? 8 : 2, any = 0;
            for (;;) {
                int d = rd_getc(r), dv;
                if (isdigit(d)) dv = d - '0';
                else if (isalpha(d)) dv = tolower(d) - 'a' + 10;
                else { rd_ungetc(r, d); break; }
                if (dv >= base) { rd_ungetc(r, d); break; }
                v = v * base + dv;
                any = 1;
            }
            if (!any) return syntax_err(p, "illegal number");
            t->kind = TK_INT; t->ival = v;
            return 0;
        }
        rd_ungetc(r, c);
    }

    buf_reset(p);
    buf_put(p, first);
    for (;;) {
        c = rd_getc(r);
        if (isdigit(c)) { buf_put(p, c); continue; }
        if (c == '_') {                     /* 1_000_000 digit grouping */
            int d = rd_getc(r);
            rd_ungetc(r, d);
            if (isdigit(d)) continue;
        }
        break;
    }
    /* Fractional part: only if a digit follows the dot. */
    if (c == '.') {
        int d = rd_getc(r);
        if (isdigit(d)) {
            buf_put(p, '.');
            buf_put(p, d);
            for (;;) {
                c = rd_getc(r);
                if (!isdigit(c)) break;
                buf_put(p, c);
            }
        } else {
            rd_ungetc(r, d);
            rd_ungetc(r, c);
            c = EOF;
            goto integer;
        }
    }
    if (c == 'e' || c == 'E') {
        int d = rd_getc(r), e = EOF;
        if (d == '+' || d == '-') { e = rd_getc(r); }
        if (isdigit(d) || isdigit(e)) {
            buf_put(p, 'e');
            if (e != EOF) { buf_put(p, d); buf_put(p, e); }
            else buf_put(p, d);
            for (;;) {
                c = rd_getc(r);
                if (!isdigit(c)) break;
                buf_put(p, c);
            }
        } else {
            if (e != EOF) rd_ungetc(r, e);
            rd_ungetc(r, d);
        }
    }
    if (c != EOF) rd_ungetc(r, c);

    if (strpbrk(p->buf, ".e")) {
        t->kind = TK_FLT;
        t->fval = strtod(p->buf, NULL);
    } else {
integer:
        t->kind = TK_INT;
        errno = 0;
        t->ival = strtoll(p->buf, NULL, 10);
        if (errno == ERANGE) {
            t->kind = TK_FLT;
            t->fval = strtod(p->buf, NULL);
        }
    }
    return 0;
}

static int next_token(Parser *p)
{
    Reader *r = p->r;
    Token *t = &p->tok;
    int c, d;

    memset(t, 0, sizeof(*t));
    t->layout = skip_layout(p);
    c = rd_getc(r);
    if (c == EOF) { t->kind = TK_EOF; return 0; }

    if (isdigit(c)) {
        if (read_number(p, t, c) < 0) return -1;
        goto done;
    }
    if (c == '_' || isupper(c)) {
        buf_reset(p);
        buf_put(p, c);
        while (is_alpha_char(c = rd_getc(r))) buf_put(p, c);
        rd_ungetc(r, c);
        t->kind = TK_VAR;
        t->atom = intern_n(p->buf, p->buflen);
        goto done;
    }
    if (islower(c) || c >= 0x80) {
        buf_reset(p);
        buf_put(p, c);
        while (is_alpha_char(c = rd_getc(r))) buf_put(p, c);
        rd_ungetc(r, c);
        t->kind = TK_ATOM;
        t->atom = intern_n(p->buf, p->buflen);
        goto done;
    }
    if (c == '\'') {
        if (read_quoted(p, '\'') < 0) return -1;
        t->kind = TK_ATOM;
        t->quoted = 1;
        t->atom = intern_n(p->buf ? p->buf : "", p->buflen);
        goto done;
    }
    if (c == '"' || c == '`') {
        if (read_quoted(p, c) < 0) return -1;
        t->kind = c == '"' ? TK_STR : TK_BQ;
        t->text = (char *)malloc(p->buflen + 1);
        memcpy(t->text, p->buf ? p->buf : "", p->buflen);
        t->text[p->buflen] = 0;
        t->tlen = p->buflen;
        goto done;
    }
    if (strchr("()[]{},|", c)) {
        t->kind = TK_PUNCT;
        t->atom = c;
        goto done;
    }
    if (c == '!' || c == ';') {
        t->kind = TK_ATOM;
        t->atom = intern_n((char[]){ (char)c }, 1);
        goto done;
    }
    if (is_symbol_char(c)) {
        buf_reset(p);
        buf_put(p, c);
        while (is_symbol_char(c = rd_getc(r))) buf_put(p, c);
        rd_ungetc(r, c);
        if (p->buflen == 1 && p->buf[0] == '.') {
            /* A lone dot followed by layout or EOF ends the clause. */
            if (c == EOF || isspace(c) || c == '%') {
                if (c != EOF) rd_getc(r);       /* consume the layout char */
                t->kind = TK_END;
                return 0;
            }
        }
        t->kind = TK_ATOM;
        t->atom = intern_n(p->buf, p->buflen);
        goto done;
    }
    {
        char msg[64];
        snprintf(msg, sizeof(msg), "illegal character (code %d)", c);
        return syntax_err(p, msg);
    }

done:
    if (t->kind == TK_ATOM) {
        d = rd_getc(r);
        if (d == '(') t->func = 1;      /* functor notation: no layout allowed */
        rd_ungetc(r, d);
    }
    return 0;
}

/* ------------------------------------------------------------------ */
/* Parser                                                             */
/* ------------------------------------------------------------------ */

static Term *var_for(Parser *p, int name)
{
    int i;
    if (atom_len(name) == 1 && atom_name(name)[0] == '_') return mk_var();
    for (i = 0; i < p->nvars; i++)
        if (p->vars[i].name == name) { p->vars[i].count++; return p->vars[i].var; }
    if (p->nvars == p->cvars) {
        p->cvars = p->cvars ? p->cvars * 2 : 16;
        p->vars = realloc(p->vars, p->cvars * sizeof(*p->vars));
    }
    p->vars[p->nvars].name = name;
    p->vars[p->nvars].var = mk_var();
    p->vars[p->nvars].count = 1;
    return p->vars[p->nvars++].var;
}

static int parse(Parser *p, int maxprec, Term **out, int *outprec);
static int parse_arglist(Parser *p, Term **args, int *n, int max);
static int expect_punct(Parser *p, int c, const char *what);
static int atom_or_compound(Parser *p, int atom, Term **out);

static int expect_punct(Parser *p, int c, const char *what)
{
    if (p->tok.kind != TK_PUNCT || p->tok.atom != c)
        return syntax_err(p, what);
    return next_token(p);
}

static int parse_arglist(Parser *p, Term **args, int *n, int max)
{
    for (;;) {
        Term *a;
        if (*n >= max) return syntax_err(p, "too many arguments");
        if (parse(p, 999, &a, NULL) < 0) return -1;
        args[(*n)++] = a;
        if (p->tok.kind == TK_PUNCT && p->tok.atom == ',') {
            if (next_token(p) < 0) return -1;
            continue;
        }
        return 0;
    }
}

static int parse_list(Parser *p, Term **out)
{
    Term *items[4096], *tail;
    int n = 0, i;

    if (p->tok.kind == TK_PUNCT && p->tok.atom == ']') {
        if (next_token(p) < 0) return -1;
        return atom_or_compound(p, a_nil, out);
    }
    if (parse_arglist(p, items, &n, 4096) < 0) return -1;
    tail = mk_atom(a_nil);
    if (p->tok.kind == TK_PUNCT && p->tok.atom == '|') {
        if (next_token(p) < 0) return -1;
        if (parse(p, 999, &tail, NULL) < 0) return -1;
    }
    if (expect_punct(p, ']', "expected ]") < 0) return -1;
    for (i = n - 1; i >= 0; i--) tail = mk_cons(items[i], tail);
    *out = tail;
    return 0;
}

/* An atom directly followed by '(' is a functor: this covers []( ) and {}( ). */
static int atom_or_compound(Parser *p, int atom, Term **out)
{
    if (p->tok.kind == TK_PUNCT && p->tok.atom == '(' && !p->tok.layout) {
        Term *args[MAX_ARITY], *s;
        int n = 0, i;
        if (next_token(p) < 0) return -1;
        if (parse_arglist(p, args, &n, MAX_ARITY) < 0) return -1;
        if (expect_punct(p, ')', "expected ) in arguments") < 0) return -1;
        s = mk_str(atom, n);
        for (i = 0; i < n; i++) ARG(s, i) = args[i];
        *out = s;
        return 0;
    }
    *out = mk_atom(atom);
    return 0;
}

static Term *make_string_term(Parser *p, Token *t)
{
    (void)p;
    switch (m_flag_double_quotes) {
    case DQ_CHARS: return mk_chars(t->text, t->tlen);
    case DQ_ATOM:  return mk_atom(intern_n(t->text, t->tlen));
    default:       return mk_codes(t->text, t->tlen);
    }
}

/* Can the current token begin a term? */
static int can_start_term(Parser *p)
{
    Token *t = &p->tok;
    switch (t->kind) {
    case TK_INT: case TK_FLT: case TK_VAR: case TK_STR: case TK_BQ:
        return 1;
    case TK_PUNCT:
        return t->atom == '(' || t->atom == '[' || t->atom == '{';
    case TK_ATOM: {
        int prec, lp, rp;
        if (t->func || t->quoted) return 1;
        /* An infix-only operator cannot start a term. */
        if (op_infix(t->atom, &prec, &lp, &rp) && !op_prefix(t->atom, &prec, &lp))
            return 0;
        return 1;
    }
    default:
        return 0;
    }
}

static int parse_primary(Parser *p, int maxprec, Term **out, int *outprec)
{
    Token t = p->tok;
    int prec = 0;

    switch (t.kind) {
    case TK_INT:
        if (next_token(p) < 0) return -1;
        *out = mk_int(t.ival);
        break;
    case TK_FLT:
        if (next_token(p) < 0) return -1;
        *out = mk_float(t.fval);
        break;
    case TK_VAR:
        if (next_token(p) < 0) return -1;
        *out = var_for(p, t.atom);
        break;
    case TK_STR: case TK_BQ: {
        Term *s;
        if (t.kind == TK_BQ) s = mk_codes(t.text, t.tlen);
        else s = make_string_term(p, &t);
        free(t.text);
        if (next_token(p) < 0) return -1;
        *out = s;
        break;
    }
    case TK_PUNCT:
        switch (t.atom) {
        case '(':
            if (next_token(p) < 0) return -1;
            if (parse(p, 1200, out, NULL) < 0) return -1;
            if (expect_punct(p, ')', "expected )") < 0) return -1;
            break;
        case '[':
            if (next_token(p) < 0) return -1;
            if (parse_list(p, out) < 0) return -1;
            break;
        case '{':
            if (next_token(p) < 0) return -1;
            if (p->tok.kind == TK_PUNCT && p->tok.atom == '}') {
                if (next_token(p) < 0) return -1;
                if (atom_or_compound(p, a_curly, out) < 0) return -1;
            } else {
                Term *inner;
                if (parse(p, 1200, &inner, NULL) < 0) return -1;
                if (expect_punct(p, '}', "expected }") < 0) return -1;
                *out = mk1(a_curly, inner);
            }
            break;
        default:
            return syntax_err(p, "unexpected token");
        }
        break;

    case TK_ATOM: {
        int pprec, argp;
        if (t.func) {
            Term *args[MAX_ARITY], *s;
            int n = 0, i;
            if (next_token(p) < 0) return -1;   /* the '(' */
            if (p->tok.kind != TK_PUNCT || p->tok.atom != '(')
                return syntax_err(p, "expected (");
            if (next_token(p) < 0) return -1;
            if (parse_arglist(p, args, &n, MAX_ARITY) < 0) return -1;
            if (expect_punct(p, ')', "expected ) in arguments") < 0) return -1;
            s = mk_str(t.atom, n);
            for (i = 0; i < n; i++) ARG(s, i) = args[i];
            *out = s;
            break;
        }
        if (next_token(p) < 0) return -1;

        /* Negative numeric literals: '-' directly before a number. */
        if (!t.quoted && (t.atom == a_minus || t.atom == a_plus) &&
            (p->tok.kind == TK_INT || p->tok.kind == TK_FLT) && !p->tok.layout) {
            Token num = p->tok;
            int neg = (t.atom == a_minus);
            if (next_token(p) < 0) return -1;
            if (num.kind == TK_INT) *out = mk_int(neg ? -num.ival : num.ival);
            else *out = mk_float(neg ? -num.fval : num.fval);
            break;
        }

        if (!t.quoted && op_prefix(t.atom, &pprec, &argp) && can_start_term(p)) {
            Term *arg;
            if (pprec > maxprec) {
                /* Try the reduced priority permitted for the operand. */
                pprec = maxprec;
                argp = maxprec;
            }
            if (parse(p, argp, &arg, NULL) < 0) return -1;
            *out = mk1(t.atom, arg);
            prec = pprec;
            break;
        }
        *out = mk_atom(t.atom);
        if (!t.quoted && op_is_op(t.atom)) prec = 0;
        break;
    }
    default:
        return syntax_err(p, t.kind == TK_END ? "unexpected end of clause"
                                              : "unexpected end of file");
    }
    if (outprec) *outprec = prec;
    return 0;
}

static int parse(Parser *p, int maxprec, Term **out, int *outprec)
{
    Term *left;
    int leftprec = 0;

    if (parse_primary(p, maxprec, &left, &leftprec) < 0) return -1;

    for (;;) {
        int name = -1, prec, lp, rp;

        if (p->tok.kind == TK_ATOM) name = p->tok.atom;
        else if (p->tok.kind == TK_PUNCT && p->tok.atom == ',') name = a_comma;
        else if (p->tok.kind == TK_PUNCT && p->tok.atom == '|') name = a_bar;
        else break;

        if (op_infix(name, &prec, &lp, &rp) && prec <= maxprec && leftprec <= lp) {
            Term *right;
            if (next_token(p) < 0) return -1;
            if (parse(p, rp, &right, NULL) < 0) return -1;
            /* '|' used as an infix operator denotes disjunction. */
            if (name == a_bar && prec >= 1001) name = a_semicolon;
            left = mk2(name, left, right);
            leftprec = prec;
            continue;
        }
        if (op_postfix(name, &prec, &lp) && prec <= maxprec && leftprec <= lp) {
            if (next_token(p) < 0) return -1;
            left = mk1(name, left);
            leftprec = prec;
            continue;
        }
        break;
    }
    *out = left;
    if (outprec) *outprec = leftprec;
    return 0;
}

/* ------------------------------------------------------------------ */
/* Entry point                                                        */
/* ------------------------------------------------------------------ */

static void parser_free(Parser *p)
{
    free(p->vars);
    free(p->buf);
}

int read_term_from(Reader *r, Term **out, Term **varnames)
{
    Parser p;
    Term *t;
    int rc;

    memset(&p, 0, sizeof(p));
    p.r = r;

    if (next_token(&p) < 0) goto error;
    if (p.tok.kind == TK_EOF) {
        parser_free(&p);
        *out = mk_atom(a_end_of_file);
        if (varnames) *varnames = mk_atom(a_nil);
        return 0;
    }
    if (parse(&p, 1200, &t, NULL) < 0) goto error;
    if (p.tok.kind != TK_END) {
        syntax_err(&p, "operator expected (unterminated clause)");
        goto error;
    }
    if (varnames) {
        Term *list = mk_atom(a_nil);
        int i;
        for (i = p.nvars - 1; i >= 0; i--) {
            const char *nm = atom_name(p.vars[i].name);
            if (nm[0] == '_' && nm[1] == 0) continue;
            list = mk_cons(mk2(a_eq, mk_atom(p.vars[i].name), p.vars[i].var), list);
        }
        *varnames = list;
    }
    *out = t;
    parser_free(&p);
    return 1;

error:
    rc = p.errline;
    {
        char msg[320];
        Term *err;
        snprintf(msg, sizeof(msg), "%s:%d: %s", r->name, rc, p.err);
        /* Skip forward to the end of the offending clause. */
        while (p.tok.kind != TK_END && p.tok.kind != TK_EOF)
            if (next_token(&p) < 0) break;
        err = mk1(intern("syntax_error"), mk_atom_str(msg));
        parser_free(&p);
        pl_throw(err);
    }
    return -1;
}
