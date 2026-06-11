# Agora Conversational AI — MCP Recipe (Python)

The **mcp** recipe in the Agora Conversational AI recipes family. Agora cloud
orchestrates a tool on a separate MCP server: the managed keyless OpenAI vendor
emits a tool call, Agora invokes the `mcp/` FastMCP server (which must be
publicly reachable), returns the result, and the LLM speaks it. STT (Deepgram)
and TTS (MiniMax) stay Agora-managed.

This recipe is **zero-key**: OpenAI is Agora-managed (no `OPENAI_API_KEY`
needed), and the `mcp/` tool is a mock (`get_time`) that needs no external
credentials. Replace it with your own tools.

**Distinct from `recipe-agent-tool-calling`**: in that recipe the tools run
inside the `llm/` endpoint. Here Agora orchestrates them on a separate MCP
server — the `mcp/` service is a standalone FastMCP HTTP server, and Agora
cloud calls it directly at `MCP_ENDPOINT`.

## Prerequisites

- [Python 3.8+](https://www.python.org/)
- [Bun](https://bun.sh/)
- [ngrok](https://ngrok.com/) (expose the MCP server publicly)
- Agora App ID + App Certificate ([Agora CLI](https://github.com/AgoraIO/cli) makes this easy)

## Run it

```bash
# 1. Install Python venvs + web deps
bun run setup

# 2. Add Agora credentials to server/.env.local
agora login
agora project use <your-project>
agora project env write server/.env.local

# 3. Expose the MCP server publicly — Agora cloud calls it directly
ngrok http 8001

# 4. Set MCP_ENDPOINT in server/.env.local (use whatever domain ngrok prints)
#    MCP_ENDPOINT=https://<your-tunnel>.ngrok-free.dev/mcp

# 5. Run all three services
bun run dev
```

Open [http://localhost:3000](http://localhost:3000) → **Start Conversation** →
ask "what time is it?".

## Architecture

```
Browser (localhost:3000)
  │  fetch /api/*
  ▼
Next.js  ──rewrite──▶  Agent backend  (server/, localhost:8000)
                          │  starts agent session (OpenAI vendor + mcp_servers)
                          ▼
                       Agora ConvoAI Cloud
                          │  user speech → Deepgram STT (managed)
                          │  OpenAI LLM (managed, keyless) → emits tool call
                          │  POST <MCP_ENDPOINT>   (streamable-http)
                          ▼
                       MCP server  (mcp/, localhost:8001)
                          ▲  public via ngrok tunnel
                          │  returns tool result → LLM speaks it
                          ▼
                       Agora ConvoAI Cloud → MiniMax TTS (managed) → user hears speech
                                          → RTM transcript / metrics → web UI
```

The browser only ever calls Next `/api/*`, which rewrites to the agent backend.
The agent backend owns Agora tokens and agent lifecycle. The **MCP server** is
separate because Agora cloud — not the browser — calls it, so it must be
publicly reachable. See [ARCHITECTURE.md](./ARCHITECTURE.md).

## Project structure

```
recipe-agent-mcp/
├── server/   # Agent backend (:8000) — tokens + agent lifecycle, OpenAI vendor + mcp_servers
│   ├── src/{server.py, agent.py, mcp_config.py}
│   └── scripts/run_fake_server.py
├── mcp/      # MCP server (:8001) — FastMCP streamable-http, no agora deps
│   └── src/mcp_server.py
├── web/      # Next.js frontend (:3000)
└── package.json
```

## Environment variables

Backend env file: [`server/.env.example`](server/.env.example).

| Variable | Required | Default | Notes |
| --- | :---: | :---: | --- |
| `AGORA_APP_ID` | Yes | — | Agora Console → Project → App ID |
| `AGORA_APP_CERTIFICATE` | Yes | — | Agora Console → Project → App Certificate |
| `MCP_ENDPOINT` | Yes | — | **Public** URL of your `mcp/` server (e.g. `https://<tunnel>/mcp`). Agora cloud calls it; cannot be `localhost`. |
| `OPENAI_MODEL` | | `gpt-4o-mini` | Model name for the managed OpenAI vendor |
| `OPENAI_API_KEY` | | — | Optional — Agora manages the OpenAI key (keyless by default) |
| `AGENT_GREETING` | | built-in | Optional opening line override |
| `PORT` | | `8000` | Agent backend port |
| `MCP_PORT` (mcp/.env.local) | | `8001` | Port for the MCP server |
| `AGENT_BACKEND_URL` (web deploy) | Yes (deploy) | — | Required when deploying `web` |

## Commands

```bash
bun run setup            # install web deps + create server/ and mcp/ venvs
bun run dev              # run mcp (:8001) + backend (:8000) + web (:3000)

bun run doctor           # prerequisite check (no creds needed)
bun run doctor:local     # + .env.local + credentials + MCP_ENDPOINT checks

bun run verify           # web-only gate (no Agora creds needed)
bun run verify:local     # full local gate: backend compile + web build
bun run clean            # remove venvs and build artifacts
```

## Replacing the mock

Add tools in [`mcp/src/mcp_server.py`](mcp/src/mcp_server.py). Each function
decorated with `@mcp.tool()` is automatically registered. The mock `get_time`
tool needs no external credentials — replace or extend it with your own logic.

## Troubleshooting

| Problem | Fix |
| --- | --- |
| Agent starts but never responds to "what time is it?" | `MCP_ENDPOINT` is not public or the `/mcp` path is wrong. Use your ngrok URL. |
| `doctor:local` warns about localhost | Replace the local URL with your public tunnel URL. |
| Local calls fail under a global proxy | Configure the proxy to send `127.0.0.1` and `localhost` DIRECT. |

## License

MIT
