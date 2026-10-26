#!/usr/bin/env python3
"""Check the website boundary, explicit exports, preserved routes, local links and retired terms."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
MARKDOWN_LINK = re.compile(r'!?\[[^\]\n]*\]\((<[^>\n]*>|[^)\n]*)\)')


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.targets = []

    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            if name in ('href', 'src', 'poster') and value:
                self.targets.append(value)


def links(text: str, markdown: bool) -> set[str]:
    if markdown:
        text = re.sub(r'^```[^\n]*\n.*?^```\s*$', '', text, flags=re.M | re.S)
    parser = Links()
    parser.feed(text)
    targets = set(parser.targets)
    if markdown:
        for match in MARKDOWN_LINK.finditer(text):
            target = match[1].strip()
            if target.startswith('<'):
                target = target[1:target.index('>')]
            else:
                target = re.sub(r'''\s+["'].*["']$''', '', target)
            targets.add(target)
    return targets


def resolve(site: Path, document: Path, target: str) -> bool:
    if not target or target.startswith(('#', '//', '{', 'javascript:', 'data:', 'mailto:', 'tel:')):
        return True
    try:
        url = urlsplit(target)
    except ValueError:
        return True  # An interpolated template value, not a literal local URL.
    if url.scheme or url.netloc:
        return True
    path = unquote(url.path)
    if not path:
        return True
    resolved = ((site / path.lstrip('/')) if path.startswith('/') else (document.parent / path)).resolve()
    if not resolved.is_relative_to(site.resolve()):
        return False
    if resolved.is_file():
        return True
    if resolved.suffix == '' and resolved.with_suffix('.md').is_file():
        return True
    # Flowershow generates the timeline without a changelog index file.
    if path.rstrip('/') == '/changelog' and (site / 'changelog').is_dir():
        return True
    if resolved.is_dir():
        return any((resolved / name).is_file() for name in ('README.md', 'index.md', 'index.html'))
    return False


def check(root: Path, migration: bool = False) -> tuple[list[str], list[dict], int]:
    manifest = json.loads((root / 'scripts/website-content.json').read_text())
    site = root / manifest['site_root']
    errors = []
    if not site.is_dir():
        return ['Website root is missing.'], [], 0
    if migration:
        for item in manifest['moves']:
            destination = root / item['to']
            if not destination.is_file():
                errors.append(f'Moved file missing: {item["to"]}')
            if (root / item['from']).exists():
                errors.append(f'Old source still exists: {item["from"]}')
            if item['to'].startswith('website/') and item['to'] != 'website/' + item['from']:
                errors.append(f'Public path changed: {item["from"]} -> {item["to"]}')
        for item in manifest['preserve_bytes']:
            path = root / item['path']
            if not path.is_file():
                continue
            data = path.read_bytes()
            blob = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
            if blob != item['git_blob']:
                errors.append(f'Moved media/artifact changed: {item["path"]}')
    forbidden = {'docs', 'apps', '.agents', '.claude', '.beads', '.git', 'scripts'}
    for path in site.rglob('*'):
        relative = path.relative_to(site)
        if path.is_symlink():
            errors.append(f'Symlink in publishing root: {relative}')
        if relative.parts[0] in forbidden or {'.git', '.beads', '.claude', '.agents', '_process'}.intersection(relative.parts):
            errors.append(f'Working material in publishing root: {relative}')
    for path in (site / 'skills').rglob('*'):
        if path.is_file() and path.name != 'README.md':
            errors.append(f'Installable skill internals in website: {path.relative_to(site)}')
    config = json.loads((site / 'config.json').read_text())
    for route in manifest['required_routes'] + [x['href'] for x in config['nav']['links']]:
        if not resolve(site, site / 'README.md', route):
            errors.append(f'Public route missing: {route}')
    for route in manifest['retired_working_routes']:
        if resolve(site, site / 'README.md', route):
            errors.append(f'Working route is still published: {route}')
    if migration:
        for name in ('ltp',):
            link = root / '.agents/skills' / name
            if not link.is_symlink() or link.resolve() != (root / 'skills' / name).resolve():
                errors.append(f'Canonical skill link does not resolve: {name}')
    export = subprocess.run([sys.executable, str(root / 'scripts/export-website.py'), '--check', '--root', str(root)], capture_output=True, text=True)
    if export.returncode:
        errors.append((export.stdout + export.stderr).strip())
    # Retired framing must not reappear on current pages; dated folders keep their wording.
    retired = re.compile('|'.join(manifest['retired_terms']['patterns']), re.I)
    allowed = tuple(manifest['retired_terms']['allowed_paths'])
    for document in sorted(site.rglob('*')):
        if not document.is_file() or document.suffix not in ('.md', '.html', '.json') or document.relative_to(site).as_posix().startswith(allowed):
            continue
        for number, line in enumerate(document.read_text().splitlines(), 1):
            if match := retired.search(line):
                errors.append(f'{document.relative_to(root)}:{number}: retired term {match[0]!r}')
    missing = []
    count = 0
    for document in sorted(site.rglob('*')):
        if not document.is_file() or document.suffix not in ('.md', '.html', '.css'):
            continue
        text = document.read_text()
        if document.suffix == '.css':
            tokens = re.findall(r'''url\(\s*(?:"([^"]*)"|'([^']*)'|([^)]*))\s*\)''', text)
            targets = {next(value for value in values if value) for values in tokens}
        else:
            targets = links(text, document.suffix == '.md')
        count += len(targets)
        for target in sorted(targets):
            if not resolve(site, document, target):
                missing.append({'document':str(document.relative_to(root)), 'target':target})
    # Candidate pages are kept as supplied, so a link their designer left broken stays as evidence; a listed link that resolves or disappears is stale.
    known = {(item['document'], item['target']) for item in manifest['known_missing_links']}
    for document, target in sorted(known - {(item['document'], item['target']) for item in missing}):
        errors.append(f'{document}: known missing link {target} now resolves or is gone; remove it from known_missing_links')
    missing = [item for item in missing if (item['document'], item['target']) not in known]
    for item in missing:
        errors.append(f'{item["document"]}: missing local target {item["target"]}')
    return errors, missing, count


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT, help=argparse.SUPPRESS)
    parser.add_argument('--migration', action='store_true', help='Also audit this migration’s historical moves, byte preservation and root/skill wiring')
    parser.add_argument('--json', action='store_true', help='Emit machine-readable results')
    args = parser.parse_args()
    try:
        errors, missing, count = check(args.root.resolve(), args.migration)
    except (OSError, ValueError, KeyError) as exc:
        parser.exit(1, f'{exc}\n')
    if args.json:
        print(json.dumps({'errors':errors,'missing_links':missing,'links_checked':count},indent=2))
    else:
        for error in errors:
            print('ERROR:', error)
        print(f'Checked {count} links/assets; {len(errors)} errors; {len(missing)} missing links.')
    return int(bool(errors))


if __name__ == '__main__':
    raise SystemExit(main())
