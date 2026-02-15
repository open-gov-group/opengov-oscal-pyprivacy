from __future__ import annotations

"""
OSCAL export helpers: convenience wrappers for serialising models to dict / JSON.

Usage::

    from opengov_oscal_pycore.export import to_dict, to_json

    data = to_dict(catalog, oscal_root_key="catalog")
    text = to_json(catalog, oscal_root_key="catalog", indent=2)
"""

import json
from typing import Any, Optional

from .models import OscalBaseModel


def to_dict(
    model: OscalBaseModel,
    *,
    oscal_root_key: Optional[str] = None,
    exclude_none: bool = True,
    by_alias: bool = True,
) -> dict[str, Any]:
    """Serialize an OSCAL model to a dict.

    Args:
        model: Any OscalBaseModel (Catalog, Profile, SSP, ComponentDefinition, etc.)
        oscal_root_key: If set, wraps output in {oscal_root_key: ...} (e.g. "catalog", "profile")
        exclude_none: Remove None fields (OSCAL best practice). Default True.
        by_alias: Use OSCAL-conformant field names (class_ -> class). Default True.
    """
    data = model.model_dump(by_alias=by_alias, exclude_none=exclude_none)
    if oscal_root_key:
        return {oscal_root_key: data}
    return data


def to_json(
    model: OscalBaseModel,
    *,
    oscal_root_key: Optional[str] = None,
    indent: int = 2,
    ensure_ascii: bool = False,
    exclude_none: bool = True,
) -> str:
    """Serialize an OSCAL model to a JSON string.

    Args:
        model: Any OscalBaseModel
        oscal_root_key: If set, wraps output in {oscal_root_key: ...}
        indent: JSON indentation (default 2)
        ensure_ascii: If True, escape non-ASCII characters. Default False.
        exclude_none: Remove None fields. Default True.
    """
    data = to_dict(model, oscal_root_key=oscal_root_key, exclude_none=exclude_none)
    return json.dumps(data, indent=indent, ensure_ascii=ensure_ascii)
