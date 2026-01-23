from __future__ import annotations

import csv
from dataclasses import dataclass
from importlib.resources import files
from typing import Any, Dict, Optional, Tuple, Literal

from opengov_oscal_pycore.models import Control
from opengov_oscal_pycore.crud.parts import parts_ref, ensure_part_container

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


def _get_prop_value(part: Dict[str, Any], prop_name: str) -> Optional[str]:
    for pr in part.get("props", []) or []:
        if isinstance(pr, dict) and pr.get("name") == prop_name:
            return pr.get("value")
    return None


def _set_or_replace_prop(part: Dict[str, Any], prop: Dict[str, Any]) -> None:
    props = part.setdefault("props", [])
    if not isinstance(props, list):
        part["props"] = props = []

    name = prop.get("name")
    cls = prop.get("class")
    props[:] = [
        p for p in props
        if not (isinstance(p, dict) and p.get("name") == name and p.get("class") == cls)
    ]
    props.append(prop)


def _as_level(val: Optional[str]) -> Optional[ImpactLevel]:
    if val in ("normal", "moderate", "high"):
        return val  # type: ignore[return-value]
    return None


def get_risk_impact_scenarios(control: Control) -> Dict[ImpactLevel, RiskImpactScenario]:
    cfg = load_risk_set()
    root_parts = parts_ref(control)

    container = None
    for p in root_parts:
        if isinstance(p, dict) and p.get("name") == cfg.container_name:
            container = p
            break

    # MVP tolerance: if no container part exists, read from root
    children = (container.get("parts", []) if isinstance(container, dict) else root_parts) or []

    out: Dict[ImpactLevel, RiskImpactScenario] = {}
    for ch in children:
        if not isinstance(ch, dict):
            continue
        if ch.get("name") != cfg.item_name:
            continue

        level = _as_level(_get_prop_value(ch, cfg.impact_prop_name))
        if not level:
            continue

        out[level] = RiskImpactScenario(
            id=ch.get("id", ""),
            level=level,
            prose=ch.get("prose", "") or "",
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

    children = container.setdefault("parts", [])
    if not isinstance(children, list):
        container["parts"] = children = []

    # find existing by impact-level prop
    existing = None
    for ch in children:
        if not isinstance(ch, dict) or ch.get("name") != cfg.item_name:
            continue
        if _get_prop_value(ch, cfg.impact_prop_name) == level:
            existing = ch
            break

    if existing is None:
        existing = {
            "id": f"{control_id}-risk-impact-{level}",
            "name": cfg.item_name,
            "class": cfg.item_class,
            "props": [],
        }
        children.append(existing)

    existing["prose"] = prose
    existing["class"] = cfg.item_class
    _set_or_replace_prop(existing, {"name": cfg.impact_prop_name, "class": cfg.impact_prop_class, "value": level})

    if data_category_example:
        _set_or_replace_prop(
            existing,
            {"name": cfg.data_category_prop_name, "class": cfg.data_category_prop_class, "value": data_category_example},
        )
    else:
        props = existing.get("props", []) or []
        existing["props"] = [
            p for p in props
            if not (
                isinstance(p, dict)
                and p.get("name") == cfg.data_category_prop_name
                and p.get("class") == cfg.data_category_prop_class
            )
        ]

    return existing.get("id", "")


def delete_risk_impact_scenario(control: Control, level: ImpactLevel) -> None:
    cfg = load_risk_set()
    scenarios = get_risk_impact_scenarios(control)
    target = scenarios.get(level)
    if not target:
        return

    root_parts = parts_ref(control)
    for p in root_parts:
        if isinstance(p, dict) and p.get("name") == cfg.container_name:
            children = p.get("parts", []) or []
            p["parts"] = [ch for ch in children if not (isinstance(ch, dict) and ch.get("id") == target.id)]
            return

    root_parts[:] = [ch for ch in root_parts if not (isinstance(ch, dict) and ch.get("id") == target.id)]
