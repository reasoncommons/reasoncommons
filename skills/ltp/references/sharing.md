# Sharing a commons on the Reason Commons site

A group can put its commons on the Reason Commons site, where it appears on a shelf of commons shared by the people working on them. It arrives as a pull request to the site's repository, which a maintainer reviews before it goes live. Nothing is shared until that pull request is opened, and nothing is live until it is merged.

Sharing is outward-facing and hard to take back: a pull request is public the moment it opens, and copies made from the site cannot be recalled. Go step by step, and stop wherever the group is unsure.

## 1. Agree what goes public

Show the group what sharing means, then settle with them:

- **Which trees**, and **which standings**: accepted, proposed, disputed, or a mix. A connection is shared only with both of its ends.
- **Assumptions and challenges** (`--notes`), and **open work** (`--open-work`). Both are left out unless chosen.
- **A title, a one-sentence summary and a slug**, the address on the site: lower-case words joined by hyphens.

Capture details, receipts, consents' own words and anything outside the trees never leave the working file. The reasoning is published under Creative Commons Attribution 4.0, so anyone may reuse it with credit; say so before anyone agrees.

## 2. Ask each named person

Everyone the selection names, as a contributor, an endorser or the author of a note, must agree to be named, under the name they choose. The person sharing it is named too. Record each agreement in `share_consents` with your file-editing tools, as [schema.md](schema.md) describes:

- When the person types their agreement in this conversation, record `source: conversation` and keep their words in `source_text`.
- When they agreed elsewhere, such as by email, record `source: attested` with a `note` saying where and how; the driver vouches for it as `recorded_by`.

Only the person can agree. The AI cannot, and a request to share, silence or someone else's say-so does not count for anyone else. If someone would rather not be named, leave out what they contributed, accepted or noted, or stop. Removing their entry withdraws their agreement.

## 3. Prepare and preview

```bash
python3 <skill-directory>/scripts/share_commons.py <working-state.yaml> --slug <slug> --title "<title>" --summary "<one sentence>" --github <their-github-username> [--trees goal,current_reality] [--standings accepted,proposed] [--notes] [--open-work]
```

It validates the working file, builds the selection with everyone's chosen names, runs the site's own checks on it, and writes `publication.json` to `share/<slug>/` in the file's hidden directory (`.reason-commons/share/` for `reason-commons.yaml`), with a preview of the pages beside it in `share/preview/`. If anyone named has not agreed, it writes nothing and lists them. The printed JSON gives the file, the preview to `open`, who is named and the counts. Open the preview as for the private view (see [views.md](views.md); `--serve` serves it on 127.0.0.1) and let the group check it.

## 4. Sign in to GitHub

The person sharing it needs a GitHub account. Check with `gh auth status`. If they are not signed in, ask them to run `gh auth login` themselves. Never ask for, type or store their password or a token.

## 5. Prepare the pull request

Work in a temporary folder, not the group's project:

```bash
gh repo fork reasoncommons/reasoncommons --clone --default-branch-only -- --depth 1
cd reasoncommons
git switch -c share/<slug>
mkdir -p apps/reasoning-demo/submissions/<slug>
cp <the publication.json from step 3> apps/reasoning-demo/submissions/<slug>/publication.json
python3 apps/reasoning-demo/build.py
python3 apps/reasoning-demo/build.py --check
python3 -m unittest discover -s apps/reasoning-demo -p 'test_*.py'
python3 scripts/check-website.py
```

The build needs Python with PyYAML. If a fork already exists, sync it with `gh repo sync <their-username>/reasoncommons` and clone that instead. If a check fails, fix the cause in the working file and prepare again; do not edit the generated pages. Commit only `apps/reasoning-demo/submissions/<slug>/` and the pages the build changed under `website/demos/reason-commons-in-use/`: the commons' own folder and the commons home page. Show the group `git status` and the list of named people before going on.

## 6. Ask before opening it

Summarise what will become public: the title, the trees and standings, who is named and how, the licence, and that the pull request is public as soon as it opens. Ask for an explicit go-ahead from the person sharing it. Only then push and open the pull request, with the body from `.github/PULL_REQUEST_TEMPLATE/share-a-commons.md` filled in:

```bash
git push -u origin share/<slug>
gh pr create --repo reasoncommons/reasoncommons --base main --title "Share <title>" --body-file <filled template>
```

Report the link, and that a maintainer will review it; until it is merged, nothing appears on the site.

## Later

To share a new version, prepare again from the working file and open a new pull request that replaces the folder and its pages. To withdraw, open a pull request that removes both, or ask a maintainer through an issue on the repository. Anyone named can ask for a change or removal the same way.
