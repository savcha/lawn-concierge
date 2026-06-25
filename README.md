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
              │         └── mowing_schedule, fertilizing_schedule, lawn_care_advice
              │
              ├──► diagnosis_agent   ◄──► Lawn Tools MCP Server
              │         └── diagnose_problem, pest_weed_library
              │
              └──► scheduler_agent  ◄──► Google Calendar API
                        └── create_lawn_reminder, create_lawn_care_calendar
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
| Deployment | GCP Cloud Run + Terraform | Containerized, auto-scaling serverless |

### Course Concepts Applied

This project demonstrates the following course concepts:

| Concept | Where |
|---|---|
| ✅ Agent / Multi-agent system (ADK) | `app/agent.py` — orchestrator + 4 sub-agents |
| ✅ MCP Server | `mcp_server/` — custom FastMCP server |
| ✅ Agent skills (Agents CLI) | Built and deployed using `agents-cli` |
| ✅ Agent skills (Claude Code) | `conventional-commits.skill` — enforces Conventional Commits on this repo |
| ✅ Deployability | Terraform + Cloud Run deployment |

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
#   GOOGLE_CLOUD_PROJECT  — your GCP project ID
#   OPENWEATHER_API_KEY   — from https://openweathermap.org/api (free tier)
```

### 4. Set up Google Calendar (optional, for reminders)

1. Go to [GCP Console](https://console.cloud.google.com) → APIs & Services → Credentials
2. Create an OAuth 2.0 Client ID (Desktop application)
3. Download the JSON file and save it as `credentials.json` in the project root
4. On first use, the agent will open a browser window for OAuth authorization

### 5. Run locally

```bash
# Start the ADK web playground (hot reload)
make dev

# Or use the agents-cli playground
uv run agents-cli playground
```

Open http://localhost:8080 in your browser to chat with the Lawn Concierge.

### 6. Run tests

```bash
# Unit tests (no API key needed)
make test

# Eval suite (requires Gemini API key or GCP project)
make eval
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
Lawn Concierge: I'll create a Google Calendar event for August 1st: "Fertilize Lawn —
  Bermuda (21-7-14)" with a reminder the day before. [Creates event → link]
```

## Deployment to GCP Cloud Run

### 1. Build and push container

```bash
export PROJECT_ID=$(gcloud config get-value project)
export REGION=us-central1
export IMAGE="$REGION-docker.pkg.dev/$PROJECT_ID/lawn-concierge/app:latest"

# Create Artifact Registry repo (first time only)
gcloud artifacts repositories create lawn-concierge \
  --repository-format=docker \
  --location=$REGION

# Build and push
gcloud builds submit --tag $IMAGE .
```

### 2. Deploy with Terraform

```bash
cd deployment/terraform/dev
terraform init
terraform apply \
  -var="project_id=$PROJECT_ID" \
  -var="region=$REGION" \
  -var="container_image=$IMAGE"
```

### 3. Add the OpenWeatherMap API key to Secret Manager

```bash
echo -n "YOUR_OPENWEATHER_KEY" | \
  gcloud secrets versions add lawn-concierge-openweather-api-key --data-file=-
```

### 4. Access the deployed agent

Terraform outputs the Cloud Run URL. Open it in your browser — the ADK web UI is served directly.

## Security

- **No secrets in code** — all API keys are stored in Secret Manager or `.env` (gitignored)
- **Least-privilege service account** — only `secretmanager.secretAccessor` and `aiplatform.user`
- **OAuth2 for Calendar** — users authorize with their own Google account; tokens stored locally
- **Non-root container** — Dockerfile runs as an unprivileged `appuser`
- **No PII stored** — agent is stateless; no user data is persisted between sessions

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
│       ├── lawn_advisor.py       # Mowing/fertilizing knowledge base
│       └── diagnosis.py         # Pest/weed/disease knowledge base
├── tests/
│   ├── eval/                     # agents-cli eval datasets
│   ├── unit/                     # Unit tests (no API needed)
│   └── integration/              # End-to-end agent tests
├── deployment/
│   └── terraform/dev/            # Cloud Run Terraform
├── Dockerfile                    # Container image
├── pyproject.toml                # Dependencies + agents-cli config
├── Makefile                      # Dev workflow shortcuts
├── GEMINI.md                     # Coding agent guidance
└── .env.example                  # Environment variable template
```

## Contributing

This is a capstone project for Kaggle's 5-Day AI Agents: Intensive Vibe Coding Course.
Issues and PRs welcome — especially for additional grass types, regional pest databases,
and soil sensor integrations.

## License

MIT
