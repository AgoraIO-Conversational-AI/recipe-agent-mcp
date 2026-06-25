# 02 · Architecture

> Single backend process. The browser talks only to Next.js `/api/*`, which rewrites to the FastAPI agent backend. That same backend process also mounts the FastMCP server at `/mcp`. Agora cloud orchestrates the tool call by POSTing to the public `MCP_ENDPOINT`.

## Topology

```
Browser (localhost:3000)
  │  fetch /api/*
  ▼
Next.js (web/)  ──rewrite──▶  Agent backend (server/, :8000)
                                 │  builds OpenAI vendor with mcp_servers=[{endpoint: MCP_ENDPOINT}]
                                 │  also mounts FastMCP at /mcp (same process, same port)
                                 ▼
                              Agora ConvoAI Cloud
                                 │  user speech → Deepgram STT (managed)
                                 │  managed OpenAI LLM (keyless) → emits get_time tool call
                                 │  POST <MCP_ENDPOINT>  (streamable-http transport)
                                 ▼
                              FastMCP server at /mcp  (same process, same port)
                                 │  executes get_time() → returns current time string
                                 ▼
                              Agora ConvoAI Cloud → LLM incorporates result → speaks answer
                                                  → MiniMax TTS (managed) → user hears speech
                                                  → RTM transcript / metrics → web UI
```

- **`web/`** — Next.js / React / TypeScript. Owns UI plus the RTC/RTM client lifecycle. Calls only `/api/*`.
- **`server/`** — Python FastAPI (:8000). Owns Agora token generation, agent session lifecycle, and the FastMCP server mounted at `/mcp` in the same process.
- No `llm/` service — the cascading STT/LLM/TTS pipeline uses Agora-managed vendors (`DeepgramSTT`, `OpenAI`, `MiniMaxTTS`).

## Request lifecycle

1. Browser `GET /api/get_config` → Next rewrites to backend `/get_config`; backend mints a Token007 from `AGORA_APP_ID` + `AGORA_APP_CERTIFICATE` and returns channel + UIDs.
2. Browser joins the RTC channel, then `POST /api/startAgent`; backend builds the `OpenAI` vendor with `mcp_servers` pointing at `MCP_ENDPOINT` and starts an async agent session.
3. Agora routes user audio through Deepgram STT (managed); the transcript goes to the managed OpenAI LLM.
4. When the LLM emits a tool call (`get_time`), Agora cloud POSTs to `MCP_ENDPOINT` via streamable-http. The FastMCP server (mounted at `/mcp` in the same process) executes the tool and returns the result.
5. Agora feeds the tool result back to the LLM; the LLM speaks the answer. MiniMax TTS (managed) converts speech to audio.
6. RTM delivers transcript + metrics to the web UI.
7. `POST /api/stopAgent { agentId }` ends the session.

## Single-process design

The FastMCP server is mounted inside the FastAPI app via Starlette's `mount()`:

```python
_mcp_asgi = mcp_server.mcp.streamable_http_app()
app.mount("/", _mcp_asgi)   # FastMCP's own /mcp path; lands at /mcp on the server
```

Its session manager lifespan runs alongside the FastAPI app lifespan (wired in `_lifespan`). One uvicorn process, one port (8000), one tunnel (`ngrok http 8000`), one Docker container.

`MCP_ENDPOINT` still points at the **public** URL (`<tunnel>/mcp`) because Agora cloud — not the browser — calls the tool endpoint.

## Distinct from recipe-agent-tool-calling

In `recipe-agent-tool-calling` the tools run **inside** the `llm/` endpoint: the custom LLM proxy intercepts tool calls locally. In this recipe Agora cloud orchestrates tools via the MCP protocol — the managed OpenAI vendor issues the call, Agora invokes `MCP_ENDPOINT`, and the result flows back to the LLM.

## Key abstractions

- **`Agent`** (`server/src/agent.py`) — async wrapper around `AgoraAgent`; owns the `AsyncAgora` client, vendor construction, and the in-memory `_sessions` map keyed by `agent_id`.
- **`build_mcp_servers()`** (`server/src/mcp_config.py`) — pure builder for the `mcp_servers` list passed to the `OpenAI` vendor; no `agora-agents` import.
- **`mcp_server.py`** — FastMCP instance with tools; mounted by `server.py` at `/mcp`.
- **Rewrite proxy** (`web/next.config.ts`) — the only browser→backend boundary; no Next Route Handlers exist for agent/token logic.

## Tech decisions

- **Single process, single port** — no separate MCP service, no second tunnel; `/mcp` is co-public on the same origin as the token endpoints.
- **Rewrites, not Route Handlers** — hides backend placement behind `/api/*` so the same client works locally and deployed.
- **Keyless OpenAI** — Agora manages the OpenAI key; `OPENAI_API_KEY` is optional.
- **`mcp_config.py` is import-isolated** — contains no `agora-agents` imports, keeping it independently testable.

## Related Deep Dives

- [mcp_tool_wiring](L2/mcp_tool_wiring.md) — full MCP tool registration, `build_mcp_servers()`, transport conventions, and how to add tools.
- [session_lifecycle](L2/session_lifecycle.md) — browser orchestration of config + start/stop, RTC/RTM, transcript mapping.
