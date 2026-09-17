# -*- coding: utf-8 -*-
"""Rename Cyrillic post directories to Latin slugs, keeping old URLs alive.

The Blogspot migration produced directories like
``posts/2013-02-09-про-безопасность-на-дорогах-ч-2-.../``. Those URLs are live,
so every rename adds a Quarto ``aliases:`` entry pointing at the old path;
Quarto then emits a redirect page there.

    python scripts/transliterate_slugs.py            # dry run
    python scripts/transliterate_slugs.py --apply
"""
import os
import re
import sys
import glob
import json
import subprocess

APPLY = "--apply" in sys.argv
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAX_SLUG = 60

TABLE = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e',
    'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
    'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
    'ф': 'f', 'х': 'h', 'ц': 'c', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
    'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
}


def translit(text):
    out = []
    for ch in text.lower():
        if ch in TABLE:
            out.append(TABLE[ch])
        elif ch.isalnum() and ord(ch) < 128:
            out.append(ch)
        else:
            out.append('-')
    s = re.sub(r'-{2,}', '-', ''.join(out)).strip('-')
    return s


def make_slug(old):
    m = re.match(r'^(\d{4}-\d{2}-\d{2})-(.*)$', old)
    if not m:
        return translit(old)[:MAX_SLUG].strip('-')
    date, rest = m.group(1), m.group(2)
    body = translit(rest)[:MAX_SLUG].strip('-')
    # do not end on a chopped-up fragment of a word if we can avoid it
    if len(translit(rest)) > MAX_SLUG and '-' in body:
        body = body.rsplit('-', 1)[0]
    return '%s-%s' % (date, body) if body else date


FM = re.compile(r'^(---\n)(.*?)(\n---\n)(.*)$', re.S)


def add_alias(qmd, old_slug):
    raw = open(qmd, encoding='utf-8').read()
    m = FM.match(raw)
    if not m:
        print('  !! no frontmatter:', qmd)
        return False
    head, fm, sep, body = m.groups()
    alias = '/posts/%s/' % old_slug
    if 'aliases:' in fm:
        if alias in fm:
            return False
        fm = re.sub(r'^aliases:\s*\n', 'aliases:\n  - %s\n' % json.dumps(alias), fm,
                    count=1, flags=re.M)
    else:
        fm = fm + '\naliases:\n  - %s' % json.dumps(alias)
    if APPLY:
        open(qmd, 'w', encoding='utf-8', newline='').write(head + fm + sep + body)
    return True


def run(*args):
    return subprocess.run(args, cwd=ROOT, capture_output=True, text=True, encoding='utf-8')


renamed = 0
taken = set()
plan = []

for path in sorted(glob.glob(os.path.join(ROOT, 'posts', '*', 'index.qmd'))):
    old = os.path.basename(os.path.dirname(path))
    if not re.search(r'[а-яё]', old, re.I):
        taken.add(old)
        continue
    new = make_slug(old)
    base = new
    n = 2
    while new in taken:
        new = '%s-%d' % (base, n)
        n += 1
    taken.add(new)
    plan.append((old, new))

for old, new in plan:
    print('%s\n  -> %s' % (old, new))
    old_dir = os.path.join(ROOT, 'posts', old)
    new_dir = os.path.join(ROOT, 'posts', new)
    if APPLY:
        r = run('git', 'mv', os.path.join('posts', old), os.path.join('posts', new))
        if r.returncode != 0:
            print('  !! git mv failed: %s' % (r.stderr or r.stdout).strip()[:160])
            continue
    add_alias(os.path.join(new_dir if APPLY else old_dir, 'index.qmd'), old)
    renamed += 1

print('\n=== %s === renamed: %d' % ('APPLIED' if APPLY else 'DRY', renamed))
