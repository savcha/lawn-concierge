.PHONY: install dev playground eval test lint clean deploy-cloud-run mcp-server

# ─── Setup ────────────────────────────────────────────────────────────────────
install:
	uv sync
	git config core.hooksPath .githooks
	@echo "✓ Git hooks installed (.githooks/commit-msg)"

# ─── Development ─────────────────────────────────────────────────────────────
dev:
	uv run agents-cli playground

playground:
	uv run adk web

# Run only the MCP server (useful for debugging)
mcp-server:
	uv run python -m mcp_server.server

# ─── Testing & Evaluation ─────────────────────────────────────────────────────
test:
	uv run pytest tests/unit tests/integration -v

eval:
	uv run agents-cli eval app tests/eval/evalsets/basic.evalset.json

# Run the custom trace generator over tests/eval/datasets/scenarios.json,
# writing populated traces to artifacts/traces/
generate-traces:
	uv run python -m scripts.generate_traces

# Grade the most recently generated traces against the custom LLM-as-judge
# metrics defined in tests/eval/eval_config.yaml.template. Resolves the
# project-qualified judge_model resource name from GOOGLE_CLOUD_PROJECT
# (.env) into a gitignored tests/eval/eval_config.yaml before grading.
grade:
	@project=$$(grep -E '^GOOGLE_CLOUD_PROJECT=' .env | cut -d= -f2); \
	if [ -z "$$project" ]; then echo "GOOGLE_CLOUD_PROJECT not set in .env"; exit 1; fi; \
	sed "s/__GCP_PROJECT__/$$project/g" tests/eval/eval_config.yaml.template > tests/eval/eval_config.yaml
	uv run agents-cli eval grade --traces artifacts/traces/ --config tests/eval/eval_config.yaml

# ─── Code Quality ─────────────────────────────────────────────────────────────
lint:
	uv run ruff check app mcp_server tests

# ─── Deployment ───────────────────────────────────────────────────────────────
deploy-cloud-run:
	@echo "Deploying to Cloud Run..."
	cd deployment/terraform/dev && terraform init && terraform apply -auto-approve

# ─── Cleanup ─────────────────────────────────────────────────────────────────
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache dist build
