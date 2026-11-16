#!/usr/bin/env python3
"""Build the published workspace pages, each one self-contained.

    python3 apps/reasoning-demo/prototypes/gandhi-2-0-workspace/build.py          # write the pages
    python3 apps/reasoning-demo/prototypes/gandhi-2-0-workspace/build.py --check  # fail if a page is stale

The Gandhi 2.0 page embeds the published release unchanged; test.cjs checks that. A workspace published for a
shared commons keeps its own shell and embedded record, and takes only the current styles and browser code.
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SOURCE = ROOT / "website/demos/reason-commons-in-use/gandhi-2-0/reasoning.json"
DEST = ROOT / "website/demos/gandhi-2-0-workspace/index.html"
# Each shared workspace, with the page its "Full record" link opens.
SHARED = {
    ROOT / "website/demos/tdi-cybernetic-futures-workspace/index.html": "../reason-commons-in-use/tdi-cybernetic-futures/items.html",
}
PARTS = (("/*CSS*/", "style.css"), ("/*MODEL*/", "model.js"), ("/*APP*/", "app.js"))
DATA = re.compile(r'(<script type="application/json" id="rc-data">)(.*?)(</script>)', re.S)


def source(name: str) -> str:
    return (HERE / name).read_text(encoding="utf-8")


def render() -> str:
    data = json.dumps(json.loads(SOURCE.read_text(encoding="utf-8")), ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    page = source("template.html")
    for key, name in PARTS:
        page = page.replace(key, source(name))
    return page.replace("/*DATA*/", data)


def refresh(page: str, record_href: str) -> str:
    """Swap the styles and the two scripts of a shared workspace for the current ones."""
    record = json.loads(DATA.search(page)[2])
    record["record_href"] = record_href
    payload = json.dumps(record, ensure_ascii=False, separators=(",", ":")).replace("<", r"<")
    page = DATA.sub(lambda found: found[1] + payload + found[3], page, count=1)
    page = re.sub(r"(<style>\n).*?(\n</style>)", lambda found: found[1] + source("style.css") + found[2], page, count=1, flags=re.S)
    scripts = iter((source("model.js"), source("app.js")))
    page, count = re.subn(r"(<script>\n).*?(\n</script>)", lambda found: found[1] + next(scripts) + found[2], page, count=2, flags=re.S)
    if count != 2:
        raise SystemExit("a shared workspace page needs its model script and its app script")
    return page


def main() -> int:
    pages = {DEST: render()}
    pages.update({path: refresh(path.read_text(encoding="utf-8"), href) for path, href in SHARED.items()})
    if "--check" in sys.argv:
        stale = [path for path, page in pages.items() if not path.exists() or path.read_text(encoding="utf-8") != page]
        for path in stale:
            print(f"{path.relative_to(ROOT)} is stale; run build.py")
        if not stale:
            print("up to date")
        return 1 if stale else 0
    for path, page in pages.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(page, encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)} ({len(page.encode('utf-8')) // 1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
