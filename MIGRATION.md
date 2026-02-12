# Migration Guide: pyprivacy v0.3.0 -> v0.4.0

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

## 7. PR Template for Service Migration

```markdown
## Service Migration: [ServiceName]

### Changes
- [ ] Replace raw-dict helpers with pyprivacy domain functions
- [ ] Replace local DTOs with pyprivacy DTO imports
- [ ] Remove deprecated helper functions
- [ ] Update tests to use typed models

### Testing
- [ ] All existing service tests pass
- [ ] New tests for migrated functions
- [ ] Manual smoke test in Workbench UI
```
