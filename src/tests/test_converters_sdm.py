"""Tests for the SDM catalog converter (#15) and group-level converters (#52)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from opengov_oscal_pycore.models import Control, Group, Property

from opengov_oscal_pyprivacy.converters.sdm_converter import (
    control_to_sdm_summary,
    control_to_sdm_detail,
    group_to_sdm_summary,
    group_to_sdm_detail,
)
from opengov_oscal_pyprivacy.converters.resilience_converter import (
    group_to_resilience_summary,
    group_to_resilience_detail,
)
from opengov_oscal_pyprivacy.dto.sdm import (
    SdmControlSummary,
    SdmControlSummaryProps,
    SdmControlDetail,
    SdmControlDetailProps,
    SdmGroupSummary,
    SdmGroupDetail,
)
from opengov_oscal_pyprivacy.dto.resilience import (
    ResilienceGroupSummary,
    ResilienceGroupDetail,
    SecurityControl,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def empty_control() -> Control:
    """A Control with no properties at all."""
    return Control(id="EMPTY-01", title="Empty Control")


@pytest.fixture
def sdm_control() -> Control:
    """A Control with typical SDM properties."""
    return Control(
        id="SDM-42",
        title="Verschluesselung",
        **{"class": "SP"},
        props=[
            Property(name="sdm-building-block", value="Datenminimierung"),
            Property(
                name="assurnace_goal",
                value="Vertraulichkeit",
                group="aim_of_measure",
                **{"class": "teleological_interpretation"},
            ),
            Property(
                name="assurnace_goal",
                value="Integritaet",
                group="aim_of_measure",
                **{"class": "teleological_interpretation"},
            ),
            Property(
                name="legal",
                value="Art. 25 DSGVO",
                group="reference",
                **{"class": "proof"},
            ),
            Property(
                name="legal",
                value="Art. 32 DSGVO",
                group="reference",
                **{"class": "proof"},
            ),
            Property(name="implementation-level", value="full"),
            Property(name="dp-risk-impact", value="high"),
            Property(
                name="related-mapping",
                value="TOM-03",
                group="sdm",
                remarks="SDM mapping",
            ),
            Property(
                name="related-mapping",
                value="SYS.1.1",
                group="bsi_itgrundschutz",
                remarks=None,
            ),
        ],
    )


# ---------------------------------------------------------------------------
# Summary converter tests
# ---------------------------------------------------------------------------

class TestControlToSdmSummary:

    def test_control_to_sdm_summary_minimal(self, empty_control: Control):
        """Empty control produces a summary with correct defaults."""
        result = control_to_sdm_summary(empty_control)

        assert isinstance(result, SdmControlSummary)
        assert result.id == "EMPTY-01"
        assert result.title == "Empty Control"
        assert result.group_id is None
        assert isinstance(result.props, SdmControlSummaryProps)
        assert result.props.sdm_module is None
        assert result.props.sdm_goals == []
        assert result.props.dsgvo_articles == []

    def test_control_to_sdm_summary_with_data(self, sdm_control: Control):
        """Control with SDM properties produces a populated summary."""
        result = control_to_sdm_summary(sdm_control)

        assert result.id == "SDM-42"
        assert result.title == "Verschluesselung"
        assert result.props.sdm_module == "Datenminimierung"
        assert result.props.sdm_goals == ["Vertraulichkeit", "Integritaet"]
        assert result.props.dsgvo_articles == ["Art. 25 DSGVO", "Art. 32 DSGVO"]

    def test_control_to_sdm_summary_with_group_id(self, sdm_control: Control):
        """group_id keyword argument is passed through to the DTO."""
        result = control_to_sdm_summary(sdm_control, group_id="GRP-DATA")

        assert result.group_id == "GRP-DATA"


# ---------------------------------------------------------------------------
# Detail converter tests
# ---------------------------------------------------------------------------

class TestControlToSdmDetail:

    def test_control_to_sdm_detail_minimal(self, empty_control: Control):
        """Empty control produces a detail DTO with correct defaults."""
        result = control_to_sdm_detail(empty_control)

        assert isinstance(result, SdmControlDetail)
        assert result.id == "EMPTY-01"
        assert result.title == "Empty Control"
        assert result.class_ is None
        assert result.group_id is None
        assert isinstance(result.props, SdmControlDetailProps)
        assert result.props.sdm_module is None
        assert result.props.sdm_goals == []
        assert result.props.dsgvo_articles == []
        assert result.props.implementation_level is None
        assert result.props.dp_risk_impact is None
        assert result.props.related_mappings == []

    def test_control_to_sdm_detail_with_data(self, sdm_control: Control):
        """Control with all SDM properties produces a fully populated detail."""
        result = control_to_sdm_detail(sdm_control, group_id="GRP-SEC")

        assert result.id == "SDM-42"
        assert result.title == "Verschluesselung"
        assert result.class_ == "SP"
        assert result.group_id == "GRP-SEC"

        # Summary-level props
        assert result.props.sdm_module == "Datenminimierung"
        assert result.props.sdm_goals == ["Vertraulichkeit", "Integritaet"]
        assert result.props.dsgvo_articles == ["Art. 25 DSGVO", "Art. 32 DSGVO"]

        # Detail-only props
        assert result.props.implementation_level == "full"
        assert result.props.dp_risk_impact == "high"
        assert len(result.props.related_mappings) == 2
        assert result.props.related_mappings[0].scheme == "sdm"
        assert result.props.related_mappings[0].value == "TOM-03"
        assert result.props.related_mappings[0].remarks == "SDM mapping"
        assert result.props.related_mappings[1].scheme == "bsi_itgrundschutz"
        assert result.props.related_mappings[1].value == "SYS.1.1"


# ---------------------------------------------------------------------------
# Serialization test
# ---------------------------------------------------------------------------

class TestSdmSummarySerialization:

    def test_sdm_summary_serialization_by_alias(self, sdm_control: Control):
        """model_dump(by_alias=True) produces camelCase keys for aliased fields."""
        result = control_to_sdm_summary(sdm_control, group_id="GRP-01")
        data = result.model_dump(by_alias=True)

        # Top-level aliased field
        assert "groupId" in data
        assert data["groupId"] == "GRP-01"

        # Nested props aliased fields
        props = data["props"]
        assert "sdmModule" in props
        assert "sdmGoals" in props
        assert "dsgvoArticles" in props
        assert props["sdmModule"] == "Datenminimierung"
        assert props["sdmGoals"] == ["Vertraulichkeit", "Integritaet"]
        assert props["dsgvoArticles"] == ["Art. 25 DSGVO", "Art. 32 DSGVO"]


# ---------------------------------------------------------------------------
# Fixture: Group from test catalog
# ---------------------------------------------------------------------------

FIXTURE = Path(__file__).parent / "data" / "open_privacy_catalog_risk.json"


@pytest.fixture
def gov_group() -> Group:
    """Load the GOV group from the test fixture."""
    raw = json.loads(FIXTURE.read_text(encoding="utf-8"))
    catalog = raw.get("catalog", raw)
    grp_data = catalog["groups"][0]
    return Group(**grp_data)


@pytest.fixture
def empty_group() -> Group:
    """A Group with no controls."""
    return Group(id="EMPTY-GRP", title="Empty Group")


# ---------------------------------------------------------------------------
# SDM Group Summary tests (#52)
# ---------------------------------------------------------------------------

class TestGroupToSdmSummary:

    def test_group_to_sdm_summary_returns_correct_type(self, gov_group: Group):
        """group_to_sdm_summary returns an SdmGroupSummary instance."""
        result = group_to_sdm_summary(gov_group)
        assert isinstance(result, SdmGroupSummary)

    def test_group_to_sdm_summary_fields(self, gov_group: Group):
        """SdmGroupSummary has correct id, title, and control_count."""
        result = group_to_sdm_summary(gov_group)
        assert result.id == "GOV"
        assert result.title == "GOV \u2013 Governance & Organisation"
        assert result.control_count == 6

    def test_group_to_sdm_summary_empty_group(self, empty_group: Group):
        """Empty group produces a summary with control_count 0."""
        result = group_to_sdm_summary(empty_group)
        assert result.id == "EMPTY-GRP"
        assert result.title == "Empty Group"
        assert result.control_count == 0


# ---------------------------------------------------------------------------
# SDM Group Detail tests (#52)
# ---------------------------------------------------------------------------

class TestGroupToSdmDetail:

    def test_group_to_sdm_detail_returns_correct_type(self, gov_group: Group):
        """group_to_sdm_detail returns an SdmGroupDetail instance."""
        result = group_to_sdm_detail(gov_group)
        assert isinstance(result, SdmGroupDetail)

    def test_group_to_sdm_detail_controls_populated(self, gov_group: Group):
        """SdmGroupDetail.controls is populated with SdmControlDetail objects."""
        result = group_to_sdm_detail(gov_group)
        assert result.control_count == 6
        assert len(result.controls) == 6
        for ctrl in result.controls:
            assert isinstance(ctrl, SdmControlDetail)

    def test_group_to_sdm_detail_control_group_id(self, gov_group: Group):
        """Each control in the detail DTO has group_id set to the group's id."""
        result = group_to_sdm_detail(gov_group)
        for ctrl in result.controls:
            assert ctrl.group_id == "GOV"

    def test_group_to_sdm_detail_alias_serialization(self, gov_group: Group):
        """model_dump(by_alias=True) produces camelCase controlCount key."""
        result = group_to_sdm_detail(gov_group)
        data = result.model_dump(by_alias=True)
        assert "controlCount" in data
        assert data["controlCount"] == 6
        assert "controls" in data
        assert len(data["controls"]) == 6


# ---------------------------------------------------------------------------
# Resilience Group Converter tests (#52)
# ---------------------------------------------------------------------------

class TestGroupToResilienceSummary:

    def test_group_to_resilience_summary_returns_correct_type(self, gov_group: Group):
        """group_to_resilience_summary returns a ResilienceGroupSummary."""
        result = group_to_resilience_summary(gov_group)
        assert isinstance(result, ResilienceGroupSummary)

    def test_group_to_resilience_summary_fields(self, gov_group: Group):
        """ResilienceGroupSummary has correct id, title, control_count."""
        result = group_to_resilience_summary(gov_group)
        assert result.id == "GOV"
        assert result.title == "GOV \u2013 Governance & Organisation"
        assert result.control_count == 6


class TestGroupToResilienceDetail:

    def test_group_to_resilience_detail_returns_correct_type(self, gov_group: Group):
        """group_to_resilience_detail returns a ResilienceGroupDetail."""
        result = group_to_resilience_detail(gov_group)
        assert isinstance(result, ResilienceGroupDetail)

    def test_group_to_resilience_detail_controls_populated(self, gov_group: Group):
        """ResilienceGroupDetail.controls is populated with SecurityControl objects."""
        result = group_to_resilience_detail(gov_group)
        assert result.control_count == 6
        assert len(result.controls) == 6
        for ctrl in result.controls:
            assert isinstance(ctrl, SecurityControl)
