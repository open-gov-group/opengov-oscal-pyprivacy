from __future__ import annotations

"""
SDM Catalog domain helpers.

Stateless functions that extract or mutate SDM-specific properties
and parts on a Control object.
"""

from typing import List, Optional

from opengov_oscal_pycore.models import Control, Property
from opengov_oscal_pycore.crud.props import find_props, get_prop, remove_props, upsert_prop
from opengov_oscal_pycore.crud.parts import parts_ref, ensure_part_container, find_part

from ..dto.mapping import MappingRef as RelatedMapping
from .. import catalog_keys as K


# ---------------------------------------------------------------------------
# Prop extraction
# ---------------------------------------------------------------------------

def extract_sdm_module(control: Control) -> Optional[str]:
    """Return the SDM building-block identifier, or *None*."""
    p = get_prop(control.props, K.SDM_BUILDING_BLOCK)
    return p.value if p else None


def extract_sdm_goals(control: Control) -> List[str]:
    """Return all assurance-goal values (tolerates legacy typo ``assurnace_goal``)."""
    names = {"assurance_goal", "assurnace_goal"}
    props = [
        p for p in control.props
        if p.name in names
        and p.class_ == K.CLASS_TELEOLOGICAL
        and getattr(p, "group", None) == K.GROUP_AIM
    ]
    return [p.value for p in props]


def extract_dsgvo_articles(control: Control) -> List[str]:
    """Return DSGVO article references (name=legal, group=reference, class=proof)."""
    props = find_props(
        control.props,
        name=K.LEGAL,
        group=K.GROUP_REFERENCE,
        class_=K.CLASS_PROOF,
    )
    return [p.value for p in props]


def extract_implementation_level(control: Control) -> Optional[str]:
    """Return the implementation-level value, or *None*."""
    p = get_prop(control.props, "implementation-level")
    return p.value if p else None


def extract_dp_risk_impact(control: Control) -> Optional[str]:
    """Return the data-protection risk-impact value, or *None*."""
    p = get_prop(control.props, "dp-risk-impact")
    return p.value if p else None


def extract_related_mappings(control: Control) -> List[RelatedMapping]:
    """Return all related-mapping props converted to RelatedMapping DTOs."""
    props = find_props(control.props, name="related-mapping")
    return [
        RelatedMapping(
            scheme=getattr(p, "group", None) or "",
            value=p.value,
            remarks=p.remarks,
        )
        for p in props
    ]


# ---------------------------------------------------------------------------
# Prop updates
# ---------------------------------------------------------------------------

def set_implementation_level(control: Control, level: str) -> None:
    """Set (upsert) the implementation-level property."""
    upsert_prop(
        control.props,
        Property(name="implementation-level", value=level),
        key=("name",),
    )


def set_dp_risk_impact(control: Control, impact: str) -> None:
    """Set (upsert) the dp-risk-impact property."""
    upsert_prop(
        control.props,
        Property(name="dp-risk-impact", value=impact),
        key=("name",),
    )


def replace_related_mappings(control: Control, mappings: List[RelatedMapping]) -> None:
    """Remove all existing related-mapping props and insert *mappings*."""
    remove_props(control.props, name="related-mapping")
    for m in mappings:
        upsert_prop(
            control.props,
            Property(
                name="related-mapping",
                value=m.value,
                group=m.scheme,
                remarks=m.remarks,
            ),
            key=("name", "group", "value"),
        )


# ---------------------------------------------------------------------------
# SDM-TOM parts (prose containers)
# ---------------------------------------------------------------------------

def extract_sdm_tom_description(control: Control) -> Optional[str]:
    """Return the prose of the ``description`` part, or *None*."""
    parts = parts_ref(control)
    p = find_part(parts, name="description")
    if p is None:
        return None
    return getattr(p, "prose", None) if not isinstance(p, dict) else p.get("prose")


def extract_sdm_tom_implementation_hints(control: Control) -> Optional[str]:
    """Return the prose of the ``implementation-hints`` part, or *None*."""
    parts = parts_ref(control)
    p = find_part(parts, name="implementation-hints")
    if p is None:
        return None
    return getattr(p, "prose", None) if not isinstance(p, dict) else p.get("prose")


def set_sdm_tom_description(control: Control, prose: str) -> None:
    """Create or update the ``description`` part with the given prose."""
    ensure_part_container(control, "description", prose=prose)


def set_sdm_tom_implementation_hints(control: Control, prose: str) -> None:
    """Create or update the ``implementation-hints`` part with the given prose."""
    ensure_part_container(control, "implementation-hints", prose=prose)
