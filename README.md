# 🌿 Lawn Concierge

> An AI-powered personal lawn care assistant built with Google ADK, MCP, and Agents CLI — deployed to GCP Cloud Run.

## Problem

Homeowners struggle to maintain healthy lawns because lawn care is surprisingly complex:
the right watering, mowing, and fertilizing schedule depends on grass type, local climate,
and season. Most people either over-water, mow too short, or fertilize at the wrong time —
leading to yellowed, patchy, or disease-prone lawns.

## Solution

Lawn Concierge is a **Concierge Agent** that acts as a knowledgeable lawn care advisor,
available 24/7 via chat. It knows your grass type, tracks your local weather, and tells
you exactly what to do — and when — to keep your lawn healthy.

## Architecture

```
User ──► Root Orchestrator (Gemini)
              │
              ├──► watering_agent    ◄──► Lawn Tools MCP Server
              │         └── weather_forecast, current_weather
              │
              ├──► lawn_care_agent   ◄──► Lawn Tools MCP Server
              │         └── mowing_schedule, fertilizing_schedule,
              │             aeration_schedule, lawn_care_advice
              │
              ├──► diagnosis_agent   ◄──► Lawn Tools MCP Server
              │         └── diagnose_problem, pest_prevention_schedule,
              │             pest_weed_library
              │
              └──► scheduler_agent  ◄──► Google Calendar API
                        └── create_lawn_reminder, create_lawn_care_calendar,
                            list_upcoming_lawn_events
```

### Components

| Component | Technology | Purpose |
|---|---|---|
| Root orchestrator | Google ADK `Agent` | Routes queries to specialist sub-agents |
| Watering sub-agent | Google ADK `Agent` | Weather-based watering advice |
| Lawn Care sub-agent | Google ADK `Agent` | Mowing and fertilizing schedules |
| Diagnosis sub-agent | Google ADK `Agent` | Pest, weed, disease identification |
| Scheduler sub-agent | Google ADK `Agent` | Google Calendar reminder creation |
| Lawn Tools MCP Server | FastMCP (Python) | Custom MCP tools: weather + lawn knowledge base |
| Weather data | OpenWeatherMap API | 7-day forecasts for watering decisions |
| Calendar integration | Google Calendar API v3 | OAuth2-secured event creation |
| Deployment | GCP Cloud Run (via `agents-cli deploy`) | Containerized, auto-scaling serverless |

## Setup

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- Google Cloud SDK (`gcloud`) — for deployment
- A [free OpenWeatherMap API key](https://openweathermap.org/api)

### 1. Install Agents CLI + Skills

```bash
uvx google-agents-cli setup
```

### 2. Clone and install

```bash
git clone https://github.com/savcha/lawn-concierge
cd lawn-concierge
uv sync
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env and fill in:
#   GOOGLE_CLOUD_PROJECT       — your GCP project ID
#   GOOGLE_GENAI_USE_VERTEXAI  — leave as TRUE (uses Vertex AI + ADC instead of
#                                 an AI Studio API key). The agent will fail to
#                                 respond at all if this isn't set — Application
#                                 Default Credentials must be configured too
#                                 (`gcloud auth application-default login`).
#   OPENWEATHER_API_KEY        — from https://openweathermap.org/api (free tier)
```

### 4. Set up Google Calendar (optional, for reminders)

1. Go to [GCP Console](https://console.cloud.google.com) → APIs & Services → Credentials
2. Create an OAuth 2.0 Client ID (Desktop application)
3. Download the JSON file and save it as `credentials.json` in the project root
4. On the [OAuth consent screen](https://console.cloud.google.com/apis/credentials/consent),
   add your own Google account under **Test users** — while the app is in "Testing"
   publishing status, OAuth will fail with `403: access_denied` for any account not
   on this list, and the resulting refresh token expires after ~7 days
5. On first use, the agent will open a browser window for OAuth authorization

### 5. Run locally

```bash
# Start the ADK web playground (hot reload)
make dev

# Or use the agents-cli playground
uv run agents-cli playground
```

Open http://localhost:8080/dev-ui/?app=app in your browser to chat with the Lawn Concierge.

### 6. Run tests

```bash
# Unit tests (no API key needed)
make test

# Legacy criteria-based eval (requires Gemini API key or GCP project)
make eval

# LLM-as-judge eval pipeline — generates traces against tests/eval/datasets/scenarios.json,
# then grades them with custom judge metrics defined in tests/eval/eval_config.yaml.template
make generate-traces
make grade
```

## Usage Examples

**Watering advice:**
```
You: It's July in Austin, TX. I have Bermuda grass. Do I need to water today?
Lawn Concierge: [fetches weather for Austin] It's going to be hot and dry this week —
  no rain expected. Your Bermuda needs about 1 inch of water per week. Water deeply
  2x this week, early morning (5–7am) to reduce evaporation...
```

**Mowing schedule:**
```
You: How short should I mow my St. Augustine grass in summer?
Lawn Concierge: Keep St. Augustine at 3–4 inches during summer — taller grass shades
  the roots and reduces water stress. Mow every 7–10 days and never remove more than
  1/3 of the blade height in a single session.
```

**Pest diagnosis:**
```
You: My lawn has yellowing patches in the sunniest spots. It feels spongy and it's spreading.
Lawn Concierge: That sounds like Chinch Bugs — a classic symptom on warm-season grasses
  during hot, dry summers. Treatment: apply bifenthrin or permethrin. Water thoroughly
  before and after application. Always read the product label for safety instructions.
```

**Calendar reminder:**
```
You: Remind me to fertilize my Bermuda lawn in August.
Lawn Concierge: Based on your lawn, you'll need about 6 lbs of 21-7-14 fertilizer.
  What date in August would you like the reminder set for?
You: August 15th.
Lawn Concierge: Done! Created "Fertilize Lawn — Bermuda (21-7-14)" for August 15th,
  with a 1-hour popup and 1-day email reminder. [Creates event → link]
```

## Deployment to GCP Cloud Run

Deployment is handled by `agents-cli` (wraps Cloud Build + `gcloud run deploy`).
No manual image build or Terraform needed.

### 1. Create Secret Manager secrets (first time only)

```bash
# OpenWeatherMap API key
printf '%s' "YOUR_OPENWEATHER_KEY" | \
  gcloud secrets create lawn-concierge-openweather-api-key \
    --replication-policy=automatic --data-file=-

# Google Calendar OAuth token (run local OAuth flow first, then store token.json)
cat token.json | \
  gcloud secrets create lawn-concierge-calendar-token \
    --replication-policy=automatic --data-file=-

# Grant the Cloud Run compute SA access to both secrets
SA="$(gcloud projects describe $GOOGLE_CLOUD_PROJECT \
  --format='value(projectNumber)')-compute@developer.gserviceaccount.com"
for secret in lawn-concierge-openweather-api-key lawn-concierge-calendar-token; do
  gcloud secrets add-iam-policy-binding "$secret" \
    --member="serviceAccount:$SA" --role="roles/secretmanager.secretAccessor"
done
```

### 2. Deploy

```bash
make deploy
```

`make deploy` runs `agents-cli deploy`, which builds the container with Cloud Build,
pushes it to Artifact Registry, and deploys a new Cloud Run revision — all in one step.

### 3. Access the deployed agent

```bash
# Open a local authenticated tunnel (token expires ~1 hour, restart when needed)
gcloud run services proxy lawn-concierge \
  --region $GOOGLE_CLOUD_LOCATION --port 8081
```

Then open `http://localhost:8081/dev-ui/?app=app` in your browser.

## Security

- **No secrets in code** — all API keys are stored in Secret Manager or `.env` (gitignored)
- **OAuth2 for Calendar** — users authorize with their own Google account; the token is
  stored locally for dev, or in Secret Manager (`GOOGLE_CALENDAR_TOKEN_JSON`) for the
  deployed service, refreshed non-interactively since there's no browser available there
- **Non-root container** — Dockerfile runs as an unprivileged `appuser`
- **No PII stored** — agent is stateless; no user data is persisted between sessions
- ⚠️ **Service account is not yet least-privilege** — `agents-cli deploy` currently runs
  the Cloud Run service under the project's default compute service account (broad
  `roles/editor`), not a dedicated least-privilege identity. Pass `--service-account`
  with a purpose-built SA (only `secretmanager.secretAccessor` + `aiplatform.user`) before
  using this beyond a personal demo.

## Project Structure

```
lawn-concierge/
├── app/                          # ADK agent code
│   ├── agent.py                  # Root orchestrator + App definition
│   ├── sub_agents/               # Specialist sub-agents
│   │   ├── watering.py
│   │   ├── lawn_care.py
│   │   ├── diagnosis.py
│   │   └── scheduler.py
│   └── tools/
│       └── calendar_tools.py     # Google Calendar API integration
├── mcp_server/                   # Custom FastMCP server
│   ├── server.py                 # MCP entry point
│   └── tools/
│       ├── weather.py            # OpenWeatherMap integration
│       ├── lawn_advisor.py       # Mowing/fertilizing/aeration knowledge base
│       └── diagnosis.py          # Pest/weed/disease diagnosis + proactive prevention
├── tests/
│   ├── eval/
│   │   ├── datasets/scenarios.json       # LLM-as-judge eval scenarios
│   │   ├── eval_config.yaml.template     # Custom judge metrics (project-agnostic)
│   │   └── evalsets/basic.evalset.json   # Legacy criteria-based evalset (`make eval`)
│   ├── unit/                     # Unit tests (no API needed)
│   └── integration/              # End-to-end agent tests
├── scripts/
│   └── generate_traces.py        # Local eval trace generator (`make generate-traces`)
├── Dockerfile                    # Container image (deployed via agents-cli)
├── agents-cli-manifest.yaml      # agents-cli project config
├── pyproject.toml                # Dependencies
├── Makefile                      # Dev workflow shortcuts
├── LICENSE                       # MIT
└── .env.example                  # Environment variable template
```

## Contributing

Issues and PRs welcome — especially for additional grass types, regional pest databases,
and soil sensor integrations.

## License

MIT
