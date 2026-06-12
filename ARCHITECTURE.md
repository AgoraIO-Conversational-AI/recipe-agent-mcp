# Architecture — MCP Recipe

Two processes. The browser talks only to Next.js `/api/*`, which rewrites to
the agent backend. The agent backend owns Agora tokens, agent lifecycle, **and**
the FastMCP server mounted at `/mcp` — all in one process on one port.

## Request flow

```
Browser
  │  GET /api/get_config            → token + channel/UIDs
  │  POST /api/startAgent           → start agent session
  ▼
Next.js  (rewrites /api/* → AGENT_BACKEND_URL)
  ▼
Agent backend (server/, :8000)
  │  builds session with OpenAI(mcp_servers=[{endpoint: MCP_ENDPOINT}])
  │  also serves FastMCP at /mcp (same uvicorn, same port)
  ▼
Agora ConvoAI Cloud
  │  user speech → Deepgram STT (managed)
  │  managed OpenAI LLM (keyless) → emits get_time tool call
  │  POST <MCP_ENDPOINT>   (streamable-http transport)
  ▼
FastMCP server at /mcp (server/, :8000, public via tunnel)
  │  executes get_time() → returns current time string
  ▼
Agora ConvoAI Cloud → LLM incorporates result → speaks answer
                     → MiniMax TTS (managed) → user hears speech
                     → RTM transcript / metrics → web UI
```

`POST /api/stopAgent { agentId }` ends the session.

## Single-process design

The FastMCP server is mounted inside the FastAPI app via Starlette's `mount()`.
Its session manager lifespan runs alongside the FastAPI app lifespan. One
uvicorn process, one port (8000), one tunnel (`ngrok http 8000`), one Docker
container.

`MCP_ENDPOINT` still points at the **public** URL (`<tunnel>/mcp`) because
Agora cloud — not the browser — calls the tool endpoint. The backend and the MCP
path are co-public on the same origin.

**Co-public caveat**: exposing port 8000 publicly also exposes `/mcp`. For
production use, add authentication to the MCP endpoint or restrict access to
Agora cloud IPs via a gateway.

## Distinct from recipe-agent-tool-calling

In `recipe-agent-tool-calling` the tools run **inside** the `llm/` endpoint:
the agent's custom LLM proxy intercepts tool calls and handles them locally. In
this recipe Agora cloud orchestrates the tools via the MCP protocol — the
managed OpenAI vendor issues the tool call, Agora invokes `MCP_ENDPOINT`, and
the result flows back to the LLM.

## API (agent backend, port 8000)

| Endpoint | Method | Description |
| --- | --- | --- |
| `/get_config` | GET | Token + channel/UID config |
| `/startAgent` | POST | Start the agent session |
| `/stopAgent` | POST | Stop the agent by `agent_id` |
| `/mcp` | POST | FastMCP streamable-HTTP endpoint (called by Agora cloud) |

The browser calls the first three as `/api/*`; Next rewrites them to
`AGENT_BACKEND_URL`. Agora cloud calls `/mcp` directly at `MCP_ENDPOINT`.

## Auth

- Browser → agent backend: none (local dev).
- Agent backend → Agora cloud: Token007, generated from `AGORA_APP_ID` +
  `AGORA_APP_CERTIFICATE`.
- Agora cloud → MCP server: streamable-http (no auth on the mock; add it for
  production use).
- OpenAI: Agora-managed (keyless) — `OPENAI_API_KEY` is optional.
