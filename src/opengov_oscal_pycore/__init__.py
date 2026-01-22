"""
opengov_oscal_pycore

Lightweight, tool-agnostic core utilities for working with OSCAL-like JSON
structures in Python.

Scope (intentionally small):
- Minimal subset models (Pydantic v2) with round-trip safety
- File-based repository IO (load/save)
- Generic CRUD helpers for props/parts/links/back-matter/metadata/params
- Catalog-focused CRUD helpers
- Simple versioning helpers
"""

from .models import Catalog, Group, Control, Property
from .repo import OscalRepository

# Generic CRUD (mechanics)
from .crud.props import list_props, find_props, get_prop as get_prop_v2, upsert_prop, remove_props
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

__all__ = [
    "Catalog",
    "Group",
    "Control",
    "Property",
    "OscalRepository",
    # props CRUD
    "list_props",
    "find_props",
    "get_prop_v2",
    "upsert_prop",
    "remove_props",
    # parts CRUD
    "parts_ref",
    "find_part",
    "ensure_part_container",
    "remove_part",
    "list_child_parts",
    "add_child_part",
    "update_child_part",
    "delete_child_part",
]
