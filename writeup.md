# Lawn Concierge — An AI Agent for Healthy Lawns

**Track:** Concierge Agents
**Repository:** https://github.com/savcha/lawn-concierge

---

## The Problem

Most homeowners want a nice lawn, but few actually have one. Not because they don't try — they do — but because lawn care is deceptively technical. The right watering schedule depends on your grass type, your local climate, and whether it rained last Tuesday. The right fertilizer has a specific nitrogen-phosphorus-potassium ratio that varies by species. Mowing at the wrong height during a heat wave can kill a lawn in days. And if a pest or fungus takes hold, the window to treat it effectively is measured in days, not weeks.

The result is a common failure pattern: homeowners either over-water (breeding fungal disease), mow too short (stressing roots in summer heat), fertilize at the wrong time (burning dormant grass), or ignore a pest until it has destroyed half the lawn. A single misstep, at the wrong time of year, can cost hundreds of dollars to repair and months to recover.

What's missing isn't information — the internet has plenty of lawn care advice. What's missing is *personalized, timely guidance*: advice that knows your specific grass type, looks up your actual local weather, and tells you what to do *right now*, not in general.

That's the gap Lawn Concierge fills.

---

## Why Agents?

A static chatbot or a decision-tree app could answer basic questions, but it can't do what Lawn Concierge does: reason across multiple specialized domains simultaneously, pull live data from external APIs, and take action on behalf of the user (like creating a Google Calendar reminder with the specific fertilizer quantity pre-filled).

Consider a request like: *"Set up lawn care reminders for my 2,500 sq ft Bermuda lawn in Dallas."* Satisfying this correctly requires:

1. Looking up Bermuda grass's fertilizing schedule (3 applications/year, 21-7-14 NPK)
2. Computing the quantity for 2,500 sq ft (10 lbs per application)
3. Checking Dallas's climate zone to confirm seasonal timing
4. Creating calendar events with all of that detail already in the description

No single model call can do this. You need an orchestrated pipeline where multiple specialist agents collaborate, each doing what it's good at, with tools that fetch real-time data. That's exactly what an agentic architecture provides — and why this problem is a natural fit for the Concierge Agents track.

---

## Solution: The Lawn Concierge

Lawn Concierge is a multi-agent AI system built on Google's Agent Development Kit (ADK). A root orchestrator agent handles conversation and routes requests to four specialist sub-agents, each backed by tools from a custom MCP server. The whole system is containerized and deployed to GCP Cloud Run.

**What it can do:**

- Tell you exactly when and how much to water based on a 7-day weather forecast for your location
- Give you mowing height and frequency by grass type and month, including dormancy warnings
- Generate a fertilizing schedule with the specific NPK ratio and quantity in pounds for your lawn size
- Diagnose pests, weeds, and fungal diseases from described symptoms and recommend treatments
- Proactively surface upcoming pest prevention windows before problems develop
- Create Google Calendar reminders with fully populated descriptions — date, product, quantity, instructions

---

## Architecture

```
User
 │
 ▼
Root Orchestrator (Gemini 2.5 Flash)
 │   Reads: grass type, location, lawn size
 │   Routes to the right specialist
 │
 ├──► watering_agent ──────────────► Lawn Tools MCP Server
 │         └── weather_forecast()        └── OpenWeatherMap API
 │         └── current_weather()
 │
 ├──► lawn_care_agent ─────────────► Lawn Tools MCP Server
 │         └── mowing_schedule()         └── Grass knowledge base
 │         └── fertilizing_schedule()
 │         └── aeration_schedule()
 │
 ├──► diagnosis_agent ─────────────► Lawn Tools MCP Server
 │         └── diagnose_problem()        └── Pest/weed/disease KB
 │         └── pest_prevention_schedule()
 │
 └──► scheduler_agent ─────────────► Google Calendar API v3
           └── create_lawn_reminder()       (OAuth2)
           └── create_lawn_care_calendar()
```

### The Root Orchestrator

The orchestrator is not just a router — it enforces multi-step workflows. Two key routing rules are baked into its instruction:

**Reminder requests are always multi-step.** A request like "remind me to fertilize" might look like a single scheduling task, but a useful reminder needs the fertilizer type, quantity, and instructions. The orchestrator is instructed to always route to `lawn_care_agent` first to compute those specifics, then pass them to `scheduler_agent` — so the calendar event reads *"Apply 10 lbs of 21-7-14 to 2,500 sq ft Bermuda"*, not just *"Fertilize lawn"*.

**Care plans always include pest prevention.** A request for a "full seasonal care plan" should never return just a mowing and fertilizing schedule. The orchestrator is instructed to always route to both `lawn_care_agent` and `diagnosis_agent` — the latter for proactive pest prevention windows, not just reactive diagnosis. This ensures users are warned about crabgrass pre-emergent timing in February, not after the crabgrass appears in May.

### The Custom MCP Server

The custom MCP server (`mcp_server/`) is the backbone of the system's specialist knowledge. It exposes eight tools via FastMCP over stdio:

- **`weather_forecast`** / **`current_weather`** — OpenWeatherMap API integration with plain-language watering advice derived from the forecast
- **`mowing_schedule`** — grass-type-specific height ranges, frequency, dormancy detection, and estimated mow time by lawn size
- **`fertilizing_schedule`** — NPK ratios, application timing, quantity calculation, and dormancy warnings
- **`aeration_schedule`** — core aeration timing by grass type with overseeding tie-in
- **`lawn_care_advice`** — open-ended seasonal advice for any stated concern
- **`diagnose_problem`** — symptom-based scoring against a pest/weed/disease knowledge base, with confidence levels
- **`pest_prevention_schedule`** — proactive treatment windows for the current and next two months
- **`pest_weed_library`** — full catalog for browsing

Each tool has a detailed docstring explaining when to use it. The LLM uses these descriptions — not just the tool name — to decide which tool to call. Writing precise docstrings is one of the most impactful things you can do for agent reliability.

### Sub-agent Tool Filtering

Each sub-agent is given a filtered view of the MCP server via `tool_filter`. The `watering_agent` only sees weather tools; the `lawn_care_agent` only sees mowing/fertilizing/aeration tools. This keeps each agent's decision space small and prevents cross-domain confusion — a watering agent that can see fertilizing tools is more likely to hallucinate cross-domain advice.

---

## Course Concepts Applied

| Concept | Implementation |
|---|---|
| **Agent / Multi-agent system (ADK)** | `app/agent.py` — root orchestrator with `sub_agents=[...]`; each specialist has a focused `description` used for routing |
| **MCP Server** | `mcp_server/server.py` — custom FastMCP server with 8 tools; connected via `MCPToolset` + `StdioServerParameters` |
| **Agent Skills (Agents CLI)** | Project scaffolded with `agents-cli`; `make dev` runs `agents-cli playground`; `make deploy` runs `agents-cli deploy` |
| **Agent Skills (Claude Code)** | `conventional-commits.skill` — a packaged skill that enforces Conventional Commits on this repository, installed via `make install` alongside a `commit-msg` git hook |
| **Deployability** | Containerized with Docker; deployed to GCP Cloud Run; secrets stored in Secret Manager; one-command deploy via `make deploy` |
| **Security** | No secrets in code; Secret Manager for API keys; OAuth2 for Calendar; least-privilege service account; non-root container user |

---

## The Build

The project was built entirely using agentic tools — specifically Claude in Cowork mode, with the `agents-cli` skills and `google-agents-cli` skills installed. Here's a condensed view of the build arc:

**Scaffolding.** The project structure follows the `agents-cli` convention (`app/`, `tests/eval/`, `pyproject.toml` with `[tool.agents-cli]`, `GEMINI.md`). This ensures `agents-cli playground`, `agents-cli eval`, and `agents-cli deploy` all work without custom configuration.

**MCP server first.** The custom MCP server was built before the ADK agents. This turned out to be the right order: writing the tool implementations first forced clarity on exactly what data each tool would return — which made writing the agent instructions much easier.

**Routing logic evolved through iteration.** The first version of the orchestrator routed naively. Testing revealed that "remind me to fertilize" went straight to `scheduler_agent`, which had no context to create a useful reminder. And "give me a care plan" returned only mowing and fertilizing — no pest prevention. Both were fixed with explicit routing rules in the orchestrator's instruction. The lesson: good routing is not just about which agent handles what, it's about enforcing *sequence* when a task is inherently multi-step.

**Eval-driven development.** The `tests/eval/evalsets/basic.evalset.json` file contains eight test cases covering each major user flow. These were used with `agents-cli eval` to verify routing accuracy and response quality throughout development. The eval config (`eval_config.json`) defines four grading criteria: routing accuracy, grass-type specificity, actionable advice, and safety (pesticide label recommendations). Running evals after each change to the orchestrator instruction made it possible to catch regressions quickly.

**Conventional Commits as a skill.** One meta-artifact of the build is `conventional-commits.skill` — a packaged Cowork/Claude Code skill that provides commit message guidance for this specific repository, including project-specific scopes (`watering`, `mcp`, `scheduler`, etc.). The skill is installed alongside a `commit-msg` git hook via `make install`, so both human developers and AI coding agents are held to the same standard.

---

## Deployment

The agent runs on GCP Cloud Run. Deployment is a single command:

```bash
make deploy  # runs: agents-cli deploy
```

Under the hood, `agents-cli deploy` builds the container image with Cloud Build, pushes it to Artifact Registry, and deploys a new Cloud Run revision. The OpenWeatherMap API key and Google Calendar OAuth token are stored in Secret Manager and injected as environment variables at runtime — they never touch the container image or source code.

The Cloud Run service is accessed via an authenticated proxy tunnel:

```bash
gcloud run services proxy lawn-concierge --region us-central1 --port 8081
# Then open: http://localhost:8081/dev-ui/?app=app
```

This setup satisfies the deployability criterion: the entire system runs on managed infrastructure with no servers to maintain, scales to zero when idle, and can be redeployed from a clean checkout in under five minutes.

---

## Results and Next Steps

The agent successfully handles the full range of lawn care conversations — from quick questions ("can I mow today?") to complex multi-step workflows ("set up my full spring care calendar for my Bermuda lawn in Austin"). All 16 unit tests pass. The eval suite demonstrates correct routing across all eight test scenarios.

The current knowledge base covers six grass types and the most common pests, weeds, and diseases in North America. Natural extensions include:

- **Soil sensor integration** — connect to smart irrigation systems (Rachio, RainBird) to replace the weather-based watering heuristic with actual soil moisture readings
- **Photo-based diagnosis** — add a vision tool to the diagnosis agent so users can upload a photo rather than describe symptoms
- **Regional expansion** — the pest and weed knowledge base is US-centric; adding regional databases for Australia, Europe, and tropical climates would make the agent globally useful
- **Pushover/SMS reminders** — complement Google Calendar with mobile push notifications for time-sensitive treatments (e.g., "apply pre-emergent within 48 hours — soil temp hitting 55°F tomorrow")

---

## Conclusion

Lawn Concierge demonstrates that agentic systems aren't just for complex enterprise workflows — they're also the right tool for personal, domain-specific assistants where good advice requires reasoning across multiple knowledge sources and taking real action on behalf of the user. The combination of ADK multi-agent delegation, a purpose-built MCP server, and Calendar integration produces an experience that's genuinely more useful than any static guide or simple chatbot could be.

The full source is at **https://github.com/savcha/lawn-concierge**.
