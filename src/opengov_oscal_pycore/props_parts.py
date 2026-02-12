from __future__ import annotations

# Backwards-compatible wrapper module.
# New code should use opengov_oscal_pycore.crud.props

import warnings
from typing import Optional

from .models import Property
from .crud.props import get_prop as _get_prop, upsert_prop as _upsert_prop, remove_props as _remove_props


def get_prop(props: list[Property] | None, name: str, cls: Optional[str] = None) -> Optional[Property]:
    warnings.warn(
        "props_parts.get_prop is deprecated, use opengov_oscal_pycore.crud.props.get_prop",
        DeprecationWarning,
        stacklevel=2,
    )
    return _get_prop(props, name, class_=cls)


def set_prop(props: list[Property], name: str, value: str, cls: Optional[str] = None, ns: Optional[str] = None) -> Property:
    warnings.warn(
        "props_parts.set_prop is deprecated, use opengov_oscal_pycore.crud.props.upsert_prop",
        DeprecationWarning,
        stacklevel=2,
    )
    p = Property(name=name, value=value, class_=cls, ns=ns)
    return _upsert_prop(props, p, key=("name", "class_"))


def remove_prop(props: list[Property], name: str, cls: Optional[str] = None) -> None:
    warnings.warn(
        "props_parts.remove_prop is deprecated, use opengov_oscal_pycore.crud.props.remove_props",
        DeprecationWarning,
        stacklevel=2,
    )
    _remove_props(props, name=name, class_=cls)
