from __future__ import annotations

from typing import List, Optional, Sequence

from ..models import Parameter


def list_params(params: Sequence[Parameter] | None) -> List[Parameter]:
    """Return a shallow copy of the params list."""
    if params is None:
        return []
    return list(params)


def find_params(
    params: Sequence[Parameter] | None,
    *,
    param_id: Optional[str] = None,
    label: Optional[str] = None,
) -> List[Parameter]:
    """Filter params by id and/or label."""
    if params is None:
        return []
    results = list(params)
    if param_id is not None:
        results = [p for p in results if p.id == param_id]
    if label is not None:
        results = [p for p in results if p.label == label]
    return results


def get_param(
    params: Sequence[Parameter] | None, param_id: str
) -> Optional[Parameter]:
    """Get a single param by id. Returns None if not found."""
    if params is None:
        return None
    for p in params:
        if p.id == param_id:
            return p
    return None


def upsert_param(params: List[Parameter], param: Parameter) -> Parameter:
    """Insert or update a param. Matches by id."""
    for i, existing in enumerate(params):
        if existing.id == param.id:
            params[i] = param
            return param
    params.append(param)
    return param


def remove_param(params: List[Parameter], param_id: str) -> None:
    """Remove a param by id. No-op if not found."""
    for i, p in enumerate(params):
        if p.id == param_id:
            params.pop(i)
            return
