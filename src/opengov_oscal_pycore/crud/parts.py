from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple, Callable


PartDict = Dict[str, Any]


def _ensure_pydantic_extra(model: Any) -> Dict[str, Any]:
    extra = getattr(model, "__pydantic_extra__", None)
    if extra is None:
        model.__dict__["__pydantic_extra__"] = {}
        extra = model.__dict__["__pydantic_extra__"]
    return extra


def parts_ref(obj: Any) -> List[PartDict]:
    """Return a mutable reference to obj.parts.

    Works for:
      - dict objects (expects key 'parts')
      - Pydantic models that store unknown fields in __pydantic_extra__ (extra='allow')
    """
    if isinstance(obj, dict):
        parts = obj.get("parts")
        if not isinstance(parts, list):
            parts = []
            obj["parts"] = parts
        return parts

    # If model has an explicit attribute, prefer it
    if hasattr(obj, "parts"):
        parts = getattr(obj, "parts")
        if isinstance(parts, list):
            return parts

    extra = _ensure_pydantic_extra(obj)
    parts = extra.get("parts")
    if not isinstance(parts, list):
        parts = []
        extra["parts"] = parts
    return parts


def find_part(parts: Sequence[PartDict], *, name: str | None = None, part_id: str | None = None) -> Optional[PartDict]:
    for p in parts:
        if not isinstance(p, dict):
            continue
        if name is not None and p.get("name") != name:
            continue
        if part_id is not None and p.get("id") != part_id:
            continue
        return p
    return None


def ensure_part_container(
    parent: Any,
    name: str,
    *,
    part_id: Optional[str] = None,
    prose: Optional[str] = None,
) -> PartDict:
    parts = parts_ref(parent)
    p = find_part(parts, name=name)
    if p is None:
        p = {"name": name}
        if part_id:
            p["id"] = part_id
        parts.append(p)
    if prose is not None:
        p["prose"] = prose
    if "parts" not in p or not isinstance(p.get("parts"), list):
        p["parts"] = []
    if "props" in p and not isinstance(p.get("props"), list):
        p["props"] = []
    if "links" in p and not isinstance(p.get("links"), list):
        p["links"] = []
    return p


def remove_part(parent: Any, *, name: str | None = None, part_id: str | None = None) -> int:
    parts = parts_ref(parent)
    before = len(parts)
    parts[:] = [
        p for p in parts
        if not (
            isinstance(p, dict)
            and (name is None or p.get("name") == name)
            and (part_id is None or p.get("id") == part_id)
        )
    ]
    return before - len(parts)


def list_child_parts(container: PartDict, *, name: str | None = None) -> List[PartDict]:
    children = container.get("parts", [])
    if not isinstance(children, list):
        return []
    out: List[PartDict] = []
    for ch in children:
        if not isinstance(ch, dict):
            continue
        if name is not None and ch.get("name") != name:
            continue
        out.append(ch)
    return out


def add_child_part(
    container: PartDict,
    *,
    name: str,
    prose: Optional[str] = None,
    part_id: Optional[str] = None,
    title: Optional[str] = None,
    props: Optional[list[dict]] = None,
    links: Optional[list[dict]] = None,
) -> PartDict:
    if "parts" not in container or not isinstance(container.get("parts"), list):
        container["parts"] = []
    child: PartDict = {"name": name}
    if part_id:
        child["id"] = part_id
    if title is not None:
        child["title"] = title
    if prose is not None:
        child["prose"] = prose
    if props is not None:
        child["props"] = props
    if links is not None:
        child["links"] = links
    container["parts"].append(child)
    return child


def update_child_part(
    container: PartDict,
    child_id: str,
    *,
    prose: Optional[str] = None,
    title: Optional[str] = None,
    props: Optional[list[dict]] = None,
    links: Optional[list[dict]] = None,
) -> PartDict:
    for ch in list_child_parts(container):
        if ch.get("id") == child_id:
            if prose is not None:
                ch["prose"] = prose
            if title is not None:
                ch["title"] = title
            if props is not None:
                ch["props"] = props
            if links is not None:
                ch["links"] = links
            return ch
    raise ValueError(f"part child not found: {child_id}")


def delete_child_part(container: PartDict, child_id: str) -> None:
    if "parts" not in container or not isinstance(container.get("parts"), list):
        container["parts"] = []
    before = len(container["parts"])
    container["parts"] = [
        ch for ch in container["parts"]
        if not (isinstance(ch, dict) and ch.get("id") == child_id)
    ]
    if len(container["parts"]) == before:
        raise ValueError(f"part child not found: {child_id}")
