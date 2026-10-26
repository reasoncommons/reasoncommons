# Readable LTP summary (draft)

**Status: draft, 2026-10-26.** Not yet linked from `SKILL.md`. It was written from the two research-group LTPs in October 2026 and is awaiting Rufus's review. Tracked in Beads.

When an LTP reaches an accepted milestone, write a summary that someone can read in five minutes without opening the YAML. The milestone is usually the end of the process, but can also be a signed-off goal tree, current reality tree or set of clouds. The YAML stays the source of truth. The summary is a view of it, written by the agent and updated when the trees change. Without one, the trees are effectively invisible: few people open a 1,500-line YAML file.

## Where it goes

- **An LTP that shapes the whole organisation or group** (purpose, strategy) goes in a `README.md` in the LTP's own folder. That makes it the folder's landing page (e.g. `purpose-ltp/README.md`). Point the folder's `context.md` "Outcome" section at it.
- **An LTP for a bounded project** goes in the project's `README.md`, under a `## LTP summary` heading below the SCQ (situation, complication, question). It replaces any "Next" or "LTP state" lines there. Keep the SCQ above it.
- If two LTPs share nodes, link across to the other summary rather than repeating its content.

## Sections, in order

1. **Opening paragraph:** the question, who worked on it and when, and the method in one line ("goal → what's wrong today → the conflicts underneath → the changes to make → a plan"). Then the standing: who signed it off, when, and that it is a working bet with a review point.
2. **TL;DR**, as 3–5 bullets:
   - the goal;
   - the core problem, with its deeper cause if the current reality tree found one;
   - what we'll do;
   - when, and where the work is tracked (Beads epic name, no task IDs).
3. **Goal tree**, in ASCII: goal → CSFs → NCs, each with its ID and a short label. Mark each CSF or NC as MET, PARTLY, NOT MET or UNCLEAR. Say plainly that the marks are the summary's own reading of the current reality tree, not part of the signed-off trees. Gloss CSF and NC once.
4. **Current reality:**
   - the undesirable effects, as a numbered list with one line each;
   - a small ASCII sketch of causes → effects, by ID;
   - which effects have no traced cause.
   - Optionally, a sentence on the virtuous loop the group wants, if the trees imply one (e.g. a flywheel).
5. **Conflict clouds:** say what an injection is, once. For each cloud:
   - a question as its heading;
   - the broken assumption, and who judged it key if the YAML says so;
   - the injection.
   Draw ASCII clouds (A; B and C; D and D′) for the two or three that matter most, and give the rest in short form, without the drawing.
6. **Future reality**, as a table: injection → the effects (and causes) it removes. Then:
   - say which injections were agreed and that their effect is a prediction to test;
   - give the predicted chain in one line;
   - list the risks checked (negative branches), each with its answer or "accepted as a risk".
7. **What we'll do:** from the prerequisite tree if there is one, grouped into stages that follow its agreed sequence. Use arrows for "must come first", put obstacles in square brackets, and give dates or fixed points. With no prerequisite tree, give the injections as next actions.
8. **Open questions:** only the few that matter, including untested necessity.
9. **Links:** the YAML, `context.md`, goal options or similar, sibling LTPs, and governing documents.

## Writing rules

- **Plain English, short sentences.** Explain each method term once (CSF, NC, injection, cloud, SOP).
- **Keep the meaning.** Use the YAML's own labels, shortened if needed but never reworded into new claims. Keep decided apart from hypothesis, and agreed apart from predicted.
- **Assume the page is public**, even if the repo isn't yet:
  - describe people's positions neutrally;
  - don't characterise individuals' capacity or leanings beyond what they would sign;
  - don't label anyone's view a "guess" or a "pull against" something.
- **ASCII:** fenced code blocks, at most 70 characters wide so they read on a phone, with box-drawing characters. Split a large tree by CSF rather than drawing one big diagram.
- **Length:** about two or three screens. Detail stays in the YAML.

## Process

1. Read the accepted trees in the YAML, and `context.md` for who, when and sign-off.
2. Draft the summary.
3. Have a subagent critique it against the YAML (fidelity, tone, width, length), then fold its points in with judgement.
4. Commit, show the human, and push only on their OK.

## Examples

- [Research group purpose: LTP summary](https://github.com/life-itself/research/blob/main/purpose-ltp/README.md): an LTP for the whole group. This is the best example so far: copied to [examples/research-purpose-ltp-summary.md](examples/research-purpose-ltp-summary.md).
- [Research web and knowledge presence: LTP summary](https://github.com/life-itself/research/blob/main/projects/2026-10-research-community/README.md#ltp-summary): a project LTP, with the summary below the SCQ, linked to the purpose LTP for the nodes they share.

Both started from a shorter brief (2026-10-26). The purpose summary added the opening paragraph with its standing, the note on the status marks, the "untraced effects" line, the flywheel sentence, clouds in short form, the risks checked and the staged prerequisite plan. Those additions are now folded into the sections above.
