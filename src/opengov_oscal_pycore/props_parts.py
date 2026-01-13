from __future__ import annotations

from typing import Optional
from .models import Property



def get_prop(props: list[Property] | None, name: str, cls: Optional[str] = None) -> Optional[Property]:
    """Sucht eine Property nach name (+ optional class)."""
    if not props:
        return None
    for p in props:
        if p.name == name and (cls is None or p.class_ == cls):
            return p
    return None

def set_prop(props: list[Property], name: str, value: str, cls: Optional[str] = None, ns: Optional[str] = None) -> Property:
    """
    Setzt eine Property (name/value) auf einem Objekt, legt sie an falls sie nicht existiert.
    """
    existing = get_prop(props, name, cls)
    if existing:
        existing.value = value
        if ns is not None:
            existing.ns = ns
        return existing

    p = Property(name=name, value=value, class_=cls, ns=ns)
    props.append(p)
    return p



def remove_prop(props: list[Property], name: str, cls: Optional[str] = None) -> None:
    """Entfernt alle Properties mit name (+ optional class)."""
    props[:] = [p for p in props if not (p.name == name and (cls is None or p.class_ == cls))]


