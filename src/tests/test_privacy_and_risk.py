"""
Tests for privacy_control.py CRUD functions and risk_guidance.py.

Covers:
- Typical measures: list, add, update, delete
- Assessment questions: list, add, update, delete
- Statement, risk hint, risk scenarios
- Maturity level texts (valid levels + invalid level)
- DP goals: list, replace
- Risk impact scenarios: get, upsert (all levels), upsert with data_category,
  update, delete, delete nonexistent
"""

from __future__ import annotations

import pytest

from opengov_oscal_pycore.models import Control

# ── privacy_control CRUD imports ─────────────────────────────────────
from opengov_oscal_pyprivacy.domain.privacy_control import (
    list_typical_measures,
    add_typical_measure,
    update_typical_measure,
    delete_typical_measure,
    list_assessment_questions,
    add_assessment_question,
    update_assessment_question,
    delete_assessment_question,
    set_statement,
    extract_statement,
    set_risk_hint,
    extract_risk_hint,
    replace_risk_scenarios,
    extract_risk_scenarios,
    set_maturity_level_text,
    get_maturity_level_text,
    list_dp_goals,
    replace_dp_goals,
)

# ── risk_guidance imports ────────────────────────────────────────────
from opengov_oscal_pyprivacy.domain.risk_guidance import (
    get_risk_impact_scenarios,
    upsert_risk_impact_scenario,
    delete_risk_impact_scenario,
)


# =====================================================================
# Fixtures
# =====================================================================

@pytest.fixture
def control():
    """Fresh Control for each test."""
    return Control(id="TEST-01", title="Test Control")


# =====================================================================
# privacy_control.py — Typical Measures CRUD
# =====================================================================

class TestTypicalMeasures:

    def test_list_typical_measures_empty(self, control: Control):
        """A fresh control has no typical measures."""
        result = list_typical_measures(control)
        assert result == []

    def test_add_typical_measure(self, control: Control):
        """Adding a measure returns an id and the measure is listed afterwards."""
        new_id = add_typical_measure(control, "Encrypt data at rest")
        assert isinstance(new_id, str)
        assert new_id != ""

        items = list_typical_measures(control)
        assert len(items) == 1
        assert items[0]["id"] == new_id
        assert items[0]["prose"] == "Encrypt data at rest"

    def test_add_multiple_typical_measures(self, control: Control):
        """Three measures get sequentially numbered ids."""
        id1 = add_typical_measure(control, "First measure")
        id2 = add_typical_measure(control, "Second measure")
        id3 = add_typical_measure(control, "Third measure")

        # ids must be unique and sequential
        assert id1 != id2 != id3
        assert id1.endswith("001")
        assert id2.endswith("002")
        assert id3.endswith("003")

        items = list_typical_measures(control)
        assert len(items) == 3

    def test_update_typical_measure(self, control: Control):
        """Add, then update the prose text."""
        new_id = add_typical_measure(control, "Original text")
        update_typical_measure(control, new_id, "Updated text")

        items = list_typical_measures(control)
        assert len(items) == 1
        assert items[0]["id"] == new_id
        assert items[0]["prose"] == "Updated text"

    def test_delete_typical_measure(self, control: Control):
        """Add, then delete — list is empty again."""
        new_id = add_typical_measure(control, "To be deleted")
        assert len(list_typical_measures(control)) == 1

        delete_typical_measure(control, new_id)
        assert list_typical_measures(control) == []


# =====================================================================
# privacy_control.py — Assessment Questions CRUD
# =====================================================================

class TestAssessmentQuestions:

    def test_list_assessment_questions_empty(self, control: Control):
        """A fresh control has no assessment questions."""
        result = list_assessment_questions(control)
        assert result == []

    def test_add_assessment_question(self, control: Control):
        """Adding a question returns an id and the question is listed."""
        new_id = add_assessment_question(control, "Is encryption applied?")
        assert isinstance(new_id, str)
        assert new_id != ""

        items = list_assessment_questions(control)
        assert len(items) == 1
        assert items[0]["id"] == new_id
        assert items[0]["prose"] == "Is encryption applied?"

    def test_update_assessment_question(self, control: Control):
        """Add, then update the prose text."""
        new_id = add_assessment_question(control, "Original question")
        update_assessment_question(control, new_id, "Revised question")

        items = list_assessment_questions(control)
        assert len(items) == 1
        assert items[0]["prose"] == "Revised question"

    def test_delete_assessment_question(self, control: Control):
        """Add, then delete — list is empty again."""
        new_id = add_assessment_question(control, "To be removed")
        assert len(list_assessment_questions(control)) == 1

        delete_assessment_question(control, new_id)
        assert list_assessment_questions(control) == []


# =====================================================================
# privacy_control.py — Statement & Risk Hint
# =====================================================================

class TestStatementAndRiskHint:

    def test_set_statement(self, control: Control):
        """Setting a statement prose is retrievable via extract_statement."""
        set_statement(control, "The organization shall implement privacy measures.")
        result = extract_statement(control)
        assert result == "The organization shall implement privacy measures."

    def test_set_risk_hint(self, control: Control):
        """Setting a risk hint prose is retrievable via extract_risk_hint."""
        set_risk_hint(control, "High risk if personal data is exposed.")
        result = extract_risk_hint(control)
        assert result == "High risk if personal data is exposed."


# =====================================================================
# privacy_control.py — Risk Scenarios
# =====================================================================

class TestRiskScenarios:

    def test_replace_risk_scenarios(self, control: Control):
        """Replace with two scenarios, then read them back."""
        scenarios = [
            {"title": "Data breach", "description": "Unauthorized access to PII"},
            {"title": "Data loss", "description": "Permanent deletion of records"},
        ]
        replace_risk_scenarios(control, scenarios)

        result = extract_risk_scenarios(control)
        assert len(result) == 2
        assert result[0]["title"] is not None
        assert result[1]["description"] == "Permanent deletion of records"


# =====================================================================
# privacy_control.py — Maturity Level Texts
# =====================================================================

class TestMaturityLevelTexts:

    def test_set_maturity_level_text(self, control: Control):
        """Set level 1 text and verify via getter."""
        set_maturity_level_text(control, 1, "Basic privacy awareness training.")
        result = get_maturity_level_text(control, 1)
        assert result == "Basic privacy awareness training."

    def test_set_maturity_level_text_all_levels(self, control: Control):
        """Set texts for all valid levels (1, 3, 5)."""
        set_maturity_level_text(control, 1, "Level 1: Basic")
        set_maturity_level_text(control, 3, "Level 3: Managed")
        set_maturity_level_text(control, 5, "Level 5: Optimized")

        assert get_maturity_level_text(control, 1) == "Level 1: Basic"
        assert get_maturity_level_text(control, 3) == "Level 3: Managed"
        assert get_maturity_level_text(control, 5) == "Level 5: Optimized"

    def test_set_maturity_level_text_invalid(self, control: Control):
        """Level 2 is not valid and must raise ValueError."""
        with pytest.raises(ValueError, match="level must be one of 1, 3, 5"):
            set_maturity_level_text(control, 2, "Should fail")


# =====================================================================
# privacy_control.py — DP Goals
# =====================================================================

class TestDpGoals:

    def test_list_dp_goals_empty(self, control: Control):
        """A fresh control has no DP goals."""
        result = list_dp_goals(control)
        assert result == []

    def test_replace_dp_goals(self, control: Control):
        """Replace goals, then list them."""
        replace_dp_goals(control, ["transparency", "data-minimization", "integrity"])

        result = list_dp_goals(control)
        assert len(result) == 3
        assert "transparency" in result
        assert "data-minimization" in result
        assert "integrity" in result


# =====================================================================
# risk_guidance.py — Risk Impact Scenarios
# =====================================================================

class TestRiskImpactScenarios:

    def test_get_risk_impact_scenarios_empty(self, control: Control):
        """A fresh control has no risk impact scenarios."""
        result = get_risk_impact_scenarios(control)
        assert result == {}

    def test_upsert_risk_impact_scenario_normal(self, control: Control):
        """Add a 'normal' level scenario, then read it back."""
        scenario_id = upsert_risk_impact_scenario(
            control,
            "normal",
            prose="Low impact scenario for basic personal data.",
        )
        assert isinstance(scenario_id, str)
        assert scenario_id != ""

        scenarios = get_risk_impact_scenarios(control)
        assert "normal" in scenarios
        assert scenarios["normal"].level == "normal"
        assert scenarios["normal"].prose == "Low impact scenario for basic personal data."
        assert scenarios["normal"].id == scenario_id

    def test_upsert_risk_impact_scenario_all_levels(self, control: Control):
        """Add scenarios for all three levels (normal, moderate, high)."""
        id_normal = upsert_risk_impact_scenario(
            control, "normal", prose="Normal impact."
        )
        id_moderate = upsert_risk_impact_scenario(
            control, "moderate", prose="Moderate impact."
        )
        id_high = upsert_risk_impact_scenario(
            control, "high", prose="High impact."
        )

        scenarios = get_risk_impact_scenarios(control)
        assert len(scenarios) == 3
        assert scenarios["normal"].prose == "Normal impact."
        assert scenarios["moderate"].prose == "Moderate impact."
        assert scenarios["high"].prose == "High impact."

        # IDs must be distinct
        assert len({id_normal, id_moderate, id_high}) == 3

    def test_upsert_risk_impact_scenario_with_data_category(self, control: Control):
        """Add a scenario with a data_category_example."""
        upsert_risk_impact_scenario(
            control,
            "high",
            prose="Severe impact on special-category data.",
            data_category_example="Health records",
        )

        scenarios = get_risk_impact_scenarios(control)
        assert "high" in scenarios
        assert scenarios["high"].data_category_example == "Health records"

    def test_upsert_risk_impact_scenario_update(self, control: Control):
        """Add a scenario, then update its prose — the id stays the same."""
        original_id = upsert_risk_impact_scenario(
            control, "normal", prose="Original prose."
        )
        updated_id = upsert_risk_impact_scenario(
            control, "normal", prose="Updated prose."
        )

        # Same level means same part is reused
        assert updated_id == original_id

        scenarios = get_risk_impact_scenarios(control)
        assert scenarios["normal"].prose == "Updated prose."

    def test_delete_risk_impact_scenario(self, control: Control):
        """Add a scenario, then delete it."""
        upsert_risk_impact_scenario(
            control, "moderate", prose="Moderate impact scenario."
        )
        assert "moderate" in get_risk_impact_scenarios(control)

        delete_risk_impact_scenario(control, "moderate")
        assert "moderate" not in get_risk_impact_scenarios(control)

    def test_delete_risk_impact_scenario_nonexistent(self, control: Control):
        """Deleting a level that does not exist must not raise an error."""
        # Should silently do nothing
        delete_risk_impact_scenario(control, "high")
        assert get_risk_impact_scenarios(control) == {}
