# Northbank Print worked commons

A generated, read-only fictional Adaptive Persistence engagement. The change log is the entry point; current reasoning, item history, prospective predictions, corrected reports and progress are connected views of one case. All authored reasoning is proposed. Fictional client agreement is described separately and never recorded as real human endorsement.

Canonical current reasoning is `ltp/examples/northbank-print/reason-commons.yaml`. Its companion `engagement.json` owns the thirteen dated events, historical item shapes, two prospective expectations, seven reports, six observation windows, metrics, sources and three deliberate fictional releases. There is no separately maintained current copy in the history. `historical()` replays item changes to derive a dated view; the final shapes must agree with the YAML. Meaningful revisions retain the exact prior shape, including joint causal conditions. Operational progress is distinct from the authored standing of the reasoning.

## Build and verify

Requires Python 3 and PyYAML, as do the existing reasoning helpers. From the repository root:

```sh
python3 apps/northbank-demo/build.py
python3 -m unittest discover -s apps/northbank-demo -p 'test_*.py'
python3 apps/northbank-demo/build.py --check
python3 scripts/export-website.py
python3 scripts/check-website.py
python3 -m http.server 8887 --bind 127.0.0.1 --directory website
```

Open `http://127.0.0.1:8887/demos/northbank-print/index.html`. Use `node scripts/phone-check.mjs http://127.0.0.1:8887/demos/northbank-print/index.html /private/tmp/northbank-phone.png` for a real 375px check. The viewer needs no network requests, external libraries, fonts, account or editing service. With JavaScript disabled or when printing, every entry, item and report remains readable. Hash links select views when JavaScript is enabled; browser back and forward work normally.

The three explicit public exports are `index.html`, `commons.json` and `reason-commons.yaml` under `website/demos/northbank-print/`. Build them; do not hand-edit them. The public YAML and JSON omit the real implementation receipt. The embedded JSON is identical to the downloadable data. No collaboration YAML, local paths, feedback sharing configuration or private material is exported. This artifact is self-contained and does not change the shared reasoning-demo generator or its publication policies.

## Maintenance

Edit reasoning first. Append a history change with an exact `before` shape when meaning changes; do not rewrite prior wording or a captured prediction. Add a correction linked both ways instead of replacing a report. Run the validator and regenerate. A report records evidence and a next decision; it does not automatically accept a causal connection. The May 28 review is pending, not invented as completed. Client review, publication routines and upkeep estimates are illustrative practices; autonomous monitoring, reminders and causal validation are not implemented.
