# Northbank Print worked commons

A generated, read-only fictional Adaptive Persistence engagement. The change log is the entry point; current reasoning, item history, prospective predictions, corrected reports and progress are connected views of one case. All authored reasoning is proposed. Fictional client agreement is described separately and never recorded as real human endorsement.

Canonical current reasoning is `ltp/examples/northbank-print/reason-commons.yaml`. Its companion `engagement.json` owns the thirteen dated events, historical item shapes, two prospective expectations, seven reports, six observation windows, metrics, sources and three deliberate fictional releases. There is no separately maintained current copy in the history. `historical()` replays item changes to derive a dated view; the final shapes must agree with the YAML. Meaningful revisions retain the exact prior shape, including joint causal conditions. Operational progress is distinct from the authored standing of the reasoning.

## Build and verify

Requires Python 3 and PyYAML, as do the existing reasoning helpers. From the repository root:

```sh
python3 apps/northbank-demo/build.py
python3 apps/northbank-demo/build_story.py
python3 -m unittest discover -s apps/northbank-demo -p 'test_*.py'
python3 apps/northbank-demo/build.py --check
python3 apps/northbank-demo/build_story.py --check
python3 scripts/export-website.py
python3 scripts/check-website.py
python3 -m http.server 8887 --bind 127.0.0.1 --directory website
```

Open `http://127.0.0.1:8887/demos/northbank-print/index.html`. Use `node scripts/phone-check.mjs http://127.0.0.1:8887/demos/northbank-print/index.html /private/tmp/northbank-phone.png` for a real 375px check. The viewer needs no network requests, external libraries, fonts, account or editing service. With JavaScript disabled or when printing, every entry, item and report remains readable. Hash links select views when JavaScript is enabled; browser back and forward work normally.

The three explicit public exports are `index.html`, `commons.json` and `reason-commons.yaml` under `website/demos/northbank-print/`. Build them; do not hand-edit them. The public YAML and JSON omit the real implementation receipt. The embedded JSON is identical to the downloadable data. No collaboration YAML, local paths, feedback sharing configuration or private material is exported. This artifact is self-contained and does not change the shared reasoning-demo generator or its publication policies.

## Maintenance

Edit reasoning first. Append a history change with an exact `before` shape when meaning changes; do not rewrite prior wording or a captured prediction. Add a correction linked both ways instead of replacing a report. Run the validator and regenerate. A report records evidence and a next decision; it does not automatically accept a causal connection. The May 28 review is pending, not invented as completed. Client review, publication routines and upkeep estimates are illustrative practices; autonomous monitoring, reminders and causal validation are not implemented.

## Trees used during facilitation

The history now contains `tree_uses`: authored fictional questions, client responses, decisions, focused statement/connection IDs and evidence references. These fields describe the facilitation scenes; they do not add claims, causal links or endorsements to the canonical reasoning. `tree_model()` selects only the nodes and connection shapes captured by the scene’s date. `tree_diagram()` draws that topology as responsive HTML, preserving shared AND conditions and keeping unconnected statements separate. Every statement and connection links to its current item history. Repeated source boxes on a separate harmful branch refer to the same item, not a second claim. Current views draw the causal, future and action relationships; full statements and ownership remain available underneath.

Scenes with `compare_with` lead with the earlier connection, the client’s check, the revised connection and the decision. Complete earlier and revised trees remain available in native disclosures. A focused connection always includes every joint source. Evidence is attached to its statement or connection, with links to the original report; validation rejects references to future reports or unavailable items. Gold and the words “In discussion” mark the question being examined, without changing reasoning standing. Action arrows say “comes before”; they do not imply causal success. The 18 January late-dispatch statement remains visibly unconnected because its incoming explanation was not recorded until 22 January. The readiness observations explicitly retain the missing baseline instead of presenting counts as proof of an increase.

## Complete AP walkthrough

The `ap` field in `engagement.json` owns fifteen dated fictional working records: Orient agreement, the five-factor assessment and twenty-four qualitative principle notes, group-owned capacity choices, two complete ACT passes, readiness, seven reassessments, and closure. Every added note is explicitly authored fiction. Each assessment retains findings, unknowns and a next check; capacity choices state an environmental demand, available capacity, considered alternatives and a consequential decision. ACT C records acknowledged difficulty and chosen action. None of these records changes the fifteen proposed reasoning statements or nine connections in the canonical YAML.

The October summary, internally dated 11 October 2026, is the procedural reference. September’s geographic context is retained and source differences remain explicit. A qualitative pass can contain unanswered questions. The source does not require a numeric scorecard, these case-specific thresholds or Reason Commons trees. A short absence is a limited check of decision cover, not proof of robustness to severe shocks.

`story.json` selects fifty-four concise views from the case. Its narration is checked verbatim against `docs/marketing/explainers/northbank-print/08-ap-script-v2.md`; the visual pass and source crosswalk are separate files beside it. `build_story.py` renders `story-template.html` to `website/explainers/northbank-print/index.html`. The template owns the page shell, inline visual style and fixed navigation; the builder owns illustrations, source links and orientation. Every drawing is static and readable without JavaScript. The script updates the current AP stage and reading position only. Published `beat-01` through `beat-40` bookmarks remain available; one earlier target view is now an alias in the combined prediction scene.

The declared digest in the AP record protects the existing metric definitions, windows, predictions, reports, releases and actions from accidental rewriting during this expansion. Validation rejects future evidence, incomplete factor profiles, a missing matrix question, a capacity choice without a mismatch and a C without acknowledged difficulty or action. These are consistency/completeness checks, not an authentication of a real consultation or a substitute for methodological review by Stephen and comprehension review by real readers.

Review the illustrated page at `http://127.0.0.1:8887/explainers/northbank-print/index.html`. AP record links open the corresponding expanded section in the full case; the viewer resolves nested record anchors to the correct dated entry. The full case and the presentation are two views of the same authored case data. The twenty-four baseline principle notes also appear after the story, with unknowns intact.
