from __future__ import annotations

from typing import List, Optional
from xml.etree.ElementTree import Element, fromstring

from ..models import CodeEntry, CodeLabel, Codelist

GC_NS = "http://docs.oasis-open.org/codelist/ns/genericode/1.0/"


def _find(element: Element, tag: str) -> Optional[Element]:
    """Find a child element with Genericode namespace."""
    return element.find(f"{{{GC_NS}}}{tag}")


def _findall(element: Element, tag: str) -> List[Element]:
    """Find all child elements with Genericode namespace."""
    return element.findall(f"{{{GC_NS}}}{tag}")


def _find_text(element: Element, tag: str) -> str:
    """Get text content of a child element, empty string if not found."""
    child = _find(element, tag)
    return (child.text or "") if child is not None else ""


def import_genericode(xml_str: str, *, namespace_uri: str = "") -> Codelist:
    """Import a Genericode 1.0 XML string into a Codelist model.

    Note: This is a lossy import. Genericode only stores code + name,
    so metadata like groups, definitions, cascade_rules, etc. are lost.
    The imported Codelist will have minimal CodeEntry objects.

    Args:
        xml_str: Genericode 1.0 XML string to parse.
        namespace_uri: Override the namespace_uri (default: use CanonicalUri
            from the XML).

    Returns:
        A Codelist with entries reconstructed from the XML rows.
    """
    root = fromstring(xml_str)

    # Extract identification
    ident = _find(root, "Identification")
    list_id = _find_text(ident, "ShortName") if ident is not None else ""
    version = _find_text(ident, "Version") if ident is not None else "1.0"
    canonical_uri = _find_text(ident, "CanonicalUri") if ident is not None else ""

    ns_uri = namespace_uri or canonical_uri

    # Determine column order from ColumnSet (currently informational)
    column_set = _find(root, "ColumnSet")
    column_ids: List[str] = []
    if column_set is not None:
        for col in _findall(column_set, "Column"):
            col_id = col.get("Id", "")
            column_ids.append(col_id)

    # Parse rows from SimpleCodeList
    entries: List[CodeEntry] = []
    simple_list = _find(root, "SimpleCodeList")
    if simple_list is not None:
        for row in _findall(simple_list, "Row"):
            code_value = ""
            name_value = ""
            for value_elem in _findall(row, "Value"):
                col_ref = value_elem.get("ColumnRef", "")
                sv = _find(value_elem, "SimpleValue")
                text = (sv.text or "") if sv is not None else ""
                if col_ref == "code":
                    code_value = text
                elif col_ref == "name":
                    name_value = text

            if code_value:
                # The exported XML uses xoev_code (if present) as the code,
                # but on import we don't know the original code, so we use
                # the XML code as-is. The name goes into the 'en' label
                # field (the only field available from a single-locale XML).
                entry = CodeEntry(
                    code=code_value,
                    labels=CodeLabel(en=name_value or code_value),
                )
                entries.append(entry)

    title_label = CodeLabel(en=list_id)

    return Codelist(
        list_id=list_id,
        version=version,
        namespace_uri=ns_uri,
        title=title_label,
        entries=entries,
    )
