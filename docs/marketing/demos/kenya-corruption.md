# Corruption in Kenya, 2014 demonstration

The demonstration at `website/demos/reason-commons-in-use/kenya-corruption/` is an entirely proposed AI reconstruction of Transparency International’s Anti-Corruption Helpdesk brief *Overview of corruption and anti-corruption in Kenya*, by Samira Lindner, dated 15 October 2014. It uses the established `apps/reasoning-demo/` generator and components; the shared stylesheet, JavaScript, fonts and diagram renderer are unchanged.

## Source and attribution

One public document: the 16-page brief, [on Transparency International’s Knowledge Hub](https://knowledgehub.transparency.org/helpdesk/overview-of-corruption-and-anti-corruption-in-kenya) with a [PDF](https://knowledgehub.transparencycdn.org/helpdesk/Country_profile_Kenya_2014.pdf). It answers a European Commission query with a focus on public financial management and updates a 2012 U4 answer. The site licenses it CC BY-ND 4.0 and the PDF says all rights reserved, so the map paraphrases and links; it does not reproduce the brief. References give PDF page numbers.

The AI selected, paraphrased and connected the material; every statement and connection is attributed to the AI assistant, with page locators labelled paraphrase, reconstruction, inference or related point. Transparency International has not reviewed or endorsed the map. Figures the brief cites from other indices and surveys are attributed observations and have not been checked. The brief names officials in connection with allegations and charges, several pending in 2014 and some since dropped; the map describes those cases by kind and names nobody, which a test enforces.

## What the map holds

91 proposed statements and 73 proposed connections across all six trees, all describing Kenya as of 2014. The goal, inferred from the brief’s focus, is that public money is raised, spent and audited openly and abuse of office is punished; six conditions sit under it, with eight supporting conditions. Current reality keeps two framing observations unconnected (index rankings, and a government elected against corruption that soon faced its own scandals) and proposes candidate causes: weak political will, diluted laws, a commission that cannot prosecute and overloaded courts lead to senior officials rarely being convicted and trust falling from 70% to 34%; thin budget oversight leads to lost school funds and KSh 34 billion without records; patronage parties, opaque campaign money and procurement favouritism lead to vote-buying and firms paying for contracts; weak police oversight leaves the police the most bribed institution. The two conflicts are ones the brief records: repaying donors for stolen school funds from the treasury or from those responsible, and settling out of court or prosecuting. The changes are the AI’s inferences from the gaps the brief identifies, with three risks each paired with what is meant to prevent it. Prerequisites come from the obstacles to reform the brief describes. Three illustrative steps follow one reform bill; nobody is assigned.

## Approval

David accepted `kenya-commons` revision 1; the receipt is in the private collaboration record, and public delivery cites the receipt ID only. The proposal estimated about 70 statements and 50 connections; the map has 91 and 73, mostly because the brief’s separate causes and both dilemmas are kept whole. Implementing the map does not endorse its reasoning.

## Validation and operation

Run `python3 apps/reasoning-demo/build.py`, `python3 -m unittest discover -s apps/reasoning-demo -p 'test_*.py'`, `python3 apps/reasoning-demo/build.py --check`, `node --check apps/reasoning-demo/app.js`, `python3 scripts/export-website.py` and `python3 scripts/check-website.py`. After a deliberate edit to `ltp/kenya-corruption/reason-commons.yaml`, refresh only this registry with `refresh_reconstruction` from `build.py`. What has changed in Kenya since 2014, and whether people working on corruption there find the map useful, remain open.
