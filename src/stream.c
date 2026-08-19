/* stream.c -- a small stream layer: files, the standard streams and
   in-memory sinks used by format/3 and with_output_to/2. */
#include "prolog.h"

struct PStream {
    FILE  *f;
    char  *buf;             /* in-memory sink */
    size_t len, cap;
    int    in_use;
    int    is_input;
    int    alias;           /* atom, or -1 */
    char  *name;
    int    peeked;          /* pushed-back character, or -2 */
    Reader reader;
    int    reader_ready;
};

#define MAX_STREAMS 64
static struct PStream streams[MAX_STREAMS];
static int cur_out = 1, cur_in = 0;
static int a_stream_functor;

void stream_init(void)
{
    a_stream_functor = intern("$stream");
    memset(streams, 0, sizeof(streams));
    streams[0].f = stdin;  streams[0].in_use = 1; streams[0].is_input = 1;
    streams[0].alias = intern("user_input");  streams[0].name = "user_input";
    streams[1].f = stdout; streams[1].in_use = 1;
    streams[1].alias = intern("user_output"); streams[1].name = "user_output";
    streams[2].f = stderr; streams[2].in_use = 1;
    streams[2].alias = intern("user_error");  streams[2].name = "user_error";
    streams[0].peeked = streams[1].peeked = streams[2].peeked = -2;
}

int stream_index(PStream *s) { return (int)(s - streams); }

PStream *stream_by_index(int i)
{
    if (i < 0 || i >= MAX_STREAMS || !streams[i].in_use) return NULL;
    return &streams[i];
}

Term *stream_term(PStream *s)
{
    return mk1(a_stream_functor, mk_int(stream_index(s)));
}

PStream *stream_of(Term *t)
{
    int i;
    t = deref(t);
    if (t->tag == TAG_STR && FN(t) == a_stream_functor && AR(t) == 1) {
        Term *n = deref(ARG(t, 0));
        if (n->tag == TAG_INT) return stream_by_index((int)IV(n));
        return NULL;
    }
    if (t->tag == TAG_ATOM) {
        for (i = 0; i < MAX_STREAMS; i++)
            if (streams[i].in_use && streams[i].alias == AT(t))
                return &streams[i];
    }
    return NULL;
}

PStream *stream_current_output(void) { return &streams[cur_out]; }
PStream *stream_current_input(void)  { return &streams[cur_in]; }
void     stream_set_output(PStream *s) { cur_out = stream_index(s); }
void     stream_set_input(PStream *s)  { cur_in = stream_index(s); }

FILE *stream_file(PStream *s) { return s->f; }
int   stream_is_input(PStream *s) { return s->is_input; }

PStream *stream_open(const char *path, const char *mode, int is_input)
{
    int i;
    FILE *f = fopen(path, mode);
    if (!f) return NULL;
    for (i = 3; i < MAX_STREAMS; i++) if (!streams[i].in_use) break;
    if (i == MAX_STREAMS) { fclose(f); return NULL; }
    memset(&streams[i], 0, sizeof(streams[i]));
    streams[i].f = f;
    streams[i].in_use = 1;
    streams[i].is_input = is_input;
    streams[i].alias = -1;
    streams[i].name = strdup(path);
    streams[i].peeked = -2;
    return &streams[i];
}

/* An in-memory output stream; the text is collected in a buffer. */
PStream *stream_open_sink(void)
{
    int i;
    for (i = 3; i < MAX_STREAMS; i++) if (!streams[i].in_use) break;
    if (i == MAX_STREAMS) return NULL;
    memset(&streams[i], 0, sizeof(streams[i]));
    streams[i].in_use = 1;
    streams[i].alias = -1;
    streams[i].cap = 256;
    streams[i].buf = (char *)malloc(streams[i].cap);
    streams[i].buf[0] = 0;
    streams[i].peeked = -2;
    return &streams[i];
}

const char *stream_sink_text(PStream *s, size_t *len)
{
    if (len) *len = s->len;
    return s->buf ? s->buf : "";
}

int stream_close(PStream *s)
{
    int i = stream_index(s);
    if (i < 3) return 0;                       /* never close the std streams */
    if (cur_out == i) cur_out = 1;
    if (cur_in == i) cur_in = 0;
    if (s->f) fclose(s->f);
    free(s->buf);
    if (s->name) free(s->name);
    memset(s, 0, sizeof(*s));
    return 1;
}

void stream_write(PStream *s, const char *buf, size_t n)
{
    if (s->f) { fwrite(buf, 1, n, s->f); return; }
    if (s->len + n + 1 > s->cap) {
        while (s->len + n + 1 > s->cap) s->cap = s->cap ? s->cap * 2 : 256;
        s->buf = (char *)realloc(s->buf, s->cap);
    }
    memcpy(s->buf + s->len, buf, n);
    s->len += n;
    s->buf[s->len] = 0;
}

int stream_getc(PStream *s)
{
    if (s->peeked != -2) { int c = s->peeked; s->peeked = -2; return c; }
    if (s->f) return fgetc(s->f);
    return EOF;
}

Reader *stream_reader(PStream *s)
{
    if (!s->reader_ready) {
        reader_init_file(&s->reader, s->f, s->name ? s->name : "stream");
        s->reader_ready = 1;
    }
    return &s->reader;
}
