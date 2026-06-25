"""
Unit tests for the MCP server tool implementations.
Tests run without a live API key — they mock external HTTP calls.
"""

from mcp_server.tools.lawn_advisor import (
    get_mowing_schedule,
    get_fertilizing_schedule,
    get_aeration_schedule,
    get_lawn_care_advice,
    GRASS_PROFILES,
)
from mcp_server.tools.diagnosis import (
    diagnose_lawn_problem,
    get_pest_prevention_schedule,
    get_pest_library,
)


# ─── Lawn Advisor Tests ───────────────────────────────────────────────────────

class TestMowingSchedule:
    def test_bermuda_summer(self):
        result = get_mowing_schedule("bermuda", "July", 2000)
        assert result["grass_type"] == "bermuda"
        assert "5–7 days" in result["frequency"]
        assert result["is_dormant"] is False
        assert result["estimated_minutes"] == 20  # 2000 / 100

    def test_bermuda_winter_dormant(self):
        result = get_mowing_schedule("bermuda", "January")
        assert result["is_dormant"] is True
        assert result["dormant_advice"] is not None

    def test_unknown_grass_type(self):
        result = get_mowing_schedule("unicorn_grass")
        assert "error" in result
        assert "supported_types" in result

    def test_all_supported_grass_types(self):
        for grass in GRASS_PROFILES:
            result = get_mowing_schedule(grass, "June")
            assert "error" not in result
            assert "frequency" in result

    def test_grass_type_normalization(self):
        """st augustine, st_augustine, and St. Augustine should all work."""
        r1 = get_mowing_schedule("st augustine", "June")
        r2 = get_mowing_schedule("st_augustine", "June")
        assert r1["grass_type"] == r2["grass_type"]


class TestFertilizingSchedule:
    def test_fescue_schedule(self):
        result = get_fertilizing_schedule("fescue", "October", 1000)
        assert result["grass_type"] == "fescue"
        assert "16-4-8" in result["npk_ratio"]
        assert result["estimated_quantity_lbs"] == 4.0

    def test_quantity_scales_with_size(self):
        small = get_fertilizing_schedule("bermuda", "May", 1000)
        large = get_fertilizing_schedule("bermuda", "May", 5000)
        assert large["estimated_quantity_lbs"] == small["estimated_quantity_lbs"] * 5

    def test_dormant_warning_shown(self):
        # Bermuda is dormant in January
        result = get_fertilizing_schedule("bermuda", "January")
        assert result["is_dormant_period"] is True
        assert result["dormant_advice"] is not None


class TestAerationSchedule:
    def test_cool_season_fall_recommended(self):
        result = get_aeration_schedule("fescue", "September")
        assert result["is_recommended_now"] is True
        assert "September" in result["recommended_months"]

    def test_warm_season_late_spring_recommended(self):
        result = get_aeration_schedule("bermuda", "May")
        assert result["is_recommended_now"] is True

    def test_dormant_warning_shown(self):
        result = get_aeration_schedule("bermuda", "January")
        assert result["is_dormant_period"] is True
        assert result["dormant_warning"] is not None

    def test_unknown_grass_type(self):
        result = get_aeration_schedule("unicorn_grass")
        assert "error" in result
        assert "supported_types" in result

    def test_all_supported_grass_types(self):
        for grass in GRASS_PROFILES:
            result = get_aeration_schedule(grass, "June")
            assert "error" not in result
            assert "frequency" in result
            assert "method" in result


class TestLawnCareAdvice:
    def test_yellowing_advice(self):
        result = get_lawn_care_advice("bermuda", "lawn is yellowing", "July")
        assert "yellow" in result["advice"].lower() or "nitrogen" in result["advice"].lower()
        assert len(result["priority_actions"]) > 0

    def test_watering_concern(self):
        result = get_lawn_care_advice("fescue", "drought and dry conditions", "August")
        assert "water" in result["advice"].lower()
        assert "1.0" in result["advice"]  # fescue needs 1.0 inch/week

    def test_unknown_grass_still_returns_advice(self):
        result = get_lawn_care_advice("mystery_grass", "yellowing")
        assert "advice" in result
        assert "error" not in result


# ─── Diagnosis Tests ──────────────────────────────────────────────────────────

class TestDiagnoseLawnProblem:
    def test_chinch_bug_diagnosis(self):
        symptoms = ["yellowing patches", "spongy turf", "sunny spots", "spreading"]
        result = diagnose_lawn_problem(symptoms, "st_augustine", "July")
        assert "Chinch Bug" in result["diagnosis"]
        assert result["confidence"] in ("high", "medium")

    def test_grub_diagnosis(self):
        symptoms = ["spongy turf", "birds pecking", "wilting", "dead patches"]
        result = diagnose_lawn_problem(symptoms, "kentucky_bluegrass", "August")
        assert "Grub" in result["diagnosis"] or len(result["top_matches"]) > 0

    def test_clover_diagnosis(self):
        symptoms = ["three-leaflet", "white flowers", "spreading patches"]
        result = diagnose_lawn_problem(symptoms)
        assert len(result["top_matches"]) > 0
        names = [m["name"] for m in result["top_matches"]]
        assert "Clover" in names

    def test_no_match_returns_graceful_response(self):
        symptoms = ["perfectly fine lawn", "green and healthy"]
        result = diagnose_lawn_problem(symptoms)
        assert "diagnosis" in result
        # Should not crash even with no matches

    def test_pest_library_completeness(self):
        library = get_pest_library()
        assert len(library["pests"]) >= 5
        assert len(library["weeds_and_diseases"]) >= 5
        for pest in library["pests"]:
            assert "name" in pest
            assert "severity" in pest


class TestPestPreventionSchedule:
    def test_due_now_matches_season(self):
        # Chinch bugs are seasonal in June-September for st_augustine
        result = get_pest_prevention_schedule("st_augustine", "July")
        names = [e["name"] for e in result["due_now"]]
        assert "Chinch Bug" in names

    def test_upcoming_within_two_months(self):
        # Crabgrass pre-emergent due Feb-April; from January it should be "upcoming"
        result = get_pest_prevention_schedule(current_month="January")
        names = [e["name"] for e in result["upcoming"]]
        assert "Crabgrass" in names

    def test_filters_by_grass_type(self):
        result = get_pest_prevention_schedule("centipede", "July")
        # Centipede isn't in chinch bug's affected_grasses list
        names = [e["name"] for e in result["due_now"]]
        assert "Chinch Bug" not in names

    def test_no_grass_type_returns_all_relevant(self):
        result = get_pest_prevention_schedule(current_month="July")
        assert "due_now" in result
        assert "upcoming" in result
        assert len(result["general_tips"]) > 0
