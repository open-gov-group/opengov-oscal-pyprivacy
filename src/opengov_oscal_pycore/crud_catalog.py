from __future__ import annotations

from typing import Optional, Iterator

from .models import Catalog, Group, Control
from .props_parts import set_prop, remove_prop


def iter_controls(cat: Catalog) -> Iterator[Control]:
    """Iteriert über alle Controls aller Gruppen."""
    for g in cat.groups:
        for c in g.controls:
            yield c


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
        remove_prop(control.props, prop_name, cls=cls)
    else:
        set_prop(control.props, prop_name, value, cls=cls)




