"""Shared-file feedback commands and explicitly enabled, one-prompt delivery."""
import asyncio
from datetime import datetime, timezone
from functools import lru_cache
import importlib.util
import json
import logging
from pathlib import Path

from .store import atomic_write, digest

LOG = logging.getLogger(__name__)


@lru_cache
def core():
    path = Path(__file__).resolve().parents[3] / "skills/ltp/scripts/feedback.py"
    spec = importlib.util.spec_from_file_location("discord_shared_feedback", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def feedback_turn(state, invocation, person):
    helper = core()
    data = invocation.feedback or {}
    ident = data.get("request_id", invocation.text.strip())
    revision = data.get("revision", 1)
    request = helper.find(state, ident, revision)
    if person not in request["feedback_from"]:
        raise ValueError("This feedback request is not assigned to you.")
    if not data.get("submit"):
        if any(data.get(field) for field in ("benefit", "reservation", "outcome", "verdict", "defer_until")) or data.get("readiness", "experienced") != "experienced":
            raise ValueError("Supply your feedback words to save an assessment or deferral.")
        return {"text": helper.render_request(state, request, person), "attachments": []}, state
    readiness = data.get("readiness", "experienced")
    answers = []
    for field in ("benefit", "reservation"):
        if data.get(field):
            items = request["benefits" if field == "benefit" else "reservations"]
            if len(items) != 1:
                raise ValueError(f"Choose a specific outcome for {field}; this request does not contain exactly one.")
            answers.append({"ref": items[0]["ref"], "verdict": data[field], "note": invocation.text})
    if data.get("outcome") or data.get("verdict"):
        if not data.get("outcome") or not data.get("verdict"):
            raise ValueError("A specific outcome and its verdict are both required.")
        answers.append({"ref": data["outcome"], "verdict": data["verdict"], "note": invocation.text})
    report = {"id": "discord-" + invocation.id, "by": person,
              "recorded_at": datetime.now(timezone.utc).isoformat(), "readiness": readiness,
              "text": invocation.text, "evidence_type": "self_report", "outcomes": answers,
              "source": {"surface": "discord", "invocation_id": invocation.id,
                         "discord_user_id": invocation.user, "guild_id": str(invocation.guild),
                         "channel_id": str(invocation.channel)}}
    if data.get("defer_until"):
        report["defer_until"] = data["defer_until"]
    after = helper.add_report(state, ident, revision, report)
    after["driver"] = person
    pending = helper.outstanding(helper.find(after, ident, revision), person)
    text = ("Type: Capture result\nSaved your feedback as attributed self-report for " + ident +
            f" revision {revision}. No reasoning endorsement was inferred.\n" +
            "Still awaiting your assessment: " + (", ".join(pending) if pending else "none for this version.") +
            ("\nDeferred until: " + report["defer_until"] if report.get("defer_until") else ""))
    harms = {o["ref"]: o for o in request["reservations"]}
    for answer in answers:
        if answer["ref"] in harms and answer["verdict"] == "observed":
            text += "\nPossible harm reported: " + harms[answer["ref"]]["text"] + " Review the intervention and relevant safeguards."
    if any(answer["verdict"] != "not_assessed" for answer in answers):
        text += "\nRecorded outcome feedback awaits interpretation in the reasoning backlog."
    return {"text": text, "attachments": []}, after


def session_prompt(state, person, history, now=None):
    now = now or datetime.now(timezone.utc)
    own = [entry for entry in history if entry.get("by") == person]
    if own:
        try:
            if (now - core().timestamp(own[-1]["recorded_at"])).total_seconds() < 1800:
                return None
        except (ValueError, KeyError):
            pass
    rows = core().queue(state, person, now)
    return core().render_request(state, rows[0]["request"], person) if rows else None


async def dispatch_once(service, send):
    """Send at most once per version/provider; journal delivery, never an outcome.

    send(user_id, text, delivery_id) returns a message URL. An exception may have
    happened after Discord accepted the message, so failures remain uncertain.
    """
    if not service.config.feedback_channel:
        return 0
    helper = core()
    sent = 0
    # One participant can have multiple mapped Discord IDs: pick one deterministically.
    identities = {}
    for user, person in sorted(service.config.participants.items()):
        identities.setdefault(person, user)
    async with service.store.lock():
        for row in service.store.prepared():
            service._finish(row)
        delivery = await service.sync_feedback()
        if delivery and delivery["state"] != "shared":
            LOG.warning("Shared feedback could not be refreshed; proactive prompts are deferred.")
            return 0
    for person, user in identities.items():
        async with service.store.lock():
            for row in service.store.prepared():
                service._finish(row)
            state = service.helper.load(service.config.state)
            service.helper.validate(state)
            pending = helper.queue(state, person)
        for row in pending:
            request = row["request"]
            async with service.store.lock():
                current = service.helper.load(service.config.state)
                service.helper.validate(current)
                still_pending = helper.queue(current, person)
                if not any((r["id"], r["revision"]) == (row["id"], row["revision"]) for r in still_pending):
                    continue
                request = helper.find(current, row["id"], row["revision"])
                own_reports = [r for r in request["reports"] if r["by"] == person]
                latest = max(own_reports, key=lambda report: (helper.timestamp(report["recorded_at"]), report["id"])) if own_reports else None
                opportunity = latest["id"] if latest and latest.get("defer_until") else "initial"
                recent = [delivery["updated"] for delivery in service.store.feedback_deliveries()
                          if json.loads(delivery["payload"])["participant"] == person
                          and delivery["state"] in {"sent", "uncertain"}]
                if opportunity == "initial" and recent and helper.utc_now().timestamp() - max(recent) < service.config.feedback_cooldown:
                    continue
                ident = digest(json.dumps([str(service.config.state.resolve()), request["id"], request["revision"], person, opportunity]))
                payload = {"request_id": request["id"], "revision": request["revision"],
                           "participant": person, "discord_user_id": user,
                           "channel": str(service.config.feedback_channel), "opportunity": opportunity}
                if not service.store.reserve_feedback_delivery(ident, payload):
                    continue
            text = (helper.render_request(current, request, person) +
                    f"\n\nUse /reason-feedback request_id:{request['id']} revision:{request['revision']} to inspect or submit your assessment.")
            try:
                url = await send(user, text, ident)
            except asyncio.CancelledError:
                raise
            except Exception:
                # Never reflect provider errors or message content into logs.
                LOG.warning("Feedback delivery %s is uncertain; reconcile before retry.", ident)
                break
            service.store.finish_feedback_delivery(ident, "sent", url)
            sent += 1
            break  # At most one prompt per participant in one polling pass.
    return sent


async def run_dispatcher(service, client):
    import discord
    await client.wait_until_ready()

    async def send(user, text, ident):
        channel = client.get_channel(service.config.feedback_channel)
        if channel is None or getattr(getattr(channel, "guild", None), "id", None) != service.config.guild_id:
            raise ValueError("Feedback channel is not available in the configured guild.")
        content = f"<@{user}>\n" + text
        files = []
        if len(content) > 1900:
            path = service.config.runtime / "artifacts" / ("feedback-" + ident + ".txt")
            atomic_write(path, text)
            content = f"<@{user}> Feedback requested. Full original expectations and response instructions are attached."
            files = [discord.File(path)]
        try:
            message = await channel.send(content, files=files,
                allowed_mentions=discord.AllowedMentions(everyone=False, roles=False, users=[discord.Object(id=int(user))]))
            return message.jump_url
        finally:
            for file in files:
                file.close()

    while not client.is_closed():
        try:
            await dispatch_once(service, send)
        except asyncio.CancelledError:
            raise
        except Exception:
            LOG.warning("Feedback queue check failed; no outcomes inferred.")
        await asyncio.sleep(service.config.feedback_interval)
