"""
Tests for the Privacy Catalog Converter (#14).

Covers:
- control_to_privacy_summary (minimal and with group_id)
- control_to_privacy_detail (minimal, from fixture, with risk impacts)
- group_to_privacy_summary
- group_to_privacy_detail (with and without controls)
- PrivacyControlDetail serialization (model_dump)
- _to_risk_impact_dto conversion
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from opengov_oscal_pycore.models import Catalog, Control, Group

from opengov_oscal_pyprivacy.converters.privacy_converter import (
    control_to_privacy_summary,
    control_to_privacy_detail,
    group_to_privacy_summary,
    group_to_privacy_detail,
    _to_risk_impact_dto,
)
from opengov_oscal_pyprivacy.domain.risk_guidance import (
    RiskImpactScenario,
    upsert_risk_impact_scenario,
)
from opengov_oscal_pyprivacy.domain.privacy_control import (
    set_statement,
    set_risk_hint,
    replace_risk_scenarios,
    set_maturity_level_text,
    add_typical_measure,
    add_assessment_question,
)
from opengov_oscal_pyprivacy.dto.privacy_catalog import (
    PrivacyControlSummary,
    PrivacyControlDetail,
    PrivacyGroupSummary,
    PrivacyGroupDetail,
    PrivacyRiskImpactScenario,
)


# =====================================================================
# Fixtures
# =====================================================================

FIXTURE_FILE = Path(__file__).parent / "data" / "open_privacy_catalog_risk.json"


@pytest.fixture
def catalog() -> Catalog:
    """Load the full test catalog."""
    data = json.loads(FIXTURE_FILE.read_text(encoding="utf-8"))
    return Catalog.model_validate(data)


@pytest.fixture
def gov01(catalog: Catalog) -> Control:
    """GOV-01 from the fixture (has statement, maturity, measures, questions)."""
    return catalog.groups[0].controls[0]


@pytest.fixture
def tom01(catalog: Catalog) -> Control:
    """TOM-01 from the fixture (has risk impact scenarios)."""
    return catalog.groups[2].controls[0]


@pytest.fixture
def gov_group(catalog: Catalog) -> Group:
    """GOV group from the fixture."""
    return catalog.groups[0]


@pytest.fixture
def empty_control() -> Control:
    """A fresh, empty control."""
    return Control(id="EMPTY-01", title="Empty Control")


# =====================================================================
# 1. test_control_to_privacy_summary_minimal
# =====================================================================

def test_control_to_privacy_summary_minimal(empty_control: Control):
    """An empty control produces a summary with defaults."""
    result = control_to_privacy_summary(empty_control)

    assert isinstance(result, PrivacyControlSummary)
    assert result.id == "EMPTY-01"
    assert result.title == "Empty Control"
    assert result.group_id is None
    assert result.tom_id is None
    assert result.dsgvo_articles == []
    assert result.dp_goals == []


# =====================================================================
# 2. test_control_to_privacy_summary_with_group_id
# =====================================================================

def test_control_to_privacy_summary_with_group_id(gov01: Control):
    """group_id kwarg is passed through to the DTO."""
    result = control_to_privacy_summary(gov01, group_id="GOV")

    assert result.group_id == "GOV"
    assert result.id == "GOV-01"
    assert result.title != ""
    assert result.tom_id == "ORG-GOV-01"
    assert len(result.dsgvo_articles) > 0
    assert len(result.dp_goals) > 0


# =====================================================================
# 3. test_control_to_privacy_detail_minimal
# =====================================================================

def test_control_to_privacy_detail_minimal(empty_control: Control):
    """An empty control produces a detail DTO with all defaults."""
    result = control_to_privacy_detail(empty_control)

    assert isinstance(result, PrivacyControlDetail)
    assert result.id == "EMPTY-01"
    assert result.ctrl_class == ""
    assert result.title == "Empty Control"
    assert result.group_id is None
    assert result.tom_id is None
    assert result.dsgvo_articles == []
    assert result.dp_goals == []
    assert result.statement is None
    assert result.maturity_hints is None
    assert result.maturity_level_1 is None
    assert result.maturity_level_3 is None
    assert result.maturity_level_5 is None
    assert result.typical_measures == []
    assert result.assessment_questions == []
    assert result.risk_hint is None
    assert result.risk_scenarios == []
    assert result.risk_impact_normal is None
    assert result.risk_impact_moderate is None
    assert result.risk_impact_high is None


# =====================================================================
# 4. test_control_to_privacy_detail_from_fixture
# =====================================================================

def test_control_to_privacy_detail_from_fixture(gov01: Control):
    """GOV-01 from the fixture populates key detail fields."""
    result = control_to_privacy_detail(gov01, group_id="GOV")

    assert result.id == "GOV-01"
    assert result.ctrl_class == "management"
    assert result.group_id == "GOV"
    assert result.tom_id == "ORG-GOV-01"

    # Legal articles
    assert len(result.dsgvo_articles) >= 2

    # DP goals
    assert len(result.dp_goals) > 0

    # Statement
    assert result.statement is not None
    assert len(result.statement) > 0

    # Maturity
    assert result.maturity_hints is not None
    assert result.maturity_level_1 is not None
    assert result.maturity_level_3 is not None
    assert result.maturity_level_5 is not None

    # Typical measures
    assert len(result.typical_measures) >= 3
    assert all(m.id != "" for m in result.typical_measures)
    assert all(m.prose != "" for m in result.typical_measures)

    # Assessment questions
    assert len(result.assessment_questions) >= 2
    assert all(q.id != "" for q in result.assessment_questions)
    assert all(q.prose != "" for q in result.assessment_questions)


# =====================================================================
# 5. test_control_to_privacy_detail_with_risk_impacts
# =====================================================================

def test_control_to_privacy_detail_with_risk_impacts():
    """A control with upserted risk impacts converts correctly."""
    ctrl = Control(id="RISK-01", title="Risk Control", **{"class": "safeguard"})

    # Set up risk impacts
    upsert_risk_impact_scenario(ctrl, "normal", prose="Normal impact.")
    upsert_risk_impact_scenario(
        ctrl, "moderate",
        prose="Moderate impact.",
        data_category_example="Financial data",
    )
    upsert_risk_impact_scenario(ctrl, "high", prose="High impact.")

    # Also add some risk scenarios and statement
    set_statement(ctrl, "Test statement.")
    set_risk_hint(ctrl, "Consider the risk carefully.")
    replace_risk_scenarios(ctrl, [
        {"title": "Data breach", "description": "Unauthorized access"},
    ])
    set_maturity_level_text(ctrl, 1, "Level 1 text")
    set_maturity_level_text(ctrl, 3, "Level 3 text")
    add_typical_measure(ctrl, "Encrypt everything")
    add_assessment_question(ctrl, "Is encryption applied?")

    result = control_to_privacy_detail(ctrl)

    # Risk impacts
    assert result.risk_impact_normal is not None
    assert result.risk_impact_normal.level == "normal"
    assert result.risk_impact_normal.prose == "Normal impact."

    assert result.risk_impact_moderate is not None
    assert result.risk_impact_moderate.level == "moderate"
    assert result.risk_impact_moderate.prose == "Moderate impact."
    assert result.risk_impact_moderate.data_category_example == "Financial data"

    assert result.risk_impact_high is not None
    assert result.risk_impact_high.level == "high"
    assert result.risk_impact_high.prose == "High impact."

    # Other fields
    assert result.statement == "Test statement."
    assert result.risk_hint == "Consider the risk carefully."
    assert len(result.risk_scenarios) == 1
    assert result.risk_scenarios[0].title == "Data breach"
    assert result.risk_scenarios[0].description == "Unauthorized access"
    assert result.maturity_level_1 == "Level 1 text"
    assert result.maturity_level_3 == "Level 3 text"
    assert result.maturity_level_5 is None
    assert len(result.typical_measures) == 1
    assert len(result.assessment_questions) == 1


# =====================================================================
# 6. test_group_to_privacy_summary
# =====================================================================

def test_group_to_privacy_summary(gov_group: Group):
    """Basic group summary conversion."""
    result = group_to_privacy_summary(gov_group)

    assert isinstance(result, PrivacyGroupSummary)
    assert result.id == "GOV"
    assert result.class_ == "governance"
    assert result.title != ""


# =====================================================================
# 7. test_group_to_privacy_detail_with_controls
# =====================================================================

def test_group_to_privacy_detail_with_controls(gov_group: Group):
    """Group detail includes controls by default."""
    result = group_to_privacy_detail(gov_group)

    assert isinstance(result, PrivacyGroupDetail)
    assert result.id == "GOV"
    assert result.class_ == "governance"
    assert result.title != ""
    assert result.control_count == len(gov_group.controls)
    assert result.control_count > 0
    assert len(result.controls) == result.control_count

    # Each control should be a PrivacyControlSummary with group_id set
    for ctrl_summary in result.controls:
        assert isinstance(ctrl_summary, PrivacyControlSummary)
        assert ctrl_summary.group_id == "GOV"


# =====================================================================
# 8. test_group_to_privacy_detail_no_controls
# =====================================================================

def test_group_to_privacy_detail_no_controls(gov_group: Group):
    """include_controls=False produces an empty controls list but correct count."""
    result = group_to_privacy_detail(gov_group, include_controls=False)

    assert result.control_count == len(gov_group.controls)
    assert result.control_count > 0
    assert result.controls == []


# =====================================================================
# 9. test_privacy_detail_serialization
# =====================================================================

def test_privacy_detail_serialization(gov01: Control):
    """model_dump produces a dict with aliased keys."""
    detail = control_to_privacy_detail(gov01, group_id="GOV")
    data = detail.model_dump(by_alias=True)

    assert isinstance(data, dict)
    # Aliased fields
    assert "ctrlClass" in data
    assert data["ctrlClass"] == "management"
    # Standard fields
    assert "id" in data
    assert data["id"] == "GOV-01"
    assert "group_id" in data
    assert "typical_measures" in data
    assert isinstance(data["typical_measures"], list)


# =====================================================================
# 10. test_risk_impact_dto_conversion
# =====================================================================

class TestRiskImpactDtoConversion:

    def test_none_input(self):
        """None input returns None."""
        assert _to_risk_impact_dto(None) is None

    def test_normal_scenario(self):
        """A RiskImpactScenario is correctly converted."""
        scenario = RiskImpactScenario(
            id="test-risk-normal",
            level="normal",
            prose="Low risk.",
            data_category_example=None,
        )
        result = _to_risk_impact_dto(scenario)

        assert isinstance(result, PrivacyRiskImpactScenario)
        assert result.id == "test-risk-normal"
        assert result.level == "normal"
        assert result.prose == "Low risk."
        assert result.data_category_example is None

    def test_with_data_category(self):
        """data_category_example is passed through."""
        scenario = RiskImpactScenario(
            id="test-risk-high",
            level="high",
            prose="Severe risk.",
            data_category_example="Health records",
        )
        result = _to_risk_impact_dto(scenario)

        assert result is not None
        assert result.data_category_example == "Health records"
        assert result.level == "high"

    def test_from_fixture_tom01(self, tom01: Control):
        """Converter handles TOM-01 from fixture (may or may not have risk impacts)."""
        from opengov_oscal_pyprivacy.domain.risk_guidance import get_risk_impact_scenarios

        raw = get_risk_impact_scenarios(tom01)
        for level, scenario in raw.items():
            dto = _to_risk_impact_dto(scenario)
            assert dto is not None
            assert dto.id == scenario.id
            assert dto.level == scenario.level
            assert dto.prose == scenario.prose

    @pytest.fixture
    def tom01(self, catalog: Catalog) -> Control:
        return catalog.groups[2].controls[0]

    @pytest.fixture
    def catalog(self) -> Catalog:
        data = json.loads(FIXTURE_FILE.read_text(encoding="utf-8"))
        return Catalog.model_validate(data)
