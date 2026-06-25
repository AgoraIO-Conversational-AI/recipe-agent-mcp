# 03 · Code Map

> Where things live. Two top-level modules: `web/` (Next.js client) and `server/` (FastAPI backend + FastMCP server). Orchestration is in the root `package.json`.

## Root

| Path                  | Responsibility                                                              |
| --------------------- | --------------------------------------------------------------------------- |
| `package.json`        | Bun workspace; `setup`, `dev`, `doctor*`, `verify*`, `clean` scripts.       |
| `README.md`           | Setup, run modes, env, architecture diagram, troubleshooting.               |
| `ARCHITECTURE.md`     | System shape, single-process design, MCP flow, auth.                        |
| `AGENTS.md`           | Coding-agent handbook + System shape / Patterns / Anti-patterns / Commands. |
| `Dockerfile`          | Single-process backend-only image (`:8000`, serves both APIs and `/mcp`).   |
| `.github/workflows/`  | `ci.yml` (backend pytest matrix + web verify), `docker.yml`, `nightly.yml`. |

## `server/` — FastAPI backend (:8000)

| Path                              | Responsibility                                                                      |
| --------------------------------- | ----------------------------------------------------------------------------------- |
| `src/server.py`                   | FastAPI app, CORS, route handlers, MCP mount, FastMCP lifespan, uvicorn entrypoint. |
| `src/agent.py`                    | `Agent` class: `AsyncAgora` client, `OpenAI` vendor + `DeepgramSTT` + `MiniMaxTTS`, `start()`/`stop()`, `_sessions`. |
| `src/mcp_config.py`               | `build_mcp_servers()` — pure builder for the `mcp_servers` list; no agora-agents import. |
| `src/mcp_server.py`               | FastMCP instance + `get_time` tool; mounted in-process by `server.py` at `/mcp`.   |
| `scripts/run_fake_server.py`      | Boots `server.app` with a `FakeAgent` for the local proxy smoke test.               |
| `tests/test_agent_construction.py`| Builds the real `AgoraAgent`, fakes the SDK session, asserts start result shape.   |
| `tests/test_mcp_config.py`        | Asserts `build_mcp_servers()` output shape and transport name.                      |
| `tests/test_tool.py`              | Asserts `current_time_message()` helper returns expected format.                    |
| `tests/conftest.py`               | `fake_env` fixture; no cloud, no real creds.                                        |
| `.env.example`                    | Env template (do not add `PORT`).                                                   |
| `requirements*.txt`               | Runtime + dev (pytest) deps.                                                        |

## `server/src/server.py` routes

- `GET /get_config` — token + channel/UID config.
- `POST /startAgent` — start the MCP agent session.
- `POST /stopAgent` — stop by `agent_id`.
- `POST /mcp` — FastMCP streamable-HTTP endpoint (called by Agora cloud, not the browser).

## `web/` — Next.js client (:3000)

| Path                                      | Responsibility                                                        |
| ----------------------------------------- | --------------------------------------------------------------------- |
| `next.config.ts`                          | `/api/*` rewrites to `AGENT_BACKEND_URL`; strict mode; Turbopack root.|
| `src/services/api.ts`                     | Browser API client: `getConfig`, `startAgent`, `stopAgent`.           |
| `src/lib/conversation.ts`                 | Transcript normalization, timestamp/UID mapping, visualizer state.    |
| `src/lib/agora.ts`                        | Agora RTC default agent UID constant.                                 |
| `src/components/LandingPage.tsx`          | Conversation entry: config fetch, agent start, RTM login, teardown.   |
| `src/components/ConversationComponent.tsx`| RTC join, mic publish, transcript/metrics/state listeners.            |
| `src/components/Quickstart*.tsx`          | Pre-call, transcript, metrics, layout panels.                         |
| `scripts/verify-api-contracts.ts`         | Asserts rewrites + client paths + response envelope (no network).     |
| `scripts/verify-local-proxy.ts`           | Stub backend; proxies `/api/*` through the rewrite map.               |
| `scripts/verify-local-fastapi.ts`         | Spawns real FastAPI with `FakeAgent`; proxies routes end-to-end.      |
| `scripts/doctor.ts`                       | Web prerequisite check.                                               |

## Related Deep Dives

- None. For runtime flow see [02_architecture](02_architecture.md); for contracts see [06_interfaces](06_interfaces.md).
