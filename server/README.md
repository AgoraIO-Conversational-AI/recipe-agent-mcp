# Agora Agent Backend — MCP Recipe

FastAPI service that owns Agora token generation and agent session lifecycle for
the mcp recipe. It is the service the web client reaches through the Next.js
`/api/*` rewrite proxy (port 8000).

## What's different from the base quickstart

The SDK attaches typed `mcp_servers` configuration to managed `OpenAI` in the
default Pipeline mode or to `OpenAIRealtime` in Realtime mode. When the model
emits a tool call, Agora cloud POSTs to `MCP_ENDPOINT` (streamable-http
transport), receives the result, and the model speaks it. The FastMCP server is
mounted at `/mcp` in this same process — no separate service or port needed.

## Run

Use the repo-root `README.md` for the full local flow (`bun run dev`). To work
on this module directly:

The root commands below select the correct virtualenv interpreter on macOS,
Linux, and Windows, so activation is not required:

```shell
bun run setup:server
bun run backend
```

## Environment

`server/.env.example` is the template. Required:

- `AGORA_APP_ID`, `AGORA_APP_CERTIFICATE` — Agora project credentials.
- `MCP_ENDPOINT` — the **public** URL of the `/mcp` endpoint (e.g.
  `https://<tunnel>/mcp`). Agora cloud calls this directly, so it cannot be
  `localhost`. Use `ngrok http 8000` to expose the backend publicly.

Optional:
- `OPENAI_MODEL` (default `gpt-4o-mini`) — Pipeline model name.
- `OPENAI_API_KEY` — optional Pipeline BYO credential; omit it to use the
  Agora-managed vendor.
- `OPENAI_BASE_URL` — optional Pipeline endpoint override. It defaults to
  OpenAI's chat completions endpoint when a BYO key is set.
- `OPENAI_REALTIME_API_KEY` — required for Realtime mode.
- `OPENAI_REALTIME_MODEL` (default `gpt-realtime`) — Realtime model.
- `AGENT_GREETING` — override the agent's opening line.
- `PORT` (default `8000`) — agent backend port.

## API

- `GET /get_config` — token + channel/UID config
- `POST /startAgent` — start an agent session; `agentMode` is `pipeline` or `realtime`
- `POST /stopAgent` — stop an agent session

The repo-root `bun run verify:web:api` exercises these routes through the Next
proxy using a fake agent (`scripts/run_fake_server.py`), so no live Agora
session is required.

## Key files

| File | Purpose |
| --- | --- |
| `src/server.py` | FastAPI app, routes |
| `src/agent.py` | Pipeline/Realtime agent modes + MCP tool execution |
| `src/mcp_config.py` | Typed `McpServerConfig` builder |
| `src/mcp_server.py` | FastMCP server with tools; mounted at `/mcp` in `server.py` |
