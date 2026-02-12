"""
Tests for the domain modules:

- sdm_catalog      (#3)
- resilience_catalog (#4)
- privacy_control extract helpers (#7)
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from opengov_oscal_pycore.models import Catalog, Control, Property, Part


# ── SDM Catalog imports ──────────────────────────────────────────────
from opengov_oscal_pyprivacy.domain.sdm_catalog import (
    extract_sdm_module,
    extract_sdm_goals,
    extract_dsgvo_articles,
    extract_implementation_level,
    set_implementation_level,
    extract_dp_risk_impact,
    set_dp_risk_impact,
    extract_related_mappings,
    replace_related_mappings,
    extract_sdm_tom_description,
    set_sdm_tom_description,
    extract_sdm_tom_implementation_hints,
    set_sdm_tom_implementation_hints,
)
from opengov_oscal_pyprivacy.dto.mapping import MappingRef as RelatedMapping

# ── Resilience Catalog imports ───────────────────────────────────────
from opengov_oscal_pyprivacy.domain.resilience_catalog import (
    extract_domain,
    set_domain,
    extract_objective,
    set_objective,
    extract_description,
    set_description,
)

# ── Privacy Control extract imports ──────────────────────────────────
from opengov_oscal_pyprivacy.domain.privacy_control import (
    extract_legal_articles,
    extract_tom_id,
    extract_statement,
    extract_risk_hint,
    extract_risk_scenarios,
    extract_maturity_level_texts,
)


# =====================================================================
# Fixtures
# =====================================================================

@pytest.fixture
def sdm_control():
    """A Control with typical SDM properties for unit testing."""
    return Control(
        id="SDM-01",
        title="Test",
        props=[
            Property(name="sdm-building-block", value="ORG-GOV-01"),
            Property(
                name="assurnace_goal",
                value="transparency",
                ns="de",
                group="aim_of_measure",
                **{"class": "teleological_interpretation"},
            ),
            Property(
                name="legal",
                value="EU:REG:GDPR:ART-5",
                ns="de",
                group="reference",
                **{"class": "proof"},
            ),
        ],
    )


@pytest.fixture
def catalog_control():
    """Load GOV-01 from the test fixture open_privacy_catalog_risk.json."""
    fixture = Path(__file__).parent / "data" / "open_privacy_catalog_risk.json"
    data = json.loads(fixture.read_text(encoding="utf-8"))
    cat = Catalog.model_validate(data)
    return cat.groups[0].controls[0]  # GOV-01


# =====================================================================
# SDM Catalog tests (#3)
# =====================================================================

class TestSdmCatalog:

    def test_extract_sdm_module(self, sdm_control: Control):
        result = extract_sdm_module(sdm_control)
        assert result == "ORG-GOV-01"

    def test_extract_sdm_goals(self, sdm_control: Control):
        goals = extract_sdm_goals(sdm_control)
        assert isinstance(goals, list)
        assert "transparency" in goals

    def test_extract_dsgvo_articles(self, sdm_control: Control):
        articles = extract_dsgvo_articles(sdm_control)
        assert isinstance(articles, list)
        assert "EU:REG:GDPR:ART-5" in articles

    def test_extract_implementation_level_none(self, sdm_control: Control):
        """No implementation-level prop present -> None."""
        result = extract_implementation_level(sdm_control)
        assert result is None

    def test_set_implementation_level(self, sdm_control: Control):
        set_implementation_level(sdm_control, "full")
        result = extract_implementation_level(sdm_control)
        assert result == "full"

    def test_set_dp_risk_impact(self, sdm_control: Control):
        assert extract_dp_risk_impact(sdm_control) is None
        set_dp_risk_impact(sdm_control, "high")
        result = extract_dp_risk_impact(sdm_control)
        assert result == "high"

    def test_replace_related_mappings(self, sdm_control: Control):
        # Initially empty
        assert extract_related_mappings(sdm_control) == []

        mappings = [
            RelatedMapping(scheme="sdm", value="TOM-03", remarks="test remark"),
            RelatedMapping(scheme="bsi_itgrundschutz", value="SYS.1.1", remarks=None),
        ]
        replace_related_mappings(sdm_control, mappings)

        result = extract_related_mappings(sdm_control)
        assert len(result) == 2
        assert result[0].scheme == "sdm"
        assert result[0].value == "TOM-03"
        assert result[1].scheme == "bsi_itgrundschutz"
        assert result[1].value == "SYS.1.1"

    def test_extract_sdm_tom_description_none(self, sdm_control: Control):
        """No description part present -> None."""
        result = extract_sdm_tom_description(sdm_control)
        assert result is None

    def test_set_and_extract_sdm_tom_description(self, sdm_control: Control):
        prose_text = "Beschreibung der TOM-Massnahme."
        set_sdm_tom_description(sdm_control, prose_text)
        result = extract_sdm_tom_description(sdm_control)
        assert result == prose_text

    def test_set_and_extract_sdm_tom_implementation_hints(self, sdm_control: Control):
        prose_text = "Hinweise zur Umsetzung der Massnahme."
        set_sdm_tom_implementation_hints(sdm_control, prose_text)
        result = extract_sdm_tom_implementation_hints(sdm_control)
        assert result == prose_text


# =====================================================================
# Resilience Catalog tests (#4)
# =====================================================================

class TestResilienceCatalog:

    def test_extract_domain_none(self):
        """Control without domain prop -> None."""
        control = Control(id="RES-01", title="Empty", props=[])
        result = extract_domain(control)
        assert result is None

    def test_set_and_extract_domain(self):
        control = Control(id="RES-01", title="Test", props=[])
        set_domain(control, "physical-security")
        result = extract_domain(control)
        assert result == "physical-security"

    def test_set_and_extract_objective(self):
        control = Control(id="RES-02", title="Test", props=[])
        set_objective(control, "Ensure continuous availability")
        result = extract_objective(control)
        assert result == "Ensure continuous availability"

    def test_set_and_extract_description(self):
        control = Control(id="RES-03", title="Test", props=[])
        assert extract_description(control) is None
        set_description(control, "Resilience measure prose text.")
        result = extract_description(control)
        assert result == "Resilience measure prose text."


# =====================================================================
# Privacy Control extract tests (#7)
# =====================================================================

class TestPrivacyControlExtract:

    def test_extract_legal_articles(self, catalog_control: Control):
        articles = extract_legal_articles(catalog_control)
        assert isinstance(articles, list)
        assert len(articles) > 0, "GOV-01 should have legal props"

    def test_extract_tom_id(self, catalog_control: Control):
        tom_id = extract_tom_id(catalog_control)
        assert tom_id is not None
        assert tom_id == "ORG-GOV-01"

    def test_extract_statement(self, catalog_control: Control):
        stmt = extract_statement(catalog_control)
        assert stmt is not None
        assert isinstance(stmt, str)
        assert len(stmt) > 0

    def test_extract_risk_hint(self, catalog_control: Control):
        """GOV-01 has no risk-hint part -> None is acceptable."""
        hint = extract_risk_hint(catalog_control)
        assert hint is None

    def test_extract_risk_scenarios(self, catalog_control: Control):
        """GOV-01 has no risk-scenarios -> empty list."""
        scenarios = extract_risk_scenarios(catalog_control)
        assert isinstance(scenarios, list)
        assert scenarios == []

    def test_extract_maturity_level_texts(self, catalog_control: Control):
        texts = extract_maturity_level_texts(catalog_control)
        assert isinstance(texts, dict)
        # GOV-01 has maturity-hints with levels 1, 3, 5
        for level in (1, 3, 5):
            assert level in texts, f"Level {level} missing from maturity texts"
            assert texts[level] is not None, f"Level {level} text should not be None"
            assert isinstance(texts[level], str)
            assert len(texts[level]) > 0, f"Level {level} text should not be empty"
