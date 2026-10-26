#!/usr/bin/env python3
"""Validate feedback commitments and derive recipient queues from the reasoning YAML.

The CLI is read-only. Hosts save validated changes with their normal file tools.
"""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path


VERDICTS = {"observed", "not_observed", "unclear", "not_assessed", "unavailable"}
READINESS = {"experienced", "not_yet", "cannot_assess"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def timestamp(value):
    require(isinstance(value, str), "Feedback timestamps must be quoted ISO 8601 strings.")
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise ValueError("Invalid feedback timestamp.") from None
    require(result.tzinfo is not None, "Feedback timestamps require a timezone.")
    return result


def utc_now():
    return datetime.now(timezone.utc)


def snapshot(state, ref):
    for tree, data in state["trees"].items():
        for node in data["nodes"]:
            if node["id"] == ref:
                return {"ref": ref, "tree": tree, "kind": node["kind"],
                        "standing": node.get("status", "proposed"), "text": node["text"]}
    raise ValueError(f"Unknown prediction statement: {ref}")


def new_request(state, ident, about, benefits, reservations, feedback_from, by, *, recorded_at=None, **optional):
    """Prepare a new immutable prediction version; this does not save or send it."""
    revision = 1 + max((r["revision"] for r in state.get("feedback_requests", []) if r["id"] == ident), default=0)
    request = {"id": ident, "revision": revision, "created_by": by,
               "recorded_at": recorded_at or utc_now().isoformat(),
               "about": snapshot(state, about), "feedback_from": list(feedback_from),
               "benefits": [snapshot(state, ref) for ref in benefits],
               "reservations": [snapshot(state, ref) for ref in reservations], "reports": [], **optional}
    trial = deepcopy(state)
    trial.setdefault("feedback_requests", []).append(request)
    guard_transition(state, trial)
    return request


def key(request):
    return request["id"], request["revision"]


def outcomes(request):
    return request["benefits"] + request["reservations"]


def find(state, ident, revision):
    for request in state.get("feedback_requests", []):
        if key(request) == (ident, revision):
            return request
    raise ValueError("Unknown feedback request/version; inspect the saved request first.")


def validate(state):
    people = state.get("participants", {})
    requests = state.get("feedback_requests", [])
    require(isinstance(requests, list), "feedback_requests must be a list.")
    seen, report_ids = set(), set()
    for request in requests:
        require(isinstance(request, dict), "A feedback request must be a mapping.")
        require(isinstance(request.get("id"), str) and bool(request["id"].strip()), "Feedback request needs an ID.")
        require(type(request.get("revision")) is int and request["revision"] > 0, "Feedback revision must be a positive integer.")
        require(key(request) not in seen, "Duplicate feedback request/version.")
        seen.add(key(request))
        require(request.get("created_by") in set(people) | {"assistant"}, "Unknown feedback creator.")
        timestamp(request.get("recorded_at"))
        providers = request.get("feedback_from")
        require(isinstance(providers, list) and bool(providers) and all(isinstance(p, str) and p in people for p in providers),
                "Feedback requires named human feedback_from participants.")
        require(len(providers) == len(set(providers)), "Duplicate feedback providers.")
        for field in ("benefits", "reservations", "reports"):
            require(isinstance(request.get(field), list), f"Feedback {field} must be a list.")
        require(bool(outcomes(request)), "Feedback needs at least one expected benefit or reservation.")
        for item in [request.get("about")] + outcomes(request):
            require(isinstance(item, dict), "Feedback needs original statement snapshots.")
            for field in ("ref", "tree", "kind", "text"):
                require(isinstance(item.get(field), str) and bool(item[field].strip()), f"Feedback snapshot needs {field}.")
            require(item.get("standing") in {"proposed", "accepted", "disputed"}, "Invalid feedback snapshot standing.")
        refs = [o["ref"] for o in outcomes(request)]
        require(len(refs) == len(set(refs)), "A feedback outcome cannot be both benefit and reservation or repeated.")
        if request.get("ask_after") is not None:
            require(timestamp(request["ask_after"]) >= timestamp(request["recorded_at"]), "ask_after precedes capture.")
        if "ready_when" in request:
            require(isinstance(request["ready_when"], str) and bool(request["ready_when"].strip()), "ready_when must describe the observation opportunity.")
        for report in request["reports"]:
            require(isinstance(report, dict), "Feedback report must be a mapping.")
            ident = report.get("id")
            require(isinstance(ident, str) and bool(ident.strip()) and ident not in report_ids, "Duplicate/missing feedback report ID.")
            report_ids.add(ident)
            require(report.get("by") in providers, "Feedback report author must be an assigned human provider.")
            require(timestamp(report.get("recorded_at")) >= timestamp(request["recorded_at"]), "Report predates its prediction capture.")
            require(report.get("readiness") in READINESS, "Unknown feedback readiness.")
            require(isinstance(report.get("text"), str) and bool(report["text"].strip()), "Keep the person's actual feedback text.")
            require(report.get("evidence_type") == "self_report", "Feedback is attributed self-report, not automatic verification.")
            if report.get("observed_at") is not None:
                require(timestamp(report["observed_at"]) <= timestamp(report["recorded_at"]), "Observation is later than its recording.")
            if report.get("defer_until") is not None:
                require(timestamp(report["defer_until"]) > timestamp(report["recorded_at"]), "Deferral must be in the future.")
            answers = report.get("outcomes")
            require(isinstance(answers, list), "Feedback outcomes must be a list.")
            answer_refs = []
            for answer in answers:
                require(isinstance(answer, dict) and answer.get("ref") in refs, "Feedback refers to an unknown outcome.")
                require(answer.get("verdict") in VERDICTS, "Unknown feedback outcome verdict.")
                require(isinstance(answer.get("note"), str) and bool(answer["note"].strip()), "Feedback outcome needs its explanation.")
                if report["readiness"] != "experienced":
                    require(answer["verdict"] in {"not_assessed", "unavailable"}, "Unexperienced change cannot have an observed outcome verdict.")
                answer_refs.append(answer["ref"])
            require(len(answer_refs) == len(set(answer_refs)), "Duplicate outcomes in one feedback report.")
            require(report["readiness"] != "experienced" or bool(answers), "An experienced report must identify the outcomes assessed or still unassessed.")


def guard_transition(before, after, authors=None):
    """Check before/after when saving: preserve original expectations and reports."""
    validate(before)
    validate(after)
    previous = {key(r): r for r in before.get("feedback_requests", [])}
    current = {key(r): r for r in after.get("feedback_requests", [])}
    require(previous.keys() <= current.keys(), "Feedback versions cannot be removed; preserve their evidence.")
    for name in {ident[0] for ident in current if ident not in previous}:
        last = max((revision for ident, revision in previous if ident == name), default=0)
        new = sorted(revision for ident, revision in current if ident == name and (ident, revision) not in previous)
        require(new == list(range(last + 1, last + 1 + len(new))), "New feedback revision must follow the previous saved revision.")
    for ident, request in current.items():
        old = previous.get(ident)
        if old:
            require({k: v for k, v in request.items() if k != "reports"} == {k: v for k, v in old.items() if k != "reports"},
                    "Original feedback expectations are immutable; add a new revision.")
            previous_reports = {report["id"]: report for report in old["reports"]}
            current_reports = {report["id"]: report for report in request["reports"]}
            require(all(current_reports.get(ident) == report for ident, report in previous_reports.items()), "Previous feedback reports are append-only.")
            added = [report for report in request["reports"] if report["id"] not in previous_reports]
        else:
            for item in [request["about"]] + outcomes(request):
                require(item == snapshot(after, item["ref"]), "New expectation snapshots must match actual saved reasoning.")
            if authors is not None:
                require(request["created_by"] in set(authors) | {"assistant"}, "Feedback creator requires authenticated attribution.")
            added = request["reports"]
        if authors is not None:
            require(all(r["by"] in authors for r in added), "Feedback cannot impersonate another participant.")


def latest_assessments(request, person):
    """Each outcome's most recent assessment by this provider, in chronological order."""
    latest = {}
    own = [r for r in request["reports"] if r["by"] == person]
    for report in sorted(own, key=lambda r: (timestamp(r["recorded_at"]), r["id"])):
        for answer in report["outcomes"]:
            if answer["verdict"] != "not_assessed":
                latest[answer["ref"]] = answer
    return latest


def outstanding(request, person):
    # An unclear assessment is inconclusive, so the outcome stays open until a later
    # report settles it as observed, not observed or unavailable.
    latest = latest_assessments(request, person)
    return [o["ref"] for o in outcomes(request) if o["ref"] not in latest or latest[o["ref"]]["verdict"] == "unclear"]


def queue(state, person, now=None, *, include_waiting=False):
    """Every unanswered outcome remains discoverable, including undated requests."""
    validate(state)
    require(person in state["participants"], "Choose a known human participant.")
    now = now or utc_now()
    rows = []
    for request in state.get("feedback_requests", []):
        if person not in request["feedback_from"]:
            continue
        pending = outstanding(request, person)
        if not pending:
            continue
        own_reports = [r for r in request["reports"] if r["by"] == person]
        dates = [request.get("ask_after")]
        if own_reports:
            latest = max(own_reports, key=lambda report: (timestamp(report["recorded_at"]), report["id"]))
            dates.append(latest.get("defer_until"))
        dates = [timestamp(d) for d in dates if d]
        available = max(dates) if dates else None
        waiting = available is not None and available > now
        if waiting and not include_waiting:
            continue
        rows.append({"id": request["id"], "revision": request["revision"], "participant": person,
                     "pending": pending, "state": "waiting" if waiting else "ready",
                     "available_at": available.isoformat() if available else None,
                     "request": request})
    return sorted(rows, key=lambda row: (row["available_at"] or "", row["request"]["recorded_at"], row["id"], row["revision"]))


def render_request(state, request, person):
    require(person in request["feedback_from"], "This participant is not assigned to this feedback request.")
    def describe(item):
        return (f"{item['tree'].replace('_', ' ').title()} · {item['kind'].replace('_', ' ').title()} · "
                f"{item['standing'].title()} — {item['ref']}: {item['text']}")
    lines = ["Type: Feedback request", f"For: {state['participants'][person]}",
             f"Request: {request['id']} · revision {request['revision']}",
             "Change being evaluated (original wording): " + describe(request["about"])]
    for label, field in (("Expected benefit", "benefits"), ("Possible harmful consequence", "reservations")):
        if not request[field]:
            lines.append(f"{label}: none recorded.")
        for item in request[field]:
            lines.append(f"{label} (at prediction capture): " + describe(item))
    if request.get("ready_when"):
        lines.append("Observation opportunity: " + request["ready_when"])
    pending = outstanding(request, person)
    lines.append("Still awaiting your assessment: " + (", ".join(pending) if pending else "none; further observations can still be recorded."))
    latest = latest_assessments(request, person)
    for ref in pending:
        if ref in latest:
            lines.append(f"Earlier you found {ref} unclear: {latest[ref]['note']}")
    lines += ["Have you experienced this change sufficiently to comment? What happened regarding the expected benefit and possible harm, including anything unexpected?",
              "You can report not experienced yet, unclear, not assessed, or evidence unavailable, and defer. No answer is inferred from silence; feedback does not endorse the reasoning."]
    return "\n\n".join(lines)


def retain_review_work(state, request, report):
    # A collected observation still needs interpretation against the reasoning.
    # Keep that work in the existing reasoning backlog, without changing standing.
    if any(answer["verdict"] != "not_assessed" for answer in report["outcomes"]):
        for tree in state["trees"].values():
            if any(node["id"] == request["about"]["ref"] for node in tree["nodes"]):
                if any(task.get("feedback_report") == report["id"] for task in tree["backlog"]):
                    break
                tree["backlog"].append({"ref": request["about"]["ref"], "work": "review_outcome_feedback",
                    "label": "Review recorded outcome feedback against the original reasoning.",
                    "feedback_request": request["id"], "feedback_revision": request["revision"], "feedback_report": report["id"],
                    "note": "Compare this attributed self-report with the original expectation and the trial conditions; no endorsement or causal conclusion was inferred."})
                break


def add_report(state, ident, revision, report):
    result = deepcopy(state)
    request = find(result, ident, revision)
    for existing in request["reports"]:
        if existing["id"] == report["id"]:
            require(existing == report, "Feedback report ID reused with different content.")
            return result
    request["reports"].append(deepcopy(report))
    retain_review_work(result, request, report)
    guard_transition(state, result, {report["by"]})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("state", type=Path)
    parser.add_argument("--participant", required=True)
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--include-waiting", action="store_true")
    args = parser.parse_args()
    import update_views
    try:
        state = update_views.load(args.state)
        update_views.validate(state)
        pending = queue(state, args.participant, include_waiting=args.include_waiting)
        if args.format == "json":
            print(json.dumps(pending, ensure_ascii=False, indent=2))
        else:
            print("\n\n---\n\n".join(render_request(state, row["request"], args.participant) +
                  ("\n\nWaiting until " + row["available_at"] if row["state"] == "waiting" else "") for row in pending)
                  or "No feedback is currently awaiting this participant.")
    except (ValueError, OSError) as exc:
        parser.exit(1, str(exc) + "\n")


if __name__ == "__main__":
    main()
