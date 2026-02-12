"""
Tests for the ROPA Converter (#28).

Covers:
- control_to_ropa_summary (minimal, from fixture, with group_id)
- control_to_ropa_detail (minimal, from fixture, serialization)
- group_to_ropa_summary
- group_to_ropa_detail (with and without controls)
- All REG controls convert without error
- Inheritance and alias verification
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from opengov_oscal_pycore.models import Catalog, Control, Group

from opengov_oscal_pyprivacy.converters.ropa_converter import (
    control_to_ropa_summary,
    control_to_ropa_detail,
    group_to_ropa_summary,
    group_to_ropa_detail,
)
from opengov_oscal_pyprivacy.dto.ropa import (
    RopaControlSummary,
    RopaControlDetail,
    RopaGroupSummary,
    RopaGroupDetail,
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
def reg_group(catalog: Catalog) -> Group:
    """REG group from the fixture (groups[4], class=records-of-processing)."""
    return catalog.groups[4]


@pytest.fixture
def reg01(catalog: Catalog) -> Control:
    """REG-01 from the fixture."""
    return catalog.groups[4].controls[0]


@pytest.fixture
def empty_control() -> Control:
    """A fresh, empty control."""
    return Control(id="EMPTY-01", title="Empty Control")


# =====================================================================
# 1. test_control_to_ropa_summary_minimal
# =====================================================================

def test_control_to_ropa_summary_minimal(empty_control: Control):
    """An empty control produces a summary with defaults."""
    result = control_to_ropa_summary(empty_control)

    assert isinstance(result, RopaControlSummary)
    assert result.id == "EMPTY-01"
    assert result.title == "Empty Control"
    assert result.group_id is None
    assert result.legal_articles == []
    assert result.evidence_artifacts == []
    assert result.maturity_domain is None
    assert result.maturity_requirement is None


# =====================================================================
# 2. test_control_to_ropa_summary_from_fixture
# =====================================================================

def test_control_to_ropa_summary_from_fixture(reg01: Control):
    """REG-01 from the fixture has legal_articles, evidence_artifacts, maturity_domain, maturity_requirement."""
    result = control_to_ropa_summary(reg01)

    assert result.id == "REG-01"
    assert result.title != ""
    assert len(result.legal_articles) > 0
    assert len(result.evidence_artifacts) > 0
    assert result.maturity_domain is not None
    assert result.maturity_requirement is not None
    assert isinstance(result.maturity_requirement, int)


# =====================================================================
# 3. test_control_to_ropa_summary_with_group_id
# =====================================================================

def test_control_to_ropa_summary_with_group_id(reg01: Control):
    """group_id kwarg is passed through to the DTO."""
    result = control_to_ropa_summary(reg01, group_id="REG")

    assert result.group_id == "REG"
    assert result.id == "REG-01"


# =====================================================================
# 4. test_control_to_ropa_detail_minimal
# =====================================================================

def test_control_to_ropa_detail_minimal(empty_control: Control):
    """An empty control produces a detail DTO with all defaults."""
    result = control_to_ropa_detail(empty_control)

    assert isinstance(result, RopaControlDetail)
    assert result.id == "EMPTY-01"
    assert result.ctrl_class == ""
    assert result.title == "Empty Control"
    assert result.group_id is None
    assert result.legal_articles == []
    assert result.evidence_artifacts == []
    assert result.maturity_domain is None
    assert result.maturity_requirement is None
    assert result.dp_goals == []
    assert result.statement is None
    assert result.maturity_hints is None
    assert result.maturity_level_1 is None
    assert result.maturity_level_3 is None
    assert result.maturity_level_5 is None
    assert result.typical_measures == []
    assert result.assessment_questions == []
    assert result.measure_category is None


# =====================================================================
# 5. test_control_to_ropa_detail_from_fixture
# =====================================================================

def test_control_to_ropa_detail_from_fixture(reg01: Control):
    """REG-01 from the fixture populates key detail fields."""
    result = control_to_ropa_detail(reg01, group_id="REG")

    assert result.id == "REG-01"
    assert result.ctrl_class == "record"
    assert result.group_id == "REG"

    # Legal articles
    assert len(result.legal_articles) > 0

    # Evidence artifacts
    assert len(result.evidence_artifacts) > 0

    # Maturity domain and requirement
    assert result.maturity_domain is not None
    assert result.maturity_requirement is not None

    # DP goals
    assert len(result.dp_goals) > 0

    # Statement
    assert result.statement is not None
    assert len(result.statement) > 0

    # Maturity hints prose
    assert result.maturity_hints is not None

    # Typical measures
    assert len(result.typical_measures) >= 1
    assert all(m.id != "" for m in result.typical_measures)
    assert all(m.prose != "" for m in result.typical_measures)

    # Measure category
    assert result.measure_category is not None


# =====================================================================
# 6. test_control_to_ropa_detail_serialization
# =====================================================================

def test_control_to_ropa_detail_serialization(reg01: Control):
    """model_dump(by_alias=True) produces a dict with correct aliased keys."""
    detail = control_to_ropa_detail(reg01, group_id="REG")
    data = detail.model_dump(by_alias=True)

    assert isinstance(data, dict)
    # Aliased fields
    assert "ctrlClass" in data
    assert data["ctrlClass"] == "record"
    assert "groupId" in data
    assert data["groupId"] == "REG"
    assert "dsgvoArticles" in data
    assert "evidenceArtifacts" in data
    assert "maturityDomain" in data
    assert "maturityRequirement" in data
    assert "dpGoals" in data
    assert "maturityHints" in data
    assert "maturityLevel1" in data
    assert "maturityLevel3" in data
    assert "maturityLevel5" in data
    assert "typicalMeasures" in data
    assert "assessmentQuestions" in data
    assert "measureCategory" in data
    # Standard fields
    assert "id" in data
    assert data["id"] == "REG-01"


# =====================================================================
# 7. test_group_to_ropa_summary
# =====================================================================

def test_group_to_ropa_summary(reg_group: Group):
    """Basic group summary conversion with correct control count."""
    result = group_to_ropa_summary(reg_group)

    assert isinstance(result, RopaGroupSummary)
    assert result.id == "REG"
    assert result.title != ""
    assert result.control_count == 5


# =====================================================================
# 8. test_group_to_ropa_detail_with_controls
# =====================================================================

def test_group_to_ropa_detail_with_controls(reg_group: Group):
    """Group detail includes controls by default."""
    result = group_to_ropa_detail(reg_group)

    assert isinstance(result, RopaGroupDetail)
    assert result.id == "REG"
    assert result.title != ""
    assert result.control_count == 5
    assert len(result.controls) == 5

    # Each control should be a RopaControlSummary with group_id set
    for ctrl_summary in result.controls:
        assert isinstance(ctrl_summary, RopaControlSummary)
        assert ctrl_summary.group_id == "REG"


# =====================================================================
# 9. test_group_to_ropa_detail_no_controls
# =====================================================================

def test_group_to_ropa_detail_no_controls(reg_group: Group):
    """include_controls=False produces an empty controls list but correct count."""
    result = group_to_ropa_detail(reg_group, include_controls=False)

    assert result.control_count == 5
    assert result.controls == []


# =====================================================================
# 10. test_all_reg_controls_convert
# =====================================================================

def test_all_reg_controls_convert(reg_group: Group):
    """All 5 REG controls convert to both summary and detail without error."""
    assert len(reg_group.controls) == 5
    for ctrl in reg_group.controls:
        summary = control_to_ropa_summary(ctrl, group_id="REG")
        assert isinstance(summary, RopaControlSummary)
        assert summary.id.startswith("REG-")

        detail = control_to_ropa_detail(ctrl, group_id="REG")
        assert isinstance(detail, RopaControlDetail)
        assert detail.id.startswith("REG-")


# =====================================================================
# 11. test_ropa_detail_inherits_summary_fields
# =====================================================================

def test_ropa_detail_inherits_summary_fields(reg01: Control):
    """RopaControlDetail inherits summary fields like evidence_artifacts."""
    detail = control_to_ropa_detail(reg01)

    # evidence_artifacts is defined on RopaControlSummary and inherited by RopaControlDetail
    assert hasattr(detail, "evidence_artifacts")
    assert len(detail.evidence_artifacts) > 0

    # legal_articles is also inherited
    assert hasattr(detail, "legal_articles")
    assert len(detail.legal_articles) > 0

    # maturity_domain and maturity_requirement are inherited
    assert hasattr(detail, "maturity_domain")
    assert detail.maturity_domain is not None
    assert hasattr(detail, "maturity_requirement")
    assert detail.maturity_requirement is not None

    # Verify it is an instance of both
    assert isinstance(detail, RopaControlSummary)
    assert isinstance(detail, RopaControlDetail)


# =====================================================================
# 12. test_ropa_summary_camel_case_aliases
# =====================================================================

def test_ropa_summary_camel_case_aliases(reg01: Control):
    """Verify alias field names in model_dump(by_alias=True) for RopaControlSummary."""
    summary = control_to_ropa_summary(reg01, group_id="REG")
    data = summary.model_dump(by_alias=True)

    # All aliased fields should use camelCase
    assert "groupId" in data
    assert "dsgvoArticles" in data
    assert "evidenceArtifacts" in data
    assert "maturityDomain" in data
    assert "maturityRequirement" in data

    # Python field names should NOT appear
    assert "group_id" not in data
    assert "legal_articles" not in data
    assert "evidence_artifacts" not in data
    assert "maturity_domain" not in data
    assert "maturity_requirement" not in data
