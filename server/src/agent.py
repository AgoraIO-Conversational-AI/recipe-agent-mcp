"""
Agent — MCP Recipe

High-level API for managing Agora Conversational AI Agents with OpenAI Pipeline
or Realtime MCP tool calling. Agora cloud orchestrates the MCP server: the model
emits a tool call, Agora invokes the public MCP_ENDPOINT, returns the result,
and the model speaks it.

Pipeline mode is managed by default and optionally accepts BYO OpenAI credentials.
OPENAI_REALTIME_API_KEY is required only for Realtime mode.
MCP_ENDPOINT must be PUBLIC — Agora cloud (not this server) calls it.
"""
import logging
import os
from typing import Any, Dict, Literal, Optional

from agora_agent import Area, AsyncAgora
from agora_agent.agentkit import Agent as AgoraAgent
from agora_agent.agentkit.vendors import (
    DeepgramSTT,
    MiniMaxTTS,
    OpenAI,
    OpenAIRealtime,
)
from mcp_config import build_mcp_servers

logger = logging.getLogger("uvicorn.error")

AGENT_GREETING = "Hi! Ask me what time it is."
AGENT_INSTRUCTIONS = (
    "You are a helpful voice assistant. When the user asks what time it is, "
    "you MUST call the get_time tool, then say the time out loud. Do not guess."
)
DEFAULT_OPENAI_BASE_URL = "https://api.openai.com/v1/chat/completions"
AgentMode = Literal["pipeline", "realtime"]


class Agent:
    """
    High-level wrapper for an Agora agent with Pipeline or Realtime MCP tools.

    When the user asks what time it is, the selected model emits a tool call,
    Agora invokes the mcp/ server at MCP_ENDPOINT, and the result is returned
    to the model so it can speak the answer.

    IMPORTANT: MCP_ENDPOINT must be publicly accessible for the Agora
    Conversational AI Engine (cloud) to reach the mcp/ server. For local
    development, use a tunnel (ngrok) — e.g. ngrok http 8000 — and paste
    the public URL here.
    """

    def __init__(self):
        self.app_id = os.getenv("AGORA_APP_ID")
        self.app_certificate = os.getenv("AGORA_APP_CERTIFICATE")
        self.greeting = os.getenv("AGENT_GREETING", AGENT_GREETING)

        # Pipeline is managed unless BYO credentials are supplied.
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_base_url = os.getenv("OPENAI_BASE_URL")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.openai_realtime_api_key = os.getenv("OPENAI_REALTIME_API_KEY")
        self.openai_realtime_model = os.getenv(
            "OPENAI_REALTIME_MODEL", "gpt-realtime"
        )
        # MCP_ENDPOINT must be PUBLIC — Agora cloud calls the mcp/ server directly.
        self.mcp_endpoint = os.getenv("MCP_ENDPOINT")
        if not self.mcp_endpoint:
            raise ValueError(
                "MCP_ENDPOINT is required (public URL of your mcp/ server, "
                "e.g. https://<tunnel>/mcp)"
            )

        if not self.app_id or not self.app_certificate:
            raise ValueError("AGORA_APP_ID and AGORA_APP_CERTIFICATE are required")

        self.client = AsyncAgora(
            area=Area.US,
            app_id=self.app_id,
            app_certificate=self.app_certificate,
        )

        # Track active sessions by agent_id
        self._sessions: Dict[str, Any] = {}

    async def start(
        self,
        channel_name: str,
        agent_uid: int,
        user_uid: int,
        output_audio_codec: Optional[str] = None,
        agent_mode: AgentMode = "pipeline",
    ) -> Dict[str, Any]:
        """Start a Pipeline or Realtime agent with MCP tool calling."""
        if not channel_name or not str(channel_name).strip():
            raise ValueError("channel_name is required and cannot be empty")
        if agent_uid <= 0:
            raise ValueError("agent_uid is required and cannot be empty")
        if user_uid <= 0:
            raise ValueError("user_uid is required and cannot be empty")
        if agent_mode not in ("pipeline", "realtime"):
            raise ValueError("agent_mode must be 'pipeline' or 'realtime'")
        if agent_mode == "realtime" and not self.openai_realtime_api_key:
            raise ValueError("OPENAI_REALTIME_API_KEY is required for realtime mode")

        mcp_servers = build_mcp_servers(self.mcp_endpoint)

        parameters = {
            "audio_scenario": "chorus",  # web client — ultra-low-latency chorus profile
            "data_channel": "rtm",
            "enable_error_message": True,
            "enable_metrics": True,
        }
        if isinstance(output_audio_codec, str) and output_audio_codec.strip():
            parameters["output_audio_codec"] = output_audio_codec.strip()

        agent_options = {
            "client": self.client,
            "greeting": self.greeting,
            "failure_message": "Please wait a moment.",
            "max_history": 50,
            "advanced_features": {"enable_rtm": True},
            "parameters": parameters,
        }
        if agent_mode == "pipeline":
            agent_options["turn_detection"] = {
                "config": {
                    "speech_threshold": 0.5,
                    "start_of_speech": {
                        "mode": "vad",
                        "vad_config": {
                            "interrupt_duration_ms": 160,
                            "prefix_padding_ms": 300,
                        },
                    },
                    "end_of_speech": {
                        "mode": "vad",
                        "vad_config": {
                            "silence_duration_ms": 480,
                        },
                    },
                },
            }
        agora_agent = AgoraAgent(**agent_options)

        if agent_mode == "pipeline":
            llm_options = {
                "model": self.openai_model,
                "system_messages": [{"role": "system", "content": AGENT_INSTRUCTIONS}],
                "mcp_servers": mcp_servers,
                "greeting_message": self.greeting,
            }
            if self.openai_api_key:
                llm_options["api_key"] = self.openai_api_key
                llm_options["base_url"] = (
                    self.openai_base_url or DEFAULT_OPENAI_BASE_URL
                )
            llm = OpenAI(**llm_options)
            stt = DeepgramSTT(model="nova-3", language="en")
            tts = MiniMaxTTS(
                model="speech_2_6_turbo",
                voice_id="English_captivating_female1",
            )
            agora_agent = (
                agora_agent.with_stt(stt).with_llm(llm).with_tts(tts).with_tools()
            )
        else:
            mllm = OpenAIRealtime(
                api_key=self.openai_realtime_api_key,
                model=self.openai_realtime_model,
                instructions=AGENT_INSTRUCTIONS,
                greeting_message=self.greeting,
                failure_message="Please wait a moment.",
                turn_detection={"mode": "server_vad"},
                mcp_servers=mcp_servers,
            )
            agora_agent = agora_agent.with_mllm(mllm).with_tools()

        session = agora_agent.create_async_session(
            channel=channel_name,
            agent_uid=str(agent_uid),
            remote_uids=[str(user_uid)],
            enable_string_uid=False,
            idle_timeout=30,
            expires_in=3600,
        )

        logger.info(
            "Starting MCP agent channel=%s agent_uid=%s user_uid=%s mode=%s mcp_endpoint=%s",
            channel_name,
            agent_uid,
            user_uid,
            agent_mode,
            self.mcp_endpoint,
        )

        try:
            agent_id = await session.start()
        except Exception:
            logger.exception(
                "Failed to start MCP agent channel=%s agent_uid=%s user_uid=%s",
                channel_name,
                agent_uid,
                user_uid,
            )
            raise

        # Save session for later stop
        self._sessions[agent_id] = session

        logger.info(
            "Started MCP agent agent_id=%s channel=%s",
            agent_id,
            channel_name,
        )

        return {
            "agent_id": agent_id,
            "channel_name": channel_name,
            "status": "started",
            "agent_mode": agent_mode,
        }

    async def stop(self, agent_id: str) -> None:
        """Stop a running agent. Falls back to the stateless client path."""
        if not agent_id or not str(agent_id).strip():
            raise ValueError("agent_id is required and cannot be empty")

        session = self._sessions.pop(agent_id, None)
        if session:
            try:
                await session.stop()
                logger.info("Stopped agent from active session agent_id=%s", agent_id)
                return
            except Exception:
                logger.warning(
                    "Failed to stop agent from active session; falling back agent_id=%s",
                    agent_id,
                    exc_info=True,
                )

        logger.info("Stopping agent through client.stop_agent agent_id=%s", agent_id)
        await self.client.stop_agent(agent_id)
