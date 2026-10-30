#!/usr/bin/env python3
"""Copy the demo site's renderer into the ltp skill, so an installed skill can show a commons in the browser; --check detects drift.

The canonical renderer is apps/reasoning-demo. An installed skill holds only skills/ltp, so the files the
skill's open_commons.py helper needs are copied to skills/ltp/viewer. Edit the originals, never the copy.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "apps/reasoning-demo"
DEST = ROOT / "skills/ltp/viewer"
FILES = ["pages.py", "diagrams.py", "revisions.py", "submissions.py", "styles.css", "app.js"]
NOTE = """# Viewer

A generated copy of the renderer in `apps/reasoning-demo/` of the Reason Commons repository, so that an installed skill can show a commons in the browser with `scripts/open_commons.py`, and check and preview a commons for sharing with `scripts/share_commons.py`. Do not edit these files here: change the originals and run `python3 scripts/export-skill-viewer.py` from the repository root. `--check` fails when the copy has drifted.

The fonts are Alegreya Sans, under the SIL Open Font License in `fonts/OFL.txt`.
"""


def expected():
    files = {name: (SOURCE / name).read_bytes() for name in FILES}
    for font in sorted((SOURCE / "fonts").iterdir()):
        files[f"fonts/{font.name}"] = font.read_bytes()
    files["README.md"] = NOTE.encode()
    return files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Report drift without writing")
    args = parser.parse_args()
    files = expected()
    present = {str(p.relative_to(DEST)) for p in DEST.rglob("*") if p.is_file() and "__pycache__" not in p.parts} if DEST.exists() else set()
    drift = sorted(name for name, data in files.items() if not (DEST / name).is_file() or (DEST / name).read_bytes() != data)
    extra = sorted(present - set(files))
    if args.check:
        if drift or extra:
            print("Skill viewer copy has drifted; run python3 scripts/export-skill-viewer.py", file=sys.stderr)
            for name in drift:
                print(f"  changed or missing: {name}", file=sys.stderr)
            for name in extra:
                print(f"  unexpected: {name}", file=sys.stderr)
            return 1
        print(f"Skill viewer copy: all {len(files)} files current")
        return 0
    for name in extra:
        (DEST / name).unlink()
    for name in drift:
        target = DEST / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(files[name])
    print(f"Skill viewer copy: {len(drift)} written, {len(extra)} removed, {len(files)} in all")
    return 0


if __name__ == "__main__":
    sys.exit(main())
