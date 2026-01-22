from __future__ import annotations

# Backwards-compatible wrapper module.
# New code should use opengov_oscal_pycore.crud.props

from typing import Optional

from .models import Property
from .crud.props import get_prop as _get_prop, upsert_prop as _upsert_prop, remove_props as _remove_props


def get_prop(props: list[Property] | None, name: str, cls: Optional[str] = None) -> Optional[Property]:
    return _get_prop(props, name, class_=cls)


def set_prop(props: list[Property], name: str, value: str, cls: Optional[str] = None, ns: Optional[str] = None) -> Property:
    p = Property(name=name, value=value, class_=cls, ns=ns)
    return _upsert_prop(props, p, key=("name", "class_"))


def remove_prop(props: list[Property], name: str, cls: Optional[str] = None) -> None:
    _remove_props(props, name=name, class_=cls)
