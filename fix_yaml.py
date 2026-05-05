"""Fix broken YAML frontmatter in migrated posts (unescaped quotes in description)."""
import os, re, glob

def fix_description(line):
    """Replace inner double-quotes in description: "..." with single quotes."""
    m = re.match(r'^(description:\s*)"(.*)"(\s*)$', line)
    if not m:
        return line
    inner = m.group(2).replace('"', "'")
    return f'{m.group(1)}"{inner}"{m.group(3)}'

fixed = 0
for path in glob.glob("posts/**/index.qmd", recursive=True):
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()

    new_lines = []
    changed = False
    in_fm = False
    fm_count = 0

    for line in lines:
        if line.strip() == "---":
            fm_count += 1
            in_fm = fm_count == 1
            new_lines.append(line)
            continue
        if in_fm and line.startswith("description:"):
            new_line = fix_description(line)
            if new_line != line:
                changed = True
            new_lines.append(new_line)
        else:
            new_lines.append(line)

    if changed:
        with open(path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        print(f"Fixed: {path}")
        fixed += 1

print(f"\nTotal fixed: {fixed}")
