# Agent Development Guide

For coding agents working in `recipe-agent-mcp`. This repository is the **mcp**
recipe (`Recipe Role: mcp`) in the Agora Conversational AI recipes family.
The managed keyless OpenAI vendor emits a tool call, Agora invokes the FastMCP
server mounted at `/mcp` in the same backend process (at `MCP_ENDPOINT`, which
must be public), returns the result, and the LLM speaks it.

## System shape

- **`server/`** — Python FastAPI agent backend (:8000). Owns Agora token
  generation, agent session lifecycle, **and** the FastMCP server mounted at
  `/mcp` (same process, same port). SDK: `agora-agents>=2.3.0`
  (`import agora_agent`).
- **`web/`** — Next.js frontend (:3000), resynced from the base quickstart with
  MCP branding.
- Auth: Token007 from `AGORA_APP_ID` + `AGORA_APP_CERTIFICATE`. OpenAI is
  Agora-managed (keyless). `OPENAI_API_KEY` is optional.

## Routing / ownership

- UI and RTC/RTM lifecycle live in `web/`.
- Browser-facing `/api/*` paths are Next rewrites (`web/next.config.ts`) to the
  agent backend; do not add `web/app/api/**/route.ts` for agent/token logic.
- Token generation and agent lifecycle live in `server/src/`.
- MCP tool logic lives in `server/src/mcp_server.py` (mounted at `/mcp` inside
  the same FastAPI app).

## Supported modes

- **Local:** `bun run dev` starts `server` (:8000, including `/mcp`) and `web`
  (:3000). The web app calls `/api/*`; Next rewrites to
  `AGENT_BACKEND_URL=http://localhost:8000`. The backend must be exposed publicly
  (`ngrok http 8000`) so Agora cloud can reach `/mcp`.
- **Deploy:** deploy `web` (Next) + `server` (a single publicly reachable FastAPI
  process that also serves `/mcp`). Set `AGENT_BACKEND_URL` in the web deployment.

## Patterns

- Keep the web client calling `/api/*`; hide backend placement behind Next rewrites.
- Keep token generation and the App Certificate in `server/`.
- Keep `server/src/mcp_server.py` free of `agora-agents` — it is a standalone
  MCP module imported into `server.py` and mounted via `app.mount("/", ...)`.
- `MCP_ENDPOINT` is required and must be public; there is no localhost default.
- `OPENAI_API_KEY` is optional — Agora manages it (keyless).
- Use `ngrok http 8000` (not 8001) — the MCP endpoint is now on the same port as
  the token APIs.

## Anti-patterns

- Do not reintroduce Next Route Handlers for agent/token logic.
- Do not add `agora-agents` to `mcp_server.py`.
- Do not default `MCP_ENDPOINT` to localhost.
- Do not put `PORT` in `server/.env.example` (it would clobber the random port
  that `verify:local:fastapi` injects via `load_dotenv(override=True)`).
- Do not reintroduce a separate `mcp/` service or `docker-entrypoint.sh`.

## Commands

```bash
bun run setup
bun run dev
bun run doctor
bun run doctor:local
bun run verify         # web-only, no creds
bun run verify:local   # full local gate
```

Narrower checks: `bun run verify:backend`, `bun run verify:web:proxy`.

## Done criteria

1. Run the narrowest relevant verification command.
2. Web-affecting changes: `bun run verify:web` passes.
3. Backend-affecting changes: `bun run verify:local` (or the narrower
   `verify:backend`) passes.
4. If you change required env vars or setup steps, update the root README, the
   relevant module README, and `server/.env.example` together.

## Git conventions

- Conventional Commits: `type: description` or `type(scope): description`
  (`feat`, `fix`, `chore`, `test`, `docs`). Lowercase after the prefix, present
  tense.
- No AI tool names in commit messages or PR descriptions. No `Co-Authored-By`
  trailers. No `--no-verify`. No git config changes.
- Branch names: `type/short-description` (e.g. `feat/add-weather-tool`).
