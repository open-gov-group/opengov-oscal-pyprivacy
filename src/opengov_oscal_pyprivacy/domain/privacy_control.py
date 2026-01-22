from __future__ import annotations

import csv
from dataclasses import dataclass
from importlib.resources import files
from typing import Any, Dict, List, Optional, Sequence, Tuple

from opengov_oscal_pycore.models import Control, Property
from opengov_oscal_pycore.crud.parts import (
    parts_ref,
    ensure_part_container,
    list_child_parts,
    add_child_part,
    update_child_part,
    delete_child_part,
)
from opengov_oscal_pycore.crud.props import find_props, remove_props, upsert_prop

from .. import catalog_keys as K


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
        if item.get("name") in cfg.accepted_item_names:
            out.append({"id": item.get("id", ""), "prose": item.get("prose", "")})
    return out


def _add_item(control: Control, container_name: str, prose: str) -> str:
    part_sets = load_part_sets()
    cfg = part_sets[container_name]
    container = ensure_part_container(control, container_name, part_id=f"{control.id.lower()}-{container_name}")
    existing_ids = [p.get("id", "") for p in list_child_parts(container) if isinstance(p.get("id", ""), str)]
    new_id = _next_seq_id(existing_ids, f"{control.id.lower()}-{cfg.id_prefix}-")
    add_child_part(container, name=cfg.canonical_item_name, part_id=new_id, prose=prose)
    return new_id


def _update_item(control: Control, container_name: str, item_id: str, prose: str) -> None:
    part_sets = load_part_sets()
    cfg = part_sets[container_name]
    container = ensure_part_container(control, container_name)
    # allow update independent of name (only id), but enforce canonical name on write
    updated = update_child_part(container, item_id, prose=prose)
    updated["name"] = cfg.canonical_item_name


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
    container["parts"] = []
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
    children = mh["parts"]
    name = f"maturity-level-{level}"
    # find by name
    child = None
    for p in children:
        if isinstance(p, dict) and p.get("name") == name:
            child = p
            break
    if child is None:
        child = {"id": f"{mh.get('id','maturity')}-level-{level:02d}", "name": name, "props": []}
        children.append(child)
    child["prose"] = prose

    # ensure maturity-level prop (as in GOV-01)
    props = child.get("props")
    if not isinstance(props, list):
        props = []
        child["props"] = props
    # remove wrong legacy prop name (maturity-level-<n>)
    props[:] = [pr for pr in props if not (isinstance(pr, dict) and pr.get("name") == f"maturity-level-{level}")]
    if not any(isinstance(pr, dict) and pr.get("name") == "maturity-level" and pr.get("value") == str(level) for pr in props):
        props.append({"name": "maturity-level", "value": str(level)})


def get_maturity_level_text(control: Control, level: int) -> Optional[str]:
    if level not in (1, 3, 5):
        raise ValueError("level must be one of 1, 3, 5")
    parts = parts_ref(control)
    mh = None
    for p in parts:
        if isinstance(p, dict) and p.get("name") == "maturity-hints":
            mh = p
            break
    if not mh:
        return None
    for ch in (mh.get("parts") or []):
        if isinstance(ch, dict) and ch.get("name") == f"maturity-level-{level}":
            return ch.get("prose")
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
