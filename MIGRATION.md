# Migration Guide: pyprivacy v0.3.0 -> v1.0.0

## 1. Update Dependency

```toml
# pyproject.toml
[project]
dependencies = [
  "opengov-oscal-pyprivacy>=0.4.0",
]
```

Or via git:
```bash
pip install git+https://github.com/open-gov-group/opengov-oscal-pyprivacy.git@v0.4.0
```

## 2. New Models: Part and Link

`Control`, `Group` now have typed fields for `parts`, `links`, `params`, `controls`/`groups`.
Parts are no longer stored in `__pydantic_extra__` but as `List[Part]`.

### Before (v0.3.0)
```python
# Parts were raw dicts in __pydantic_extra__
control = Catalog.model_validate(data).groups[0].controls[0]
parts = control.__pydantic_extra__.get("parts", [])
part = parts[0]  # dict
name = part["name"]
```

### After (v0.4.0)
```python
from opengov_oscal_pycore import Control, Part, Link

control = Catalog.model_validate(data).groups[0].controls[0]
part = control.parts[0]  # Part object
name = part.name
```

### Round-trip safety preserved
`Part` and `Link` use `extra="allow"`, so unknown OSCAL fields survive load/save cycles.

## 3. Service Migration Plan (per Workbench Service)

Each service should be migrated in a separate PR.

### 3.1 PrivacyCatalogService

Replace manual prop-extraction helpers with:

| Old (manual) | New (pyprivacy) |
|---|---|
| `_get_legal_articles(ctrl_dict)` | `extract_legal_articles(control)` |
| `_get_tom_id(ctrl_dict)` | `extract_tom_id(control)` |
| `_get_statement(ctrl_dict)` | `extract_statement(control)` |
| `_get_maturity_texts(ctrl_dict)` | `extract_maturity_level_texts(control)` |
| `_get_risk_scenarios(ctrl_dict)` | `extract_risk_scenarios(control)` |

### 3.2 SdmCatalogService

Replace raw-dict SDM logic (~290 LOC) with:

```python
from opengov_oscal_pyprivacy.domain.sdm_catalog import (
    extract_sdm_module,
    extract_sdm_goals,
    extract_dsgvo_articles,
    extract_implementation_level,
    extract_dp_risk_impact,
    extract_related_mappings,
    set_implementation_level,
    set_dp_risk_impact,
    replace_related_mappings,
)
```

### 3.3 SdmPrivacyCatalogService

Replace SDM-TOM helpers with:

```python
from opengov_oscal_pyprivacy.domain.sdm_catalog import (
    extract_sdm_tom_description,
    extract_sdm_tom_implementation_hints,
    set_sdm_tom_description,
    set_sdm_tom_implementation_hints,
)
```

DTOs available:
```python
from opengov_oscal_pyprivacy.dto import SdmTomControlSummary, SdmTomControlDetail
```

### 3.4 ResilienceCatalogService

Replace raw-dict logic (~88 LOC) with:

```python
from opengov_oscal_pyprivacy.domain.resilience_catalog import (
    extract_domain, extract_objective, extract_description,
    set_domain, set_objective, set_description,
)
from opengov_oscal_pyprivacy.dto import SecurityControl, SecurityControlUpdateRequest
```

### 3.5 MappingService

Import DTOs directly:
```python
from opengov_oscal_pyprivacy.dto import (
    SecurityControlRef, MappingStandards, SdmSecurityMapping,
)
```

## 4. Workbench models.py Cleanup

After all services are migrated, clean up `workbench/app/models.py`:

```python
# Re-export from pyprivacy (no local definitions needed)
from opengov_oscal_pyprivacy.dto import (
    PrivacyControlSummary, PrivacyControlDetail,
    SdmControlSummary, SdmControlDetail,
    SdmTomControlSummary, SdmTomControlDetail,
    SecurityControl, SecurityControlUpdateRequest,
    SecurityControlRef, MappingStandards, SdmSecurityMapping,
)
```

## 5. Breaking Changes

### Parts are now Part objects (not dicts)

If your code accesses parts as dicts:
```python
# OLD: dict access
part["name"]
part.get("prose", "")

# NEW: attribute access
part.name
part.prose or ""
```

The CRUD layer (`parts_ref`, `find_part`, `ensure_part_container`, etc.) handles both
types transparently (Mixed-Mode). If you use CRUD functions exclusively, no changes needed.

### New exports in __init__.py

`opengov_oscal_pycore` now exports `Link`, `Part` and all link CRUD functions.
`opengov_oscal_pyprivacy` now exports all extract/set functions from domain modules.

No removed exports — fully backward compatible.

## 6. Converter Functions (v0.5.0)

v0.5.0 adds converter functions that replace manual DTO assembly with a single call.

### Before (v0.4.0 — manual assembly)

```python
detail = PrivacyControlDetail(
    id=control.id,
    ctrl_class=control.class_ or "",
    title=control.title or "",
    group_id=group_id,
    tom_id=extract_tom_id(control),
    dsgvo_articles=extract_legal_articles(control),
    dp_goals=list_dp_goals(control),
    statement=extract_statement(control),
    # ... 10 more fields
)
```

### After (v0.5.0 — single call)

```python
from opengov_oscal_pyprivacy.converters import control_to_privacy_detail

detail = control_to_privacy_detail(control, group_id=group_id)
```

### Available Converters

| Converter | DTO | Service |
| --------- | --- | ------- |
| `control_to_privacy_summary` | `PrivacyControlSummary` | PrivacyCatalogService |
| `control_to_privacy_detail` | `PrivacyControlDetail` | PrivacyCatalogService |
| `group_to_privacy_summary` | `PrivacyGroupSummary` | PrivacyCatalogService |
| `group_to_privacy_detail` | `PrivacyGroupDetail` | PrivacyCatalogService |
| `control_to_sdm_summary` | `SdmControlSummary` | SdmCatalogService |
| `control_to_sdm_detail` | `SdmControlDetail` | SdmCatalogService |
| `control_to_sdm_tom_summary` | `SdmTomControlSummary` | SdmPrivacyCatalogService |
| `control_to_sdm_tom_detail` | `SdmTomControlDetail` | SdmPrivacyCatalogService |
| `control_to_security_control` | `SecurityControl` | ResilienceCatalogService |

### DTO Naming Change (v0.5.0)

All DTO fields are now snake_case in Python. Use `model_dump(by_alias=True)` for camelCase JSON output.

```python
detail = control_to_sdm_detail(control)
detail.props.sdm_module           # Python access (snake_case)
detail.model_dump(by_alias=True)  # JSON output (camelCase)
```

## 8. Typed Metadata (v0.6.0) — BREAKING CHANGE

`Catalog.metadata` changed from `Dict[str, Any]` to `OscalMetadata` Pydantic model.

### Before (v0.5.0)

```python
cat.metadata["title"]              # dict access
cat.metadata["last-modified"]      # hyphenated key
cat.metadata.get("version", "")    # dict .get()
```

### After (v0.6.0)

```python
cat.metadata.title                 # attribute access
cat.metadata.last_modified         # snake_case (alias: "last-modified")
cat.metadata.version or ""         # Optional field
cat.metadata.oscal_version         # alias: "oscal-version"
cat.metadata.roles                 # List[Role] (typed)
cat.metadata.parties               # List[Party] (typed)
```

### JSON serialization

```python
# Aliases are used automatically when serializing:
cat.metadata.model_dump(by_alias=True)
# {"title": "...", "last-modified": "...", "oscal-version": "..."}
```

### Round-trip safety preserved

`OscalMetadata` uses `extra="allow"`, so unknown metadata fields survive load/save cycles.

### Versioning helpers

```python
from opengov_oscal_pycore import touch_metadata, bump_version

touch_metadata(cat.metadata)        # sets last_modified to now (UTC)
bump_version(cat.metadata, "2.0.0") # sets version + touches last_modified
```

## 9. BackMatter Support (v0.6.0)

The `back-matter` section is now a typed field on `Catalog`.

```python
from opengov_oscal_pycore import find_resource, add_resource, Resource

# Access typed back-matter
if cat.back_matter:
    for res in cat.back_matter.resources:
        print(res.title, res.rlinks[0].href)

# CRUD
resource = find_resource(cat.back_matter, uuid="...")
add_resource(cat.back_matter, Resource(uuid="new-uuid", title="New Resource"))
```

## 10. Group CRUD (v0.6.0)

```python
from opengov_oscal_pycore import (
    add_group, delete_group, update_group_title, move_control, find_group,
    Group,
)

add_group(cat, Group(id="NEW", title="New Group"))
update_group_title(cat, "NEW", "Renamed Group")
move_control(cat, "GOV-01", "NEW")      # move control to different group
delete_group(cat, "OLD")                 # remove group + contents
find_group(cat, "nested-id")            # recursive search in nested groups
```

## 11. Validation (v0.6.0)

```python
from opengov_oscal_pycore import validate_catalog

issues = validate_catalog(cat)
for issue in issues:
    print(f"[{issue.severity}] {issue.path}: {issue.message}")
# [warning] metadata.version: Catalog version not specified
# [error] groups[1].controls[0].id: Duplicate control ID 'GOV-01'
```

## 13. ROPA + DPIA Converters (v0.7.0)

v0.7.0 adds ROPA (Records of Processing) and DPIA (Data Protection Impact Assessment) support.

### ROPA Converters

```python
from opengov_oscal_pyprivacy.converters import (
    control_to_ropa_summary, control_to_ropa_detail,
    group_to_ropa_summary, group_to_ropa_detail,
)
from opengov_oscal_pyprivacy.dto import (
    RopaControlSummary, RopaControlDetail,
    RopaGroupSummary, RopaGroupDetail,
)
```

### DPIA Converters

```python
from opengov_oscal_pyprivacy.converters import (
    control_to_dpia_summary, control_to_dpia_detail,
    group_to_dpia_summary, group_to_dpia_detail,
)
from opengov_oscal_pyprivacy.dto import (
    DpiaControlSummary, DpiaControlDetail,
    DpiaGroupSummary, DpiaGroupDetail,
)
```

### New Extract Functions (v0.7.0)

```python
from opengov_oscal_pyprivacy import (
    extract_evidence_artifacts,
    extract_maturity_domain,
    extract_maturity_requirement,
    extract_measure_category,
)
```

### New Query Helpers (v0.7.0)

```python
from opengov_oscal_pyprivacy import (
    find_controls_by_evidence,
    find_controls_by_maturity_domain,
)
```

## 12. PR Template for Service Migration

```markdown
## Service Migration: [ServiceName]

### Changes
- [ ] Replace raw-dict helpers with pyprivacy domain functions
- [ ] Replace local DTOs with pyprivacy DTO imports
- [ ] Remove deprecated helper functions
- [ ] Update tests to use typed models
- [ ] Migrate metadata dict access to attribute access (v0.6.0)

### Testing
- [ ] All existing service tests pass
- [ ] New tests for migrated functions
- [ ] Manual smoke test in Workbench UI
```

## 14. Codelist Engine (v0.8.0)

v0.8.0 adds a comprehensive Codelist Engine for standardized privacy vocabularies.

### CodelistRegistry

```python
from opengov_oscal_pyprivacy.codelist import CodelistRegistry

registry = CodelistRegistry.load_defaults()
registry.validate_code("data-categories", "health-data")  # True
registry.get_label("data-categories", "health-data", "de")  # "Gesundheitsdaten"
registry.search("data-categories", "health")  # [CodeEntry(...)]
```

### CascadeService

```python
from opengov_oscal_pyprivacy.codelist import CascadeService

cascade = CascadeService.load_defaults()
impacts = cascade.evaluate_impact("health-data", current_protection_level="baseline")
# Returns: enhanced protection required, DPIA required, AES-256 required
```

### OSCAL Props Integration

```python
from opengov_oscal_pyprivacy.codelist import create_codelist_prop, validate_codelist_props

prop = create_codelist_prop("data-categories", "health-data")
issues = validate_codelist_props(catalog, registry)
```

### i18n Overlays

```python
from opengov_oscal_pyprivacy.codelist import TranslationOverlay

overlay = TranslationOverlay.load_defaults()
overlay.get_label("data-categories", "health-data", "fr")  # "Données de santé"
```

## 15. OSCAL Architecture Models (v0.9.0)

v0.9.0 adds the three missing OSCAL document types (Profile, SSP, ComponentDefinition), a Mapping Domain, and a DiffService.

### Profile Model + Resolver

```python
from opengov_oscal_pycore import Profile, ImportRef, Modify

profile = Profile.model_validate(json.load(open("profile.json")))
print(profile.imports[0].href)

# Resolve imports into a flat catalog
from opengov_oscal_pyprivacy import resolve_profile_imports
resolved = resolve_profile_imports(profile, catalog_loader=my_loader)

# Build a new profile selecting specific controls
from opengov_oscal_pyprivacy import build_profile_from_controls
profile = build_profile_from_controls(catalog, ["GOV-01", "GOV-02"], title="My Profile", version="1.0")
```

### SSP Model + IR Generation

```python
from opengov_oscal_pycore import SystemSecurityPlan, SspImplementedRequirement

ssp = SystemSecurityPlan.model_validate(json.load(open("ssp.json")))
print(ssp.import_profile.href)

# Generate IR stubs for all controls
from opengov_oscal_pyprivacy import generate_implemented_requirements
irs = generate_implemented_requirements(resolved_catalog)

# Attach evidence
from opengov_oscal_pyprivacy import attach_evidence_to_ssp
from opengov_oscal_pycore import Resource
attach_evidence_to_ssp(ssp, Resource(uuid="...", title="Evidence"), statement_control_id="GOV-01")
```

### ComponentDefinition Model

```python
from opengov_oscal_pycore import ComponentDefinition, Component, Capability

comp_def = ComponentDefinition.model_validate(json.load(open("component-definition.json")))
print(comp_def.components[0].title)
print(comp_def.components[0].control_implementations[0].implemented_requirements)
```

### Mapping Domain + Coverage

```python
from opengov_oscal_pyprivacy import (
    list_mappings, get_mapping, upsert_mapping, delete_mapping,
    calculate_mapping_coverage, resolve_transitive_mappings,
)

mappings = list_mappings(mapping_data)
coverage = calculate_mapping_coverage(catalog, mapping_data)
print(f"{coverage.coverage_percent}% controls mapped")
print(f"Per group: {coverage.per_group_coverage}")
```

### DiffService

```python
from opengov_oscal_pyprivacy import OscalDiffService
from opengov_oscal_pycore import diff_catalogs, diff_controls

# Low-level
result = diff_catalogs(old_catalog, new_catalog)
print(result.summary.added, result.summary.changed, result.summary.removed)

# High-level service
svc = OscalDiffService(ignore_paths=["metadata.last-modified"])
result = svc.diff_files(Path("old.json"), Path("new.json"))
print(svc.format_diff_summary(result))
```

### Optional: deepdiff dependency

```bash
pip install opengov-oscal-pyprivacy[diff]  # install with deepdiff support
```

Without deepdiff, the diff falls back to a simple recursive dict comparison.

## 16. Typed Parameters (v1.0.0) — BREAKING CHANGE

`Control.params` changed from `List[Dict[str, Any]]` to `List[Parameter]`.

### Before (v0.9.0)

```python
control.params  # List[Dict[str, Any]]
param = control.params[0]  # dict
param["id"]
param.get("label", "")
```

### After (v1.0.0)

```python
from opengov_oscal_pycore import Parameter

control.params  # List[Parameter]
param = control.params[0]  # Parameter object
param.id
param.label or ""
param.values       # List[str]
param.constraints  # List[Dict[str, Any]]
```

### Parameter CRUD

```python
from opengov_oscal_pycore import list_params, find_params, get_param_value, upsert_param, remove_param

all_params = list_params(control)
matching = find_params(control, id="freq")
param = get_param_value(control, "freq")
upsert_param(control, Parameter(id="freq", label="Frequency", values=["quarterly"]))
remove_param(control, "freq")
```

## 17. Export Helpers (v1.0.0)

```python
from opengov_oscal_pycore import to_json, to_dict

# OSCAL-compliant JSON with aliases (e.g. "last-modified", "back-matter")
json_str = to_json(catalog)
json_str = to_json(catalog, indent=2)  # pretty-printed

# Dict with by_alias=True
data = to_dict(catalog)
```

## 18. JSON-Schema Validation (v1.0.0)

```python
from opengov_oscal_pycore import validate_against_oscal_schema

result = validate_against_oscal_schema(data, "catalog")
if not result.valid:
    for issue in result.issues:
        print(f"[{issue.severity}] {issue.path}: {issue.message}")
```

Supported types: `catalog`, `profile`, `component-definition`, `system-security-plan`.

## 19. PrivacyVocabs Deprecation (v1.0.0)

`load_default_privacy_vocabs()` and `PrivacyVocabs` are deprecated. Use `CodelistRegistry` instead.

### Before (v0.8.0)

```python
from opengov_oscal_pyprivacy.vocab import load_default_privacy_vocabs
vocabs = load_default_privacy_vocabs()
vocabs.assurance_goals  # set of strings
```

### After (v1.0.0)

```python
from opengov_oscal_pyprivacy.codelist import CodelistRegistry
registry = CodelistRegistry.load_defaults()
registry.list_codes("assurance-goals")  # list of CodeEntry
registry.validate_code("assurance-goals", "transparency")  # True
```

## 20. Genericode Roundtrip (v1.0.0)

```python
from opengov_oscal_pyprivacy.codelist import export_genericode, import_genericode

# Export to XML
xml_str = export_genericode(codelist)

# Import back from XML
codelist = import_genericode(xml_str)
```
