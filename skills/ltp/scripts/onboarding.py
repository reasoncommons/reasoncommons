#!/usr/bin/env python3
"""Print the first-session introduction for a participant, once per repository.

    onboarding.py reason-commons.yaml --participant rufus
    onboarding.py reason-commons.yaml --participant rufus --again

Prints nothing for someone who has already seen it in this repository's main checkout
or any of its worktrees. Who has seen it is kept in the main checkout's local folder;
the shared reasoning file is only read.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess

import feedback
import feedback_sync
import update_views

TEMPLATE = Path(__file__).resolve().parents[1] / "references" / "onboarding.md"


def template():
    match = re.search(r"^```markdown\n(.*?)^```", TEMPLATE.read_text(), re.M | re.S)
    return match.group(1).strip()


def git(state, *args):
    result = subprocess.run(["git", "-C", str(state.parent), *args], capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else None


def sharing(state, person):
    policy = feedback_sync.local_dir(state) / "feedback-sync.json"
    off = (feedback_sync.local_dir(state) / "feedback-sync-off.json").exists()
    configured = json.loads(policy.read_text()) if policy.exists() else None if off else feedback_sync.main_grant(state)
    if configured:
        shared = f"on. Your answers reach the other participants automatically through `{configured['remote']}/{configured['branch']}`"
        inherited = configured.get("inherited_from") or (None if policy.exists() else configured["repo"])
        return shared + (f", using the authorisation you gave in your main checkout, `{inherited}`." if inherited else ".")
    if git(state, "rev-parse", "--show-toplevel") is None:
        return "not available, because this reasoning file is not in a Git checkout. Your answers stay on this computer."
    remotes = (git(state, "remote") or "").split()
    remote = "origin" if "origin" in remotes else (remotes[0] if remotes else "origin")
    # The branch other participants read, not this checkout's own (often a session branch).
    default = git(state, "symbolic-ref", "--short", f"refs/remotes/{remote}/HEAD")
    branch = default.split("/", 1)[1] if default and "/" in default else "main"
    script = Path(__file__).resolve().with_name("feedback_sync.py")
    # Configure the main checkout's copy: every worktree inherits it, while a worktree's own setting vanishes with it.
    target = main_copy(state) or state
    later = " It sets up your main checkout, so sessions in other worktrees share too." if target != state else ""
    return ("off in this checkout, so your answers stay on this computer. To share them with the other participants, "
            "run this once, replacing the quoted words with your own authorisation." + later + "\n\n```bash\n"
            f"python3 {script} {target} configure --remote {remote} --branch {branch} --by {person} "
            "--source-text 'I authorise automatic feedback commits and pushes'\n```")


def waiting(state, person):
    count = len(feedback.queue(state, person))
    if not count:
        return "nothing right now."
    return "1 feedback request. It comes next." if count == 1 else f"{count} feedback requests. The first comes next."


def introduction(path, person):
    state = update_views.load(path)
    names = state.get("participants") or {}
    if person not in names:
        raise ValueError(f"Unknown participant: {person}")
    others = [name for ident, name in names.items() if ident != person]
    return template().format(name=names[person], project=state.get("project") or path.stem,
                             others=" You share it with " + ", ".join(others) + "." if others else "",
                             sharing=sharing(path, person), waiting=waiting(state, person))


def main_copy(path):
    """The same reasoning file in the main checkout, when path is in a linked worktree and it exists there."""
    found = feedback_sync.checkouts(path)
    if not found:
        return None
    repo, (main, *_) = found
    copy = main / path.relative_to(repo)
    return copy if main != repo and copy.exists() else None


def seen_files(path):
    """Every record of who has seen the introduction for this file; new showings go in the first."""
    own = feedback_sync.local_dir(path) / "onboarding.json"
    found = feedback_sync.checkouts(path)
    if not found:
        return [own]
    repo, roots = found
    relative = path.relative_to(repo)
    # A file absent from the main checkout keeps its record beside it, creating nothing there.
    first = feedback_sync.local_dir(main_copy(path) or path) / "onboarding.json"
    return list(dict.fromkeys([first, own] + [feedback_sync.local_dir(root / relative) / "onboarding.json" for root in roots]))


def seen_file(path):
    return seen_files(path)[0]


def show(path, person, again=False):
    """The introduction text, or None when this participant has already seen it in this repository."""
    path = Path(path).expanduser().resolve()
    records = seen_files(path)
    if not again and any(person in json.loads(record.read_text()) for record in records if record.exists()):
        return None
    text = introduction(path, person)
    seen = json.loads(records[0].read_text()) if records[0].exists() else {}
    seen[person] = datetime.now(timezone.utc).isoformat()
    feedback_sync.atomic(records[0], json.dumps(seen, indent=2) + "\n")
    return text


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("state", type=Path)
    parser.add_argument("--participant", required=True)
    parser.add_argument("--again", action="store_true", help="show it even if this participant has seen it")
    args = parser.parse_args()
    try:
        text = show(args.state, args.participant, args.again)
    except (ValueError, OSError) as exc:
        parser.exit(1, str(exc) + "\n")
    if text:
        print(text)


if __name__ == "__main__":
    main()
