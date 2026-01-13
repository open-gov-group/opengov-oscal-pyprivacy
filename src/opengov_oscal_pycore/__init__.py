"""
opengov_oscal_pycore

Lightweight, tool-agnostic core utilities for working with OSCAL-like JSON
structures in Python.

Scope (intentionally small):
- Minimal subset models (Pydantic v2) with round-trip safety
- File-based repository IO (load/save)
- Utilities for props (and later parts/prose)
- Catalog-focused CRUD helpers
- Simple versioning helpers
"""

from .models import Catalog, Group, Control, Property
from .repo import OscalRepository

__all__ = ["Catalog", "Group", "Control", "Property", "OscalRepository"]
