"""Genericode roundtrip tests: JSON -> Genericode XML -> JSON.

Issue #54: Verify that codelists survive the export/import cycle with
codes, labels, and identification preserved. The roundtrip is lossy --
metadata, groups, definitions, cascade_rules, etc. are NOT preserved.
"""

from __future__ import annotations

import pytest

from opengov_oscal_pyprivacy.codelist import (
    CodelistRegistry,
    export_genericode,
    import_genericode,
)
from opengov_oscal_pyprivacy.codelist.models import CodeEntry, CodeLabel, Codelist


@pytest.fixture(scope="module")
def registry() -> CodelistRegistry:
    return CodelistRegistry.load_defaults()


class TestGenericodeRoundtrip:
    """Test JSON -> Genericode XML -> JSON roundtrip."""

    def test_roundtrip_assurance_goals(self, registry: CodelistRegistry) -> None:
        """assurance-goals survives roundtrip."""
        original = registry.get_list("assurance-goals")
        xml = export_genericode(original, locale="de")
        reimported = import_genericode(xml)
        # list_id preserved
        assert reimported.list_id == original.list_id
        # version preserved
        assert reimported.version == original.version
        # same number of non-deprecated entries
        orig_active = [e for e in original.entries if not e.deprecated]
        assert len(reimported.entries) == len(orig_active)
        # codes match
        orig_codes = {e.xoev_code or e.code for e in orig_active}
        reimp_codes = {e.code for e in reimported.entries}
        assert reimp_codes == orig_codes

    def test_roundtrip_all_codelists(self, registry: CodelistRegistry) -> None:
        """All codelists survive roundtrip (codes + count)."""
        for list_id in registry.list_ids():
            cl = registry.get_list(list_id)
            xml = export_genericode(cl, locale="de")
            reimported = import_genericode(xml)
            active = [e for e in cl.entries if not e.deprecated]
            assert len(reimported.entries) == len(active), (
                f"{list_id}: entry count mismatch"
            )
            assert reimported.list_id == cl.list_id, (
                f"{list_id}: list_id mismatch"
            )

    def test_roundtrip_preserves_version(self, registry: CodelistRegistry) -> None:
        """Version string survives roundtrip."""
        cl = registry.get_list("data-categories")
        xml = export_genericode(cl)
        reimported = import_genericode(xml)
        assert reimported.version == cl.version

    def test_roundtrip_preserves_labels(self, registry: CodelistRegistry) -> None:
        """German labels survive roundtrip in the 'en' field of reimported entries."""
        cl = registry.get_list("protection-levels")
        xml = export_genericode(cl, locale="de")
        reimported = import_genericode(xml)
        # The reimported labels are in 'en' (the only field available from XML)
        for orig_entry in cl.entries:
            if orig_entry.deprecated:
                continue
            reimp_entry = next(
                (
                    e
                    for e in reimported.entries
                    if e.code == (orig_entry.xoev_code or orig_entry.code)
                ),
                None,
            )
            assert reimp_entry is not None, (
                f"Entry {orig_entry.code} not found in reimport"
            )
            orig_de = orig_entry.get_label("de")
            assert reimp_entry.labels.en == orig_de

    def test_roundtrip_skips_deprecated(self) -> None:
        """Deprecated entries are excluded from export and thus from reimport."""
        cl = Codelist(
            list_id="test-deprecated",
            version="1.0",
            namespace_uri="urn:test",
            title=CodeLabel(en="Test"),
            entries=[
                CodeEntry(code="active", labels=CodeLabel(en="Active")),
                CodeEntry(
                    code="old", labels=CodeLabel(en="Old"), deprecated=True
                ),
            ],
        )
        xml = export_genericode(cl)
        reimported = import_genericode(xml)
        assert len(reimported.entries) == 1
        assert reimported.entries[0].code == "active"

    def test_roundtrip_xoev_codes(self, registry: CodelistRegistry) -> None:
        """XOeV codes (xoev_code) are used as XML code values."""
        cl = registry.get_list("data-categories")
        xml = export_genericode(cl, locale="de")
        reimported = import_genericode(xml)
        # Check that xoev_code entries appear with their xoev_code as the code
        for entry in cl.entries:
            if entry.deprecated or not entry.xoev_code:
                continue
            matches = [e for e in reimported.entries if e.code == entry.xoev_code]
            assert len(matches) == 1, (
                f"xoev_code {entry.xoev_code} not found in reimport"
            )

    def test_roundtrip_en_locale(self, registry: CodelistRegistry) -> None:
        """Roundtrip with EN locale produces valid entries."""
        cl = registry.get_list("assurance-goals")
        xml = export_genericode(cl, locale="en")
        reimported = import_genericode(xml)
        assert len(reimported.entries) > 0
        # Verify English labels are in the reimported data
        for orig_entry in cl.entries:
            if orig_entry.deprecated:
                continue
            reimp_entry = next(
                (
                    e
                    for e in reimported.entries
                    if e.code == (orig_entry.xoev_code or orig_entry.code)
                ),
                None,
            )
            assert reimp_entry is not None
            orig_en = orig_entry.get_label("en")
            assert reimp_entry.labels.en == orig_en

    def test_import_namespace_uri(self, registry: CodelistRegistry) -> None:
        """CanonicalUri becomes namespace_uri."""
        cl = registry.get_list("measure-types")
        xml = export_genericode(cl)
        reimported = import_genericode(xml)
        assert "measure-types" in reimported.namespace_uri

    def test_import_custom_namespace(self) -> None:
        """Custom namespace_uri overrides CanonicalUri."""
        cl = Codelist(
            list_id="test",
            version="1.0",
            namespace_uri="urn:original",
            title=CodeLabel(en="Test"),
            entries=[CodeEntry(code="a", labels=CodeLabel(en="A"))],
        )
        xml = export_genericode(cl)
        reimported = import_genericode(xml, namespace_uri="urn:override")
        assert reimported.namespace_uri == "urn:override"

    def test_xml_is_valid_genericode(self, registry: CodelistRegistry) -> None:
        """Exported XML has correct Genericode structure."""
        cl = registry.get_list("protection-levels")
        xml = export_genericode(cl)
        assert "<?xml version" in xml
        assert "xmlns:gc=" in xml
        assert "gc:CodeList" in xml
        assert "gc:SimpleCodeList" in xml

    def test_roundtrip_empty_codelist(self) -> None:
        """Codelist with no entries roundtrips cleanly."""
        cl = Codelist(
            list_id="empty-list",
            version="0.1",
            namespace_uri="urn:empty",
            title=CodeLabel(en="Empty"),
            entries=[],
        )
        xml = export_genericode(cl)
        reimported = import_genericode(xml)
        assert reimported.list_id == "empty-list"
        assert reimported.version == "0.1"
        assert len(reimported.entries) == 0

    def test_roundtrip_all_codes_unique(self, registry: CodelistRegistry) -> None:
        """Each reimported codelist has unique codes (no duplicates)."""
        for list_id in registry.list_ids():
            cl = registry.get_list(list_id)
            xml = export_genericode(cl, locale="de")
            reimported = import_genericode(xml)
            codes = [e.code for e in reimported.entries]
            assert len(codes) == len(set(codes)), (
                f"{list_id}: duplicate codes in reimport"
            )
