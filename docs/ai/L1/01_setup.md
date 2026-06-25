# 01 · Setup

> Install dependencies, configure env, and run the MCP recipe locally. This recipe is **zero-key**: `OPENAI_API_KEY` is optional — Agora manages it. The only required non-Agora configuration is `MCP_ENDPOINT`, which must be a public URL so Agora cloud can call the FastMCP server.

## Prerequisites

- Python 3.10+ (backend runs on 3.10 and 3.13 in CI)
- [Bun](https://bun.sh/) (runs the web app and orchestration scripts)
- [Agora CLI](https://github.com/AgoraIO/cli) (optional; easiest way to mint App ID + Certificate)
- [ngrok](https://ngrok.com/) (or equivalent tunnel) — Agora cloud must reach `MCP_ENDPOINT` publicly

## Install

```bash
bun run setup            # installs web deps + creates server/ venv from requirements.txt
```

`setup` runs `setup:env` (copies `server/.env.example` → `server/.env.local` if missing), `setup:server` (recreates `server/venv`, installs `requirements.txt`), and `setup:web` (`bun install`).

## Configure env

Backend env file is `server/.env.local` (template: `server/.env.example`).

| Variable                | Required | Default                | Notes                                                                          |
| ----------------------- | :------: | ---------------------- | ------------------------------------------------------------------------------ |
| `AGORA_APP_ID`          |    ✅    | —                      | Agora Console → Project → App ID                                               |
| `AGORA_APP_CERTIFICATE` |    ✅    | —                      | Agora Console → Project → App Certificate                                      |
| `MCP_ENDPOINT`          |    ✅    | —                      | **Public** URL of the `/mcp` endpoint (e.g. `https://<tunnel>/mcp`). Agora cloud calls it — cannot be `localhost`. |
| `OPENAI_MODEL`          |          | `gpt-4o-mini`          | Model name for the managed OpenAI vendor                                       |
| `OPENAI_API_KEY`        |          | —                      | Optional — Agora manages the OpenAI key (keyless by default)                   |
| `AGENT_GREETING`        |          | `Hi! Ask me what time it is.` | Optional opening utterance override                                     |

Fill credentials via the Agora CLI or by hand:

```bash
agora login
agora project use <your-project>
agora project env write server/.env.local   # writes App ID + Certificate
# then expose the backend and set MCP_ENDPOINT:
ngrok http 8000
# add to server/.env.local:
# MCP_ENDPOINT=https://<your-tunnel>.ngrok-free.dev/mcp
```

> Do **not** add `PORT` to `server/.env.example` — see [07_gotchas](07_gotchas.md).

## Run

```bash
bun run dev              # backend (:8000, including /mcp) + web (:3000) via concurrently
```

Open <http://localhost:3000> → **Start Conversation** → ask "what time is it?". Backend API docs at <http://localhost:8000/docs>.

## Quick commands

```bash
bun run doctor           # shared prereqs (bun + node_modules); no creds needed
bun run doctor:local     # + .env.local + AGORA_APP_ID/CERTIFICATE + MCP_ENDPOINT present (warns if localhost)
bun run verify           # web-only gate (doctor + api contracts + web build)
bun run verify:local     # full local gate: backend compile + proxy + web build
bun run clean            # remove venv and build artifacts
```

Backend unit tests run standalone (no cloud, no creds):

```bash
cd server && pytest tests -v
```

## Related Deep Dives

- None. For what each verify command asserts, see [05_workflows](05_workflows.md) and [06_interfaces](06_interfaces.md).
