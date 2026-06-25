"""
Integration test for the Lawn Concierge agent.

Runs the agent end-to-end using ADK's InMemoryRunner.
Requires GEMINI_API_KEY or GOOGLE_CLOUD_PROJECT to be set.
"""

import os
import uuid

import pytest
from dotenv import load_dotenv

load_dotenv()


@pytest.mark.skipif(
    not (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_CLOUD_PROJECT")),
    reason="Requires GEMINI_API_KEY or GOOGLE_CLOUD_PROJECT",
)
class TestLawnConciergeAgent:
    @pytest.fixture(autouse=True)
    def setup(self):
        """Import agent and set up ADK runner."""
        from google.adk.runners import InMemoryRunner
        from app.agent import root_agent

        self.runner = InMemoryRunner(agent=root_agent)

    async def _ask(self, question: str) -> str:
        """Helper: run a single turn and return the final text response."""
        from google.genai import types

        user_id = "test_user"
        session_id = f"test_session_{uuid.uuid4().hex[:8]}"
        await self.runner.session_service.create_session(
            app_name=self.runner.app_name, user_id=user_id, session_id=session_id
        )

        final_text = ""
        async for event in self.runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=types.Content(role="user", parts=[types.Part(text=question)]),
        ):
            if event.content:
                for part in event.content.parts:
                    if getattr(part, "text", None):
                        final_text = part.text
        return final_text

    async def test_greeting(self):
        """Agent should introduce itself and ask for lawn details."""
        response = await self._ask("Hello, I need help with my lawn.")
        assert len(response) > 20
        # Should ask about grass type or location
        keywords = ["grass", "lawn", "help", "type", "location"]
        assert any(kw in response.lower() for kw in keywords)

    async def test_mowing_advice_routes_correctly(self):
        """Mowing question should produce height/frequency advice."""
        response = await self._ask(
            "I have Bermuda grass and want to know how often to mow it this summer."
        )
        # Should mention frequency and height
        assert any(kw in response.lower() for kw in ["day", "week", "inch", "height"])

    async def test_fertilizer_question(self):
        """Fertilizer question should return NPK and timing."""
        response = await self._ask(
            "What fertilizer should I use for my 2000 sq ft Fescue lawn?"
        )
        # Should mention NPK ratio or product type
        assert any(kw in response.lower() for kw in ["nitrogen", "npk", "16-4", "fertiliz"])

    async def test_pest_diagnosis_question(self):
        """Pest diagnosis should identify common issues."""
        response = await self._ask(
            "My St. Augustine lawn has yellow patches in sunny areas in July. "
            "The patches are spreading and the grass feels spongy. What's wrong?"
        )
        # Should mention chinch bugs or diagnosis
        assert any(kw in response.lower() for kw in ["chinch", "insect", "pest", "diagnos"])

    async def test_unknown_grass_type_asks_for_clarification(self):
        """If grass type is unknown, agent should ask the user."""
        response = await self._ask("How should I water my lawn?")
        # Should ask about grass type or location
        assert any(kw in response.lower() for kw in ["grass", "type", "location", "city", "what kind"])
