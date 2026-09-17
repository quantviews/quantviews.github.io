# -*- coding: utf-8 -*-
"""Regenerate broken `description:` fields left over from the Blogspot migration."""
import re
import glob
import os
import sys
import json

APPLY = "--apply" in sys.argv


def clean(md):
    t = md
    t = re.sub(r'<!--.*?-->', ' ', t, flags=re.S)
    t = re.sub(r'::: *\{[^}]*\}(.*?):::', ' ', t, flags=re.S)        # fenced divs
    t = re.sub(r'```.*?```', ' ', t, flags=re.S)
    t = re.sub(r'<[^>]+>', ' ', t)
    t = re.sub(r'\[!\[[^\]]*\]\([^)]*\)\]\([^)]*\)', ' ', t)         # linked images
    t = re.sub(r'!\[[^\]]*\]\([^)]*\)', ' ', t)                      # images
    t = re.sub(r'\[([^\]]*)\]\([^)]*\)', r' \1 ', t)                 # links -> text
    t = re.sub(r'\(\s*https?://[^)]*\)', ' ', t)
    t = re.sub(r'https?://\S+', ' ', t)
    t = re.sub(r'^\s{0,3}#{1,6}\s+.*$', ' ', t, flags=re.M)          # headings
    t = re.sub(r'^\s{0,3}>\s?', ' ', t, flags=re.M)                  # quotes
    t = re.sub(r'^\s{0,3}[-*+]\s+', ' ', t, flags=re.M)              # bullets
    t = re.sub(r'^[\s\-:|]*$', ' ', t, flags=re.M)                   # table separators
    t = '\n'.join(' ' if ('|' in ln and len(ln) < 120) else ln       # byline table rows
                  for ln in t.split('\n'))
    t = re.sub(r'\*\*|__', '', t)
    t = re.sub(r'(?<![A-Za-zА-я0-9])[*_]|[*_](?![A-Za-zА-я0-9])', '', t)
    t = t.replace(' ', ' ')
    t = re.sub(r'\s+', ' ', t).strip()
    # tidy spacing introduced by stripping inline markup
    t = re.sub(r'\s+([,.:;!?»\)])', r'\1', t)
    t = re.sub(r'([«\(])\s+', r'\1', t)
    t = re.sub(r'\s+([–—-])\s+', r' \1 ', t)
    return t.strip()


# leading fragments that are pure "see also" pointers, not description material
LEAD_NOISE = re.compile(
    r'^(?:'
    r'Отсюда'            # Отсюда
    r'|Марсель'     # Марсель
    r'|Салихов'     # Салихов
    r'|Update|UPDATE|update'
    r'|[\s.,:;–—-]'
    r')+', re.I)

POINTER = re.compile(
    r'здесь'                  # здесь
    r'|Отсюда'           # Отсюда
    r'|^Первая часть$'   # Первая часть
    r'|^Вторая часть'    # Вторая часть
    r'|^Начало')         # Начало


def describe(body, limit=200):
    t = clean(body)
    for _ in range(3):
        t = LEAD_NOISE.sub('', t).strip()
        m = re.match(r'^(.{0,70}?)(?:[.!?]\s+|\s{2,})', t)
        if m and POINTER.search(m.group(1).strip()):
            t = t[m.end():].strip()
            continue
        # pointer running straight into the next sentence with no punctuation:
        # "Первая часть В первой части я ...", "... доступны здесь Все уже слышали ..."
        m = re.match(r'^.{0,70}?(?:здесь|часть)'
                     r'\s+(?=[А-ЯЁA-Z])', t)
        if m:
            t = t[m.end():].strip()
        else:
            break
    t = LEAD_NOISE.sub('', t).strip()
    t = re.sub(r'\s{2,}', ' ', t)
    if not t:
        return None
    if len(t) <= limit:
        return t
    cut = t[:limit]
    if ' ' in cut:
        cut = cut.rsplit(' ', 1)[0]
    return cut.rstrip(' ,;:—-') + '…'


FM = re.compile(r'^(---\n)(.*?)(\n---\n)(.*)$', re.S)
DESC = re.compile(r'^description:[ \t]*(.*)$', re.M)

fixed = skipped = 0
for qmd in sorted(glob.glob('posts/*/index.qmd')):
    raw = open(qmd, encoding='utf-8').read()
    m = FM.match(raw)
    if not m:
        print('NO FRONTMATTER:', qmd)
        continue
    head, fm, sep, body = m.group(1), m.group(2), m.group(3), m.group(4)
    dm = DESC.search(fm)
    cur = (dm.group(1).strip() if dm else '').strip('"\'')
    if cur and not re.search(r'https?://', cur) and not cur.startswith('('):
        skipped += 1
        continue
    new = describe(body)
    if not new:
        print('EMPTY BODY, left as is:', qmd)
        continue
    line = 'description: ' + json.dumps(new, ensure_ascii=False)
    fm2 = DESC.sub(lambda _: line, fm, count=1) if dm else fm + '\n' + line
    slug = os.path.basename(os.path.dirname(qmd))
    print('\n%s\n  OLD: %s\n  NEW: %s' % (slug[:70], cur[:100], new))
    if APPLY:
        open(qmd, 'w', encoding='utf-8', newline='').write(head + fm2 + sep + body)
    fixed += 1

print('\n=== %s === rewritten: %d  untouched: %d'
      % ('APPLIED' if APPLY else 'DRY', fixed, skipped))
