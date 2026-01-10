"""
Model-Reexports für OSCAL-Artefakte.

Diese Datei kapselt oscal-pydantic, damit höher liegende Module
sich nur auf opengov_oscal_pycore.models beziehen müssen.
"""

from oscal_pydantic import catalog as _cat
from oscal_pydantic import profile as _prof
from oscal_pydantic import component as _comp
from oscal_pydantic import ssp as _ssp

Catalog = _cat.Catalog
Profile = _prof.Profile
ComponentDefinition = _comp.ComponentDefinition
SystemSecurityPlan = _ssp.SystemSecurityPlanSSP

# Optional: Type-Aliases für typische Unterstrukturen (Properties, Parts, Controls usw.)
Property = _cat.Property
Part = _cat.Part
Group = _cat.ControlGroup
Control = _cat.Control

__all__ = [
    "Catalog",
    "Profile",
    "ComponentDefinition",
    "SystemSecurityPlan",
    "Property",
    "Part",
    "Group",
    "Control",
]
