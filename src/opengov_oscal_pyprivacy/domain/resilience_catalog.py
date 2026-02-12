from __future__ import annotations

"""
Resilience Catalog domain helpers.

Thin, stateless accessor functions for the three resilience-catalog
fields stored on a Control:

  - **domain**      -- Property ``name="domain"``
  - **objective**   -- Property ``name="objective"``
  - **description** -- Part ``name="description"`` (prose)

All functions are round-trip safe and delegate to the pycore CRUD layer.
"""

from typing import Optional

from opengov_oscal_pycore.models import Control, Property
from opengov_oscal_pycore.crud.parts import (
    parts_ref,
    ensure_part_container,
    find_part,
)
from opengov_oscal_pycore.crud.props import get_prop, upsert_prop


# ------------------------------------------------------------------
# Extract helpers
# ------------------------------------------------------------------

def extract_domain(control: Control) -> Optional[str]:
    """Return the *domain* property value, or ``None`` if absent."""
    prop = get_prop(control.props, "domain")
    return prop.value if prop is not None else None


def extract_objective(control: Control) -> Optional[str]:
    """Return the *objective* property value, or ``None`` if absent."""
    prop = get_prop(control.props, "objective")
    return prop.value if prop is not None else None


def extract_description(control: Control) -> Optional[str]:
    """Return the prose of the *description* part, or ``None`` if absent."""
    part = find_part(parts_ref(control), name="description")
    if part is None:
        return None
    # Transparent access: works for both Part models and dicts
    if isinstance(part, dict):
        return part.get("prose")
    return getattr(part, "prose", None)


# ------------------------------------------------------------------
# Set helpers
# ------------------------------------------------------------------

def set_domain(control: Control, domain: str) -> None:
    """Create or update the *domain* property on *control*."""
    upsert_prop(
        control.props,
        Property(name="domain", value=domain),
        key=("name",),
    )


def set_objective(control: Control, objective: str) -> None:
    """Create or update the *objective* property on *control*."""
    upsert_prop(
        control.props,
        Property(name="objective", value=objective),
        key=("name",),
    )


def set_description(control: Control, prose: str) -> None:
    """Create or update the *description* part prose on *control*."""
    ensure_part_container(control, "description", prose=prose)
