from __future__ import annotations

from typing import Optional

from ..models import BackMatter, Resource


def find_resource(back_matter: BackMatter, uuid: str) -> Optional[Resource]:
    """Find a resource by UUID."""
    for r in back_matter.resources:
        if r.uuid == uuid:
            return r
    return None


def add_resource(back_matter: BackMatter, resource: Resource) -> None:
    """Add a resource. Raises ValueError if UUID already exists."""
    if find_resource(back_matter, resource.uuid) is not None:
        raise ValueError(f"Resource {resource.uuid} already exists")
    back_matter.resources.append(resource)


def remove_resource(back_matter: BackMatter, uuid: str) -> bool:
    """Remove a resource by UUID. Returns True if removed."""
    before = len(back_matter.resources)
    back_matter.resources = [r for r in back_matter.resources if r.uuid != uuid]
    return len(back_matter.resources) < before
