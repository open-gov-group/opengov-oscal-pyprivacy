# opengov-oscal-pyprivacy

Lightweight Python toolkit for OSCAL privacy catalogs and privacy/SDM-specific conventions.

**Version:** 0.8.0 | **Python:** >=3.10 | **License:** GPL-3.0-only

## Packages

### opengov_oscal_pycore

Minimal OSCAL subset models + generic CRUD utilities.

| Module | Purpose |
|--------|---------|
| `models.py` | Pydantic v2 models: `Catalog`, `Group`, `Control`, `Property`, `Part`, `Link`, `OscalMetadata`, `BackMatter`, `Resource` |
| `crud/props.py` | Property CRUD: `list_props`, `find_props`, `get_prop`, `upsert_prop`, `remove_props` |
| `crud/parts.py` | Part CRUD (Mixed-Mode: Part models + dicts): `parts_ref`, `find_part`, `ensure_part_container`, `add_child_part`, ... |
| `crud/links.py` | Link CRUD: `list_links`, `find_links`, `get_link`, `upsert_link`, `remove_links` |
| `crud/back_matter.py` | BackMatter CRUD: `find_resource`, `add_resource`, `remove_resource` |
| `crud_catalog.py` | Catalog-level CRUD + query: `find_control`, `find_group`, `add_group`, `delete_group`, `move_control`, ... |
| `validation.py` | Catalog validation: `validate_catalog`, `validate_metadata`, `validate_unique_ids` |
| `repo.py` | File-based I/O: `OscalRepository[T]` with `load()` / `save()` |

### opengov_oscal_pyprivacy

Privacy/SDM helpers, domain modules, CSV-backed vocabularies, and DTOs.

| Module | Purpose |
|--------|---------|
| `domain/privacy_control.py` | CRUD for measures, questions, maturity, risk scenarios + extract helpers |
| `domain/risk_guidance.py` | Risk impact scenario management (normal/moderate/high) |
| `domain/sdm_catalog.py` | SDM-specific property extraction/mutation (13 functions) |
| `domain/resilience_catalog.py` | Resilience catalog domain (domain/objective/description) |
| `dto/` | Pydantic DTOs for API integration (Privacy, SDM, SDM-TOM, Resilience, Mapping) |
| `vocab.py` | CSV-backed vocabulary loading (assurance goals, measures, maturity, ...) |
| `legal_adapter.py` | Legal reference normalization (integrates with opengov-pylegal-utils) |
| `domain/query.py` | Query helpers: `find_controls_by_tom_id`, `find_controls_by_legal_article` |
| `converters/` | DTO factory functions: Control/Group -> DTO in one call |
| `dto/ropa.py` | ROPA DTOs: RopaControlSummary, RopaControlDetail, RopaGroupSummary, RopaGroupDetail |
| `dto/dpia.py` | DPIA DTOs: DpiaControlSummary, DpiaControlDetail, DpiaGroupSummary, DpiaGroupDetail |
| `catalog_keys.py` | Constants for property/group/class patterns |
| `codelist/models.py` | Codelist, CodeEntry, CodeLabel, CascadeRule — strict Pydantic models |
| `codelist/registry.py` | CodelistRegistry: central registry with validate, search, load_defaults |
| `codelist/i18n.py` | TranslationOverlay: multilingual label resolution (EN/DE/FR) |
| `codelist/cascade.py` | CascadeService: cascading compliance impacts on data category changes |
| `codelist/export/` | Genericode 1.0 XML export + OSCAL Props integration |

## Installation

### Development (editable)
```bash
pip install -e ".[dev]"
```

### From GitHub
```bash
pip install git+https://github.com/open-gov-group/opengov-oscal-pyprivacy.git
```

## Design Goals

- **Round-trip safety**: All models use `extra="allow"` to preserve unknown OSCAL fields
- **CSV-first vocabularies**: Policy data separated from code (`data/*.csv`)
- **Mixed-Mode parts**: `crud/parts.py` transparently handles both `Part` Pydantic models and plain dicts
- **Minimal scope**: Intentionally small surface area, extend as needed

## Quick Usage

### Load a Workbench catalog
```python
import json
from opengov_oscal_pycore import Catalog

data = json.loads(open("catalog.json", encoding="utf-8").read())
cat = Catalog.model_validate(data)  # accepts {"catalog": {...}} and direct form

control = cat.groups[0].controls[0]
print(control.title)
print(control.parts[0].prose)  # typed Part objects
```

### Extract SDM properties
```python
from opengov_oscal_pyprivacy.domain.sdm_catalog import (
    extract_sdm_module, extract_sdm_goals, extract_dsgvo_articles,
)

module = extract_sdm_module(control)       # "ORG-GOV-01"
goals = extract_sdm_goals(control)         # ["transparency", "intervenability"]
articles = extract_dsgvo_articles(control)  # ["EU:REG:GDPR:ART-5_ABS-2", ...]
```

### Extract privacy control data
```python
from opengov_oscal_pyprivacy import (
    extract_legal_articles, extract_tom_id, extract_statement,
    extract_maturity_level_texts, list_typical_measures,
)

statement = extract_statement(control)
maturity = extract_maturity_level_texts(control)  # {1: "...", 3: "...", 5: "..."}
measures = list_typical_measures(control)          # [{"id": "...", "prose": "..."}]
```

### Normalize legal references
```python
from opengov_oscal_pyprivacy import normalize_legal_from_text

normalize_legal_from_text(control, "Art. 5 Abs. 2 DSGVO")
```

### Convert Control to DTO (v0.5.0)

```python
from opengov_oscal_pyprivacy import control_to_privacy_detail, control_to_sdm_detail

# Single call replaces 15+ manual extract calls
detail = control_to_privacy_detail(control, group_id="GOV")
print(detail.statement)           # extracted statement
print(detail.typical_measures)    # [TextItem(id=..., prose=...)]
print(detail.risk_impact_high)    # PrivacyRiskImpactScenario or None

sdm = control_to_sdm_detail(control, group_id="GOV")
print(sdm.props.sdm_module)      # "ORG-GOV-01"
print(sdm.props.sdm_goals)       # ["transparency", ...]
```

### Typed Metadata (v0.6.0)

```python
from opengov_oscal_pycore import Catalog, OscalMetadata

cat = Catalog.model_validate(data)
print(cat.metadata.title)          # typed attribute access
print(cat.metadata.oscal_version)  # "1.1.2"
print(cat.metadata.roles[0].id)   # "owner"
```

### Group CRUD (v0.6.0)

```python
from opengov_oscal_pycore import add_group, delete_group, move_control, Group

add_group(cat, Group(id="NEW", title="New Group"))
move_control(cat, control_id="GOV-01", target_group_id="NEW")
```

### Validate a catalog (v0.6.0)

```python
from opengov_oscal_pycore import validate_catalog

issues = validate_catalog(cat)
for issue in issues:
    print(f"[{issue.severity}] {issue.path}: {issue.message}")
```

### ROPA Converter (v0.7.0)

```python
from opengov_oscal_pyprivacy import control_to_ropa_detail

detail = control_to_ropa_detail(control, group_id="REG")
print(detail.evidence_artifacts)   # ["record-of-processing"]
print(detail.maturity_domain)      # "records-of-processing"
print(detail.maturity_requirement) # 3
```

### DPIA Converter (v0.7.0)

```python
from opengov_oscal_pyprivacy import control_to_dpia_detail

detail = control_to_dpia_detail(control, group_id="DPIA")
print(detail.evidence_artifacts)   # ["dpia-report", "risk-register"]
print(detail.maturity_domain)      # "risk-management"
print(detail.measure_category)     # "process"
```

### Codelist Registry (v0.8.0)

```python
from opengov_oscal_pyprivacy.codelist import CodelistRegistry

registry = CodelistRegistry.load_defaults()
print(registry.validate_code("data-categories", "health-data"))  # True
print(registry.get_label("data-categories", "health-data", "de"))  # "Gesundheitsdaten"
```

### Cascade Compliance (v0.8.0)

```python
from opengov_oscal_pyprivacy.codelist import CascadeService

cascade = CascadeService.load_defaults()
impacts = cascade.suggest_changes("contact-data", "health-data")
for i in impacts:
    print(f"[{i.severity}] {i.description}")
```

### Risk impact scenarios
```python
from opengov_oscal_pyprivacy import (
    upsert_risk_impact_scenario, get_risk_impact_scenarios,
)

upsert_risk_impact_scenario(control, "high", prose="Identitaetsdiebstahl moeglich")
scenarios = get_risk_impact_scenarios(control)
```

## Development

```bash
pytest                    # run tests (423 tests)
pytest --tb=short -v      # verbose
coverage run -m pytest    # with coverage (97%)
```

## Target Consumers

- **opengov-oscal-workbench** — catalog creation & maintenance
- **DSMS / RoPA tooling** — API/gateway integration
- See [MIGRATION.md](MIGRATION.md) for Workbench migration strategy

## License

GPL-3.0-only
