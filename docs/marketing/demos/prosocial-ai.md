# Evolving Prosocial AI demonstration

The demonstration at `website/demos/reason-commons-in-use/prosocial-ai/` is an entirely proposed AI reconstruction of Paul Atkins and David Sloan Wilson’s *Evolving Prosocial AI: How We Shape the Systems that Shape AI - and Us*. It uses the established `apps/reasoning-demo/` generator and components; the shared stylesheet, JavaScript, fonts and diagram renderer are unchanged.

## Source and attribution

One supplied document: the 67-page manuscript, version of 28 June 2026, accepted for Cambridge Elements in Applied Evolutionary Science. References give PDF page numbers, which match the manuscript’s own, with the section heading. The manuscript is not public yet, so the source is not linked and the file is not published. David also supplied the 6 March 2026 draft that was circulated on Substack; the later version supersedes it, so the map does not cite it, and About says so.

The AI selected, paraphrased and connected the material; every statement and connection is attributed to the AI assistant, with page locators labelled paraphrase, reconstruction, inference or related point. The authors have not reviewed or endorsed the map. Findings they cite from other work, such as Ostrom’s Nepal irrigation studies and vTaiwan’s legislative record, are attributed observations and have not been checked.

## What the map holds

105 proposed statements and 88 proposed connections across all six trees. The goal is AI that strengthens cooperation and flourishing at every scale. Six conditions sit under it: the four scales of Sections 3 and 4, institutions that make cooperation pay, with Ostrom’s core design principles and a capability measure as their conditions, and prosocial worldviews. Current reality keeps three framing claims as unconnected attributed observations: worldviews as replicators, machine behaviour and the partial evolutionary transition. It then proposes candidate causes: the four extractive worldviews, held up by power and training and joined with temporal discounting, shape what institutions reward, which leads to eroded capabilities, a race to the bottom, epistemic breakdown, unaccountable public systems, inequality and ecological costs, and finally the social trap. There are two conflicts, each with a stated assumption: a firm keeping up with rivals while avoiding harm, and a person choosing between convenience and keeping a skill. The proposed changes are the design principles, scaffolding design, honoured preferences, ownership models, bridging algorithms, measurement, procurement audits, energy reporting, demonstrations, networks, stories, and learning from communities that already govern commons. The authors’ own cautions appear as risks: imposed principles, weakened shared understanding, late fact-checks and the movement paradox. Prerequisites come from the authors’ limits. Four illustrative steps follow the book’s closing suggestions for researchers, technologists, policymakers and funders; nobody is assigned.

## Approval

David accepted `pai-commons` revision 1; the receipt is in the private collaboration record, and public delivery cites the receipt ID only. The proposal estimated about 85 statements and 70 connections; the map has 105 and 88, mostly because all eight core design principles and every scale’s harms are kept as separate statements. Implementing the map does not endorse its reasoning.

## Validation and operation

Run `python3 apps/reasoning-demo/build.py`, `python3 -m unittest discover -s apps/reasoning-demo -p 'test_*.py'`, `python3 apps/reasoning-demo/build.py --check`, `node --check apps/reasoning-demo/app.js`, `python3 scripts/export-website.py` and `python3 scripts/check-website.py`. After a deliberate edit to `ltp/prosocial-ai/reason-commons.yaml`, refresh only this registry with `refresh_reconstruction` from `build.py`. Whether the authors find the reconstruction faithful or useful remains open.
