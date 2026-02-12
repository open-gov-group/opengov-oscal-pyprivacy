from __future__ import annotations

from typing import Optional, Iterator

from .models import Catalog, Group, Control, Property
from .crud.props import upsert_prop, remove_props


def iter_controls(cat: Catalog) -> Iterator[Control]:
    """Iteriert über alle Controls aller Gruppen."""
    for g in cat.groups:
        for c in g.controls:
            yield c


def iter_controls_with_group(cat: Catalog) -> Iterator[tuple[Control, Group]]:
    """Yield (control, parent_group) pairs for all controls in top-level groups."""
    for g in cat.groups:
        for c in g.controls:
            yield c, g


def find_controls_by_prop(
    cat: Catalog,
    *,
    prop_name: str,
    prop_value: Optional[str] = None,
    prop_class: Optional[str] = None,
) -> list[Control]:
    """Find all controls having a property matching the given criteria."""
    results = []
    for c in iter_controls(cat):
        for p in c.props:
            if p.name != prop_name:
                continue
            if prop_value is not None and p.value != prop_value:
                continue
            if prop_class is not None and p.class_ != prop_class:
                continue
            results.append(c)
            break
    return results


def find_group(cat: Catalog, group_id: str) -> Optional[Group]:
    for g in cat.groups:
        if g.id == group_id:
            return g
    return None


def find_control(cat: Catalog, control_id: str) -> Optional[Control]:
    for c in iter_controls(cat):
        if c.id == control_id:
            return c
    return None


def add_control(cat: Catalog, group_id: str, control: Control) -> None:
    """
    Fügt eine bestehende Control-Instanz einer Gruppe hinzu.
    ID-Strategie ist Sache des Callers (Domain-Layer).
    """
    group = find_group(cat, group_id)
    if not group:
        raise ValueError(f"Group {group_id} not found in catalog")
    group.controls.append(control)


def delete_control(cat: Catalog, control_id: str) -> bool:
    """
    Löscht eine Control nach id, gibt True zurück wenn etwas gelöscht wurde.
    """
    changed = False
    for g in cat.groups:
        before = len(g.controls)
        g.controls = [c for c in g.controls if c.id != control_id]
        if len(g.controls) != before:
            changed = True
    return changed


def set_control_prop(cat: Catalog, control_id: str, prop_name: str, value: Optional[str], cls: Optional[str] = None) -> None:
    """
    Setzt oder entfernt eine Property auf einer Control.
    value=None => Property wird entfernt.
    """
    control = find_control(cat, control_id)
    if not control:
        raise ValueError(f"Control {control_id} not found in catalog")

    if value is None:
        remove_props(control.props, name=prop_name, class_=cls)
    else:
        upsert_prop(
            control.props,
            Property(name=prop_name, value=value, **({"class": cls} if cls else {})),
            key=("name", "class_"),
        )




