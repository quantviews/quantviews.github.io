# -*- coding: utf-8 -*-
"""Post-migration frontmatter tidy-up.

* rewrites ``\\uXXXX``-escaped alias paths as plain Cyrillic
* trims stray leading/trailing whitespace and double spaces out of
  ``title:`` / ``description:`` values

    python scripts/tidy_frontmatter.py
"""
import re
import io
import glob
import json

QUOTED = r'"(?:[^"\\]|\\.)*"'
ALIAS_LINE = re.compile(r'^  - (' + QUOTED + r')$', re.M)
FIELD_LINE = re.compile(r'^(title|description):[ \t]*(' + QUOTED + r')[ \t]*$', re.M)

n_alias = 0
n_field = 0

for qmd in sorted(glob.glob('posts/*/index.qmd')):
    raw = io.open(qmd, encoding='utf-8').read()
    original = raw

    def unescape_alias(m):
        global n_alias
        value = json.loads(m.group(1))
        out = '  - ' + json.dumps(value, ensure_ascii=False)
        if out != m.group(0):
            n_alias += 1
        return out

    def tidy_field(m):
        global n_field
        value = json.loads(m.group(2))
        tidy = re.sub(r'\s{2,}', ' ', value).strip()
        if tidy != value:
            n_field += 1
        return '%s: %s' % (m.group(1), json.dumps(tidy, ensure_ascii=False))

    raw = ALIAS_LINE.sub(unescape_alias, raw)
    raw = FIELD_LINE.sub(tidy_field, raw)

    if raw != original:
        io.open(qmd, 'w', encoding='utf-8', newline='').write(raw)

print('aliases rewritten: %d | title/description values tidied: %d' % (n_alias, n_field))
