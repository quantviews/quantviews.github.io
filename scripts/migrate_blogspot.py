"""
Migrate Blogspot posts to Quarto QMD files.

Usage:
    pip install requests html2text
    python migrate_blogspot.py

Output: creates posts/<date>-<slug>/index.qmd for each post.
"""

import requests
import json
import os
import re
from datetime import datetime

try:
    import html2text
except ImportError:
    raise SystemExit("Run: pip install html2text")

BLOG_URL = "https://quantviews.blogspot.com"
OUTPUT_DIR = "posts"
AUTHOR = "Марсель Салихов"

converter = html2text.HTML2Text()
converter.ignore_links = False
converter.ignore_images = False
converter.body_width = 0  # no line wrapping


def fetch_all_posts():
    posts = []
    url = f"{BLOG_URL}/feeds/posts/default?max-results=500&alt=json"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    entries = data.get("feed", {}).get("entry", [])
    print(f"Found {len(entries)} posts")
    return entries


def get_labels(entry):
    labels = []
    for cat in entry.get("category", []):
        scheme = cat.get("scheme", "")
        term = cat.get("term", "")
        if "kind" not in scheme and term:
            labels.append(term)
    return labels


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text[:55].rstrip("-")


def yaml_str(value):
    """Wrap a string as a safe single-quoted YAML value (escapes ' as '')."""
    return "'" + value.replace("'", "''") + "'"

def make_frontmatter(title, date_str, labels, description=""):
    cats = ", ".join(f'"{l}"' for l in labels) if labels else ""
    desc_line = f"description: {yaml_str(description)}\n" if description else ""
    return (
        f"---\n"
        f"title: {yaml_str(title)}\n"
        f"date: {date_str}\n"
        f"author: {yaml_str(AUTHOR)}\n"
        f"categories: [{cats}]\n"
        f"{desc_line}"
        f"---\n\n"
    )


def convert_entry(entry):
    title = entry.get("title", {}).get("$t", "Без названия")
    published = entry.get("published", {}).get("$t", "2000-01-01")
    date_str = published[:10]

    content_html = entry.get("content", {}).get("$t", "")
    labels = get_labels(entry)

    # Convert HTML → Markdown
    body_md = converter.handle(content_html).strip()

    # Use first sentence as description (up to 160 chars)
    plain = re.sub(r"\n+", " ", re.sub(r"[#*`\[\]!]", "", body_md))
    description = plain[:160].rsplit(" ", 1)[0].strip(".,;:") if len(plain) > 30 else ""

    slug = slugify(title)
    dir_path = os.path.join(OUTPUT_DIR, f"{date_str}-{slug}")
    os.makedirs(dir_path, exist_ok=True)

    frontmatter = make_frontmatter(title, date_str, labels, description)
    qmd_path = os.path.join(dir_path, "index.qmd")

    with open(qmd_path, "w", encoding="utf-8") as f:
        f.write(frontmatter + body_md + "\n")

    return qmd_path, title


if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    entries = fetch_all_posts()

    ok, fail = 0, 0
    for entry in entries:
        try:
            path, title = convert_entry(entry)
            print(f"  ✓  {path}")
            ok += 1
        except Exception as e:
            title = entry.get("title", {}).get("$t", "?")
            print(f"  ✗  {title!r}: {e}")
            fail += 1

    print(f"\nDone: {ok} converted, {fail} failed")
    print("Review the files, then run: quarto render")
