# -*- coding: utf-8 -*-
"""Shared page furniture for the generated documentation.

    Both doc/reference.html and doc/internals.html are built from this module:
    it owns the escaping helpers, the block builders, the design tokens and the
    page shell, so the two documents stay a matched pair.
"""

import html, re, io, os

def esc(s):
    return html.escape(s, quote=False)

MODE_RE = re.compile(r'(?<=[(,\s])([+\-?:@])(?=[A-Z])')

def code(s):
    """Escaped inline code with mode letters marked up."""
    return MODE_RE.sub(r'<span class="mode">\1</span>', esc(s))

def lit(s):
    """Marks text that contains literal backticks, so it is not read as code."""
    return '\x01' + s

def inline(s):
    """Escapes text, then turns `x` into inline code."""
    if s.startswith('\x01'):
        return esc(s[1:])
    if s.count('`') % 2:
        raise SystemExit('unbalanced backtick in: %r' % s)
    out, parts = [], esc(s).split('`')
    for i, p in enumerate(parts):
        out.append(p if i % 2 == 0 else '<code>%s</code>' % p)
    return ''.join(out)

def para(s):
    return '<p>%s</p>' % inline(s)

def ul(items):
    return '<ul>%s</ul>' % ''.join('<li>%s</li>' % inline(i) for i in items)

def pre(s):
    return '<pre><code>%s</code></pre>' % esc(s.strip('\n'))

def table(headers, rows, cls=''):
    h = ''.join('<th>%s</th>' % inline(x) for x in headers)
    body = []
    for r in rows:
        body.append('<tr>%s</tr>' % ''.join('<td>%s</td>' % inline(c) for c in r))
    return ('<div class="scroll"><table class="%s"><thead><tr>%s</tr></thead>'
            '<tbody>%s</tbody></table></div>' % (cls, h, ''.join(body)))

def note(kind, title, body):
    return ('<aside class="note note-%s"><span class="note-tag">%s</span>'
            '<div>%s</div></aside>' % (kind, esc(title), inline(body)))

GROUPS = []

def preds(entries):
    """entries: list of (signature, description) or ('##', 'Group name')."""
    out = ['<div class="preds">']
    for sig, desc in entries:
        if sig == '##':
            gid = 'g-' + re.sub(r'[^a-z0-9]+', '-', desc.lower()).strip('-')
            GROUPS.append((gid, desc))
            out.append('<h4 class="pred-group" id="%s">%s</h4>' % (gid, esc(desc)))
            continue
        key = esc((sig + ' ' + desc).lower().replace('"', ''))
        out.append('<div class="pred" data-key="%s">'
                   '<code class="sig">%s</code>'
                   '<div class="pdesc">%s</div></div>' % (key, code(sig), inline(desc)))
    out.append('</div>')
    return ''.join(out)


# ---------------------------------------------------------------- sections

SECTIONS = []

def section(sid, title, body):
    SECTIONS.append((sid, title, body))

def figure(svg, caption):
    return '<figure>%s<figcaption>%s</figcaption></figure>' % (svg, inline(caption))
# ---------------------------------------------------------------- page shell

CSS = """
:root {
  color-scheme: light;
  --paper:      #F6F7FA;
  --surface:    #FFFFFF;
  --ink:        #151922;
  --ink-soft:   #333C4E;
  --muted:      #5C657A;
  --rule:       #E0E4EE;
  --rule-soft:  #EDF0F6;
  --accent:     #2E3A8C;
  --accent-bg:  #ECEEF9;
  --ochre:      #8A5D0F;
  --ochre-bg:   #F7F0E1;
  --code-bg:    #F0F2F8;
  --serif: "Source Serif 4", Georgia, "Times New Roman", serif;
  --sans:  "IBM Plex Sans", system-ui, -apple-system, "Segoe UI", sans-serif;
  --mono:  "IBM Plex Mono", ui-monospace, "SF Mono", Menlo, monospace;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    color-scheme: dark;
    --paper:     #101319;
    --surface:   #161A22;
    --ink:       #DDE3EF;
    --ink-soft:  #C2CADA;
    --muted:     #8C96AC;
    --rule:      #262C39;
    --rule-soft: #1D222C;
    --accent:    #9CAAFF;
    --accent-bg: #1B2137;
    --ochre:     #DBA649;
    --ochre-bg:  #2A2317;
    --code-bg:   #1C212B;
  }
}
:root[data-theme="dark"] {
  color-scheme: dark;
  --paper:     #101319;
  --surface:   #161A22;
  --ink:       #DDE3EF;
  --ink-soft:  #C2CADA;
  --muted:     #8C96AC;
  --rule:      #262C39;
  --rule-soft: #1D222C;
  --accent:    #9CAAFF;
  --accent-bg: #1B2137;
  --ochre:     #DBA649;
  --ochre-bg:  #2A2317;
  --code-bg:   #1C212B;
}

* { box-sizing: border-box; }
html { scroll-behavior: smooth; scroll-padding-top: 1.5rem; }
@media (prefers-reduced-motion: reduce) { html { scroll-behavior: auto; } }

body {
  margin: 0;
  background: var(--paper);
  color: var(--ink);
  font-family: var(--serif);
  font-size: 17px;
  line-height: 1.62;
  -webkit-font-smoothing: antialiased;
}

/* ---- masthead ---- */
.masthead {
  border-bottom: 1px solid var(--rule);
  background: var(--surface);
}
.masthead-inner {
  max-width: 1180px;
  margin: 0 auto;
  padding: 2.4rem 2rem 2rem;
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 0.6rem 1.4rem;
}
.masthead h1 {
  font-size: clamp(1.9rem, 4vw, 2.6rem);
  font-weight: 600;
  letter-spacing: -0.015em;
  margin: 0;
  text-wrap: balance;
}
.masthead .prompt {
  font-family: var(--mono);
  font-size: 0.8rem;
  color: var(--accent);
  background: var(--accent-bg);
  padding: 0.25rem 0.55rem;
  border-radius: 3px;
  letter-spacing: 0.02em;
}
.masthead p {
  margin: 0;
  color: var(--muted);
  font-size: 1.02rem;
  max-width: 62ch;
  flex-basis: 100%;
}

/* ---- shell ---- */
.shell {
  max-width: 1180px;
  margin: 0 auto;
  padding: 0 2rem 6rem;
  display: grid;
  grid-template-columns: 250px minmax(0, 1fr);
  gap: 3.5rem;
  align-items: start;
}
@media (max-width: 940px) {
  .shell { grid-template-columns: minmax(0, 1fr); gap: 2rem; }
}

/* ---- sidebar ---- */
.rail {
  position: sticky;
  top: 0;
  max-height: 100vh;
  overflow-y: auto;
  padding: 2.2rem 0 3rem;
  font-family: var(--sans);
  font-size: 0.86rem;
}
@media (max-width: 940px) {
  .rail {
    position: static;
    max-height: none;
    border-bottom: 1px solid var(--rule);
    padding-bottom: 1.5rem;
  }
}
.rail-title {
  font-size: 0.68rem;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: var(--muted);
  margin: 0 0 0.9rem;
  font-weight: 600;
}
.rail ol { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 0.1rem; }
.rail a {
  display: block;
  padding: 0.28rem 0.6rem;
  color: var(--ink-soft);
  text-decoration: none;
  border-left: 2px solid transparent;
  border-radius: 0 3px 3px 0;
}
.rail a:hover { color: var(--accent); background: var(--rule-soft); }
.rail a.active {
  color: var(--accent);
  border-left-color: var(--accent);
  background: var(--accent-bg);
  font-weight: 500;
}
.rail .sub { margin-left: 0.6rem; }
.rail .sub a { font-size: 0.8rem; color: var(--muted); padding-block: 0.2rem; }

/* ---- main ---- */
main { padding-top: 2.2rem; min-width: 0; }
section { margin-bottom: 4rem; scroll-margin-top: 1.5rem; }
section > h2 {
  font-size: 1.55rem;
  font-weight: 600;
  letter-spacing: -0.01em;
  margin: 0 0 1.1rem;
  padding-bottom: 0.5rem;
  border-bottom: 2px solid var(--rule);
  text-wrap: balance;
}
h3 {
  font-size: 1.12rem;
  font-weight: 600;
  margin: 2.2rem 0 0.7rem;
  color: var(--ink);
}
p { margin: 0 0 1rem; max-width: 68ch; color: var(--ink-soft); }
ul { margin: 0 0 1.2rem; padding-left: 1.2rem; max-width: 68ch; color: var(--ink-soft); }
li { margin-bottom: 0.45rem; }
a { color: var(--accent); }

code {
  font-family: var(--mono);
  font-size: 0.86em;
  background: var(--code-bg);
  padding: 0.1em 0.32em;
  border-radius: 3px;
  color: var(--ink);
}
pre {
  background: var(--surface);
  border: 1px solid var(--rule);
  border-left: 3px solid var(--accent);
  border-radius: 3px;
  padding: 0.95rem 1.1rem;
  overflow-x: auto;
  margin: 0 0 1.4rem;
}
pre code {
  background: none;
  padding: 0;
  font-size: 0.83rem;
  line-height: 1.6;
  color: var(--ink-soft);
}

/* ---- tables ---- */
.scroll { overflow-x: auto; margin: 0 0 1.5rem; }
table {
  border-collapse: collapse;
  width: 100%;
  font-family: var(--sans);
  font-size: 0.87rem;
  font-variant-numeric: tabular-nums;
}
th {
  text-align: left;
  font-size: 0.68rem;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--muted);
  font-weight: 600;
  padding: 0 0.9rem 0.5rem 0;
  border-bottom: 1px solid var(--rule);
  white-space: nowrap;
}
td {
  padding: 0.5rem 0.9rem 0.5rem 0;
  border-bottom: 1px solid var(--rule-soft);
  color: var(--ink-soft);
  vertical-align: top;
}
td:last-child, th:last-child { padding-right: 0; }
table.mono1 td:first-child,
table.mono2 td:nth-child(2),
table.ops td:nth-child(3) {
  font-family: var(--mono);
  font-size: 0.82rem;
  color: var(--ink);
  white-space: nowrap;
}
table.ops td:nth-child(3) { white-space: normal; }
table.ops td:first-child { color: var(--muted); }

/* ---- predicate entries ---- */
.filter {
  display: flex;
  align-items: center;
  gap: 0.8rem;
  margin: 1.4rem 0 0.4rem;
}
.filter input {
  flex: 1 1 auto;
  min-width: 0;
  font-family: var(--mono);
  font-size: 0.85rem;
  padding: 0.55rem 0.75rem;
  color: var(--ink);
  background: var(--surface);
  border: 1px solid var(--rule);
  border-radius: 3px;
}
.filter input:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 1px;
  border-color: var(--accent);
}
.filter-count {
  font-family: var(--sans);
  font-size: 0.76rem;
  color: var(--muted);
  white-space: nowrap;
}
.preds { margin-bottom: 1rem; }
.pred-group {
  font-family: var(--sans);
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: var(--ochre);
  font-weight: 600;
  margin: 2.4rem 0 0.2rem;
  padding-bottom: 0.4rem;
  border-bottom: 1px solid var(--rule);
  scroll-margin-top: 1.5rem;
}
.pred {
  padding: 0.75rem 0 0.7rem;
  border-bottom: 1px solid var(--rule-soft);
}
.pred .sig {
  font-family: var(--mono);
  font-size: 0.85rem;
  background: none;
  padding: 0;
  color: var(--ink);
  font-weight: 500;
  display: block;
  margin-bottom: 0.25rem;
  overflow-wrap: anywhere;
}
.pred .mode { color: var(--ochre); }
.pdesc { color: var(--muted); font-size: 0.95rem; max-width: 68ch; }
.pdesc code { font-size: 0.82em; }
.pred.hidden, .pred-group.hidden { display: none; }

/* ---- notes ---- */
.note {
  display: flex;
  gap: 0.9rem;
  align-items: flex-start;
  background: var(--ochre-bg);
  border: 1px solid var(--rule);
  border-left: 3px solid var(--ochre);
  border-radius: 3px;
  padding: 0.85rem 1rem;
  margin: 0 0 1.4rem;
  font-size: 0.95rem;
  color: var(--ink-soft);
  max-width: 72ch;
}
.note-tag {
  font-family: var(--sans);
  font-size: 0.64rem;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  font-weight: 600;
  color: var(--ochre);
  white-space: nowrap;
  padding-top: 0.28rem;
  flex: 0 0 auto;
  width: 7.5rem;
}
@media (max-width: 620px) {
  .note { flex-direction: column; gap: 0.3rem; }
  .note-tag { width: auto; padding-top: 0; }
}

.visually-hidden {
  position: absolute; width: 1px; height: 1px;
  overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap;
}
a:focus-visible, .rail a:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
  border-radius: 2px;
}
/* ---- figures ---- */
figure { margin: 0 0 1.7rem; }
figure svg { max-width: 100%; height: auto; display: block; color: var(--ink-soft); }
figcaption {
  font-family: var(--sans);
  font-size: 0.8rem;
  color: var(--muted);
  margin-top: 0.6rem;
  max-width: 68ch;
  line-height: 1.5;
}
.svg-frame {
  background: var(--surface);
  border: 1px solid var(--rule);
  border-radius: 3px;
  padding: 1.1rem 1rem;
  overflow-x: auto;
}

/* ---- document switcher ---- */
.docnav {
  display: flex;
  gap: 0.4rem;
  flex-basis: 100%;
  margin-top: 0.4rem;
  font-family: var(--sans);
  font-size: 0.82rem;
}
.docnav a {
  text-decoration: none;
  color: var(--muted);
  padding: 0.22rem 0.6rem;
  border: 1px solid var(--rule);
  border-radius: 3px;
}
.docnav a:hover { color: var(--accent); border-color: var(--accent); }
.docnav a[aria-current="page"] {
  color: var(--accent);
  background: var(--accent-bg);
  border-color: var(--accent-bg);
  font-weight: 500;
}

footer {
  border-top: 1px solid var(--rule);
  margin-top: 2rem;
  padding-top: 1.2rem;
  font-family: var(--sans);
  font-size: 0.8rem;
  color: var(--muted);
}
"""

JS = """
(function () {
  var input = document.getElementById('pfilter');
  var count = document.getElementById('pcount');
  var preds = Array.prototype.slice.call(document.querySelectorAll('.pred'));
  var groups = Array.prototype.slice.call(document.querySelectorAll('.pred-group'));
  var total = preds.length;

  function report(n, filtering) {
    if (!count) return;
    count.textContent = filtering ? n + ' of ' + total + ' shown'
                                  : total + ' predicates';
  }
  report(total, false);

  if (input && count) {
    input.addEventListener('input', function () {
      var q = input.value.trim().toLowerCase();
      var shown = 0;
      preds.forEach(function (el) {
        var hit = !q || el.getAttribute('data-key').indexOf(q) !== -1;
        el.classList.toggle('hidden', !hit);
        if (hit) shown++;
      });
      groups.forEach(function (g) {
        var any = false, el = g.nextElementSibling;
        while (el && el.classList.contains('pred')) {
          if (!el.classList.contains('hidden')) { any = true; break; }
          el = el.nextElementSibling;
        }
        g.classList.toggle('hidden', !any);
      });
      report(shown, q.length > 0);
    });
  }

  /* Highlight the section the reader is in. */
  var links = {};
  Array.prototype.forEach.call(document.querySelectorAll('.rail a'), function (a) {
    links[a.getAttribute('href').slice(1)] = a;
  });
  var targets = document.querySelectorAll('section[id]');
  var current = null;
  var observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (!entry.isIntersecting) return;
      var link = links[entry.target.id];
      if (!link || link === current) return;
      if (current) current.classList.remove('active');
      link.classList.add('active');
      current = link;
    });
  }, { rootMargin: '0px 0px -75% 0px' });
  Array.prototype.forEach.call(targets, function (t) { observer.observe(t); });
})();
"""

# The two documents cross-link to each other. In a checkout they sit side by
# side, so the links are relative; when they are published as separate pages,
# each has its own URL, which is supplied through the environment:
#
#   DOC_URL_REFERENCE=... DOC_URL_INTERNALS=... make doc
#
DOCS = [('reference.html', 'Language reference', 'DOC_URL_REFERENCE'),
        ('internals.html', 'Engine internals',   'DOC_URL_INTERNALS')]

def render(title, prompt, subtitle, outfile, sub_under=None):
    """Writes one document. sub_under names the section whose predicate groups
       are listed as sub-entries in the contents rail."""
    toc = []
    for sid, sec_title, _ in SECTIONS:
        toc.append('<li><a href="#%s">%s</a></li>' % (sid, esc(sec_title)))
        if sub_under and sid == sub_under:
            subs = ''.join('<li><a href="#%s">%s</a></li>' % (gid, esc(name))
                           for gid, name in GROUPS)
            toc.append('<li><ol class="sub">%s</ol></li>' % subs)

    body = []
    for sid, sec_title, content in SECTIONS:
        body.append('<section id="%s"><h2>%s</h2>%s</section>'
                    % (sid, esc(sec_title), content))

    nav = ''.join(
        '<a href="%s"%s>%s</a>'
        % (os.environ.get(env) or fname,
           ' aria-current="page"' if fname == outfile else '', esc(name))
        for fname, name, env in DOCS)

    page = """<title>%s</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&display=swap">
<style>%s</style>
<header class="masthead">
  <div class="masthead-inner">
    <h1>%s</h1>
    <span class="prompt">%s</span>
    <p>%s</p>
    <nav class="docnav" aria-label="Documents">%s</nav>
  </div>
</header>
<div class="shell">
  <nav class="rail" aria-label="Contents">
    <p class="rail-title">Contents</p>
    <ol>%s</ol>
  </nav>
  <main>
    %s
    <footer>Generated from the interpreter's own tables and checked against the
    running system. Source: <code>src/</code> for the engine, <code>lib/boot.pl</code>
    for the library written in Prolog.</footer>
  </main>
</div>
<script>%s</script>
""" % (esc(title), CSS, esc(title), esc(prompt), inline(subtitle), nav,
       ''.join(toc), ''.join(body), JS)

    with io.open('doc/' + outfile, 'w', encoding='utf-8') as f:
        f.write(page)
    print('wrote doc/' + outfile)
