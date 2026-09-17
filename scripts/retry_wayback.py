# -*- coding: utf-8 -*-
"""Retry recovering images marked as unavailable, via the Wayback Machine.

Posts whose images could not be downloaded carry a marker:

    ::: {.qv-missing-image}
    Изображение недоступно ...
    :::
    <!-- original-image: <alt> | <url> -->

Run when archive.org is reachable again:

    python scripts/retry_wayback.py            # dry run
    python scripts/retry_wayback.py --apply
"""
import os, re, sys, glob
from urllib.parse import urlparse, unquote
import requests

DRY = "--apply" not in sys.argv
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLOCK = re.compile(
    r'::: \{\.qv-missing-image\}\n[^\n]*\n:::\n<!-- original-image: (.*?) \| (\S+) -->',
    re.MULTILINE)
IMG_EXT = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp'}
CT_EXT = {'image/png': '.png', 'image/jpeg': '.jpg', 'image/gif': '.gif', 'image/webp': '.webp'}
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; quantviews-migration/1.0)"}
s = requests.Session()


def archived(url):
    try:
        r = s.get("https://archive.org/wayback/available",
                  params={"url": url}, headers=HEADERS, timeout=40)
        if not r.headers.get("Content-Type", "").startswith("application/json"):
            print("    archive.org unavailable (HTTP %s)" % r.status_code)
            return None
        snap = (r.json().get("archived_snapshots") or {}).get("closest") or {}
        if snap.get("available") and snap.get("url"):
            return re.sub(r'/web/(\d+)/', r'/web/\1id_/',
                          snap["url"].replace("http://", "https://", 1))
    except Exception as e:
        print("    lookup failed: %s" % str(e)[:70])
    return None


def safe_name(url, idx, ct):
    base = os.path.basename(unquote(urlparse(url).path)) or 'image'
    base = re.sub(r'[^A-Za-z0-9._-]+', '-', base).strip('-.') or 'image'
    stem, ext = os.path.splitext(base)
    ce = CT_EXT.get((ct or '').split(';')[0].strip().lower(), '')
    if not ce:
        ce = ext.lower() if ext.lower() in IMG_EXT else '.png'
    return "wb%02d-%s%s" % (idx, stem[:40] or 'image', ce)


ok = fail = 0
for qmd in sorted(glob.glob(os.path.join(ROOT, 'posts', '*', 'index.qmd'))):
    post_dir = os.path.dirname(qmd)
    text = open(qmd, encoding='utf-8').read()
    blocks = BLOCK.findall(text)
    if not blocks:
        continue
    print("\n%s" % os.path.basename(post_dir)[:70])
    idx = 0
    changed = False
    for alt, url in blocks:
        idx += 1
        print("  try %s" % url[:80])
        wb = archived(url)
        if not wb:
            print("    no snapshot"); fail += 1; continue
        try:
            r = s.get(wb, headers=HEADERS, timeout=90)
            r.raise_for_status()
            ct = r.headers.get('Content-Type', '')
            if not ct.lower().startswith('image/'):
                raise ValueError('not an image: %s' % ct)
            fname = safe_name(url, idx, ct)
            if not DRY:
                os.makedirs(os.path.join(post_dir, 'images'), exist_ok=True)
                open(os.path.join(post_dir, 'images', fname), 'wb').write(r.content)
            block = next(m.group(0) for m in BLOCK.finditer(text) if m.group(2) == url)
            text = text.replace(block, '![%s](images/%s)' % (alt, fname))
            changed = True; ok += 1
            print("    OK -> images/%s (%d KB)" % (fname, len(r.content) // 1024))
        except Exception as e:
            print("    FAIL %s" % str(e)[:70]); fail += 1
    if changed and not DRY:
        open(qmd, 'w', encoding='utf-8', newline='').write(text)

print("\n=== %s === recovered: %d  still missing: %d" % ('DRY' if DRY else 'APPLIED', ok, fail))
