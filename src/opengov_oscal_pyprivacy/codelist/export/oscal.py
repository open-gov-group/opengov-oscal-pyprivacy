from __future__ import annotations

from typing import List, Optional

from opengov_oscal_pycore.models import Catalog, Control, Property
from opengov_oscal_pycore.validation import ValidationIssue
from opengov_oscal_pycore.crud_catalog import iter_controls_with_group

from ..registry import CodelistRegistry

CODELIST_NAMESPACE = "https://open-gov-group.org/oscal/privacy/codelist"


def create_codelist_prop(
    list_id: str,
    code: str,
    prop_name: Optional[str] = None,
) -> Property:
    """Create an OSCAL Property referencing a codelist code.

    Args:
        list_id: The codelist ID (used as class_)
        code: The code value
        prop_name: Override for prop name (defaults to list_id)
    """
    return Property(
        name=prop_name or list_id,
        value=code,
        ns=CODELIST_NAMESPACE,
        class_=list_id,
    )


def extract_codelist_codes(
    control: Control,
    list_id: str,
) -> List[str]:
    """Extract all codelist codes of a given list from a control's props.

    Matches props where ns == CODELIST_NAMESPACE and class_ == list_id.
    """
    codes = []
    for prop in control.props:
        if getattr(prop, "ns", None) == CODELIST_NAMESPACE and prop.class_ == list_id:
            codes.append(prop.value)
    return codes


def validate_codelist_props(
    catalog: Catalog,
    registry: CodelistRegistry,
) -> List[ValidationIssue]:
    """Validate all codelist-referenced props in a catalog.

    Checks every Property with ns == CODELIST_NAMESPACE:
    - class_ must be a known codelist ID
    - value must be a valid code in that codelist
    """
    issues: List[ValidationIssue] = []

    for control, group in iter_controls_with_group(catalog):
        path_prefix = f"groups[{group.id}].controls[{control.id}]"
        for i, prop in enumerate(control.props):
            if getattr(prop, "ns", None) != CODELIST_NAMESPACE:
                continue

            prop_path = f"{path_prefix}.props[{i}]"
            list_id = prop.class_

            if list_id is None:
                issues.append(ValidationIssue(
                    severity="error",
                    path=prop_path,
                    message=f"Codelist prop '{prop.name}' missing class_ (codelist ID)",
                ))
                continue

            # Check if the codelist exists
            try:
                registry.get_list(list_id)
            except KeyError:
                issues.append(ValidationIssue(
                    severity="warning",
                    path=prop_path,
                    message=f"Unknown codelist '{list_id}' referenced in prop '{prop.name}'",
                ))
                continue

            # Check if the code is valid
            if not registry.validate_code(list_id, prop.value):
                issues.append(ValidationIssue(
                    severity="error",
                    path=prop_path,
                    message=f"Invalid code '{prop.value}' in codelist '{list_id}'",
                ))

    return issues
