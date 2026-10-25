# David Joseph’s analysis of the Wisdom and AI map

Supplied by David Joseph on 25 October 2026. This is a proposed analysis of the initial map, not empirical evidence or endorsement of the resulting trees. Section numbers below are the source locators used by the demonstration.

I’d **expand the goal and diagnosis, then make the proposed interventions follow from them**. The [published map](https://reasoncommons.com/demos/reason-commons-in-use/wisdom-ai/map.html) currently contains trees 1, 2 and 4; trees 3, 5 and 6 would be new drafts.

Everything below should enter as **proposed reasoning**. Keep the [original research questions](https://ai.lifeitself.org/) attached as questions, with separate attribution for these additional claims.

1. **Goal tree: make substantive judgment central.**

   Replace the current goal with this proposed wording:

   > People and institutions approach AI development and use wisely, with defensible reasons for the aims, risks and responsibilities they accept.

   Develop candidate necessary conditions under the source’s four strands:

   | Branch | Proposed condition to investigate |
   |---|---|
   | Alignment | The intended ends are ethically defensible, and claims that AI will pursue them are adequately supported. |
   | Risk and pace | Development choices account for alignment uncertainty, catastrophic consequences and feasible alternatives. |
   | Broader impacts | Adoption decisions account for human agency, relationships and institutions. |
   | Consciousness | Treatment of AI responds responsibly to uncertainty about its possible moral standing. |

   Across each branch, examine what particular wisdom traditions contribute, where they disagree and where their analogies fail.

   Retain **understanding consequences** and **revising decisions** as supporting conditions. Add the capacity to exercise restraint before consequences become irreversible. These conditions need justification; listing them does not establish their necessity or sufficiency.

2. **Current Reality Tree: replace the single uncertainty explanation with competing causal hypotheses.**

   Keep the existing uncertainty branch, but stop treating it as the central explanation without evidence. Add candidate branches such as:

   - **Contested ends + implicit value choices** → apparently technical alignment disagreements conceal ethical disagreements.
   - **Competitive pressure + perceived disadvantage from restraint + weak coordination** → actors proceed despite recognising risks.
   - **Delegation of judgment + reduced opportunities to practise it** → some AI uses weaken human agency.
   - **Uncertain AI moral standing + absent decision criteria** → potentially important moral considerations receive inconsistent treatment.

   Each arrow needs a mechanism and supporting observations before acceptance. Preserve alternatives: uncertainty could encourage restraint; AI assistance could strengthen judgment.

   The task here is to discover **which problems occur, under which conditions, and what sustains them**. The source’s questions alone cannot establish those findings.

3. **Conflict Cloud: represent a specific development decision and the legitimate needs on both sides.**

   A candidate cloud for **one specified capability and release decision**:

   ```mermaid
   flowchart TD
       A["Defensible AI development"] -->|needs| B["Timely benefits and security"]
       A -->|needs| C["Protection against unacceptable harm"]
       B -.->|assumed to require| D["Release this capability now"]
       C -.->|assumed to require| E["Defer this capability"]
       D <-->|conflict| E
   ```

   Attach the assumptions that make the positions seem necessary:

   - Why would obtaining benefits or protecting security require release **now**?
   - Why would preventing unacceptable harm require deferral?
   - Could narrower capabilities, restricted access, safeguards or coordinated restraint satisfy both needs?
   - Would a slower trajectory create other serious risks?

   Keep this as a candidate conflict until relevant participants recognise both needs. Review points may help, but they do not automatically resolve the conflict.

4. **Future Reality Tree: make review conditional, and add interventions addressing values and incentives.**

   Replace the direct review-to-revision connection with:

   > Explicit review points **AND** usable evidence **AND** authority and incentives to act **AND** feasible alternatives → consequential revision becomes possible.

   Then add proposed intervention branches:

   | Proposed change | Mechanism to test | Expected intermediate effect |
   |---|---|---|
   | Make ethical aims and disagreements explicit | Exposes assumptions hidden inside evaluations | Alternatives can be assessed against defensible criteria. |
   | Introduce a specified wisdom-derived practice | Changes attention, motivation or judgment through an identified mechanism | A relevant aspect of decision making improves. |
   | Establish proportionate safeguards or coordination | Changes what actors can or are motivated to do | Restraint or redirection becomes practicable. |

   Each branch needs evidence; invoking wisdom does not establish an effect.

   Add a negative branch: **formal review → unwarranted reassurance → premature action**. A corresponding design requirement is that completing a review cannot substitute for meeting substantive criteria. Where harms are irreversible, safeguards must operate before the action.

5. **Prerequisite Tree: identify what must become true before testing an intervention.**

   Set a bounded objective: **One proposed decision practice can be responsibly tested in a defined setting.**

   | Obstacle | Necessary intermediate objective |
   |---|---|
   | “Wise” remains underspecified | Evaluation criteria, disagreements and unacceptable outcomes are explicit. |
   | The causal diagnosis is unsupported | Evidence distinguishes the leading explanation from credible alternatives. |
   | The contribution from a tradition is vague | A specific practice, proposed mechanism and limits are identified. |
   | The proposed change exceeds participants’ powers | A feasible intervention and relevant decision authority are identified. |
   | Success could be confused with completing the process | Outcome measures, guardrails and reconsideration criteria are defined. |

   Draw dependencies where they matter. For example, selecting a test requires both a sufficiently clear outcome and a plausible mechanism.

6. **Transition Tree: turn the bounded test into executable steps.**

   Each step should contain **current condition + action → expected effect**, rather than a task alone.

   | Current condition | Proposed action | Expected effect |
   |---|---|---|
   | The model discusses AI choices generally | Select one actor, decision and time horizon | The alternatives and responsibilities become concrete. |
   | Important premises remain implicit | Record ethical aims, empirical claims and disagreements | The decision’s justification becomes inspectable. |
   | Several explanations could fit | Gather evidence that distinguishes them | The intervention targets a better-supported mechanism. |
   | A bounded intervention is sufficiently justified | Specify and, where appropriate, conduct a test with guardrails | Evidence becomes available about its effects. |
   | Results are available | Compare them with the recorded prediction and alternatives | Revise the affected claims and next decision. |

   Owners and dates should remain unassigned until someone makes an actual commitment. Where a safe test is unavailable, the next action should gather information or improve safeguards.

Across all six trees, retain a visible distinction between **source question, proposed answer, causal hypothesis, supporting evidence and action commitment**. In particular, the trees should allow the investigation to reject the review-points proposal if another diagnosis or intervention proves stronger.
