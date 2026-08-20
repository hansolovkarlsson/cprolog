# -*- coding: utf-8 -*-
"""Generates docs/index.html, the front page of the project site.

    Run from the top of the source tree:  make doc

    The HTML is generated, so edit the content here rather than in
    docs/index.html, which is overwritten. Everything quoted on the page --
    the transcript, the figures, the measurements -- comes from the running
    interpreter.
"""
import io, os
from docpage import CSS, esc, inline, FAVICON

REPO = 'https://github.com/hansolovkarlsson/cprolog'

EXTRA_CSS = """
/* ---- landing page ---- */
.hero {
  border-bottom: 1px solid var(--rule);
  background: var(--surface);
}
.hero-inner {
  max-width: 1080px;
  margin: 0 auto;
  padding: 3.2rem 2rem 2.6rem;
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 3rem;
  align-items: center;
}
@media (max-width: 900px) {
  .hero-inner { grid-template-columns: minmax(0, 1fr); gap: 2rem; padding-top: 2.4rem; }
}
.hero h1 {
  font-size: clamp(2.2rem, 5vw, 3.1rem);
  font-weight: 600;
  letter-spacing: -0.02em;
  margin: 0 0 0.7rem;
  text-wrap: balance;
}
.hero .lede {
  font-size: 1.12rem;
  color: var(--ink-soft);
  margin: 0 0 1.4rem;
  max-width: 46ch;
}
.hero .meta {
  font-family: var(--sans);
  font-size: 0.82rem;
  color: var(--muted);
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem 1.1rem;
  margin-bottom: 1.5rem;
}
.cta { display: flex; flex-wrap: wrap; gap: 0.6rem; }
.cta a {
  font-family: var(--sans);
  font-size: 0.88rem;
  text-decoration: none;
  padding: 0.5rem 1rem;
  border-radius: 3px;
  border: 1px solid var(--rule);
  color: var(--ink-soft);
}
.cta a.primary {
  background: var(--accent);
  border-color: var(--accent);
  color: var(--surface);
  font-weight: 500;
}
.cta a:hover { border-color: var(--accent); color: var(--accent); }
.cta a.primary:hover { color: var(--surface); opacity: 0.9; }

.term {
  background: var(--code-bg);
  border: 1px solid var(--rule);
  border-radius: 4px;
  padding: 1rem 1.1rem;
  overflow-x: auto;
  font-family: var(--mono);
  font-size: 0.8rem;
  line-height: 1.65;
  color: var(--ink-soft);
  white-space: pre;
}
.term .q { color: var(--accent); font-weight: 500; }
.term .c { color: var(--muted); }

.band { max-width: 1080px; margin: 0 auto; padding: 3.2rem 2rem 0; }
.band h2 {
  font-size: 0.72rem;
  font-family: var(--sans);
  text-transform: uppercase;
  letter-spacing: 0.13em;
  color: var(--muted);
  font-weight: 600;
  margin: 0 0 1.4rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--rule);
}
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.6rem 2.4rem;
}
.grid h3 { margin: 0 0 0.4rem; font-size: 1.02rem; }
.grid p { margin: 0; font-size: 0.95rem; color: var(--muted); }
.grid .fig {
  font-family: var(--mono);
  font-size: 0.78rem;
  color: var(--ochre);
  display: block;
  margin-top: 0.5rem;
}

.cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.2rem; }
.card {
  display: block;
  text-decoration: none;
  border: 1px solid var(--rule);
  border-radius: 4px;
  padding: 1.2rem 1.3rem;
  background: var(--surface);
  color: inherit;
}
.card:hover { border-color: var(--accent); }
.card h3 { margin: 0 0 0.4rem; font-size: 1.05rem; color: var(--accent); }
.card p { margin: 0; font-size: 0.92rem; color: var(--muted); }

table.plain { width: 100%; border-collapse: collapse; font-family: var(--sans); font-size: 0.88rem; }
table.plain td { padding: 0.45rem 1rem 0.45rem 0; border-bottom: 1px solid var(--rule-soft); color: var(--ink-soft); vertical-align: top; }
table.plain td:first-child { font-family: var(--mono); font-size: 0.82rem; color: var(--ink); white-space: nowrap; }

.site-footer {
  max-width: 1080px;
  margin: 3.5rem auto 0;
  padding: 1.3rem 2rem 3rem;
  border-top: 1px solid var(--rule);
  font-family: var(--sans);
  font-size: 0.8rem;
  color: var(--muted);
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem 1.5rem;
}
.site-footer a { color: var(--muted); }
"""

TRANSCRIPT = [
    ('c', '$ git clone https://github.com/hansolovkarlsson/cprolog'),
    ('c', '$ cd cprolog && make'),
    ('c', '$ ./prolog'),
    ('', 'C Prolog 1.0 -- a Prolog interpreter in C'),
    ('', 'Type help. for help, halt. to quit.'),
    ('', ''),
    ('q', '?- X = hello, atom_length(X, N).'),
    ('', 'X = hello,'),
    ('', 'N = 5.'),
    ('', ''),
    ('q', '?- member(X, [a,b,c]).'),
    ('', 'X = a ;'),
    ('', 'X = b ;'),
    ('', 'X = c ;'),
    ('', 'false.'),
    ('', ''),
    ('q', '?- findall(Y, (between(1,5,X), Y is X*X), Squares).'),
    ('', 'Squares = [1,4,9,16,25].'),
]

HIGHLIGHTS = [
    ("An engine you can read",
     "No abstract machine and no clause compiler: goals live in an explicit list, "
     "alternatives on a choice point stack, and cut is one integer carried in each "
     "goal frame. The whole solver is one file.",
     "5,300 lines of C99, no dependencies beyond libc"),
    ("Memory that behaves",
     "Backtracking rewinds the heap to a choice point's mark, a copying collector "
     "handles what backtracking cannot, and generators retry a single choice point "
     "so failure-driven loops stay flat.",
     "5M-iteration recursion: 25 MB · 1M-iteration loop: 2.8 MB"),
    ("The language, not a subset",
     "A full operator-precedence reader with user-defined operators, grammars, "
     "exceptions, bagof/setof, format/2,3, streams, first-argument indexing and "
     "UTF-8 text throughout.",
     "162 builtin predicates"),
    ("Tested like a compiler",
     "The suite runs three times: normally, with the collector forced every 1024 "
     "inferences, and under the address and undefined behaviour sanitizers. It "
     "builds warning-free under both clang and gcc.",
     "248 tests · make check · make test-asan"),
]

EXAMPLES = [
    ('examples/queens.pl', 'The N queens problem, printed as a board. All 92 solutions '
                           'for 8 queens take 9 ms.'),
    ('examples/zebra.pl', "Einstein's riddle, solved by plain unification and "
                          'backtracking in under a millisecond.'),
    ('examples/calc.pl', 'A calculator: a grammar that reads an arithmetic expression '
                         'and evaluates it as it parses.'),
    ('examples/hanoi.pl', 'Towers of Hanoi, the first recursive program most people '
                          'write in Prolog.'),
    ('examples/family.pl', 'Facts, rules and queries — the place to start if Prolog is '
                           'new to you.'),
]

def transcript():
    rows = []
    for kind, text in TRANSCRIPT:
        if kind:
            rows.append('<span class="%s">%s</span>' % (kind, esc(text)))
        else:
            rows.append(esc(text))
    return '<div class="term">%s</div>' % '\n'.join(rows)

def render():
    highlights = ''.join(
        '<div><h3>%s</h3><p>%s</p><span class="fig">%s</span></div>'
        % (esc(t), inline(b), esc(f)) for t, b, f in HIGHLIGHTS)

    cards = ''.join([
        '<a class="card" href="%s"><h3>Tutorial</h3><p>New to Prolog, or returning to '
        'it? Level 1 covers facts, rules, unification and the search; level 2 '
        'covers lists and collecting answers. Every query is one you run against '
        'this interpreter.</p></a>'
        % (os.environ.get('DOC_URL_TUTORIAL1') or 'tutorial-1.html'),
        '<a class="card" href="%s"><h3>Language reference</h3><p>Syntax, control, '
        'arithmetic, every builtin predicate, grammars, errors, and where it parts '
        'company with the ISO standard.</p></a>'
        % (os.environ.get('DOC_URL_REFERENCE') or 'reference.html'),
        '<a class="card" href="%s"><h3>Engine internals</h3><p>Terms in memory, the '
        'solver loop, choice points and cut, the three memory regions and the '
        'collector — with the measurements and the bugs the design produced.</p></a>'
        % (os.environ.get('DOC_URL_INTERNALS') or 'internals.html'),
    ])

    examples = ''.join('<tr><td>%s</td><td>%s</td></tr>' % (esc(f), inline(d))
                       for f, d in EXAMPLES)

    return """<title>C Prolog</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="A Prolog interpreter written from scratch in C99: reader, engine, copying garbage collector and library, with no dependencies beyond libc.">
<!--FAVICON-->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&display=swap">
<style>%s%s</style>

<header class="hero">
  <div class="hero-inner">
    <div>
      <h1>C Prolog</h1>
      <p class="lede">A Prolog interpreter written from scratch in C99 — reader,
        engine, garbage collector and library, with no dependencies beyond libc.</p>
      <div class="meta">
        <span>MIT licensed</span><span>C99, no dependencies</span>
        <span>macOS, Linux, BSD</span>
      </div>
      <nav class="cta">
        <a class="primary" href="%s">Start the tutorial</a>
        <a href="%s">Get the source</a>
        <a href="%s">Language reference</a>
        <a href="%s">Engine internals</a>
      </nav>
    </div>
    <div>%s</div>
  </div>
</header>

<section class="band">
  <h2>What it is</h2>
  <div class="grid">%s</div>
</section>

<section class="band">
  <h2>Build and run</h2>
  <div class="cards" style="grid-template-columns: minmax(0,1fr);">
    <div class="card">
      <p style="font-family: var(--mono); font-size: 0.82rem; color: var(--ink); line-height: 1.8;">
make<br>./prolog<br>make check<span style="color: var(--muted)">      # 248 tests, twice</span><br>make examples</p>
    </div>
  </div>
  <p style="margin-top: 1rem; color: var(--muted); font-size: 0.92rem; max-width: 68ch;">
    Nothing to configure and nothing to install: a C99 compiler and make are the
    whole toolchain. <code>make install</code> puts the binary in
    <code>/usr/local/bin</code>.</p>
</section>

<section class="band">
  <h2>Documentation</h2>
  <div class="cards">%s</div>
</section>

<section class="band">
  <h2>Examples in the repository</h2>
  <table class="plain"><tbody>%s</tbody></table>
</section>

<footer class="site-footer">
  <span>MIT licensed</span>
  <a href="%s">Source on GitHub</a>
  <a href="%s/blob/main/ROADMAP.md">Roadmap</a>
  <span>Documentation generated from the interpreter's own tables.</span>
</footer>
""" % (CSS, EXTRA_CSS,
       os.environ.get('DOC_URL_TUTORIAL1') or 'tutorial-1.html',
       REPO,
       os.environ.get('DOC_URL_REFERENCE') or 'reference.html',
       os.environ.get('DOC_URL_INTERNALS') or 'internals.html',
       transcript(), highlights, cards, examples, REPO, REPO)

with io.open('docs/index.html', 'w', encoding='utf-8') as f:
    f.write(render().replace('<!--FAVICON-->', FAVICON))
print('wrote docs/index.html')
