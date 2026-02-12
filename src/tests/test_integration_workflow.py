"""Integration workflow tests: Load -> Convert -> Modify -> Re-Convert -> Verify (#19)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from opengov_oscal_pycore.models import Catalog, Control
from opengov_oscal_pycore.repo import OscalRepository

FIXTURE_FILE = Path(__file__).parent / "data" / "open_privacy_catalog_risk.json"


@pytest.fixture
def catalog() -> Catalog:
    data = json.loads(FIXTURE_FILE.read_text(encoding="utf-8"))
    return Catalog.model_validate(data)


class TestPrivacyWorkflow:
    """Simulate PrivacyCatalogService end-to-end operations."""

    def test_load_and_list_groups(self, catalog: Catalog):
        from opengov_oscal_pyprivacy.converters import group_to_privacy_detail

        for group in catalog.groups:
            detail = group_to_privacy_detail(group)
            assert detail.id == group.id
            assert detail.control_count == len(group.controls)

    def test_load_and_convert_control(self, catalog: Catalog):
        from opengov_oscal_pyprivacy.converters import control_to_privacy_detail

        control = catalog.groups[0].controls[0]
        detail = control_to_privacy_detail(control, group_id=catalog.groups[0].id)
        assert detail.id == control.id
        assert detail.group_id == catalog.groups[0].id

    def test_modify_statement_then_reconvert(self, catalog: Catalog):
        from opengov_oscal_pyprivacy.converters import control_to_privacy_detail
        from opengov_oscal_pyprivacy.domain.privacy_control import set_statement

        control = catalog.groups[0].controls[0]

        # Convert initially
        detail1 = control_to_privacy_detail(control)
        assert detail1.id == control.id

        # Modify
        set_statement(control, "Neues Statement")

        # Re-convert -- verify the change is reflected
        detail2 = control_to_privacy_detail(control)
        assert detail2.statement == "Neues Statement"

    def test_add_measure_reflected_in_detail(self, catalog: Catalog):
        from opengov_oscal_pyprivacy.converters import control_to_privacy_detail
        from opengov_oscal_pyprivacy.domain.privacy_control import add_typical_measure

        control = catalog.groups[0].controls[0]

        before = control_to_privacy_detail(control)
        count_before = len(before.typical_measures)

        add_typical_measure(control, "Neue Massnahme")

        after = control_to_privacy_detail(control)
        assert len(after.typical_measures) == count_before + 1
        assert any(m.prose == "Neue Massnahme" for m in after.typical_measures)


class TestSdmWorkflow:
    """Simulate SdmCatalogService operations."""

    def test_convert_sdm_controls(self, catalog: Catalog):
        from opengov_oscal_pyprivacy.converters import control_to_sdm_detail

        control = catalog.groups[0].controls[0]
        detail = control_to_sdm_detail(control, group_id=catalog.groups[0].id)
        assert detail.id == control.id

    def test_set_implementation_level_reflected(self, catalog: Catalog):
        from opengov_oscal_pyprivacy.converters import control_to_sdm_detail
        from opengov_oscal_pyprivacy.domain.sdm_catalog import set_implementation_level

        control = catalog.groups[0].controls[0]
        set_implementation_level(control, "full")

        detail = control_to_sdm_detail(control)
        assert detail.props.implementation_level == "full"


class TestResilienceWorkflow:
    """Simulate ResilienceCatalogService operations."""

    def test_convert_and_update(self, catalog: Catalog):
        from opengov_oscal_pyprivacy.converters import control_to_security_control
        from opengov_oscal_pyprivacy.domain.resilience_catalog import set_domain, set_objective

        control = catalog.groups[0].controls[0]

        set_domain(control, "Netzwerk")
        set_objective(control, "Schutz der Integritaet")

        sc = control_to_security_control(control)
        assert sc.domain == "Netzwerk"
        assert sc.objective == "Schutz der Integritaet"


class TestRoundtripSafety:
    """Verify modifications don't break OSCAL round-trip."""

    def test_modify_save_reload_preserves_extra(self, catalog: Catalog, tmp_path: Path):
        from opengov_oscal_pyprivacy.domain.privacy_control import set_statement, extract_statement

        repo = OscalRepository(tmp_path)

        # Modify a control
        control = catalog.groups[0].controls[0]
        set_statement(control, "Modified statement")

        # Save and reload
        repo.save("test.json", catalog)
        reloaded = repo.load("test.json", Catalog)

        # Verify modification survived
        ctrl = reloaded.groups[0].controls[0]
        assert extract_statement(ctrl) == "Modified statement"

        # Verify metadata survived (extra fields)
        assert reloaded.metadata.get("title") is not None
