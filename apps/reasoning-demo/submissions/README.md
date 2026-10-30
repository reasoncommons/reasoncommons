# Commons shared by their participants

Each folder here is one commons a group shared from the ltp skill: `<slug>/publication.json` and nothing else. The build finds them without a `site.json` entry, checks them with `submissions.py` and writes their pages to `website/demos/reason-commons-in-use/<slug>/`, on their own shelf of the commons home page. The skill prepares the file with `share_commons.py` and opens the pull request; see [the skill's sharing guide](../../../skills/ltp/references/sharing.md).

The file holds what the group chose to share: statements and connections with their standing, who contributed and who accepted each, and optionally assumptions, challenges and open work. Everyone it names agreed to the name shown, and `people` records when and whether they agreed in the conversation or elsewhere. It is published under Creative Commons Attribution 4.0.

## Reviewing a submission

`build.py --check` and the tests already confirm the format, consents for every name, no private fields, no slug already in use, and that the pages match the file. A maintainer still reads it before merging:

- The pull request changes only this commons' folder and the pages generated from it.
- The submitter's account and the people named look genuine, and nothing suggests someone was named without agreeing.
- It is a commons: a goal and reasoning about it, not advertising or spam.
- It doesn't name people outside the group in connection with wrongdoing, or reveal private details about anyone.

Merging publishes it. It does not mean Reason Commons agrees with the reasoning, and the pages say so.

## Changes and removal

A new version replaces the folder and its pages in a new pull request. To remove a commons, delete its folder and its pages folder together; `build.py --check` fails while either is left behind. Act promptly on a request from anyone named, and say in the issue that copies made elsewhere can't be recalled.
