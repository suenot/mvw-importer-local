"""Import local <name>.mp4 + <name>.jpg pairs from a folder into the warehouse (copy, never move).

Usage: ./run.sh --source own-docs-site /path/to/videos
Entries without an mp4 (jpg only) are skipped.
"""
import argparse
import shutil
from pathlib import Path

from mvw_core import Item


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("folder")
    ap.add_argument("--source", required=True, help="warehouse source name, e.g. own-docs-site")
    a = ap.parse_args()
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
        it.save_meta(title=mp4.stem, source_url=str(mp4.parent))
        n += 1
    print(f"{a.source}: {n} items, {new} new")


main()
