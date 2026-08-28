# -*- coding: utf-8 -*-
"""Generates docs/postmortem.html from POSTMORTEM.md.

    Run from the top of the source tree:  make doc

    The Markdown file is the source; this only chooses the page furniture and
    says where the links in it should point once published.
"""
import os
from mdpage import build

REPO = 'https://github.com/hansolovkarlsson/cprolog/blob/main/'

build(mdfile='POSTMORTEM.md',
      outfile='postmortem.html',
      title='Postmortem',
      prompt='?- postmortem',
      subtitle="Every defect this project has found in itself, what caused it, "
               "and — the part worth the paper — what found it. A 256-test suite "
               "found three of sixteen; writing the documentation found five.",
      rewrite={
          'JOURNAL.md':   os.environ.get('DOC_URL_JOURNAL') or 'journal.html',
          'CHANGELOG.md': REPO + 'CHANGELOG.md',
          'ROADMAP.md':   REPO + 'ROADMAP.md',
          'README.md':    REPO + 'README.md',
      },
      retitle={
          'JOURNAL.md':   'The journal',
          'CHANGELOG.md': 'the changelog',
      },
      footer="Rendered from `POSTMORTEM.md` at the top of the source tree, which is "
             "the source of truth; `make doc` rebuilds this page and CI "
             "fails if the two no longer match.")
