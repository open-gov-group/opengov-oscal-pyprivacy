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
    """Find a group by ID, searching recursively in nested groups."""
    def _search(groups: list[Group]) -> Optional[Group]:
        for g in groups:
            if g.id == group_id:
                return g
            found = _search(g.groups)
            if found:
                return found
        return None
    return _search(cat.groups)


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


# ---------------------------------------------------------------------------
# Group CRUD operations (Issue #23)
# ---------------------------------------------------------------------------

def add_group(cat: Catalog, group: Group) -> None:
    """Add a group to the catalog's top-level groups. Raises ValueError if ID already exists."""
    if find_group(cat, group.id) is not None:
        raise ValueError(f"Group {group.id!r} already exists in catalog")
    cat.groups.append(group)


def delete_group(cat: Catalog, group_id: str) -> bool:
    """Delete a top-level group by ID. Returns True if a group was removed."""
    before = len(cat.groups)
    cat.groups = [g for g in cat.groups if g.id != group_id]
    return len(cat.groups) < before


def update_group_title(cat: Catalog, group_id: str, title: str) -> None:
    """Update the title of a group. Raises ValueError if not found."""
    group = find_group(cat, group_id)
    if group is None:
        raise ValueError(f"Group {group_id!r} not found in catalog")
    group.title = title


def move_control(cat: Catalog, control_id: str, target_group_id: str) -> bool:
    """Move a control from its current group to the target group.
    Returns True if the control was moved, False if not found.
    Raises ValueError if target group not found.
    """
    target = find_group(cat, target_group_id)
    if target is None:
        raise ValueError(f"Target group {target_group_id!r} not found in catalog")

    # Find and remove from source group
    control = None
    for g in cat.groups:
        for c in g.controls:
            if c.id == control_id:
                control = c
                g.controls.remove(c)
                break
        if control:
            break

    if control is None:
        return False

    target.controls.append(control)
    return True


