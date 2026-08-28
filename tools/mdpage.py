# -*- coding: utf-8 -*-
"""Renders one of the project's Markdown documents as a site page.

    The Markdown file is the source of truth: JOURNAL.md and POSTMORTEM.md are
    read in a checkout, and this module turns them into pages built from the
    same shell as the reference and the tutorials, so the two cannot drift.
    CI regenerates docs/ and fails on any difference, which is what enforces it.

    Only the subset those two documents use is supported -- headings,
    paragraphs, bullet and numbered lists, tables, fenced code -- and anything
    outside it raises rather than being silently dropped. The inline subset
    (`code`, **bold**, *emphasis*, [links](target)) is docpage.inline's.
"""

import io, re, os
from docpage import esc, inline, para, ul, pre, table, section, render

H1_RE    = re.compile(r'^# (.*)$')
H2_RE    = re.compile(r'^## (.*)$')
H3_RE    = re.compile(r'^### (.*)$')
BULLET_RE = re.compile(r'^- (.*)$')
NUMBER_RE = re.compile(r'^\d+\. (.*)$')
FENCE_RE  = re.compile(r'^```')


def split_row(line):
    """Splits a table row on |, ignoring bars inside a code span."""
    cells, cur, in_code = [], [], False
    for ch in line:
        if ch == '`':
            in_code = not in_code
        if ch == '|' and not in_code:
            cells.append(''.join(cur))
            cur = []
            continue
        cur.append(ch)
    cells.append(''.join(cur))
    cells = [c.strip() for c in cells]
    # A row is written |a|b|, so the outer bars leave an empty cell each end.
    if cells and not cells[0]:
        cells.pop(0)
    if cells and not cells[-1]:
        cells.pop()
    return cells


def blocks(text, source):
    """Turns Markdown into a list of (kind, payload) blocks."""
    out = []
    lines = text.split('\n')
    i, n = 0, len(lines)

    def fail(msg):
        raise SystemExit('%s:%d: %s' % (source, i + 1, msg))

    while i < n:
        line = lines[i]

        if not line.strip():
            i += 1
            continue

        m = H1_RE.match(line)
        if m:
            out.append(('h1', m.group(1)))
            i += 1
            continue

        m = H2_RE.match(line)
        if m:
            out.append(('h2', m.group(1)))
            i += 1
            continue

        m = H3_RE.match(line)
        if m:
            out.append(('h3', m.group(1)))
            i += 1
            continue

        if FENCE_RE.match(line):
            i += 1
            start = i
            while i < n and not FENCE_RE.match(lines[i]):
                i += 1
            if i >= n:
                fail('unterminated code fence')
            out.append(('pre', '\n'.join(lines[start:i])))
            i += 1
            continue

        if line.startswith('|'):
            rows = []
            while i < n and lines[i].startswith('|'):
                rows.append(split_row(lines[i]))
                i += 1
            if len(rows) < 2 or not all(set(c) <= set('- :') for c in rows[1]):
                fail('a table needs a header and a --- separator row')
            out.append(('table', (rows[0], rows[2:])))
            continue

        m = BULLET_RE.match(line) or NUMBER_RE.match(line)
        if m:
            kind = 'ul' if BULLET_RE.match(line) else 'ol'
            items, cur = [], [m.group(1)]
            i += 1
            while i < n:
                nxt = lines[i]
                if not nxt.strip():
                    break
                m2 = BULLET_RE.match(nxt) if kind == 'ul' else NUMBER_RE.match(nxt)
                if m2:
                    items.append(' '.join(cur))
                    cur = [m2.group(1)]
                elif nxt.startswith('  '):
                    cur.append(nxt.strip())
                else:
                    fail('list item continuation must be indented')
                i += 1
            items.append(' '.join(cur))
            out.append((kind, items))
            continue

        # Anything else is a paragraph, running to the next blank line or the
        # next line that starts a block of its own.
        buf = []
        while i < n and lines[i].strip():
            if (H2_RE.match(lines[i]) or H3_RE.match(lines[i])
                    or lines[i].startswith('|') or FENCE_RE.match(lines[i])
                    or BULLET_RE.match(lines[i])):
                break
            buf.append(lines[i].strip())
            i += 1
        out.append(('p', ' '.join(buf)))

    return out


def to_html(kind, payload):
    if kind == 'p':
        return para(payload)
    if kind == 'h3':
        return '<h3>%s</h3>' % inline(payload)
    if kind == 'ul':
        return ul(payload)
    if kind == 'ol':
        return '<ol>%s</ol>' % ''.join('<li>%s</li>' % inline(x) for x in payload)
    if kind == 'table':
        return table(payload[0], payload[1])
    if kind == 'pre':
        return pre(payload)
    raise SystemExit('no renderer for block %r' % kind)


def slug(s):
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')


def build(mdfile, outfile, title, prompt, subtitle, rewrite=None, retitle=None,
          footer=None):
    """Reads mdfile and writes docs/outfile. rewrite maps a link target in the
       Markdown to the one the published page should use; retitle does the same
       for the link text, since a file name reads oddly once it is a page."""
    with io.open(mdfile, encoding='utf-8') as f:
        text = f.read()

    if rewrite or retitle:
        rewrite, retitle = rewrite or {}, retitle or {}

        def fix(m):
            label, target = m.group(1), m.group(2)
            return '[%s](%s)' % (retitle.get(target, label),
                                 rewrite.get(target, target))
        text = re.sub(r'\[([^\]]+)\]\(([^)\s]+)\)', fix, text)

    lead, current, body = [], None, []

    def flush():
        if current is not None:
            section(slug(current), current, ''.join(body))

    for kind, payload in blocks(text, mdfile):
        if kind == 'h1':
            continue                      # the masthead already carries it
        if kind == 'h2':
            flush()
            current, body = payload, []
            continue
        html = to_html(kind, payload)
        (body if current is not None else lead).append(html)
    flush()

    kwargs = {} if footer is None else {'footer': footer}
    render(title=title, prompt=prompt, subtitle=subtitle, outfile=outfile,
           lead='<div class="lead">%s</div>' % ''.join(lead) if lead else '',
           **kwargs)
