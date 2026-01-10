from __future__ import annotations

from typing import List, Optional

from opengov_oscal_pycore.models import Property, Part


def get_prop(
    props: Optional[List[Property]],
    name: str,
    cls: Optional[str] = None,
) -> Optional[Property]:
    """Sucht eine Property nach name (+ optional class)."""
    if not props:
        return None
    for p in props:
        if p.name == name and (cls is None or p.class_ == cls):
            return p
    return None


def set_prop(
    props: List[Property],
    name: str,
    value: str,
    cls: Optional[str] = None,
    ns: Optional[str] = None,
) -> Property:
    """
    Setzt eine Property (name/value) auf einem Objekt, legt sie an falls sie nicht existiert.
    """
    existing = get_prop(props, name, cls)
    if existing:
        existing.value = value
        if ns is not None:
            existing.ns = ns
        return existing

    new_prop = Property(
        name=name,
        value=value,
        class_=cls,
        ns=ns,
    )
    props.append(new_prop)
    return new_prop


def remove_prop(
    props: List[Property],
    name: str,
    cls: Optional[str] = None,
) -> None:
    """Entfernt alle Properties mit name (+ optional class)."""
    remaining: List[Property] = []
    for p in props:
        if not (p.name == name and (cls is None or p.class_ == cls)):
            remaining.append(p)
    props[:] = remaining


def find_part(parts: Optional[list[Part]], part_id: str) -> Optional[Part]:
    """Findet eine Part (rekursiv) anhand ihrer id."""
    if not parts:
        return None
    for part in parts:
        if part.id == part_id:
            return part
        result = find_part(part.parts, part_id)
        if result:
            return result
    return None
