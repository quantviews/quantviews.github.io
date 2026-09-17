"""
Clean up migration artifacts in posts/:
  - Remove stray `_  _` / `_\n_` empty italic lines (render as dashes)
  - Fix ### headings that have an image link appended: ### Title [![](url)](url)
  - Strip trailing whitespace
"""
import re
from pathlib import Path

posts_dir = Path("posts")
fixed = 0

for qmd in posts_dir.rglob("index.qmd"):
    text = qmd.read_text(encoding="utf-8")
    original = text

    # Remove empty italic lines like `_  _` or `_  \n_` (render as stray dashes)
    text = re.sub(r'^_[ \t]*_[ \t]*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^_[ \t]*\n_[ \t]*$', '', text, flags=re.MULTILINE)

    # Remove image links appended to headings: ### Heading [![](url)](url)
    # Pattern: heading text followed by [![...](url)](url)
    text = re.sub(r'(#{1,6}\s+.+?)\s+\[!\[.*?\]\(.*?\)\]\(.*?\)', r'\1', text)

    # Collapse 3+ consecutive blank lines to 2
    text = re.sub(r'\n{4,}', '\n\n\n', text)

    if text != original:
        qmd.write_text(text, encoding="utf-8")
        print(f"Fixed: {fixed + 1}")
        fixed += 1

print(f"\nDone: {fixed} files updated")
