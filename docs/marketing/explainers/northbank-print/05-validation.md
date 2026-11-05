# Northbank Print scrolling presentation: validation

Proposal: `northbank-scroll-story` revision 1 by `david`. The acceptance receipt and the two open collaboration review entries are retained in the primary workspace's collaboration YAML, separately from this presentation checkout. Implementation approval does not endorse the fictional reasoning or establish that this retelling is useful.

## Result

`website/explainers/northbank-print/index.html` is a self-contained scrolling presentation with forty static illustrated views covering all thirteen original events, in order. It uses warm paper, ink and terracotta, a consistent order-record metaphor, and focused reasoning fragments. Normal browser scrolling is the only required input. Each view links to its original dated engagement entry. The existing Northbank demo, its generator, canonical reasoning and exported data remain unchanged.

The v2 script contains 1,232 words. Its narration is preserved exactly in the visual script and page, with the original Orient criteria grouped before the completed Assess baseline. The longest narration block is forty-four words. An editorial accuracy check replaced “twelve-week trial” with “twelve-week engagement”: the engagement lasts twelve weeks, while the operational trials start later. The visual script was regenerated after that correction.

The script, adversarial critique and revision were committed before the visual script; the visual script was committed before the build. Editorial review was performed by the author. No independent human editorial review or reader-comprehension test is claimed.

## Source integrity

- All thirteen event dates and titles match `ltp/examples/northbank-print/engagement.json`; the forty page views retain their chronological order.
- The embedded metric definitions, all six observation windows, both predictions, all seven reports and all three releases equal the source values exactly.
- Both displayed joint connections retain every original source and their target: `nb-r-l1` has waiting authority and premature release; `nb-f-l1` has the revised adjustment and authorized cover with paid preparation.
- The 18 January explanation appears in its initial dated form. The first meeting-to-decision expectation remains distinguishable from the later joint condition. Action connections say “comes before”, rather than claiming causal success.
- The first-week report retains 17/20 beside the corrected 11/20. The full first trial retains 21/40 decisions and 16/80 late dispatches, against its original 32/40 and 12/80 expectation. Two unpaid preparation hours are paid and included in the corrected nineteen-hour week.
- The first-trial target stays separate from the ten-percent completion criterion. Missing speaking-up responses remain missing. The revised trial gets its own prospective window. Readiness has no invented baseline. March qualifies without proving a unique cause; May remains one failed window and 28 May remains pending.
- SHA-256 comparisons confirm that the canonical example YAML, engagement JSON and all three original public demo files are unchanged from the source checkout.
- The public HTML embeds no implementation acceptance receipts or collaboration material.

## Browser checks

| Viewport | Views checked | Result |
| --- | --- | --- |
| 1440 × 900 | 40 | No horizontal overflow or narration/diagram collision; key moments and full contact sheets visually reviewed. |
| 1280 × 720 | 40 | After compact-layout revision, all figures end above the fixed reading rail; no clipped leaf labels or narration/diagram collision. |
| 390 × 844 | 40 | Each complete figure fits beneath its headline and above the reading rail; no clipped leaf labels or horizontal overflow. Supporting narration follows the figure. |
| Real emulated 375px device | Entire document | Repository `scripts/phone-check.mjs` reports viewport 375px, scrollWidth 375px and no overflowing elements. |

Browser inspection caught and corrected merged words at forced label breaks, an opening illustration extending under the reading rail at short desktop height, and a phone layout that placed an AND connection's target below the first screen. On phones, the drawing now directly follows the headline; the unchanged narration follows the drawing. Short desktop layouts reduce drawing spacing while retaining readable labels.

Reverse scrolling was checked around the revised future connection: from view 25, two upward page scrolls reached view 23; two downward page scrolls returned to view 25. The complete joint-connection text was unchanged, and the date/view indicator followed the visible scene. The diagrams do not depend on previous animation states.

The script-free fixture contains zero scripts and retains all forty displayed narration blocks and figures. It was inspected at phone width on the revised joint condition. A reduced-motion fixture applies the same motion-suppression declarations as the page's preference rule; it retains forty scenes, zero animated elements and no horizontal overflow. The page itself contains no animated diagrams, scroll snapping, timed playback or programmatic scrolling. These are fixture and source checks; a native operating-system preference toggle and a browser setting disabling JavaScript were not exercised.

Screenshots, contact sheets and geometry observations are local QA artifacts under `/private/tmp/northbank-story-qa/`, outside the publishing root. The screenshots cover every view at each of the three presentation sizes. The script-free and motion-suppressed fixtures are also outside the repository and are not published.

## Checks and local review

```sh
python3 apps/northbank-demo/build.py --check
python3 scripts/export-website.py
python3 scripts/check-website.py
python3 -m http.server 8893 --bind 127.0.0.1 --directory website
node scripts/phone-check.mjs http://127.0.0.1:8893/explainers/northbank-print/index.html
```

Source validation passes. Website exports are current. The website checker reports 8,723 links/assets, zero errors and zero missing links. The preview is `http://127.0.0.1:8893/explainers/northbank-print/index.html` while its local server is running. No remote preview, production deployment, push or pull request is included in this delivery.

## Review still needed

The existing `review_northbank_story` and `review_northbank_demo` work remains open. Stephen and client readers have not reviewed this presentation. A useful comprehension review would ask readers to explain why Ben was not assigned a sales fix, why the first decision count changed, which conditions the revised arrangement needs, and why May prompts another review without erasing March. Their answers, difficulties and proposed corrections should inform the next revision; these questions have not been asked in a real audience test.
