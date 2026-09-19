"""Construction smoke: the real AgoraAgent is built and a session is created (SDK session faked).

Closes the gap where the rest of the suite stubs the whole Agent (FakeAgent) and never
exercises AgoraAgent construction — the exact path that agora-agents 2.3.x changed.
"""
import asyncio
import sys


def _fresh_agent_module():
    sys.modules.pop("agent", None)
    import agent
    return agent


def test_start_constructs_real_agent_and_returns_shape(fake_env, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "pipeline-key")
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    agent = _fresh_agent_module()
    captured = {}

    class FakeSession:
        async def start(self):
            return "test-agent-id"

        async def stop(self):
            captured["stopped"] = True

    def fake_create_async_session(self, **kwargs):
        captured["channel"] = kwargs.get("channel")
        captured["remote_uids"] = kwargs.get("remote_uids")
        captured["llm"] = self.llm
        captured["mllm"] = self.mllm
        captured["advanced_features"] = self.advanced_features
        return FakeSession()

    from agora_agent.agentkit import Agent as AgoraAgent
    monkeypatch.setattr(AgoraAgent, "create_async_session", fake_create_async_session)

    instance = agent.Agent()
    result = asyncio.run(instance.start(channel_name="ch", agent_uid=111, user_uid=222))

    assert result["agent_id"] == "test-agent-id"
    assert result["channel_name"] == "ch"
    assert result["status"] == "started"
    assert captured["channel"] == "ch"
    assert captured["remote_uids"] == ["222"]
    assert captured["llm"]["api_key"] == "pipeline-key"
    assert (
        captured["llm"]["url"]
        == "https://api.openai.com/v1/chat/completions"
    )
    assert captured["llm"]["mcp_servers"][0]["transport"] == "streamable_http"
    assert captured["advanced_features"]["enable_tools"] is True


def test_start_constructs_realtime_agent_with_mcp(fake_env, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "pipeline-key")
    monkeypatch.setenv("OPENAI_REALTIME_API_KEY", "realtime-key")
    agent = _fresh_agent_module()
    captured = {}

    class FakeSession:
        async def start(self):
            return "test-realtime-agent-id"

    def fake_create_async_session(self, **kwargs):
        captured["llm"] = self.llm
        captured["mllm"] = self.mllm
        captured["advanced_features"] = self.advanced_features
        return FakeSession()

    from agora_agent.agentkit import Agent as AgoraAgent

    monkeypatch.setattr(AgoraAgent, "create_async_session", fake_create_async_session)
    result = asyncio.run(
        agent.Agent().start(
            channel_name="ch", agent_uid=111, user_uid=222, agent_mode="realtime"
        )
    )

    assert result["agent_mode"] == "realtime"
    assert captured["llm"] is None
    assert captured["mllm"]["api_key"] == "realtime-key"
    assert captured["mllm"]["params"]["model"] == "gpt-realtime"
    assert captured["mllm"]["mcp_servers"][0]["transport"] == "streamable_http"
    assert "mcp_servers" not in captured["mllm"].get("params", {})
    assert captured["advanced_features"]["enable_tools"] is True


def test_pipeline_remains_managed_without_openai_api_key(fake_env, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    agent = _fresh_agent_module()
    captured = {}

    class FakeSession:
        async def start(self):
            return "test-managed-agent-id"

    def fake_create_async_session(self, **kwargs):
        captured["llm"] = self.llm
        return FakeSession()

    from agora_agent.agentkit import Agent as AgoraAgent

    monkeypatch.setattr(AgoraAgent, "create_async_session", fake_create_async_session)
    asyncio.run(agent.Agent().start(channel_name="ch", agent_uid=111, user_uid=222))

    assert captured["llm"].get("api_key") is None
