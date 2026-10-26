# Persistent Systems Theory demonstration

The demonstration at `website/demos/reason-commons-in-use/persistent-systems/` is an entirely proposed AI reconstruction of Stephen Le’s Adaptive Persistence, the protocol for cooperation in his Persistence Framework, which also includes Procedural Ethics and Persistent Systems Theory. It uses the established `apps/reasoning-demo/` generator and components; the shared stylesheet, JavaScript, fonts and diagram renderer are unchanged.

## Sources and attribution

Two supplied documents by Stephen Le, both in the public [persistent-systems-theory](https://github.com/dvdgdn/persistent-systems-theory) repository: his three-page *Adaptive Persistence* overview (30 September 2026) and his ten-page summary for Analogue Group, *Adaptive Persistence: A Meta-Protocol for Cooperation* (11 October 2026). References give PDF page numbers. Each source links to its original, which is why `build.py` allows an optional `https` link on a `supplied_document` source.

The AI selected, paraphrased and connected the material; every statement and connection is attributed to the AI assistant, with source locators labelled paraphrase, reconstruction, inference or related point. Stephen Le has not reviewed or endorsed the map. David reports that Stephen agreed to his material appearing on the public site.

## What the map holds

62 proposed statements and 45 proposed connections across all six trees. The goal joins Adaptive Persistence’s aims (performance, trust and well-being, fewer conflicts) with lasting through time; its four conditions are the protocol’s three questions (cooperate, adapt, tolerate disruption) and the fit between capacities and environment, supported by the summary’s design principles. Current reality proposes candidate causes: pressure for visible progress and fear of vulnerability jointly keeping fixes superficial, and free riders making cooperation hard to sustain. One conflict sets openness against guardedness in competitive fields, with a stated assumption. The changes are the Adaptive Persistence cycle, the summary’s rule for which capacity an environment calls for, the ACT group matrix, a lighter first pass for wary groups and agreed success criteria, which has no connection yet. Prerequisites and the five steps (orient, assess, analyse, adjust, repeat) are illustrative; no group, facilitator, owner or date is assigned. The summary’s four case studies are one attributed observation, the author’s own reports.

`pages.py` previously assumed every supplied-document commons was Margeret Heath’s talks. That wording now applies to Re-membering only; this commons gets its own About copy (`SUPPLIED_ABOUT`), review note and source labels. Re-membering’s pages are byte-identical.

## Approval

David accepted `pst-commons` revisions 1 and 2; the receipts are in the private collaboration record, and public delivery cites the receipt IDs only. Revision 2 renamed the commons and removed an earlier third source along with the statements and connections that relied on it alone; release `2026-10-26.1` was replaced in place because it had not been published live. Implementing the map does not endorse its reasoning.

## Validation and operation

Run `python3 apps/reasoning-demo/build.py`, `python3 -m unittest discover -s apps/reasoning-demo -p 'test_*.py'`, `python3 apps/reasoning-demo/build.py --check`, `node --check apps/reasoning-demo/app.js`, `python3 scripts/export-website.py` and `python3 scripts/check-website.py`. After a deliberate edit to `ltp/persistent-systems/reason-commons.yaml`, refresh only this registry with `refresh_reconstruction` from `build.py`. Whether Stephen finds the reconstruction faithful or useful, and whether it helps a real group, remain open.
