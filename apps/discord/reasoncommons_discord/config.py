"""Explicit local configuration; never discover or print credentials."""
from dataclasses import dataclass, field
import json
import math
import os
from pathlib import Path


@dataclass(frozen=True)
class Config:
    repo: Path
    state: Path
    runtime: Path
    guild_id: int
    channels: frozenset[int]
    participants: dict[str, str]
    model: str = ""
    budget_usd: float = 0
    timeout: float = 120
    token: str = field(default="", repr=False)
    api_key: str = field(default="", repr=False)
    feedback_channel: int | None = None
    feedback_interval: float = 300
    feedback_cooldown: float = 86400

    @property
    def skill(self):
        return self.repo / "skills/ltp"

    @property
    def scripts(self):
        return self.skill / "scripts"

    @property
    def tasks(self):
        return self.runtime / "tasks.json"

    def validate(self, live=False):
        from .service import helpers
        state = helpers(self).load(self.state)
        helpers(self).validate(state)
        if self.guild_id <= 0 or not self.channels or any(c <= 0 for c in self.channels):
            raise ValueError("Configure a guild and explicit channel IDs.")
        if not isinstance(self.participants, dict) or not self.participants or any(not isinstance(k, str) or not k.isdecimal() or int(k) <= 0 or v not in state["participants"]
                                        for k, v in self.participants.items()):
            raise ValueError("Discord IDs must map to existing human participants.")
        if not math.isfinite(self.timeout) or self.timeout <= 0:
            raise ValueError("AGENT_TIMEOUT_SECONDS must be positive.")
        if self.feedback_channel is not None and self.feedback_channel not in self.channels:
            raise ValueError("DISCORD_FEEDBACK_CHANNEL_ID must be an explicitly configured reasoning channel.")
        if not math.isfinite(self.feedback_interval) or self.feedback_interval < 30:
            raise ValueError("FEEDBACK_POLL_SECONDS must be at least 30 seconds.")
        if not math.isfinite(self.feedback_cooldown) or self.feedback_cooldown < 0:
            raise ValueError("FEEDBACK_PROMPT_COOLDOWN_SECONDS must be nonnegative.")
        if self.state == self.runtime or self.runtime in self.state.parents:
            raise ValueError("Keep the canonical state outside the runtime directory.")
        for relative in ("SKILL.md", "references/schema.md", "references/responses.md",
                         "references/diagrams.md", "references/views.md", "scripts/render_view.py",
                         "scripts/update_views.py", "scripts/feedback.py", "references/feedback.md"):
            if not (self.skill / relative).is_file():
                raise ValueError(f"Incomplete skill package: {relative}")
        if live and (not self.token or not self.api_key or not self.model or not math.isfinite(self.budget_usd) or self.budget_usd <= 0):
            raise ValueError("Live operation requires Discord token, API key, model and positive per-call budget.")
        return self

    @classmethod
    def from_env(cls):
        repo = Path(__file__).resolve().parents[3]
        try:
            return cls(
                repo=repo,
                state=Path(os.environ["REASON_COMMONS_STATE"]).expanduser().resolve(),
                runtime=Path(os.environ.get("REASON_COMMONS_RUNTIME",
                                           str(repo / "apps/discord/.runtime"))).expanduser().resolve(),
                guild_id=int(os.environ["DISCORD_GUILD_ID"]),
                channels=frozenset(int(v.strip()) for v in os.environ["DISCORD_CHANNEL_IDS"].split(",") if v.strip()),
                participants=json.loads(os.environ["DISCORD_PARTICIPANTS"]),
                model=os.environ.get("CLAUDE_MODEL", ""),
                budget_usd=float(os.environ.get("AGENT_MAX_BUDGET_USD") or 0),
                timeout=float(os.environ.get("AGENT_TIMEOUT_SECONDS", "120")),
                token=os.environ.get("DISCORD_TOKEN", ""),
                api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
                feedback_channel=int(os.environ["DISCORD_FEEDBACK_CHANNEL_ID"]) if os.environ.get("DISCORD_FEEDBACK_CHANNEL_ID") else None,
                feedback_interval=float(os.environ.get("FEEDBACK_POLL_SECONDS", "300")),
                feedback_cooldown=float(os.environ.get("FEEDBACK_PROMPT_COOLDOWN_SECONDS", "86400")),
            ).validate()
        except (KeyError, TypeError, json.JSONDecodeError) as exc:
            raise ValueError("Missing or invalid configuration; see .env.example.") from exc
