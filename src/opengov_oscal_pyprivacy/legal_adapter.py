from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional, List

from opengov_oscal_pycore.models import Control, Property

from . import catalog_keys as K

# Public API from opengov-pylegal-utils (separate repo/package)
from opengov_pylegal_utils import NormIdentity, parse_norm_references


@dataclass(frozen=True)
class LegalPropSpec:
    """
    Default mapping of normalized legal references into OSCAL props.
    Matches the Workbench catalog conventions.
    """
    name: str = K.LEGAL
    ns: str = "de"
    group: str = K.GROUP_REFERENCE
    class_: str = K.CLASS_PROOF


def iter_legal_props(control: Control, spec: LegalPropSpec = LegalPropSpec()) -> Iterable[Property]:
    for p in (control.props or []):
        if p.name == spec.name:
            yield p


def list_normalized_legal_ids(control: Control, spec: LegalPropSpec = LegalPropSpec()) -> List[str]:
    ids: List[str] = []
    for p in iter_legal_props(control, spec):
        if p.value:
            ids.append(p.value)
    return ids


def add_legal_id(
    control: Control,
    norm_id: str | NormIdentity,
    *,
    label: Optional[str] = None,
    spec: LegalPropSpec = LegalPropSpec(),
) -> None:
    """
    Add a normalized legal identifier to a control.

    - value: canonical normalized id (string)
    - remarks: human-readable label (optional)
    """
    if control.props is None:
        control.props = []

    norm_str = str(norm_id)

    # Do not duplicate the same norm id
    for p in control.props:
        if p.name == spec.name and p.value == norm_str:
            # ensure spec fields are enforced
            p.ns = spec.ns
            p.group = spec.group
            p.class_ = spec.class_
            if label:
                p.remarks = label
            return

    control.props.append(
        Property(
            name=spec.name,
            value=norm_str,
            ns=spec.ns,
            group=spec.group,
            class_=spec.class_,
            remarks=label,
        )
    )


def normalize_legal_from_text(
    control: Control,
    text: str,
    *,
    spec: LegalPropSpec = LegalPropSpec(),
) -> List[str]:
    """
    Parse free text for legal references and attach normalized identifiers as OSCAL props.

    Uses the default CSV-backed registry shipped with opengov-pylegal-utils.
    Returns the list of normalized identifiers added/ensured.
    """
    refs = parse_norm_references(text)
    added: List[str] = []

    for ref in refs:
        identity = getattr(ref, "identity", None)
        if identity is None:
            continue

        # keep the human-readable original if available
        label = getattr(ref, "original", None) or getattr(ref, "label", None)

        add_legal_id(control, identity, label=label, spec=spec)
        added.append(str(identity))

    return added
