# Why Things Last demonstration

The demonstration at `website/demos/reason-commons-in-use/persistent-systems/` is an entirely proposed AI reconstruction of Stephen Le’s Persistence Framework: Persistent Systems Theory, his proposal about why some structures keep going while others stop, and Adaptive Persistence, his protocol for cooperation in human groups. It uses the established `apps/reasoning-demo/` generator and components; the shared stylesheet, JavaScript, fonts and diagram renderer are unchanged.

## Sources and attribution

Three supplied documents, all in the public [persistent-systems-theory](https://github.com/dvdgdn/persistent-systems-theory) repository: *Why Things Last*, an introduction to Persistent Systems Theory from the Thrival theory compendium, which does not name its author; Stephen Le’s three-page *Adaptive Persistence* overview (30 September 2026); and his ten-page summary for Analogue Group, *Adaptive Persistence: A Meta-Protocol for Cooperation* (11 October 2026). Essay references give its numbered sections; PDF references give page numbers. Each source links to its original, which is why `build.py` now allows an optional `https` link on a `supplied_document` source.

The AI selected, paraphrased and connected the material; every statement and connection is attributed to the AI assistant, with source locators labelled paraphrase, reconstruction, inference or related point. Stephen Le has not reviewed or endorsed the map. David reports that Stephen agreed to his material appearing on the public site.

## What the map holds

79 proposed statements and 58 proposed connections across all six trees. The goal joins Adaptive Persistence’s aims (performance, trust and well-being, fewer conflicts) with the essay’s question of what lasts; its four conditions are the protocol’s three questions (cooperate, adapt, tolerate disruption) and the essay’s fit between capacities and environment, each supported by two of the summary’s 24 design principles. Current reality keeps three of the theory’s claims as unconnected attributed observations, then proposes candidate causes: pressure for visible progress and fear of vulnerability jointly keeping fixes superficial, growth and free riding, and cuts to reserves and experiments that look sensible in good weather. Two conflicts: reserves against experiments over one budget, and openness against guardedness in competitive fields, each with a stated assumption. The changes are the Adaptive Persistence cycle, the summary’s rule for which capacity an environment calls for, the ACT group matrix, a lighter first pass for wary groups, the essay’s walled-off variation and agreed success criteria, with the essay’s filing-cabinet warning as a negative branch. Prerequisites and the five steps (orient, assess, analyse, adjust, repeat) are illustrative; no group, facilitator, owner or date is assigned. The summary’s four case studies are one attributed observation, the author’s own reports.

`pages.py` previously assumed every supplied-document commons was Margeret Heath’s talks. That wording now applies to Re-membering only; this commons gets its own About copy (`SUPPLIED_ABOUT`) and plainer banner, review note and source labels. Re-membering’s pages are byte-identical.

## Approval

David accepted `pst-commons` revision 1; the receipt is in the private collaboration record, and public delivery cites the receipt ID only. The proposal estimated about 50 statements and 35 connections; the map has 79 and 58, mostly because each of the five steps needs a condition, an action and an effect. Implementing the map does not endorse its reasoning.

## Validation and operation

Run `python3 apps/reasoning-demo/build.py`, `python3 -m unittest discover -s apps/reasoning-demo -p 'test_*.py'`, `python3 apps/reasoning-demo/build.py --check`, `node --check apps/reasoning-demo/app.js`, `python3 scripts/export-website.py` and `python3 scripts/check-website.py`. After a deliberate edit to `ltp/persistent-systems/reason-commons.yaml`, refresh only this registry with `refresh_reconstruction` from `build.py`. Whether Stephen finds the reconstruction faithful or useful, and whether it helps a real group, remain open.
