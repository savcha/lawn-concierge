# Lawn Concierge Agent — Coding Agent Guidance

## Project Overview

This is an ADK multi-agent system that helps users maintain healthy lawns. It uses
Google's Agent Development Kit (ADK) with agents-cli for development and deployment.

## Architecture

```
root_agent (Orchestrator)
├── watering_agent     — weather-based watering schedules
├── lawn_care_agent    — mowing & fertilizing recommendations
├── diagnosis_agent    — pest & weed identification
└── scheduler_agent    — Google Calendar reminder creation
```

The orchestrator routes user queries to the appropriate sub-agent. Sub-agents use
tools from the custom MCP server (`mcp_server/`) and Google Calendar API.

## Key Files

- `app/agent.py` — root orchestrator + App definition
- `app/sub_agents/` — four specialist sub-agents
- `app/tools/` — shared tool functions (weather, calendar, knowledge base)
- `mcp_server/server.py` — custom FastMCP server with lawn tools
- `mcp_server/tools/` — tool implementations for the MCP server
- `tests/eval/` — evaluation datasets and config

## ADK Patterns Used

- **Multi-agent delegation**: `root_agent` has `sub_agents=[...]`; each sub-agent
  has a `description` the orchestrator uses to decide routing.
- **MCP integration**: `MCPToolset` with `StdioServerParameters` connects the agent
  to the custom MCP server via subprocess stdio.
- **Google Calendar tools**: Implemented as plain ADK tool functions using the
  `google-api-python-client` library.

## Environment Variables

Copy `.env.example` to `.env` and fill in:
- `GOOGLE_CLOUD_PROJECT` — GCP project ID
- `OPENWEATHER_API_KEY` — from https://openweathermap.org/api (free tier)
- `GOOGLE_CALENDAR_CREDENTIALS_FILE` — OAuth2 credentials JSON

## Development Workflow

```bash
make install      # install deps with uv
make dev          # start ADK playground (hot reload)
make eval         # run eval suite
make test         # run unit + integration tests
make deploy-cloud-run  # deploy to GCP Cloud Run
```

## Coding Conventions

- All tool functions must have detailed docstrings — the LLM uses them for tool selection.
- Sub-agent instructions should be specific about what they do and do NOT handle.
- Never hardcode API keys; always read from environment variables.
- Add type hints to all tool function parameters and return types.
- Keep sub-agents focused: each handles one concern, delegates everything else.

## Commit Messages

See the `conventional-commits` skill (`conventional-commits.skill`) for the full
specification, type table, project-specific scopes, and examples.
A `commit-msg` hook (installed by `make install`) enforces the format automatically.
