from __future__ import annotations

from typing import Any, Dict, List, Optional

from opengov_oscal_pycore.models import Catalog
from opengov_oscal_pycore.crud_catalog import iter_controls, iter_controls_with_group
from ..dto.mapping_workbench import SdmSecurityMapping, MappingStandards
from ..dto.mapping_coverage import MappingCoverageResult, TransitiveMappingPath


def list_mappings(mapping_data: List[Dict[str, Any]]) -> List[SdmSecurityMapping]:
    """Parse raw mapping dicts into typed SdmSecurityMapping objects."""
    return [SdmSecurityMapping.model_validate(m) for m in mapping_data]


def get_mapping(
    mapping_data: List[Dict[str, Any]], sdm_control_id: str
) -> Optional[SdmSecurityMapping]:
    """Find a mapping by SDM control ID. Returns None if not found."""
    for m in mapping_data:
        mid = m.get("sdmControlId") or m.get("sdm_control_id", "")
        if mid == sdm_control_id:
            return SdmSecurityMapping.model_validate(m)
    return None


def upsert_mapping(
    mapping_data: List[Dict[str, Any]], mapping: SdmSecurityMapping
) -> SdmSecurityMapping:
    """Insert or update a mapping. Returns the upserted mapping."""
    dumped = mapping.model_dump(by_alias=True)
    for i, m in enumerate(mapping_data):
        mid = m.get("sdmControlId") or m.get("sdm_control_id", "")
        if mid == mapping.sdm_control_id:
            mapping_data[i] = dumped
            return mapping
    mapping_data.append(dumped)
    return mapping


def delete_mapping(
    mapping_data: List[Dict[str, Any]], sdm_control_id: str
) -> None:
    """Remove a mapping by SDM control ID. No-op if not found."""
    for i, m in enumerate(mapping_data):
        mid = m.get("sdmControlId") or m.get("sdm_control_id", "")
        if mid == sdm_control_id:
            mapping_data.pop(i)
            return


def calculate_mapping_coverage(
    source_catalog: Catalog,
    mapping_data: List[Dict[str, Any]],
) -> MappingCoverageResult:
    """Calculate how many catalog controls are covered by mappings.

    A control is "mapped" if there exists a mapping entry with its control ID
    as the sdmControlId AND that entry has at least one security_control or
    at least one non-empty standard (bsi, iso27001, or iso27701).
    """
    # Collect all control IDs with their group
    controls_by_group: Dict[str, List[str]] = {}
    all_control_ids: List[str] = []

    for ctrl, group in iter_controls_with_group(source_catalog):
        gid = group.id if group else "__ungrouped__"
        controls_by_group.setdefault(gid, []).append(ctrl.id)
        all_control_ids.append(ctrl.id)

    # Build set of mapped control IDs
    mapped_ids = set()
    for m in mapping_data:
        mid = m.get("sdmControlId") or m.get("sdm_control_id", "")
        # Check if mapping has actual content
        has_security = bool(m.get("securityControls") or m.get("security_controls"))
        standards = m.get("standards", {})
        has_standards = bool(
            standards.get("bsi") or standards.get("iso27001") or standards.get("iso27701")
        )
        if has_security or has_standards:
            mapped_ids.add(mid)

    total = len(all_control_ids)
    mapped = len([cid for cid in all_control_ids if cid in mapped_ids])
    unmapped = [cid for cid in all_control_ids if cid not in mapped_ids]
    coverage_pct = round((mapped / total * 100) if total > 0 else 0.0, 1)

    # Per-group coverage
    per_group: Dict[str, float] = {}
    for gid, cids in controls_by_group.items():
        g_total = len(cids)
        g_mapped = len([c for c in cids if c in mapped_ids])
        per_group[gid] = round((g_mapped / g_total * 100) if g_total > 0 else 0.0, 1)

    return MappingCoverageResult(
        total_controls=total,
        mapped_controls=mapped,
        coverage_percent=coverage_pct,
        unmapped_control_ids=unmapped,
        per_group_coverage=per_group,
    )


def resolve_transitive_mappings(
    mappings: List[Dict[str, Any]],
    source_id: str,
) -> List[TransitiveMappingPath]:
    """Find transitive mapping paths from a source control.

    A transitive path: source -> security_controls -> their mappings -> ...
    This follows security_control references to find indirect standard mappings.
    """
    # Build lookup: controlId -> mapping
    by_id: Dict[str, Dict[str, Any]] = {}
    for m in mappings:
        mid = m.get("sdmControlId") or m.get("sdm_control_id", "")
        by_id[mid] = m

    paths: List[TransitiveMappingPath] = []
    source = by_id.get(source_id)
    if not source:
        return paths

    # Get direct security control refs
    sec_controls = source.get("securityControls") or source.get("security_controls", [])
    for ref in sec_controls:
        ctrl_id = ref.get("controlId") or ref.get("control_id", "")
        target = by_id.get(ctrl_id)
        target_standards: List[str] = []
        if target:
            standards = target.get("standards", {})
            for std_name, std_vals in standards.items():
                if std_vals:
                    target_standards.extend(f"{std_name}:{v}" for v in std_vals)

        paths.append(TransitiveMappingPath(
            source_id=source_id,
            path=[source_id, ctrl_id],
            target_standards=target_standards,
        ))

    return paths
