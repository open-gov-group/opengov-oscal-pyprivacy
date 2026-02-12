from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Union

from pydantic import BaseModel

PartDict = Dict[str, Any]

# Union type for mixed-mode: Part model or plain dict
PartOrDict = Union[Any, PartDict]


# ---------------------------------------------------------------------------
# Internal helpers for transparent dict / Pydantic access
# ---------------------------------------------------------------------------

def _is_pydantic(obj: Any) -> bool:
    """Return True if *obj* is a Pydantic BaseModel instance."""
    return isinstance(obj, BaseModel)


def _is_part_model(obj: Any) -> bool:
    """Return True if *obj* is a Part Pydantic model (has explicit 'name' field)."""
    return (
        _is_pydantic(obj)
        and "name" in type(obj).model_fields
    )


def _has_explicit_parts_field(obj: Any) -> bool:
    """Return True if *obj* is a Pydantic model with an explicit 'parts' field declaration."""
    return _is_pydantic(obj) and "parts" in type(obj).model_fields


def _get(obj: Any, key: str, default: Any = None) -> Any:
    """Transparent getter: dict.get() or getattr()."""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _set(obj: Any, key: str, value: Any) -> None:
    """Transparent setter: dict[key]= or setattr()."""
    if isinstance(obj, dict):
        obj[key] = value
    else:
        setattr(obj, key, value)


def _ensure_pydantic_extra(model: Any) -> Dict[str, Any]:
    extra = getattr(model, "__pydantic_extra__", None)
    if extra is None:
        model.__dict__["__pydantic_extra__"] = {}
        extra = model.__dict__["__pydantic_extra__"]
    return extra


def _container_uses_part_models(parent: Any) -> bool:
    """Decide whether new children should be Part model instances or dicts.

    Heuristic:
      1. If parent is a Pydantic model with an explicit ``parts`` field -> True
      2. If existing children are Part models -> True
      3. Otherwise -> False (dict mode)
    """
    if _has_explicit_parts_field(parent):
        return True

    children = _get(parent, "parts")
    if isinstance(children, list):
        for ch in children:
            if _is_part_model(ch):
                return True
            if isinstance(ch, dict):
                return False
    return False


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parts_ref(obj: Any) -> List[PartOrDict]:
    """Return a mutable reference to obj.parts.

    Works for:
      - dict objects (expects key 'parts')
      - Pydantic models with an explicit ``parts`` field (Part, Control, Group)
      - Pydantic models that store unknown fields in ``__pydantic_extra__`` (extra='allow')
    """
    if isinstance(obj, dict):
        parts = obj.get("parts")
        if not isinstance(parts, list):
            parts = []
            obj["parts"] = parts
        return parts

    # Pydantic model with an explicit parts field -> return direct mutable reference
    if _has_explicit_parts_field(obj):
        parts = getattr(obj, "parts")
        if isinstance(parts, list):
            return parts

    # If model has an explicit attribute (but not declared in model_fields),
    # prefer it if it's a list
    if hasattr(obj, "parts"):
        parts = getattr(obj, "parts")
        if isinstance(parts, list):
            return parts

    # Fallback to __pydantic_extra__
    extra = _ensure_pydantic_extra(obj)
    parts = extra.get("parts")
    if not isinstance(parts, list):
        parts = []
        extra["parts"] = parts
    return parts


def find_part(
    parts: Sequence[PartOrDict],
    *,
    name: str | None = None,
    part_id: str | None = None,
) -> Optional[PartOrDict]:
    """Find a part by name and/or id.  Works with Part models and dicts."""
    for p in parts:
        p_name = _get(p, "name")
        p_id = _get(p, "id")
        if name is not None and p_name != name:
            continue
        if part_id is not None and p_id != part_id:
            continue
        return p
    return None


def _make_part(
    parent: Any,
    *,
    name: str,
    part_id: Optional[str] = None,
    prose: Optional[str] = None,
    title: Optional[str] = None,
    props: Optional[list] = None,
    links: Optional[list] = None,
) -> PartOrDict:
    """Create a new part as Part model or dict, depending on parent context."""
    if _container_uses_part_models(parent):
        # Lazy import to avoid circular dependency at module level
        from ..models import Part as PartModel
        kwargs: Dict[str, Any] = {"name": name}
        if part_id:
            kwargs["id"] = part_id
        if title is not None:
            kwargs["title"] = title
        if prose is not None:
            kwargs["prose"] = prose
        if props is not None:
            kwargs["props"] = props
        if links is not None:
            kwargs["links"] = links
        return PartModel(**kwargs)
    else:
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
        return child


def ensure_part_container(
    parent: Any,
    name: str,
    *,
    part_id: Optional[str] = None,
    prose: Optional[str] = None,
) -> PartOrDict:
    """Find or create a top-level part container by *name*.

    Works with both dict-based and Part-model-based parents.
    """
    parts = parts_ref(parent)
    p = find_part(parts, name=name)

    if p is None:
        p = _make_part(parent, name=name, part_id=part_id)
        parts.append(p)

    if prose is not None:
        _set(p, "prose", prose)

    # Ensure sub-collections exist
    p_parts = _get(p, "parts")
    if not isinstance(p_parts, list):
        _set(p, "parts", [])

    if isinstance(p, dict):
        if "props" in p and not isinstance(p.get("props"), list):
            p["props"] = []
        if "links" in p and not isinstance(p.get("links"), list):
            p["links"] = []

    return p


def remove_part(parent: Any, *, name: str | None = None, part_id: str | None = None) -> int:
    """Remove parts matching *name* and/or *part_id*.  Works with both types."""
    parts = parts_ref(parent)
    before = len(parts)

    def _matches(p: Any) -> bool:
        p_name = _get(p, "name")
        p_id = _get(p, "id")
        return (
            (name is None or p_name == name)
            and (part_id is None or p_id == part_id)
        )

    parts[:] = [p for p in parts if not _matches(p)]
    return before - len(parts)


def list_child_parts(
    container: PartOrDict,
    *,
    name: str | None = None,
) -> List[PartOrDict]:
    """List child parts of *container*, optionally filtered by *name*."""
    children = _get(container, "parts", [])
    if not isinstance(children, list):
        return []
    out: List[PartOrDict] = []
    for ch in children:
        ch_name = _get(ch, "name")
        if name is not None and ch_name != name:
            continue
        out.append(ch)
    return out


def add_child_part(
    container: PartOrDict,
    *,
    name: str,
    prose: Optional[str] = None,
    part_id: Optional[str] = None,
    title: Optional[str] = None,
    props: Optional[list] = None,
    links: Optional[list] = None,
) -> PartOrDict:
    """Append a new child part to *container*.  Returns the new child."""
    children = _get(container, "parts")
    if not isinstance(children, list):
        children = []
        _set(container, "parts", children)

    child = _make_part(
        container,
        name=name,
        part_id=part_id,
        prose=prose,
        title=title,
        props=props,
        links=links,
    )
    children.append(child)
    return child


def update_child_part(
    container: PartOrDict,
    child_id: str,
    *,
    prose: Optional[str] = None,
    title: Optional[str] = None,
    props: Optional[list] = None,
    links: Optional[list] = None,
) -> PartOrDict:
    """Update the child part identified by *child_id*.  Returns the updated child."""
    for ch in list_child_parts(container):
        if _get(ch, "id") == child_id:
            if prose is not None:
                _set(ch, "prose", prose)
            if title is not None:
                _set(ch, "title", title)
            if props is not None:
                _set(ch, "props", props)
            if links is not None:
                _set(ch, "links", links)
            return ch
    raise ValueError(f"part child not found: {child_id}")


def delete_child_part(container: PartOrDict, child_id: str) -> None:
    """Delete the child part identified by *child_id*."""
    children = _get(container, "parts")
    if not isinstance(children, list):
        _set(container, "parts", [])
        children = _get(container, "parts")

    before = len(children)
    children[:] = [
        ch for ch in children
        if _get(ch, "id") != child_id
    ]
    if len(children) == before:
        raise ValueError(f"part child not found: {child_id}")
