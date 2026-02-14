from __future__ import annotations

"""
Profile operations: resolve imports, build profiles, add imports.

All functions are stateless (except add_profile_import which mutates in place).
"""

import copy
import uuid
from typing import Callable, List

from opengov_oscal_pycore.models import Catalog, Control, Group, OscalMetadata
from opengov_oscal_pycore.models_profile import ImportRef, Profile


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_NAMESPACE_PROFILE = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")


def _collect_with_ids(selector_list: List[dict]) -> set[str]:
    """Extract control IDs from include-controls / exclude-controls entries.

    Each entry is typically ``{"with-ids": ["GOV-01", "GOV-02"]}``.
    """
    ids: set[str] = set()
    for entry in selector_list:
        for cid in entry.get("with-ids", []):
            ids.add(cid)
    return ids


def _filter_controls(
    controls: List[Control],
    include_ids: set[str] | None,
    exclude_ids: set[str],
) -> List[Control]:
    """Return a filtered copy of controls based on include/exclude sets."""
    result: List[Control] = []
    for ctrl in controls:
        if exclude_ids and ctrl.id in exclude_ids:
            continue
        if include_ids is not None and ctrl.id not in include_ids:
            continue
        result.append(copy.deepcopy(ctrl))
    return result


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def resolve_profile_imports(
    profile: Profile,
    catalog_loader: Callable[[str], Catalog],
) -> Catalog:
    """Resolve all imports and return a flat resolved catalog.

    For each :class:`ImportRef` in the profile:
    - Call *catalog_loader(href)* to obtain the source catalog.
    - Apply ``include-controls`` / ``exclude-controls`` filtering.
    - Collect resulting controls, preserving group structure.

    Returns a new :class:`Catalog` with the profile's metadata and a fresh UUID.
    """
    resolved_groups: List[Group] = []

    for imp in profile.imports:
        source_catalog = catalog_loader(imp.href)
        include_ids = (
            _collect_with_ids(imp.include_controls)
            if imp.include_controls
            else None
        )
        exclude_ids = _collect_with_ids(imp.exclude_controls)

        for group in source_catalog.groups:
            filtered = _filter_controls(group.controls, include_ids, exclude_ids)
            if filtered:
                resolved_groups.append(
                    Group(
                        id=group.id,
                        title=group.title,
                        controls=filtered,
                    )
                )

    resolved_uuid = str(
        uuid.uuid5(_NAMESPACE_PROFILE, f"resolved-{profile.uuid}")
    )
    return Catalog(
        uuid=resolved_uuid,
        metadata=copy.deepcopy(profile.metadata),
        groups=resolved_groups,
    )


def build_profile_from_controls(
    catalog: Catalog,
    control_ids: List[str],
    *,
    title: str,
    version: str,
) -> Profile:
    """Build a new Profile selecting specific controls from a catalog.

    Creates an :class:`ImportRef` with ``href="#"`` (self-referencing)
    whose ``include-controls`` lists the requested *control_ids*.
    Generates a deterministic UUID from *title* via ``uuid5``.
    """
    profile_uuid = str(uuid.uuid5(_NAMESPACE_PROFILE, title))

    metadata = OscalMetadata(
        title=title,
        version=version,
        oscal_version="1.1.2",
    )

    import_ref = ImportRef(
        href="#",
        include_controls=[{"with-ids": list(control_ids)}],
    )

    return Profile(
        uuid=profile_uuid,
        metadata=metadata,
        imports=[import_ref],
    )


def add_profile_import(
    profile: Profile,
    href: str,
    control_ids: List[str],
) -> None:
    """Add an import reference to a profile (mutates in place).

    Creates an :class:`ImportRef` with the given *href* and
    ``include-controls`` populated from *control_ids*, then appends it
    to ``profile.imports``.
    """
    import_ref = ImportRef(
        href=href,
        include_controls=[{"with-ids": list(control_ids)}],
    )
    profile.imports.append(import_ref)
