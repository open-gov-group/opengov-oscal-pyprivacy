from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from opengov_oscal_pyprivacy.codelist.models import Codelist, CodeEntry, CodeLabel
from opengov_oscal_pyprivacy.codelist.export.genericode import (
    GC_NS,
    export_genericode,
    export_genericode_to_file,
)


@pytest.fixture
def sample_codelist() -> Codelist:
    return Codelist(
        list_id="test-list",
        version="1.0.0",
        namespace_uri="urn:test:test-list",
        title=CodeLabel(en="Test List", de="Testliste"),
        entries=[
            CodeEntry(
                code="active",
                labels=CodeLabel(en="Active", de="Aktiv"),
                xoev_code="aktiv",
            ),
            CodeEntry(
                code="inactive",
                labels=CodeLabel(en="Inactive", de="Inaktiv"),
                xoev_code="inaktiv",
            ),
            CodeEntry(
                code="deprecated-item",
                labels=CodeLabel(en="Old", de="Alt"),
                deprecated=True,
            ),
        ],
    )


class TestGenericodeExport:
    """Tests for OASIS Genericode 1.0 XML export."""

    def test_export_returns_xml_string(self, sample_codelist: Codelist) -> None:
        result = export_genericode(sample_codelist)
        assert isinstance(result, str)
        assert result.startswith("<?xml")

    def test_export_contains_list_id(self, sample_codelist: Codelist) -> None:
        result = export_genericode(sample_codelist)
        root = ET.fromstring(result)
        ns = {"gc": GC_NS}
        short_name = root.find(".//gc:Identification/gc:ShortName", ns)
        assert short_name is not None
        assert short_name.text == "test-list"

    def test_export_contains_version(self, sample_codelist: Codelist) -> None:
        result = export_genericode(sample_codelist)
        root = ET.fromstring(result)
        ns = {"gc": GC_NS}
        version = root.find(".//gc:Identification/gc:Version", ns)
        assert version is not None
        assert version.text == "1.0.0"

    def test_export_contains_rows(self, sample_codelist: Codelist) -> None:
        result = export_genericode(sample_codelist)
        root = ET.fromstring(result)
        ns = {"gc": GC_NS}
        rows = root.findall(".//gc:SimpleCodeList/gc:Row", ns)
        # 2 non-deprecated entries
        assert len(rows) == 2

    def test_export_uses_xoev_code(self, sample_codelist: Codelist) -> None:
        result = export_genericode(sample_codelist)
        root = ET.fromstring(result)
        ns = {"gc": GC_NS}
        rows = root.findall(".//gc:SimpleCodeList/gc:Row", ns)
        first_code_val = rows[0].find(
            "gc:Value[@ColumnRef='code']/gc:SimpleValue", ns
        )
        assert first_code_val is not None
        assert first_code_val.text == "aktiv"

    def test_export_locale_de(self, sample_codelist: Codelist) -> None:
        result = export_genericode(sample_codelist, locale="de")
        root = ET.fromstring(result)
        ns = {"gc": GC_NS}
        rows = root.findall(".//gc:SimpleCodeList/gc:Row", ns)
        first_name_val = rows[0].find(
            "gc:Value[@ColumnRef='name']/gc:SimpleValue", ns
        )
        assert first_name_val is not None
        assert first_name_val.text == "Aktiv"

    def test_export_locale_en(self, sample_codelist: Codelist) -> None:
        result = export_genericode(sample_codelist, locale="en")
        root = ET.fromstring(result)
        ns = {"gc": GC_NS}
        rows = root.findall(".//gc:SimpleCodeList/gc:Row", ns)
        first_name_val = rows[0].find(
            "gc:Value[@ColumnRef='name']/gc:SimpleValue", ns
        )
        assert first_name_val is not None
        assert first_name_val.text == "Active"

    def test_export_skips_deprecated(self, sample_codelist: Codelist) -> None:
        result = export_genericode(sample_codelist)
        # "deprecated-item" / "Old" / "Alt" should not appear
        assert "deprecated-item" not in result
        assert ">Old<" not in result
        assert ">Alt<" not in result

    def test_export_to_file(
        self, sample_codelist: Codelist, tmp_path: Path
    ) -> None:
        out = tmp_path / "test.gc.xml"
        export_genericode_to_file(sample_codelist, out)
        assert out.exists()
        content = out.read_text(encoding="utf-8")
        assert content.startswith("<?xml")
        assert "gc:CodeList" in content

    def test_export_parseable_xml(self, sample_codelist: Codelist) -> None:
        result = export_genericode(sample_codelist)
        # Should not raise
        root = ET.fromstring(result)
        # ET expands prefixes to Clark notation {namespace}localname
        assert root.tag == f"{{{GC_NS}}}CodeList"
