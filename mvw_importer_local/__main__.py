"""Import local <name>.mp4 + <name>.jpg pairs from a folder into the warehouse (copy, never move).

Usage: ./run.sh --source own-docs-site /path/to/videos
Entries without an mp4 (jpg only) are skipped.

With --docs <@docs dir> each video also gets its build record from <docs>/videos/<name>.md:
  how.md     whole page (idea, script, how it was made, audit, checklist)
  prompt.txt the "Prompts to repeat it" section (else "How it was made")
  style.md   <docs>/styles/<style>.md named in the front matter
and <docs>/guides + <docs>/styles are copied once into <source>/_guides/.
"""
import argparse
import re
import shutil
from pathlib import Path

from mvw_core import Item


def front_matter(text):
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    fm = {}
    if m:
        for line in m.group(1).splitlines():
            k, _, v = line.partition(":")
            if v.strip():
                fm[k.strip()] = v.strip().strip('"')
    return fm, text[m.end():] if m else text


def section(body, *titles):
    for t in titles:
        m = re.search(rf"^## {re.escape(t)}\s*\n(.*?)(?=^## |\Z)", body, re.S | re.M)
        if m and m.group(1).strip():
            return f"## {t}\n\n" + m.group(1).strip() + "\n"
    return None


def import_docs(it, docs, stem):
    page = docs / "videos" / f"{stem}.md"
    if not page.exists():
        return {}
    text = page.read_text(encoding="utf-8")
    fm, body = front_matter(text)
    it.save_text("how.md", text)
    prompt = section(body, "Prompts to repeat it", "How it was made")
    if prompt:
        it.save_text("prompt.txt", prompt)
    style = docs / "styles" / f"{fm.get('style', '')}.md"
    if fm.get("style") and style.exists():
        it.save_text("style.md", style.read_text(encoding="utf-8"))
    return {k: fm[k] for k in ("title", "style", "duration", "summary", "date") if k in fm}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("folder")
    ap.add_argument("--source", required=True, help="warehouse source name, e.g. own-docs-site")
    ap.add_argument("--docs", help="@docs folder with videos/, styles/, guides/")
    a = ap.parse_args()
    docs = Path(a.docs).expanduser() if a.docs else None
    if docs:
        from mvw_core import warehouse_root

        for sub in ("guides", "styles"):
            for f in (docs / sub).glob("*.md"):
                dst = warehouse_root() / a.source / "_guides" / sub
                dst.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, dst / f.name)
    n = new = 0
    for mp4 in sorted(Path(a.folder).expanduser().glob("*.mp4")):
        it = Item(a.source, mp4.stem)
        new += it.is_new
        files = {}
        for src, name in ((mp4, "original.mp4"), (mp4.with_suffix(".jpg"), "poster.jpg")):
            if src.exists() and not it.has(name):
                it.dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, it.dir / name)
                files[name] = {"path": str(src), "bytes": src.stat().st_size}
        it.meta.setdefault("files", {}).update(files)
        extra = import_docs(it, docs, mp4.stem) if docs else {}
        it.save_meta(source_url=str(mp4.parent), **{"title": mp4.stem, **extra})
        n += 1
    print(f"{a.source}: {n} items, {new} new")


main()
