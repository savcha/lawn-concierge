"""
Trace generator for local evaluation.

Runs each scenario in tests/eval/datasets/scenarios.json through the Lawn
Concierge agent using ADK's local in-memory Runner, and writes the resulting
conversation traces (agent text, tool calls, tool responses) in the
EvaluationDataset grading-input format expected by `agents-cli eval grade`.

Usage:
    uv run python scripts/generate_traces.py
    uv run python scripts/generate_traces.py --dataset path/to/scenarios.json --output artifacts/traces/
"""

import argparse
import asyncio
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from google.adk.runners import InMemoryRunner
from google.genai import types

from app.agent import app, root_agent


def _collect_sub_agents(agent) -> dict:
    """Walk the agent tree and build the EvalCase `agents` map."""
    agents = {
        agent.name: {
            "agent_id": agent.name,
            "instruction": getattr(agent, "instruction", "") or "",
        }
    }
    for sub_agent in getattr(agent, "sub_agents", None) or []:
        agents.update(_collect_sub_agents(sub_agent))
    return agents


def _final_response_content(events: list[dict]) -> dict | None:
    """Extract the final agent text response from a list of events.

    Walks events in reverse for the most recent text-bearing part. Mirrors
    `agents-cli eval generate`'s extraction so EvalCase.responses is
    populated the same way LLMMetric grading expects.
    """
    for event in reversed(events):
        parts = (event.get("content") or {}).get("parts") or []
        texts = [p.get("text") for p in parts if p.get("text")]
        if texts:
            return {
                "role": event["content"].get("role") or "model",
                "parts": [{"text": "".join(texts)}],
            }
    return None


async def _run_scenario(scenario: dict) -> dict:
    runner = InMemoryRunner(app=app)
    user_id = "eval-user"
    session_id = f"eval-{uuid.uuid4().hex[:8]}"

    await runner.session_service.create_session(
        app_name=app.name, user_id=user_id, session_id=session_id
    )

    prompt_content = types.Content.model_validate(scenario["prompt"])

    events = [
        {"author": "user", "content": prompt_content.model_dump(mode="json", exclude_none=True)}
    ]
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=prompt_content,
    ):
        if event.content is None:
            continue
        events.append(
            {
                "author": event.author,
                "content": event.content.model_dump(mode="json", exclude_none=True),
            }
        )

    final_response = _final_response_content(events)

    return {
        "eval_case_id": scenario["eval_case_id"],
        "responses": [{"response": final_response}] if final_response else [],
        "agent_data": {
            "agents": _collect_sub_agents(root_agent),
            "turns": [{"turn_index": 0, "events": events}],
        },
    }


async def main(dataset_path: Path, output_path: Path) -> None:
    dataset = json.loads(dataset_path.read_text())
    scenarios = dataset["eval_cases"]

    print(f"Running {len(scenarios)} scenario(s) through the local ADK runner...")
    traces = []
    for scenario in scenarios:
        print(f"  -> {scenario['eval_case_id']}")
        traces.append(await _run_scenario(scenario))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps({"eval_cases": traces}, indent=2))
    print(f"Wrote {len(traces)} trace(s) to {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path("tests/eval/datasets/scenarios.json"),
        help="Path to the inference-input eval dataset.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output trace file path. Defaults to a timestamped file under artifacts/traces/.",
    )
    args = parser.parse_args()

    out = args.output or Path(
        f"artifacts/traces/traces_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    )
    asyncio.run(main(args.dataset, out))
