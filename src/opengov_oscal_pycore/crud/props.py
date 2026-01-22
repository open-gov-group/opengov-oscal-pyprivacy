from __future__ import annotations

from typing import Iterable, Optional, List, Sequence

from ..models import Property


def list_props(props: Sequence[Property] | None) -> List[Property]:
    return list(props or [])


def find_props(
    props: Sequence[Property] | None,
    *,
    name: str | None = None,
    ns: str | None = None,
    group: str | None = None,
    class_: str | None = None,
    value: str | None = None,
) -> List[Property]:
    """Return all props matching the given filters."""
    out: List[Property] = []
    for p in props or []:
        if name is not None and p.name != name:
            continue
        if ns is not None and p.ns != ns:
            continue
        if group is not None and getattr(p, "group", None) != group:
            continue
        if class_ is not None and p.class_ != class_:
            continue
        if value is not None and p.value != value:
            continue
        out.append(p)
    return out


def get_prop(
    props: Sequence[Property] | None,
    name: str,
    *,
    class_: str | None = None,
    ns: str | None = None,
    group: str | None = None,
    value: str | None = None,
) -> Optional[Property]:
    matches = find_props(props, name=name, class_=class_, ns=ns, group=group, value=value)
    return matches[0] if matches else None


def upsert_prop(
    props: List[Property],
    prop: Property,
    *,
    key: Iterable[str] = ("name", "ns", "group", "class_", "value"),
) -> Property:
    """Insert or update a Property in-place.

    Default idempotency key is (name, ns, group, class_, value). This works well for
    normalized references and avoids duplicates.
    """
    def _k(p: Property) -> tuple:
        vals = []
        for field in key:
            if field == "group":
                vals.append(getattr(p, "group", None))
            else:
                vals.append(getattr(p, field))
        return tuple(vals)

    target_key = _k(prop)
    for existing in props:
        if _k(existing) == target_key:
            # update fields (keep same identity key)
            existing.remarks = getattr(prop, "remarks", None)
            existing.value = prop.value
            existing.ns = prop.ns
            if hasattr(existing, "group"):
                existing.group = getattr(prop, "group", None)
            existing.class_ = prop.class_
            return existing

    props.append(prop)
    return prop


def remove_props(
    props: List[Property],
    *,
    name: str | None = None,
    ns: str | None = None,
    group: str | None = None,
    class_: str | None = None,
    value: str | None = None,
) -> None:
    """Remove all properties matching the filters."""
    props[:] = [
        p for p in props
        if not (
            (name is None or p.name == name)
            and (ns is None or p.ns == ns)
            and (group is None or getattr(p, "group", None) == group)
            and (class_ is None or p.class_ == class_)
            and (value is None or p.value == value)
        )
    ]
