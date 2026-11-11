#!/usr/bin/env python3
"""Build the Gandhi 2.0 workspace prototype as one self-contained page.

    python3 apps/reasoning-demo/prototypes/gandhi-2-0-workspace/build.py          # write the page
    python3 apps/reasoning-demo/prototypes/gandhi-2-0-workspace/build.py --check  # fail if the page is stale

The page embeds the published Gandhi 2.0 release unchanged; test.cjs checks that.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SOURCE = ROOT / "website/demos/reason-commons-in-use/gandhi-2-0/reasoning.json"
DEST = ROOT / "website/demos/gandhi-2-0-workspace/index.html"


def render() -> str:
    data = json.dumps(json.loads(SOURCE.read_text(encoding="utf-8")), ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    page = (HERE / "template.html").read_text(encoding="utf-8")
    for key, name in (("/*CSS*/", "style.css"), ("/*MODEL*/", "model.js"), ("/*APP*/", "app.js")):
        page = page.replace(key, (HERE / name).read_text(encoding="utf-8"))
    return page.replace("/*DATA*/", data)


def main() -> int:
    page = render()
    if "--check" in sys.argv:
        if not DEST.exists() or DEST.read_text(encoding="utf-8") != page:
            print(f"{DEST.relative_to(ROOT)} is stale; run build.py")
            return 1
        print("up to date")
        return 0
    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(page, encoding="utf-8")
    print(f"wrote {DEST.relative_to(ROOT)} ({len(page.encode('utf-8')) // 1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
