"""Tests for the CascadeService — cascading compliance engine."""

from __future__ import annotations

import pytest

from opengov_oscal_pyprivacy.codelist.cascade import CascadeImpact, CascadeService
from opengov_oscal_pyprivacy.codelist.registry import CodelistRegistry


@pytest.fixture(scope="module")
def registry() -> CodelistRegistry:
    return CodelistRegistry.load_defaults()


@pytest.fixture(scope="module")
def cascade(registry: CodelistRegistry) -> CascadeService:
    return CascadeService.load_defaults(registry)


# ------------------------------------------------------------------
# TestCascadeServiceLoad
# ------------------------------------------------------------------


class TestCascadeServiceLoad:
    """Loading and initialization tests."""

    def test_load_defaults(self, registry: CodelistRegistry) -> None:
        """load_defaults() returns a CascadeService without error."""
        svc = CascadeService.load_defaults(registry)
        assert isinstance(svc, CascadeService)

    def test_has_rules(self, cascade: CascadeService) -> None:
        """Loaded service contains cascade rules."""
        assert len(cascade._rules) > 0


# ------------------------------------------------------------------
# TestEvaluateImpact
# ------------------------------------------------------------------


class TestEvaluateImpact:
    """Tests for evaluate_impact()."""

    def test_health_data_impacts(self, cascade: CascadeService) -> None:
        """Health data (special category) triggers 3+ impacts."""
        impacts = cascade.evaluate_impact("health-data")
        assert len(impacts) >= 3

    def test_health_data_has_protection_impact(
        self, cascade: CascadeService
    ) -> None:
        """At least one impact targets protection-levels."""
        impacts = cascade.evaluate_impact("health-data")
        protection_impacts = [
            i for i in impacts if i.target_list == "protection-levels"
        ]
        assert len(protection_impacts) >= 1

    def test_health_data_has_dpia_impact(
        self, cascade: CascadeService
    ) -> None:
        """At least one impact targets dpia with required_value 'true'."""
        impacts = cascade.evaluate_impact("health-data")
        dpia_impacts = [
            i
            for i in impacts
            if i.target_list == "dpia" and i.required_value == "true"
        ]
        assert len(dpia_impacts) >= 1

    def test_criminal_data_impacts(self, cascade: CascadeService) -> None:
        """Criminal data triggers 2+ impacts."""
        impacts = cascade.evaluate_impact("criminal-data")
        assert len(impacts) >= 2

    def test_criminal_data_requires_national_law(
        self, cascade: CascadeService
    ) -> None:
        """Criminal data triggers legal-instruments impact with national-law."""
        impacts = cascade.evaluate_impact("criminal-data")
        law_impacts = [
            i
            for i in impacts
            if i.target_list == "legal-instruments"
            and i.required_value == "national-law"
        ]
        assert len(law_impacts) >= 1

    def test_general_data_no_special_impacts(
        self, cascade: CascadeService
    ) -> None:
        """Contact data (general group) triggers no special-category impacts."""
        impacts = cascade.evaluate_impact("contact-data")
        special_impacts = [
            i
            for i in impacts
            if i.rule_id
            in (
                "special-category-requires-enhanced",
                "health-data-enhanced-crypto",
                "criminal-data-requires-national-law",
            )
        ]
        assert len(special_impacts) == 0

    def test_unknown_category_empty(self, cascade: CascadeService) -> None:
        """Unknown category returns empty impact list."""
        impacts = cascade.evaluate_impact("nonexistent")
        assert impacts == []


# ------------------------------------------------------------------
# TestSuggestChanges
# ------------------------------------------------------------------


class TestSuggestChanges:
    """Tests for suggest_changes()."""

    def test_contact_to_health(self, cascade: CascadeService) -> None:
        """Upgrading from contact-data to health-data suggests 3+ changes."""
        changes = cascade.suggest_changes("contact-data", "health-data")
        assert len(changes) >= 3

    def test_same_category_no_changes(self, cascade: CascadeService) -> None:
        """Same category suggests no changes."""
        changes = cascade.suggest_changes("health-data", "health-data")
        assert changes == []

    def test_health_to_contact_no_new(self, cascade: CascadeService) -> None:
        """Downgrade from health-data to contact-data suggests no new impacts."""
        changes = cascade.suggest_changes("health-data", "contact-data")
        assert changes == []


# ------------------------------------------------------------------
# TestViolationDetection
# ------------------------------------------------------------------


class TestViolationDetection:
    """Tests for violation detection logic."""

    def test_violation_when_level_too_low(
        self, cascade: CascadeService
    ) -> None:
        """Baseline level for special category data is a violation."""
        impacts = cascade.evaluate_impact(
            "health-data", current_protection_level="baseline"
        )
        violations = [
            i
            for i in impacts
            if i.target_list == "protection-levels" and i.is_violation
        ]
        assert len(violations) >= 1

    def test_no_violation_when_level_sufficient(
        self, cascade: CascadeService
    ) -> None:
        """Enhanced level for special category data is not a violation."""
        impacts = cascade.evaluate_impact(
            "health-data", current_protection_level="enhanced"
        )
        protection_violations = [
            i
            for i in impacts
            if i.target_list == "protection-levels" and i.is_violation
        ]
        assert len(protection_violations) == 0


# ------------------------------------------------------------------
# TestTransferRules
# ------------------------------------------------------------------


class TestTransferRules:
    """Tests for recipient/transfer cascade rules."""

    def test_third_country_recipient(self, cascade: CascadeService) -> None:
        """Third-country recipient triggers transfer instrument impact."""
        impacts = cascade.evaluate_impact(
            "contact-data", current_recipients=["third-country"]
        )
        transfer_impacts = [
            i
            for i in impacts
            if i.target_list == "legal-instruments"
            and i.required_value == "scc"
        ]
        assert len(transfer_impacts) >= 1
