from __future__ import annotations

import csv
from dataclasses import dataclass
from importlib.resources import files
from typing import Any, Dict, Optional, Tuple, Literal

from opengov_oscal_pycore.models import Control, Property
from opengov_oscal_pycore.crud.parts import (
    parts_ref, ensure_part_container, _get, _set,
)
from opengov_oscal_pycore.crud.props import find_props, remove_props

ImpactLevel = Literal["normal", "moderate", "high"]


@dataclass(frozen=True)
class RiskSet:
    container_name: str
    item_name: str
    impact_prop_name: str
    allowed_levels: Tuple[str, ...]
    item_class: str
    impact_prop_class: str
    data_category_prop_name: str
    data_category_prop_class: str


_RISK_SET_CACHE: Optional[RiskSet] = None


def load_risk_set() -> RiskSet:
    global _RISK_SET_CACHE
    if _RISK_SET_CACHE is not None:
        return _RISK_SET_CACHE

    path = files("opengov_oscal_pyprivacy").joinpath("data/privacy_risk_sets.csv")
    content = path.read_text(encoding="utf-8")
    rows = list(csv.DictReader(content.splitlines()))
    if not rows:
        raise ValueError("privacy_risk_sets.csv is empty")
    r = rows[0]  # single-set for now; can be extended later

    _RISK_SET_CACHE = RiskSet(
        container_name=r["container_name"],
        item_name=r["item_name"],
        impact_prop_name=r["impact_prop_name"],
        allowed_levels=tuple((r["allowed_levels"] or "").split("|")),
        item_class=r["item_class"],
        impact_prop_class=r["impact_prop_class"],
        data_category_prop_name=r["data_category_prop_name"],
        data_category_prop_class=r["data_category_prop_class"],
    )
    return _RISK_SET_CACHE


@dataclass(frozen=True)
class RiskImpactScenario:
    id: str
    level: ImpactLevel
    prose: str
    data_category_example: Optional[str] = None


# ---------------------------------------------------------------------------
# Mixed-mode prop helpers for parts (dict or Part/Property objects)
# ---------------------------------------------------------------------------

def _get_prop_value(part: Any, prop_name: str) -> Optional[str]:
    """Read a prop value from a part (dict or Part model)."""
    props = _get(part, "props", []) or []
    for pr in props:
        if _get(pr, "name") == prop_name:
            return _get(pr, "value")
    return None


def _set_or_replace_prop(part: Any, *, name: str, class_: str, value: str) -> None:
    """Set or replace a property on a part (dict or Part model)."""
    from pydantic import BaseModel
    props = _get(part, "props")
    if not isinstance(props, list):
        props = []
        _set(part, "props", props)

    # Remove existing with same name+class
    props[:] = [
        p for p in props
        if not (_get(p, "name") == name and _get(p, "class", _get(p, "class_")) == class_)
    ]

    # Add new prop: use Property model if parent uses Pydantic, else dict
    if isinstance(part, BaseModel):
        props.append(Property(name=name, value=value, **{"class": class_}))
    else:
        props.append({"name": name, "class": class_, "value": value})


def _remove_prop(part: Any, *, name: str, class_: str) -> None:
    """Remove a property from a part by name+class."""
    props = _get(part, "props")
    if not isinstance(props, list):
        return
    props[:] = [
        p for p in props
        if not (_get(p, "name") == name and _get(p, "class", _get(p, "class_")) == class_)
    ]


def _as_level(val: Optional[str]) -> Optional[ImpactLevel]:
    if val in ("normal", "moderate", "high"):
        return val  # type: ignore[return-value]
    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_risk_impact_scenarios(control: Control) -> Dict[ImpactLevel, RiskImpactScenario]:
    cfg = load_risk_set()
    root_parts = parts_ref(control)

    container = None
    for p in root_parts:
        if _get(p, "name") == cfg.container_name:
            container = p
            break

    # MVP tolerance: if no container part exists, read from root
    children = (_get(container, "parts", []) if container is not None else root_parts) or []

    out: Dict[ImpactLevel, RiskImpactScenario] = {}
    for ch in children:
        if _get(ch, "name") != cfg.item_name:
            continue

        level = _as_level(_get_prop_value(ch, cfg.impact_prop_name))
        if not level:
            continue

        out[level] = RiskImpactScenario(
            id=_get(ch, "id", ""),
            level=level,
            prose=_get(ch, "prose", "") or "",
            data_category_example=_get_prop_value(ch, cfg.data_category_prop_name),
        )
    return out


def upsert_risk_impact_scenario(
    control: Control,
    level: ImpactLevel,
    *,
    prose: str,
    data_category_example: Optional[str] = None,
) -> str:
    cfg = load_risk_set()
    control_id = getattr(control, "id", "ctrl").lower()

    container = ensure_part_container(
        control,
        cfg.container_name,
        part_id=f"{control_id}-{cfg.container_name}",
        prose=None,
    )

    children = _get(container, "parts", [])
    if not isinstance(children, list):
        children = []
        _set(container, "parts", children)

    # find existing by impact-level prop
    existing = None
    for ch in children:
        if _get(ch, "name") != cfg.item_name:
            continue
        if _get_prop_value(ch, cfg.impact_prop_name) == level:
            existing = ch
            break

    if existing is None:
        # Create new child matching the container's type (Part model or dict)
        from opengov_oscal_pycore.crud.parts import _container_uses_part_models
        from opengov_oscal_pycore.models import Part
        if _container_uses_part_models(container):
            existing = Part(
                id=f"{control_id}-risk-impact-{level}",
                name=cfg.item_name,
                **{"class": cfg.item_class},
            )
        else:
            existing = {
                "id": f"{control_id}-risk-impact-{level}",
                "name": cfg.item_name,
                "class": cfg.item_class,
                "props": [],
            }
        children.append(existing)

    _set(existing, "prose", prose)
    _set_or_replace_prop(existing, name=cfg.impact_prop_name, class_=cfg.impact_prop_class, value=level)

    if data_category_example:
        _set_or_replace_prop(
            existing,
            name=cfg.data_category_prop_name,
            class_=cfg.data_category_prop_class,
            value=data_category_example,
        )
    else:
        _remove_prop(existing, name=cfg.data_category_prop_name, class_=cfg.data_category_prop_class)

    return _get(existing, "id", "")


def delete_risk_impact_scenario(control: Control, level: ImpactLevel) -> None:
    cfg = load_risk_set()
    scenarios = get_risk_impact_scenarios(control)
    target = scenarios.get(level)
    if not target:
        return

    root_parts = parts_ref(control)
    for p in root_parts:
        if _get(p, "name") == cfg.container_name:
            children = _get(p, "parts", []) or []
            _set(p, "parts", [ch for ch in children if _get(ch, "id") != target.id])
            return

    root_parts[:] = [ch for ch in root_parts if _get(ch, "id") != target.id]
