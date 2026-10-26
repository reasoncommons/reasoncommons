from dataclasses import replace
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

import claude_agent_sdk as sdk

from reasoncommons_discord.agent import Agent, package_version
from reasoncommons_discord.config import Config
from reasoncommons_discord.service import Invocation

REPO = Path(__file__).resolve().parents[3]


class AgentTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.stage = Path(self.temp.name) / "job/reason-commons.yaml"
        self.stage.parent.mkdir()
        self.stage.write_text("fixture")
        self.config = Config(REPO, self.stage, Path(self.temp.name), 10, frozenset({20}),
                             {"100": "alice"}, model="configured-model", budget_usd=0.02, api_key="fixture-key")

    def tearDown(self):
        self.temp.cleanup()

    def fake_sdk(self, *, available=True, read=True, failed=False, missing_result=False, terminal_reason=None):
        test = self
        class Client:
            def __init__(self, options):
                test.options = options
            async def __aenter__(self):
                return self
            async def __aexit__(self, *args):
                return False
            async def query(self, prompt):
                test.prompt = prompt
            async def receive_response(self):
                yield sdk.SystemMessage(subtype="init", data={"skills": ["ltp"] if available else []})
                hook = test.options.hooks["PreToolUse"][0].hooks[0]
                if read:
                    event = {"tool_name": "Read", "tool_input": {"file_path": str(test.config.skill / "SKILL.md")}}
                    result = await hook(event, None, None)
                    test.assertEqual(result["hookSpecificOutput"]["permissionDecision"], "allow")
                    await test.options.hooks["PostToolUse"][0].hooks[0](event, None, None)
                yield sdk.ResultMessage(subtype="success", duration_ms=1, duration_api_ms=1,
                                        is_error=failed, num_turns=1, session_id="fixture",
                                        terminal_reason=terminal_reason,
                                        structured_output=None if missing_result else {
                                            "text": "Type: Answer\nScope is limited.", "review_ids": [],
                                            "reasoning_ids": ["r-productivity-gain"]})
        return SimpleNamespace(ClaudeAgentOptions=sdk.ClaudeAgentOptions, ClaudeSDKClient=Client,
                               PermissionResultAllow=sdk.PermissionResultAllow,
                               PermissionResultDeny=sdk.PermissionResultDeny, HookMatcher=sdk.HookMatcher,
                               SystemMessage=sdk.SystemMessage, ResultMessage=sdk.ResultMessage)

    async def run_agent(self, **options):
        return await Agent(self.config, self.fake_sdk(**options)).run(
            request=Invocation("1", 10, 20, "100", "What do we know?"), person="alice",
            state_path=self.stage, history=[], task_context="unavailable")

    async def test_skill_dispatch_loading_evidence_and_explicit_api_settings(self):
        reply = await self.run_agent()
        self.assertTrue(self.prompt.startswith("/ltp\n"))
        self.assertEqual(self.options.skills, ["ltp"])
        self.assertEqual(self.options.setting_sources, ["project"])
        self.assertTrue(self.options.strict_mcp_config)
        self.assertNotIn("Bash", self.options.tools)
        self.assertEqual(self.options.env["ANTHROPIC_API_KEY"], "fixture-key")
        self.assertEqual(self.options.env["CLAUDE_CODE_OAUTH_TOKEN"], "")
        self.assertEqual(reply.skill_version, package_version(self.config.skill))
        self.assertTrue((self.stage.parent / ".claude/skills/ltp").is_symlink())

    async def test_missing_skill_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "loading was not observed"):
            await self.run_agent(available=False)

    async def test_discovered_but_not_read_skill_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "loading was not observed"):
            await self.run_agent(read=False)

    async def test_failed_result_not_published(self):
        with self.assertRaisesRegex(ValueError, "did not finish"):
            await self.run_agent(failed=True)

    async def test_api_error_with_success_subtype_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "did not finish"):
            await self.run_agent(terminal_reason="api_error")

    async def test_unstructured_result_rejected(self):
        with self.assertRaisesRegex(ValueError, "structured"):
            await self.run_agent(missing_result=True)

    async def test_api_auth_is_required_even_when_constructed_without_cli(self):
        agent = Agent(replace(self.config, api_key=""), self.fake_sdk())
        with self.assertRaisesRegex(ValueError, "API key"):
            await agent.run(request=Invocation("1", 10, 20, "100", "Question"), person="alice",
                            state_path=self.stage, history=[], task_context="")

    def test_tool_permissions_reject_path_escape_shell_and_unknown_skills(self):
        agent = Agent(self.config, self.fake_sdk())
        for tool, args in [("Read", {"file_path": "/etc/passwd"}),
                           ("Read", {"file_path": "../outside.yaml"}),
                           ("Write", {"file_path": str(self.config.skill / "SKILL.md")}),
                           ("Bash", {"command": "echo danger"}),
                           ("Skill", {"skill": "other-skill"}),
                           ("Skill", {"skill": "reason-commons"})]:
            self.assertFalse(agent.permitted(tool, args, self.stage, True))
        self.assertTrue(agent.permitted("Skill", {"skill": "ltp"}, self.stage, False))
        self.assertTrue(agent.permitted("Read", {"file_path": str(self.config.skill / "references/schema.md")}, self.stage, False))
        self.assertFalse(agent.permitted("Edit", {"file_path": str(self.stage)}, self.stage, False))
        self.assertTrue(agent.permitted("Edit", {"file_path": str(self.stage)}, self.stage, True))

    async def test_hook_denies_untrusted_read_and_write(self):
        await self.run_agent()
        hook = self.options.hooks["PreToolUse"][0].hooks[0]
        for tool in ("Read", "Write", "Bash"):
            value = await hook({"tool_name": tool, "tool_input": {"file_path": "/etc/passwd"}}, None, None)
            self.assertEqual(value["hookSpecificOutput"]["permissionDecision"], "deny")
