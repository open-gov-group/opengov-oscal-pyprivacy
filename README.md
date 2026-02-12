# opengov-oscal-pyprivacy

Lightweight Python toolkit for OSCAL privacy catalogs and privacy/SDM-specific conventions.

**Version:** 0.4.0 | **Python:** >=3.10 | **License:** GPL-3.0-only

## Packages

### opengov_oscal_pycore

Minimal OSCAL subset models + generic CRUD utilities.

| Module | Purpose |
|--------|---------|
| `models.py` | Pydantic v2 models: `Catalog`, `Group`, `Control`, `Property`, `Part`, `Link` |
| `crud/props.py` | Property CRUD: `list_props`, `find_props`, `get_prop`, `upsert_prop`, `remove_props` |
| `crud/parts.py` | Part CRUD (Mixed-Mode: Part models + dicts): `parts_ref`, `find_part`, `ensure_part_container`, `add_child_part`, ... |
| `crud/links.py` | Link CRUD: `list_links`, `find_links`, `get_link`, `upsert_link`, `remove_links` |
| `crud_catalog.py` | Catalog-level CRUD: `find_control`, `add_control`, `delete_control`, `set_control_prop` |
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
| `catalog_keys.py` | Constants for property/group/class patterns |

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
pytest                    # run tests (129 tests)
pytest --tb=short -v      # verbose
coverage run -m pytest    # with coverage (90%)
```

## Target Consumers

- **opengov-oscal-workbench** — catalog creation & maintenance
- **DSMS / RoPA tooling** — API/gateway integration
- See [MIGRATION.md](MIGRATION.md) for Workbench migration strategy

## License

GPL-3.0-only
