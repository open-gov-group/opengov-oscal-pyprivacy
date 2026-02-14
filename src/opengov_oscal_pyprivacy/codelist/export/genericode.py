from __future__ import annotations

import io
from pathlib import Path
from xml.etree.ElementTree import Element, ElementTree, SubElement, indent

from ..models import Codelist

GC_NS = "http://docs.oasis-open.org/codelist/ns/genericode/1.0/"


def export_genericode(
    codelist: Codelist,
    *,
    locale: str = "de",
    urn_prefix: str = "urn:xoev-de:llm-cai:codeliste",
) -> str:
    """Export a Codelist to OASIS Genericode 1.0 XML string.

    Args:
        codelist: The codelist to export
        locale: Language for display labels (default: "de" for XÖV compat)
        urn_prefix: URN prefix for CanonicalUri
    """
    root = Element("gc:CodeList")
    root.set("xmlns:gc", GC_NS)

    # Identification
    ident = SubElement(root, "gc:Identification")
    short_name = SubElement(ident, "gc:ShortName")
    short_name.text = codelist.list_id

    canonical_uri = SubElement(ident, "gc:CanonicalUri")
    canonical_uri.text = f"{urn_prefix}:{codelist.list_id}"

    version = SubElement(ident, "gc:Version")
    version.text = codelist.version

    # ColumnSet
    column_set = SubElement(root, "gc:ColumnSet")

    # Code column
    col_code = SubElement(column_set, "gc:Column")
    col_code.set("Id", "code")
    col_code.set("Use", "required")
    col_code_short = SubElement(col_code, "gc:ShortName")
    col_code_short.text = "Code"
    col_code_data = SubElement(col_code, "gc:Data")
    col_code_data.set("Type", "string")

    # Name column
    col_name = SubElement(column_set, "gc:Column")
    col_name.set("Id", "name")
    col_name.set("Use", "required")
    col_name_short = SubElement(col_name, "gc:ShortName")
    col_name_short.text = "Name"
    col_name_data = SubElement(col_name, "gc:Data")
    col_name_data.set("Type", "string")

    # Key
    key_elem = SubElement(column_set, "gc:Key")
    key_elem.set("Id", "codeKey")
    key_col_ref = SubElement(key_elem, "gc:ColumnRef")
    key_col_ref.set("Ref", "code")

    # SimpleCodeList
    simple_list = SubElement(root, "gc:SimpleCodeList")
    for entry in codelist.entries:
        if entry.deprecated:
            continue
        row = SubElement(simple_list, "gc:Row")

        # Code value
        val_code = SubElement(row, "gc:Value")
        val_code.set("ColumnRef", "code")
        sv_code = SubElement(val_code, "gc:SimpleValue")
        sv_code.text = entry.xoev_code if entry.xoev_code else entry.code

        # Name value (localized)
        val_name = SubElement(row, "gc:Value")
        val_name.set("ColumnRef", "name")
        sv_name = SubElement(val_name, "gc:SimpleValue")
        sv_name.text = entry.get_label(locale)

    indent(root, space="  ")

    stream = io.BytesIO()
    tree = ElementTree(root)
    tree.write(stream, encoding="utf-8", xml_declaration=True)
    return stream.getvalue().decode("utf-8")


def export_genericode_to_file(
    codelist: Codelist,
    output_path: Path,
    **kwargs,
) -> None:
    """Export a Codelist to a Genericode 1.0 XML file."""
    xml_str = export_genericode(codelist, **kwargs)
    output_path.write_text(xml_str, encoding="utf-8")
