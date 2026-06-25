# Doc Test Results

**Repo:** `AgoraIO-Conversational-AI/recipe-agent-mcp`
**Date:** 2026-06-25
**Reviewer:** automated doc-test run

---

## Structural Checks

| Check | Result |
| --- | --- |
| `docs/ai/L0_repo_card.md` exists | PASS |
| L0 ≤ 50 lines (actual: 36) | PASS |
| L0 Identity table present | PASS |
| L0 L1 summary table present | PASS |
| `docs/ai/RECIPE.md` exists | PASS |
| RECIPE.md has YAML frontmatter | PASS |
| `docs/ai/L1/` contains exactly 8 files | PASS |
| All 8 L1 files have H1 heading | PASS |
| All 8 L1 files have `> purpose` blockquote | PASS |
| All 8 L1 files have `## Related Deep Dives` | PASS |
| `docs/ai/L1/L2/_index.md` exists | PASS |
| `docs/ai/L1/L2/mcp_tool_wiring.md` exists | PASS |
| `docs/ai/L1/L2/session_lifecycle.md` exists | PASS |
| Both L2 deep dives have `**When to Read This:**` | PASS |
| `AGENTS.md` has `## How to Load` | PASS |
| `AGENTS.md` has `## Git Conventions` | PASS |
| `AGENTS.md` has `## Doc Commands` | PASS |
| `AGENTS.md` Recipe Role = `base` | PASS |
| `CLAUDE.md` redirects to `@AGENTS.md` | PASS |
| No stale "docs/ai not present" note in AGENTS.md | PASS |

**Structural check total: 20/20 PASS**

---

## Relative Link Check

| L1 file | L2 links declared | Target files exist |
| --- | --- | --- |
| `01_setup.md` | 0 | n/a |
| `02_architecture.md` | 2 (`mcp_tool_wiring`, `session_lifecycle`) | PASS |
| `03_code_map.md` | 0 | n/a |
| `04_conventions.md` | 1 (`mcp_tool_wiring`) | PASS |
| `05_workflows.md` | 2 (`mcp_tool_wiring`, `session_lifecycle`) | PASS |
| `06_interfaces.md` | 1 (`mcp_tool_wiring`) | PASS |
| `07_gotchas.md` | 1 (`mcp_tool_wiring`) | PASS |
| `08_security.md` | 0 | n/a |
| `L2/_index.md` | 2 entries | PASS |

**Relative link total: 7 checked links, 7 PASS**

---

## pytest (server/tests)

Run in throwaway venv `/tmp/v_mcp` (Python 3.14.4), `requirements.txt` + `requirements-dev.txt` installed. Venv removed after run.

```
platform darwin -- Python 3.14.4, pytest-9.1.1
collected 4 items

tests/test_agent_construction.py::test_start_constructs_real_agent_and_returns_shape PASSED
tests/test_mcp_config.py::test_build_mcp_servers PASSED
tests/test_mcp_config.py::test_build_mcp_servers_custom_name PASSED
tests/test_tool.py::test_current_time_message PASSED

4 passed in 1.16s
```

**pytest total: 4/4 PASS**

---

## Q&A — Source-Verified (≥12 across 5 categories)

### Category A: Setup & Prerequisites

| # | Question | Answer | Source |
| --- | --- | --- | --- |
| A1 | What is the minimum required env var unique to the MCP recipe? | `MCP_ENDPOINT` — a public URL of the `/mcp` endpoint; the server will not boot without it | `server/src/agent.py` `Agent.__init__()` raises `ValueError` if missing |
| A2 | Is `OPENAI_API_KEY` required? | No — Agora manages the OpenAI key (keyless). `OPENAI_API_KEY` is optional. | `server/.env.example` comment; `agent.py` `self.openai_api_key = os.getenv("OPENAI_API_KEY")` (no raise) |
| A3 | What command installs all dependencies? | `bun run setup` | `package.json` `setup` script |

### Category B: Architecture

| # | Question | Answer | Source |
| --- | --- | --- | --- |
| B1 | Is the FastMCP server a separate process? | No — it is mounted in the same uvicorn process as the FastAPI app via `app.mount("/", _mcp_asgi)` | `server/src/server.py` lines 36–44, 214 |
| B2 | Which port serves both the token APIs and `/mcp`? | Port 8000 | `server/src/server.py` `uvicorn.run(app, ..., port=port)` default 8000; `package.json` dev script |
| B3 | Who calls `MCP_ENDPOINT` during a tool call? | Agora cloud — not the browser and not the backend process itself | `server/src/agent.py` docstring; `ARCHITECTURE.md` |
| B4 | What STT and TTS vendors does this recipe use? | Deepgram STT (`nova-3`) and MiniMax TTS (`speech_2_6_turbo`) — both Agora-managed | `server/src/agent.py` `Agent.start()` `stt =` and `tts =` lines |

### Category C: MCP Wiring

| # | Question | Answer | Source |
| --- | --- | --- | --- |
| C1 | What is the transport string in the Agora `mcp_servers` list? | `"streamable_http"` (underscore) | `server/src/mcp_config.py` `build_mcp_servers()` |
| C2 | Which `advanced_features` flag must be set for tool calls to be dispatched? | `enable_tools: True` | `server/src/agent.py` `AgoraAgent(advanced_features={"enable_rtm": True, "enable_tools": True})` |
| C3 | Which decorator registers a function as an MCP tool? | `@mcp.tool()` | `server/src/mcp_server.py` `get_time` function |
| C4 | Does `mcp_config.py` import `agora-agents`? | No — it is explicitly kept import-free of `agora-agents` | `server/src/mcp_config.py` (no agora import); docstring "Pure builder — no agora_agent import" |

### Category D: Interfaces & Contracts

| # | Question | Answer | Source |
| --- | --- | --- | --- |
| D1 | What does `POST /startAgent` return? | `{ code: 0, msg: "success", data: { agent_id, channel_name, status: "started" } }` | `server/src/server.py` `start_agent` route |
| D2 | What happens to the rewrite map when `AGENT_BACKEND_URL` is unset? | `rewrites()` returns `[]` — no rewrites | `web/next.config.ts` |

### Category E: Security & Deployment

| # | Question | Answer | Source |
| --- | --- | --- | --- |
| E1 | What is the co-public caveat when deploying this recipe? | Exposing port 8000 publicly also exposes `/mcp` — add auth or restrict by source IP for production | `README.md` "Co-public caveat" section; `ARCHITECTURE.md` |
| E2 | Which secrets must never reach the browser? | `AGORA_APP_CERTIFICATE` and (if set) `OPENAI_API_KEY` — both stay in `server/.env.local` | `server/src/agent.py` env loading; `server/.env.example` |

**Q&A total: 15 questions, 15 PASS (all source-verified)**

---

## Summary Table by Category

| Category | Questions | Pass | Fail |
| --- | --- | --- | --- |
| A — Setup & Prerequisites | 3 | 3 | 0 |
| B — Architecture | 4 | 4 | 0 |
| C — MCP Wiring | 4 | 4 | 0 |
| D — Interfaces & Contracts | 2 | 2 | 0 |
| E — Security & Deployment | 2 | 2 | 0 |
| **Total** | **15** | **15** | **0** |

---

## Fix / Retest Section

No failures. No fixes required.

---

## Sandbox Note

pytest ran in throwaway venv `/tmp/v_mcp` — sandbox constraints (network, filesystem) did not interfere. `bun run verify:web` and `bun run verify:backend` were not run as part of this doc test (no bun workspace installed in the test environment). CI (`ci.yml`) covers these on push.
