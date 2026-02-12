from __future__ import annotations

import csv
from dataclasses import dataclass
from importlib.resources import files
from typing import Any, Dict, List, Optional, Sequence, Tuple

from opengov_oscal_pycore.models import Control, Property
from opengov_oscal_pycore.crud.parts import (
    parts_ref,
    find_part,
    ensure_part_container,
    list_child_parts,
    add_child_part,
    update_child_part,
    delete_child_part,
    _get,
    _set,
)
from opengov_oscal_pycore.crud.props import find_props, remove_props, upsert_prop, get_prop

from .. import catalog_keys as K

from .risk_guidance import (
    get_risk_impact_scenarios,
    upsert_risk_impact_scenario,
    delete_risk_impact_scenario,
)


@dataclass(frozen=True)
class PartSet:
    container_name: str
    canonical_item_name: str
    accepted_item_names: Tuple[str, ...]
    id_prefix: str


_PART_SETS_CACHE: Optional[Dict[str, PartSet]] = None


def load_part_sets() -> Dict[str, PartSet]:
    global _PART_SETS_CACHE
    if _PART_SETS_CACHE is not None:
        return _PART_SETS_CACHE

    path = files("opengov_oscal_pyprivacy").joinpath("data/privacy_part_sets.csv")
    content = path.read_text(encoding="utf-8")
    rows = list(csv.DictReader(content.splitlines()))
    out: Dict[str, PartSet] = {}
    for r in rows:
        out[r["container_name"]] = PartSet(
            container_name=r["container_name"],
            canonical_item_name=r["canonical_item_name"],
            accepted_item_names=tuple((r["accepted_item_names"] or "").split("|")),
            id_prefix=r["id_prefix"],
        )
    _PART_SETS_CACHE = out
    return out


def _next_seq_id(existing_ids: Sequence[str], prefix: str) -> str:
    nums: List[int] = []
    for eid in existing_ids:
        if isinstance(eid, str) and eid.startswith(prefix):
            tail = eid[len(prefix):]
            if tail.isdigit():
                nums.append(int(tail))
    nxt = (max(nums) + 1) if nums else 1
    return f"{prefix}{nxt:03d}"


# -----------------------------
# Generic item-container CRUD
# -----------------------------

def _list_items(control: Control, container_name: str) -> List[Dict[str, str]]:
    part_sets = load_part_sets()
    cfg = part_sets[container_name]
    container = ensure_part_container(control, container_name)
    out: List[Dict[str, str]] = []
    for item in list_child_parts(container):
        if _get(item, "name") in cfg.accepted_item_names:
            out.append({"id": _get(item, "id", ""), "prose": _get(item, "prose", "")})
    return out


def _add_item(control: Control, container_name: str, prose: str) -> str:
    part_sets = load_part_sets()
    cfg = part_sets[container_name]
    container = ensure_part_container(control, container_name, part_id=f"{control.id.lower()}-{container_name}")
    existing_ids = [_get(p, "id", "") for p in list_child_parts(container) if isinstance(_get(p, "id", ""), str)]
    new_id = _next_seq_id(existing_ids, f"{control.id.lower()}-{cfg.id_prefix}-")
    add_child_part(container, name=cfg.canonical_item_name, part_id=new_id, prose=prose)
    return new_id


def _update_item(control: Control, container_name: str, item_id: str, prose: str) -> None:
    part_sets = load_part_sets()
    cfg = part_sets[container_name]
    container = ensure_part_container(control, container_name)
    # allow update independent of name (only id), but enforce canonical name on write
    updated = update_child_part(container, item_id, prose=prose)
    _set(updated, "name", cfg.canonical_item_name)


def _delete_item(control: Control, container_name: str, item_id: str) -> None:
    container = ensure_part_container(control, container_name)
    delete_child_part(container, item_id)


# -----------------------------
# Public Privacy Field-sets
# -----------------------------

def list_typical_measures(control: Control) -> List[Dict[str, str]]:
    return _list_items(control, "typical-measures")


def add_typical_measure(control: Control, prose: str) -> str:
    return _add_item(control, "typical-measures", prose)


def update_typical_measure(control: Control, item_id: str, prose: str) -> None:
    _update_item(control, "typical-measures", item_id, prose)


def delete_typical_measure(control: Control, item_id: str) -> None:
    _delete_item(control, "typical-measures", item_id)


def list_assessment_questions(control: Control) -> List[Dict[str, str]]:
    return _list_items(control, "assessment-questions")


def add_assessment_question(control: Control, prose: str) -> str:
    return _add_item(control, "assessment-questions", prose)


def update_assessment_question(control: Control, item_id: str, prose: str) -> None:
    _update_item(control, "assessment-questions", item_id, prose)


def delete_assessment_question(control: Control, item_id: str) -> None:
    _delete_item(control, "assessment-questions", item_id)


def set_statement(control: Control, prose: str) -> None:
    ensure_part_container(control, "statement", prose=prose)


def set_risk_hint(control: Control, prose: str) -> None:
    ensure_part_container(control, "risk-hint", prose=prose)


def replace_risk_scenarios(control: Control, scenarios: List[Dict[str, str]]) -> None:
    container = ensure_part_container(control, "risk-scenarios", part_id=f"{control.id.lower()}-risk-scenarios")
    _set(container, "parts", [])
    for i, sc in enumerate(scenarios, start=1):
        add_child_part(
            container,
            name="risk-scenario",
            part_id=f"{control.id.lower()}-rs-{i:03d}",
            title=sc.get("title") or "",
            prose=sc.get("description") or "",
        )


def set_maturity_level_text(control: Control, level: int, prose: str) -> None:
    if level not in (1, 3, 5):
        raise ValueError("level must be one of 1, 3, 5")

    mh = ensure_part_container(control, "maturity-hints", part_id=f"{control.id.lower()}-maturity")
    # ensure children list
    children = _get(mh, "parts", [])
    name = f"maturity-level-{level}"
    # find by name
    child = None
    for p in children:
        if _get(p, "name") == name:
            child = p
            break
    if child is None:
        child = {"id": f"{_get(mh, 'id', 'maturity')}-level-{level:02d}", "name": name, "props": []}
        children.append(child)
    _set(child, "prose", prose)

    # ensure maturity-level prop (as in GOV-01)
    props = _get(child, "props")
    if not isinstance(props, list):
        props = []
        _set(child, "props", props)
    # remove wrong legacy prop name (maturity-level-<n>)
    props[:] = [pr for pr in props if not (_get(pr, "name") == f"maturity-level-{level}")]
    if not any(_get(pr, "name") == "maturity-level" and _get(pr, "value") == str(level) for pr in props):
        props.append({"name": "maturity-level", "value": str(level)})


def get_maturity_level_text(control: Control, level: int) -> Optional[str]:
    if level not in (1, 3, 5):
        raise ValueError("level must be one of 1, 3, 5")
    parts = parts_ref(control)
    mh = None
    for p in parts:
        if _get(p, "name") == "maturity-hints":
            mh = p
            break
    if not mh:
        return None
    for ch in (_get(mh, "parts") or []):
        if _get(ch, "name") == f"maturity-level-{level}":
            return _get(ch, "prose")
    return None


# -----------------------------
# Props helpers (privacy)
# -----------------------------

def list_dp_goals(control: Control) -> List[str]:
    # compat: assurance_goal|assurnace_goal
    names = {"assurance_goal", "assurnace_goal"}
    props = [p for p in control.props if p.name in names and p.class_ == K.CLASS_TELEOLOGICAL and getattr(p, "group", None) == K.GROUP_AIM]
    return [p.value for p in props]


def replace_dp_goals(control: Control, goals: List[str]) -> None:
    names = {"assurance_goal", "assurnace_goal"}
    control.props[:] = [p for p in control.props if not (p.name in names and p.class_ == K.CLASS_TELEOLOGICAL and getattr(p, "group", None) == K.GROUP_AIM)]
    for g in goals:
        upsert_prop(
            control.props,
            Property(name="assurance_goal", value=g, ns="de", group=K.GROUP_AIM, class_=K.CLASS_TELEOLOGICAL),
            key=("name", "group", "class_", "value"),
        )


# -----------------------------
# Extract helpers (read-only)
# -----------------------------

def _val(obj: Any, key: str, default: Any = None) -> Any:
    """Mixed-mode accessor: works for both dicts and Pydantic model objects."""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def extract_legal_articles(control: Control) -> List[str]:
    """Return all legal-article values from the control's props.

    Searches for props with name=K.LEGAL, group=K.GROUP_REFERENCE, class_=K.CLASS_PROOF.
    """
    matches = find_props(
        control.props,
        name=K.LEGAL,
        group=K.GROUP_REFERENCE,
        class_=K.CLASS_PROOF,
    )
    return [p.value for p in matches]


def extract_tom_id(control: Control) -> Optional[str]:
    """Return the SDM building-block identifier, or None."""
    prop = get_prop(control.props, K.SDM_BUILDING_BLOCK)
    return prop.value if prop is not None else None


def extract_statement(control: Control) -> Optional[str]:
    """Return the statement prose from the control's top-level parts, or None."""
    parts = parts_ref(control)
    part = find_part(parts, name="statement")
    if part is None:
        return None
    return _get(part, "prose")


def extract_risk_hint(control: Control) -> Optional[str]:
    """Return the risk-hint prose from the control's top-level parts, or None."""
    parts = parts_ref(control)
    part = find_part(parts, name="risk-hint")
    if part is None:
        return None
    return _get(part, "prose")


def extract_risk_scenarios(control: Control) -> List[Dict[str, str]]:
    """Return risk-scenario children as a list of {title, description} dicts."""
    parts = parts_ref(control)
    container = find_part(parts, name="risk-scenarios")
    if container is None:
        return []
    children = list_child_parts(container)
    out: List[Dict[str, str]] = []
    for ch in children:
        title = _val(ch, "title") or _val(ch, "prose") or ""
        description = _val(ch, "prose") or ""
        out.append({"title": title, "description": description})
    return out


def extract_maturity_level_texts(control: Control) -> Dict[int, Optional[str]]:
    """Return maturity-level texts for levels 1, 3, 5."""
    return {
        level: get_maturity_level_text(control, level)
        for level in (1, 3, 5)
    }
