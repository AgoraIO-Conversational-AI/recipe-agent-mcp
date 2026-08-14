# Agora Conversational AI — MCP Recipe (Python)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Python](https://img.shields.io/badge/python-%3E%3D3.10-blue)](https://www.python.org/)
[![Bun](https://img.shields.io/badge/bun-latest-black)](https://bun.sh/)

The **mcp** recipe in the Agora Conversational AI recipes family. The managed
keyless OpenAI vendor emits a tool call, Agora invokes the FastMCP server
mounted at `/mcp` in the same backend process, returns the result, and the LLM
speaks it. STT (Deepgram) and TTS (MiniMax) stay Agora-managed.

This recipe is **zero-key**: OpenAI is Agora-managed (no `OPENAI_API_KEY`
needed), and the tool is a mock (`get_time`) that needs no external credentials.
Replace it with your own tools in `server/src/mcp_server.py`.

**Distinct from `recipe-agent-tool-calling`**: in that recipe the tools run
inside the `llm/` endpoint. Here Agora orchestrates them via the MCP protocol —
the managed OpenAI vendor issues a tool call, Agora invokes `MCP_ENDPOINT`, and
the result flows back to the LLM.

## Prerequisites

- [Python 3.10+](https://www.python.org/)
- [Bun](https://bun.sh/)
- [Agora CLI](https://github.com/AgoraIO/cli) — makes generating an App ID + App Certificate easy
- [ngrok](https://ngrok.com/) — the backend (including the `/mcp` endpoint) must be publicly reachable so Agora cloud can call it

The same commands work on macOS, Linux, and Windows. On macOS/Linux, setup uses
`python3`; on Windows, it uses the Python launcher (`py`) or `python`. WSL and
virtualenv activation are not required.

## Run It

```bash
# 1. Install Python venv + web deps
bun run setup

# 2. Add Agora credentials to server/.env.local
agora login
agora project use <your-project>
agora project env write server/.env.local

# 3. Expose the backend publicly — Agora cloud calls /mcp on this tunnel
ngrok http 8000

# 4. Set MCP_ENDPOINT in server/.env.local (use whatever domain ngrok prints)
#    MCP_ENDPOINT=https://<your-tunnel>.ngrok-free.dev/mcp

# 5. Run the backend and the web frontend
bun run dev
```

Open [http://localhost:3000](http://localhost:3000) → **Start Conversation** →
ask "what time is it?".

### Working from a clone

If you cloned this repo (rather than scaffolding via the Agora CLI), the steps
above are complete as written: `bun run setup` creates the Python venv and
installs web dependencies, then `bun run dev` brings up both services. You
still need Agora credentials in `server/.env.local` and a public `MCP_ENDPOINT`
tunnel before a conversation can connect.

Services:

- Frontend — http://localhost:3000
- Backend + MCP server — http://localhost:8000 (including `/mcp`)
- API docs — http://localhost:8000/docs

## Deploy

Deploy `web` (Next.js) and `server` (a single publicly reachable FastAPI
process that also serves `/mcp`, so Agora cloud can reach `MCP_ENDPOINT`).
Set `AGENT_BACKEND_URL` in the web deployment so the Next rewrites reach the
backend.

A single-process Docker image is published to
`ghcr.io/AgoraIO-Conversational-AI/recipe-agent-mcp` on `v*` tags. It runs the
agent backend and the FastMCP server in one process on port 8000. Expose port
8000 publicly and point `MCP_ENDPOINT` at `<public-url>/mcp`.

**Co-public caveat**: because the `/mcp` endpoint is served on the same port as
the token endpoints, deploying this image publicly also exposes `/mcp`. For
production use, add authentication to the MCP server or deploy behind a gateway
that restricts `/mcp` access to Agora cloud IPs.

## Environment variables

Backend env file: [`server/.env.example`](server/.env.example).

| Variable | Required | Default | Notes |
| --- | :---: | :---: | --- |
| `AGORA_APP_ID` | Yes | — | Agora Console → Project → App ID |
| `AGORA_APP_CERTIFICATE` | Yes | — | Agora Console → Project → App Certificate |
| `MCP_ENDPOINT` | Yes | — | **Public** URL of the `/mcp` endpoint (e.g. `https://<tunnel>/mcp`). Agora cloud calls it; cannot be `localhost`. |
| `OPENAI_MODEL` | | `gpt-4o-mini` | Model name for the managed OpenAI vendor |
| `OPENAI_API_KEY` | | — | Optional — Agora manages the OpenAI key (keyless by default) |
| `AGENT_GREETING` | | built-in | Optional opening line override |
| `PORT` | | `8000` | Agent backend port |
| `AGENT_BACKEND_URL` (web deploy) | Yes (deploy) | — | Required when deploying `web` |

## Commands

```bash
bun run setup            # install web deps + create server/ venv
bun run dev              # run backend (:8000, including /mcp) + web (:3000)

bun run doctor           # prerequisite check (no creds needed)
bun run doctor:local     # + .env.local + credentials + MCP_ENDPOINT checks

bun run verify           # web-only gate (no Agora creds needed)
bun run verify:local     # full local gate: backend compile + web build
bun run clean            # remove venv and build artifacts
```

Tests run standalone (no Agora cloud needed): `pytest` in `server/`, plus
`bun run verify` in `web/`. CI runs them on Linux/macOS/Windows × Python 3.10 &
3.13.

## Architecture

```
Browser (localhost:3000)
  │  fetch /api/*
  ▼
Next.js  ──rewrite──▶  Agent backend  (server/, localhost:8000)
                          │  starts agent session (OpenAI vendor + mcp_servers)
                          │  also serves FastMCP at /mcp (same process)
                          ▼
                       Agora ConvoAI Cloud
                          │  user speech → Deepgram STT (managed)
                          │  OpenAI LLM (managed, keyless) → emits tool call
                          │  POST <MCP_ENDPOINT>   (streamable-http)
                          ▼
                       FastMCP server at /mcp  (same process, same port)
                          │  returns tool result → LLM speaks it
                          ▼
                       Agora ConvoAI Cloud → MiniMax TTS (managed) → user hears speech
                                          → RTM transcript / metrics → web UI
```

The browser only ever calls Next `/api/*`, which rewrites to the agent backend.
The agent backend owns Agora tokens and agent lifecycle. The **FastMCP server**
is mounted in the same process on the same port — `ngrok http 8000` exposes
both. See [ARCHITECTURE.md](./ARCHITECTURE.md).

## What You Get

- A **Next.js** web client (:3000) that drives the RTC/RTM lifecycle and only
  ever calls `/api/*`.
- A **FastAPI** agent backend (:8000) that owns Agora token generation and the
  agent session lifecycle.
- The `/api/get_config` · `/api/startAgent` · `/api/stopAgent` contract between
  the web client and the backend (Next rewrites, no Route Handlers).
- Agora-managed keyless OpenAI with `mcp_servers` + `enable_tools` — Agora cloud
  orchestrates the FastMCP `get_time` tool without any OpenAI API key on your end.
- A **zero-key mock** MCP server mounted in-process so the full pipeline runs
  with no LLM API key and only one port to expose.

## How It Works

1. The browser calls `/api/get_config`, which Next rewrites to the backend; the
   backend mints an Agora token from `AGORA_APP_ID` + `AGORA_APP_CERTIFICATE`.
2. The browser joins the RTC channel, then calls `/api/startAgent`; the backend
   starts an agent session using the managed `OpenAI` vendor with `mcp_servers`
   pointing at the public `MCP_ENDPOINT`.
3. The user speaks. Agora runs STT (Deepgram), then sends the transcript to the
   managed OpenAI LLM.
4. When the LLM emits a tool call (e.g. `get_time`), Agora cloud issues a
   streamable-HTTP request to `MCP_ENDPOINT`. The FastMCP server (mounted at
   `/mcp` in the same process) runs the tool and returns the result.
5. Agora feeds the tool result back to the LLM, which speaks the reply. Agora
   runs TTS (MiniMax) and plays it back in the channel.
6. `/api/stopAgent` ends the session.

### Replacing the mock

Add tools in [`server/src/mcp_server.py`](server/src/mcp_server.py). Each
function decorated with `@mcp.tool()` is automatically registered. The mock
`get_time` tool needs no external credentials — replace or extend it with your
own logic.

## Repo Map

- `web/` — Next.js frontend (:3000); RTC/RTM lifecycle and UI.
- `server/` — FastAPI agent backend (:8000); Agora tokens + agent lifecycle,
  managed OpenAI vendor with `mcp_servers`, FastMCP server mounted at `/mcp`.
- `ARCHITECTURE.md` — system shape and component boundaries.
- `AGENTS.md` — guide for coding agents working in this repo.

## Troubleshooting

| Problem | Fix |
| --- | --- |
| Agent starts but never responds to "what time is it?" | `MCP_ENDPOINT` is not public or the `/mcp` path is wrong. Use your ngrok URL. |
| `doctor:local` warns about localhost | Replace the local URL with your public tunnel URL. |
| Local calls fail under a global proxy | Configure the proxy to send `127.0.0.1` and `localhost` DIRECT. |

## More Docs

- [ARCHITECTURE.md](./ARCHITECTURE.md)
- [AGENTS.md](./AGENTS.md)

## License

Released under the [MIT License](./LICENSE).
