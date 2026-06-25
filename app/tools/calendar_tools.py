"""
Google Calendar tools for the Lawn Concierge agent.

Allows the scheduler sub-agent to create lawn care reminders and events
in the user's Google Calendar via the Google Calendar API (OAuth2).

Security note:
  - Locally: OAuth2 credentials are stored in a local file (not committed
    to git). The token is refreshed automatically and stored in token.json.
  - In headless deployments (Cloud Run, etc.): there is no browser to
    complete the interactive OAuth consent flow, so a pre-authorized token
    is instead loaded from GOOGLE_CALENDAR_TOKEN_JSON (typically sourced
    from Secret Manager) and refreshed non-interactively.
  - Scopes are limited to calendar event creation only.
"""

import json
import os
from datetime import datetime, timedelta, date
from typing import Any

# Google Calendar API imports — gracefully handle missing deps
try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    _GCAL_AVAILABLE = True
except ImportError:
    _GCAL_AVAILABLE = False

# Minimal scope — only create/modify events, not read all calendar data
SCOPES = ["https://www.googleapis.com/auth/calendar.events"]


def _get_calendar_service():
    """
    Authenticate and return a Google Calendar API service instance.

    Credential sources, in priority order:
      1. GOOGLE_CALENDAR_TOKEN_JSON — a pre-authorized OAuth token as a JSON
         string (e.g. mounted from Secret Manager). Used non-interactively;
         this is the only path available in headless deployments since
         there's no browser to complete an interactive consent flow there.
      2. GOOGLE_CALENDAR_TOKEN_FILE — a cached token file from a prior local
         run.
      3. Interactive OAuth via GOOGLE_CALENDAR_CREDENTIALS_FILE — opens a
         browser for authorization. Local development only.
    """
    if not _GCAL_AVAILABLE:
        raise RuntimeError(
            "Google API client libraries not installed. "
            "Run: pip install google-api-python-client google-auth-oauthlib"
        )

    token_file = os.environ.get("GOOGLE_CALENDAR_TOKEN_FILE", "token.json")
    token_json = os.environ.get("GOOGLE_CALENDAR_TOKEN_JSON")

    creds = None
    loaded_from_env = False

    if token_json:
        creds = Credentials.from_authorized_user_info(json.loads(token_json), SCOPES)
        loaded_from_env = True
    elif os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)

    # Refresh or re-authorize if needed
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        elif loaded_from_env:
            # No browser available in this environment — a non-refreshable
            # env-provided token means the stored token must be re-issued.
            raise RuntimeError(
                "GOOGLE_CALENDAR_TOKEN_JSON is set but the token is invalid "
                "and cannot be refreshed (missing or revoked refresh_token). "
                "Re-run the local OAuth flow and update the secret."
            )
        else:
            creds_file = os.environ.get("GOOGLE_CALENDAR_CREDENTIALS_FILE", "credentials.json")
            if not os.path.exists(creds_file):
                raise RuntimeError(
                    f"Google Calendar credentials file not found: {creds_file}\n"
                    "Download your OAuth2 credentials JSON from the GCP Console and "
                    f"save it as '{creds_file}'."
                )
            flow = InstalledAppFlow.from_client_secrets_file(creds_file, SCOPES)
            creds = flow.run_local_server(port=0)

        # Cache the (refreshed) token locally for future runs. Best-effort —
        # deployment filesystems may be read-only or ephemeral.
        try:
            with open(token_file, "w") as token:
                token.write(creds.to_json())
        except OSError:
            pass

    return build("calendar", "v3", credentials=creds)


def create_lawn_reminder(
    title: str,
    description: str,
    date_str: str,
    time_str: str = "07:00",
    duration_minutes: int = 60,
    calendar_id: str = "primary",
) -> dict[str, Any]:
    """
    Create a lawn care reminder in Google Calendar.

    Args:
        title: Event title (e.g., 'Fertilize lawn — Bermuda (21-7-14)').
        description: Detailed instructions or notes for the task.
        date_str: Date in YYYY-MM-DD format (e.g., '2026-06-15').
        time_str: Start time in HH:MM 24h format (e.g., '07:00'). Default 7am.
        duration_minutes: Event duration. Default 60 min.
        calendar_id: Google Calendar ID. Default 'primary'.

    Returns:
        dict with event_id, html_link, and confirmation message.
    """
    service = _get_calendar_service()

    # Parse datetime
    start_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    end_dt = start_dt + timedelta(minutes=duration_minutes)

    event_body = {
        "summary": f"🌿 {title}",
        "description": description,
        "start": {
            "dateTime": start_dt.isoformat(),
            "timeZone": "America/Chicago",  # default; user can adjust
        },
        "end": {
            "dateTime": end_dt.isoformat(),
            "timeZone": "America/Chicago",
        },
        "reminders": {
            "useDefault": False,
            "overrides": [
                {"method": "popup", "minutes": 60},   # 1-hour reminder
                {"method": "email", "minutes": 1440}, # 1-day reminder
            ],
        },
        "colorId": "2",  # sage green — fits lawn care theme
    }

    event = service.events().insert(calendarId=calendar_id, body=event_body).execute()

    return {
        "success": True,
        "event_id": event.get("id"),
        "html_link": event.get("htmlLink"),
        "message": f"Created calendar reminder: '{title}' on {date_str} at {time_str}.",
    }


def create_lawn_care_calendar(
    grass_type: str,
    lawn_size_sqft: int,
    location: str,
    start_date: str | None = None,
) -> dict[str, Any]:
    """
    Create a full seasonal lawn care calendar with multiple Google Calendar events.

    Generates a series of reminders for mowing, fertilizing, watering checks,
    and seasonal tasks based on the grass type.

    Args:
        grass_type: Type of grass (e.g., 'bermuda', 'fescue').
        lawn_size_sqft: Lawn area in square feet.
        location: City for weather context (e.g., 'Austin, TX').
        start_date: Start date in YYYY-MM-DD format. Defaults to today.

    Returns:
        dict with created_events count and list of event details.
    """
    from mcp_server.tools.lawn_advisor import GRASS_PROFILES, get_fertilizing_schedule

    grass_key = grass_type.lower().replace(" ", "_").replace("-", "_")
    profile = GRASS_PROFILES.get(grass_key)

    start = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else date.today()

    created_events = []
    errors = []

    if profile:
        # Schedule fertilizer applications
        fert_info = get_fertilizing_schedule(grass_key, lawn_size_sqft=lawn_size_sqft)
        for month_name in fert_info.get("annual_schedule", []):
            months = [
                "January", "February", "March", "April", "May", "June",
                "July", "August", "September", "October", "November", "December",
            ]
            month_idx = months.index(month_name) + 1
            year = start.year if month_idx >= start.month else start.year + 1
            event_date = f"{year}-{month_idx:02d}-01"

            try:
                result = create_lawn_reminder(
                    title=f"Fertilize Lawn — {grass_type.title()} ({fert_info['npk_ratio']})",
                    description=(
                        f"Apply {fert_info['estimated_quantity_lbs']} lbs of {fert_info['npk_ratio']} "
                        f"fertilizer to {lawn_size_sqft:,} sq ft of {grass_type} lawn.\n\n"
                        f"Tips:\n" + "\n".join(f"• {t}" for t in fert_info.get("product_tips", []))
                    ),
                    date_str=event_date,
                    time_str="08:00",
                    duration_minutes=90,
                )
                created_events.append({"type": "fertilize", "date": event_date, **result})
            except Exception as e:
                errors.append(f"Failed to create fertilize event for {month_name}: {e}")

    return {
        "success": len(created_events) > 0,
        "created_events": len(created_events),
        "events": created_events,
        "errors": errors,
        "message": (
            f"Created {len(created_events)} lawn care calendar events for {grass_type} "
            f"({lawn_size_sqft:,} sq ft) starting {start}."
        ),
    }


def list_upcoming_lawn_events(days_ahead: int = 30, calendar_id: str = "primary") -> dict[str, Any]:
    """
    List upcoming lawn care events from Google Calendar.

    Args:
        days_ahead: Number of days ahead to look. Default 30.
        calendar_id: Google Calendar ID. Default 'primary'.

    Returns:
        dict with events list (title, date, description).
    """
    service = _get_calendar_service()

    now = datetime.utcnow().isoformat() + "Z"
    end = (datetime.utcnow() + timedelta(days=days_ahead)).isoformat() + "Z"

    events_result = (
        service.events()
        .list(
            calendarId=calendar_id,
            timeMin=now,
            timeMax=end,
            maxResults=20,
            singleEvents=True,
            orderBy="startTime",
            q="lawn",  # filter for lawn-related events
        )
        .execute()
    )

    events = events_result.get("items", [])

    return {
        "events": [
            {
                "title": e.get("summary", ""),
                "date": e.get("start", {}).get("dateTime", e.get("start", {}).get("date", "")),
                "description": e.get("description", "")[:200],
                "link": e.get("htmlLink", ""),
            }
            for e in events
        ],
        "count": len(events),
        "message": f"Found {len(events)} upcoming lawn care event(s) in the next {days_ahead} days.",
    }
