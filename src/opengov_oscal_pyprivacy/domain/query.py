from __future__ import annotations
from typing import List

from opengov_oscal_pycore.models import Catalog, Control
from opengov_oscal_pycore.crud_catalog import find_controls_by_prop
from .. import catalog_keys as K


def find_controls_by_tom_id(cat: Catalog, tom_id: str) -> List[Control]:
    """Find all controls with the given SDM building-block identifier."""
    return find_controls_by_prop(cat, prop_name=K.SDM_BUILDING_BLOCK, prop_value=tom_id)


def find_controls_by_implementation_level(cat: Catalog, level: str) -> List[Control]:
    """Find all controls with the given implementation-level."""
    return find_controls_by_prop(cat, prop_name="implementation-level", prop_value=level)


def find_controls_by_legal_article(cat: Catalog, article: str) -> List[Control]:
    """Find all controls referencing the given legal article."""
    return find_controls_by_prop(
        cat, prop_name=K.LEGAL, prop_value=article, prop_class=K.CLASS_PROOF,
    )
