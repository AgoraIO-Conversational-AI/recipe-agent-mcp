---
recipe_version: 1.0.0
recipe_status: experimental
extension_points:
  - id: api.routes
    name: Browser-facing API routes
  - id: agent.mcp-tools
    name: MCP tools registered in mcp_server.py and exposed at MCP_ENDPOINT
  - id: agent.vendor-config
    name: OpenAI vendor model/system-prompt, STT vendor, TTS vendor
  - id: web.conversation-ui
    name: Conversation UI panels and controls
  - id: verification.contracts
    name: Contract, proxy, and local FastAPI smoke verification
invariants:
  - id: api.rewrite-boundary
    summary: Browser calls stay on /api/* and Next rewrites to FastAPI; no Route Handlers for agent/token logic.
  - id: secrets.server-only
    summary: Agora App Certificate stays in the Python backend; OPENAI_API_KEY (if supplied) also stays server-side.
  - id: mcp.single-process
    summary: The FastMCP server is mounted in the same uvicorn process as the FastAPI app; no separate mcp/ service or second port.
  - id: mcp.public-endpoint
    summary: MCP_ENDPOINT must be a publicly reachable URL; Agora cloud (not the browser) calls it.
  - id: mcp.import-isolation
    summary: mcp_server.py and mcp_config.py must not import agora-agents; they are standalone modules.
  - id: tools.enable-flag
    summary: enable_tools=True must be set in AgoraAgent advanced_features for tool calls to be routed to MCP_ENDPOINT.
  - id: token.uid-concrete
    summary: Backend resolves missing, zero, or negative UIDs before issuing an RTC+RTM token.
stable_contracts:
  - id: env.required
    summary: AGORA_APP_ID, AGORA_APP_CERTIFICATE, and MCP_ENDPOINT are required; AGENT_BACKEND_URL is required by deployed web rewrites.
  - id: api.core-routes
    summary: GET /api/get_config, POST /api/startAgent, and POST /api/stopAgent remain the browser-facing contract.
  - id: response.envelope
    summary: Successful backend responses use { code, msg, data }.
  - id: mcp.endpoint-path
    summary: The FastMCP server is always served at /mcp on the backend port.
---

# Recipe Contract

This base recipe defines the reusable surface for a Python-backed Agora Conversational AI **MCP** quickstart: a managed keyless OpenAI LLM with MCP tool calling (via Agora cloud → FastMCP server) behind a Next.js web client.

## Recipe Role

- Role: `base` recipe (self-contained, clone-and-run; no `Extends` pin).
- Target audience: developers adding MCP tools to an Agora Conversational AI agent without managing an OpenAI API key.
- Reuse model: clone, bind project, expose the backend publicly (`ngrok http 8000`), set `MCP_ENDPOINT`, run, then add tools in `mcp_server.py`.

## Recipe Scope

- Python FastAPI token generation and managed agent lifecycle.
- Cascading STT/LLM/TTS using Agora-managed vendors (`DeepgramSTT`, `OpenAI`, `MiniMaxTTS`). OpenAI is keyless by default.
- FastMCP server with one mock tool (`get_time`) mounted in-process at `/mcp`.
- Agora cloud orchestrating tool calls via streamable-HTTP to `MCP_ENDPOINT`.
- Next.js browser UI with RTC audio, RTM transcript/metrics, connection status.
- Rewrite-only `/api/*` browser facade hiding backend placement.
- Contract, proxy, and backend compile verification that need no live Agora calls.

## Baseline Implementation Guidance

Use this repo's source and progressive disclosure docs as the starting point, then customize. Do not recreate the Agora ConvoAI MCP integration from memory — vendor schemas, SDK builder fields, transport conventions, and token behavior drift. Copy verified patterns from this repo.

## Extension Points

| ID | Surface | How to extend | Required follow-up |
| -- | ------- | ------------- | ------------------ |
| `api.routes` | `server/src/server.py`, `web/next.config.ts`, `web/src/services/api.ts` | Add FastAPI route, add rewrite, add browser fetch helper. | Extend `web/scripts/verify-api-contracts.ts`; add proxy coverage. |
| `agent.mcp-tools` | `server/src/mcp_server.py` | Add `@mcp.tool()` decorated functions. | Add helper test in `server/tests/test_tool.py`; run `pytest tests`. |
| `agent.vendor-config` | `server/src/agent.py` | Change `OPENAI_MODEL`, `system_messages`, `DeepgramSTT` config, `MiniMaxTTS` config, or session `parameters`. | Run `verify:backend` + `pytest tests`; document new env in `server/.env.example` (never add `PORT`). |
| `web.conversation-ui` | `web/src/components/*`, `web/src/lib/conversation.ts` | Customize pre-call, transcript, metrics, connection status, mic, or visualizer UI. | Preserve RTC/RTM lifecycle ownership and transcript UID normalization. |
| `verification.contracts` | `web/scripts/*.ts`, root `package.json` | Add checks for new browser/backend boundaries. | Keep checks runnable without live Agora credentials. |

## Invariants

- Browser code calls only `/api/get_config`, `/api/startAgent`, and `/api/stopAgent` for the default flow.
- Next.js owns `/api/*` through rewrites only; no `web/app/api/**/route.ts` for agent/token logic.
- FastAPI owns token generation, `AGORA_APP_CERTIFICATE`, and agent lifecycle.
- The FastMCP server is mounted in the same process and port as the FastAPI app; no separate service.
- `MCP_ENDPOINT` must be a public URL; Agora cloud (not the browser) calls it.
- `mcp_server.py` and `mcp_config.py` must not import `agora-agents`.
- `enable_tools: True` must be in `AgoraAgent(advanced_features=...)`.
- The backend issues one RTC+RTM-capable token for a concrete non-zero UID.

## Stable Contracts

| Contract | Stable shape |
| -------- | ------------ |
| Required backend env | `AGORA_APP_ID`, `AGORA_APP_CERTIFICATE`, `MCP_ENDPOINT` |
| Optional backend env | `OPENAI_MODEL`, `OPENAI_API_KEY`, `AGENT_GREETING`, `PORT` (env only) |
| Required web deploy env | `AGENT_BACKEND_URL` |
| `GET /api/get_config` | Query `channel?`, `uid?`; returns `data.app_id`, `data.token`, `data.uid`, `data.channel_name`, `data.agent_uid`. |
| `POST /api/startAgent` | Body `{ channelName, rtcUid, userUid, parameters? }`; returns `data.agent_id`, `data.channel_name`, `data.status`. |
| `POST /api/stopAgent` | Body `{ agentId }`; returns `{ code: 0, msg: "success" }`. |
| MCP endpoint path | `/mcp` on the backend port; served by FastMCP streamable-HTTP. |
| Success envelope | `{ "code": 0, "msg": "success", "data": ... }` where the route has data. |
| Verification entry points | `bun run verify:web`, `bun run verify:backend`, `bun run verify:web:proxy`, `bun run verify:local`. |

## Internal / Subject to Change

- Visual layout, component composition, Tailwind classes, and assets under `web/src/components/`.
- Exact model name, voice, greeting text, and system prompt, as long as they stay documented extension points.
- In-memory `Agent._sessions` details; the stable behavior is start by channel/user and stop by returned `agent_id`.
- Verification internals under `web/scripts/`; the stable surface is the root script names and what they assert.
- `agora-agents` SDK minor-version behavior; this recipe lower-bounds `>=2.3.0` but does not freeze every field.
- The mock `get_time` tool content; it is a demo placeholder to replace.

## Related Progressive Disclosure Docs

- `L1/01_setup.md` — setup, env, and commands.
- `L1/02_architecture.md` — request flow, single-process topology, MCP tool call flow.
- `L1/05_workflows.md` — common modification workflows (add tool, change vendors, add route).
- `L1/06_interfaces.md` — route, rewrite, env, and MCP server contracts.
- `L1/L2/mcp_tool_wiring.md` — full MCP wiring detail.
- `L1/L2/session_lifecycle.md` — RTC/RTM/session orchestration.
