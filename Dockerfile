# ─── Build stage ──────────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

# Install uv for fast dependency resolution
RUN pip install uv --no-cache-dir

# Copy dependency files first (layer caching)
COPY pyproject.toml ./
RUN uv pip install --system --no-cache-dir -e ".[dev]" 2>/dev/null || \
    uv pip install --system --no-cache-dir .

# ─── Runtime stage ─────────────────────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY app/ ./app/
COPY mcp_server/ ./mcp_server/

# Security: run as non-root user
RUN useradd --no-create-home --shell /bin/false appuser
USER appuser

# ADK serves on port 8080 by default
EXPOSE 8080

# Start the ADK web server
# Cloud Run injects PORT env var; ADK respects it
# Agents-dir is "." (WORKDIR /app, containing the app/ package) so ADK
# discovers "app" as the single app — passing "app" here would make ADK
# treat /app/app as the agents-root and scan ITS subdirectories instead.
# --allow_origins is required for the browser dev-ui to work when accessed
# via `gcloud run services proxy` (its Origin won't otherwise be allowed).
CMD ["python", "-m", "google.adk.cli", "web", "--host", "0.0.0.0", "--port", "8080", "--allow_origins", "*", "."]
