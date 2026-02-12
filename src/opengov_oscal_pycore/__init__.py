"""
opengov_oscal_pycore

Lightweight, tool-agnostic core utilities for working with OSCAL-like JSON
structures in Python.

Scope (intentionally small):
- Minimal subset models (Pydantic v2) with round-trip safety
- File-based repository IO (load/save)
- Generic CRUD helpers for props/parts/links/back-matter/metadata/params
- Catalog-focused CRUD helpers (controls + groups)
- Simple versioning helpers
- Validation helpers
"""

# Models
from .models import (
    Catalog, Group, Control, Property, Link, Part,
    OscalMetadata, Role, Party,
    BackMatter, Resource, Rlink,
)

# Repository
from .repo import OscalRepository

# Catalog CRUD
from .crud_catalog import (
    iter_controls,
    iter_controls_with_group,
    find_controls_by_prop,
    find_control,
    find_group,
    add_control,
    delete_control,
    set_control_prop,
    add_group,
    delete_group,
    update_group_title,
    move_control,
)

# Generic CRUD (props)
from .crud.props import list_props, find_props, get_prop as get_prop_v2, upsert_prop, remove_props

# Generic CRUD (parts)
from .crud.parts import (
    parts_ref,
    find_part,
    ensure_part_container,
    remove_part,
    list_child_parts,
    add_child_part,
    update_child_part,
    delete_child_part,
)

# Generic CRUD (links)
from .crud.links import list_links, find_links, get_link, upsert_link, remove_links

# Generic CRUD (back-matter)
from .crud.back_matter import find_resource, add_resource, remove_resource

# Versioning
from .versioning import touch_metadata, bump_version

# Validation
from .validation import (
    ValidationIssue,
    validate_catalog,
    validate_metadata,
    validate_unique_ids,
    validate_control,
)

__all__ = [
    # Models
    "Catalog", "Group", "Control", "Property", "Link", "Part",
    "OscalMetadata", "Role", "Party",
    "BackMatter", "Resource", "Rlink",
    # Repository
    "OscalRepository",
    # Catalog CRUD
    "iter_controls", "iter_controls_with_group", "find_controls_by_prop",
    "find_control", "find_group",
    "add_control", "delete_control", "set_control_prop",
    "add_group", "delete_group", "update_group_title", "move_control",
    # Props CRUD
    "list_props", "find_props", "get_prop_v2", "upsert_prop", "remove_props",
    # Parts CRUD
    "parts_ref", "find_part", "ensure_part_container", "remove_part",
    "list_child_parts", "add_child_part", "update_child_part", "delete_child_part",
    # Links CRUD
    "list_links", "find_links", "get_link", "upsert_link", "remove_links",
    # Back-matter CRUD
    "find_resource", "add_resource", "remove_resource",
    # Versioning
    "touch_metadata", "bump_version",
    # Validation
    "ValidationIssue", "validate_catalog", "validate_metadata",
    "validate_unique_ids", "validate_control",
]
