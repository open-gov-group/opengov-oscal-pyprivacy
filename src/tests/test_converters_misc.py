"""
Tests for SDM-TOM and Resilience converters (#16).
"""

from __future__ import annotations

import pytest

from opengov_oscal_pycore.models import Control, Property, Part

from opengov_oscal_pyprivacy.converters.sdm_tom_converter import (
    control_to_sdm_tom_summary,
    control_to_sdm_tom_detail,
)
from opengov_oscal_pyprivacy.converters.resilience_converter import (
    control_to_security_control,
)


# =====================================================================
# SDM-TOM Converter Tests
# =====================================================================


class TestSdmTomSummaryConverter:

    def test_control_to_sdm_tom_summary_minimal(self):
        """A bare control yields a summary with empty/None defaults."""
        control = Control(id="TOM-00", title="Bare")
        result = control_to_sdm_tom_summary(control)

        assert result.id == "TOM-00"
        assert result.title == "Bare"
        assert result.sdm_module is None
        assert result.sdm_goals == []
        assert result.dsgvo_articles == []

    def test_control_to_sdm_tom_summary_with_data(self):
        """Control with SDM props populates summary fields correctly."""
        control = Control(
            id="TOM-01",
            title="TOM Test",
            props=[
                Property(name="sdm-building-block", value="ORG-GOV-01"),
                Property(
                    name="assurnace_goal",
                    value="transparency",
                    group="aim_of_measure",
                    **{"class": "teleological_interpretation"},
                ),
                Property(
                    name="assurance_goal",
                    value="data_minimisation",
                    group="aim_of_measure",
                    **{"class": "teleological_interpretation"},
                ),
                Property(
                    name="legal",
                    value="EU:REG:GDPR:ART-5",
                    group="reference",
                    **{"class": "proof"},
                ),
                Property(
                    name="legal",
                    value="EU:REG:GDPR:ART-25",
                    group="reference",
                    **{"class": "proof"},
                ),
            ],
        )
        result = control_to_sdm_tom_summary(control)

        assert result.id == "TOM-01"
        assert result.title == "TOM Test"
        assert result.sdm_module == "ORG-GOV-01"
        assert "transparency" in result.sdm_goals
        assert "data_minimisation" in result.sdm_goals
        assert len(result.sdm_goals) == 2
        assert "EU:REG:GDPR:ART-5" in result.dsgvo_articles
        assert "EU:REG:GDPR:ART-25" in result.dsgvo_articles
        assert len(result.dsgvo_articles) == 2


class TestSdmTomDetailConverter:

    def test_control_to_sdm_tom_detail_minimal(self):
        """A bare control yields a detail DTO with None description/hints."""
        control = Control(id="TOM-00", title="Bare")
        result = control_to_sdm_tom_detail(control)

        assert result.id == "TOM-00"
        assert result.title == "Bare"
        assert result.sdm_module is None
        assert result.sdm_goals == []
        assert result.dsgvo_articles == []
        assert result.description is None
        assert result.implementation_hints is None

    def test_control_to_sdm_tom_detail_with_data(self):
        """Control with description and implementation-hints parts."""
        control = Control(
            id="TOM-02",
            title="TOM Detail",
            props=[
                Property(name="sdm-building-block", value="TECH-SEC-03"),
                Property(
                    name="assurnace_goal",
                    value="integrity",
                    group="aim_of_measure",
                    **{"class": "teleological_interpretation"},
                ),
                Property(
                    name="legal",
                    value="EU:REG:GDPR:ART-32",
                    group="reference",
                    **{"class": "proof"},
                ),
            ],
            parts=[
                Part(
                    name="description",
                    prose="Implement encryption for data at rest.",
                ),
                Part(
                    name="implementation-hints",
                    prose="Use AES-256; rotate keys annually.",
                ),
            ],
        )
        result = control_to_sdm_tom_detail(control)

        assert result.id == "TOM-02"
        assert result.title == "TOM Detail"
        assert result.sdm_module == "TECH-SEC-03"
        assert result.sdm_goals == ["integrity"]
        assert result.dsgvo_articles == ["EU:REG:GDPR:ART-32"]
        assert result.description == "Implement encryption for data at rest."
        assert result.implementation_hints == "Use AES-256; rotate keys annually."


# =====================================================================
# Resilience Converter Tests
# =====================================================================


class TestResilienceConverter:

    def test_control_to_security_control_minimal(self):
        """A bare control yields a SecurityControl with None optional fields."""
        control = Control(id="RES-00", title="Bare")
        result = control_to_security_control(control)

        assert result.id == "RES-00"
        assert result.title == "Bare"
        assert result.class_ is None
        assert result.domain is None
        assert result.objective is None
        assert result.description is None

    def test_control_to_security_control_with_data(self):
        """Control with domain/objective props and description part."""
        control = Control(
            id="RES-01",
            title="Physical Security",
            props=[
                Property(name="domain", value="physical-security"),
                Property(name="objective", value="Ensure continuous availability"),
            ],
            parts=[
                Part(
                    name="description",
                    prose="Protect physical infrastructure against threats.",
                ),
            ],
            **{"class": "resilience"},
        )
        result = control_to_security_control(control)

        assert result.id == "RES-01"
        assert result.title == "Physical Security"
        assert result.class_ == "resilience"
        assert result.domain == "physical-security"
        assert result.objective == "Ensure continuous availability"
        assert result.description == "Protect physical infrastructure against threats."
