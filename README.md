# opengov-oscal-pyprivacy

`opengov-oscal-pyprivacy` provides a lightweight Python toolkit for working with OSCAL privacy catalogs and privacy/SDM-specific conventions.

It contains:
- `opengov_oscal_pycore`: minimal OSCAL subset models + CRUD utilities (Catalog/Group/Control/Property)
- `opengov_oscal_pyprivacy`: privacy/SDM helpers, CSV-backed vocabularies, and legal reference integration

The library is designed for reuse in:
- **opengov-oscal-workbench** (catalog creation & maintenance)
- **DSMS / RoPA tooling** (later: API/gateway integration)

## Installation

### Development (editable)
```bash
pip install -e ".[dev]"
```
### From GitHub
```bash
pip install git+https://github.com/open-gov-group/opengov-oscal-pyprivacy.git
```

### CSV-first vocabularies (Policy/Data separated from Code)

Privacy/SDM vocabularies (assurance goals, measures, evidence types, maturity domains/levels) are stored as CSV files:

* `src/opengov_oscal_pyprivacy/data/*.csv`

This allows changes without code updates and supports later migration (CSV → database/search index).

Workbench catalog round-trip safety

### Workbench exports may contain OSCAL fields not explicitly modeled in the minimal subset.
All core models are configured to allow unknown fields (extra="allow") so catalogs can be loaded and saved without data loss.

`Property` supports 'group` and `remarks` to preserve workbench conventions.

### Legal reference normalization

This project integrates with opengov-pylegal-utils to normalize heterogeneous legal citations into canonical identifiers.

Typical workflow:

1. Parse free-text legal references (e.g. 'Art. 5 Abs. 2 DSGVO`)

2. Resolve against the CSV-based registry (aliases + descriptors)

3. Write normalized IDs back into OSCAL props:
   * `name="legal"`
   * `group="reference"`
   * `class="proof"`
   * `ns="de"`
   * `value="<normalized-id>"`
   * `remarks="<human label>"` (optional)

## Quick usage
### Load a workbench catalog
```bash
import json
from opengov_oscal_pycore.models import Catalog

data = json.loads(open("open_privacy_catalog_risk.json", "r", encoding="utf-8").read())

# supports both {"catalog": {...}} and direct {"uuid": ..., "metadata": ..., ...}
cat = Catalog.model_validate(data)
```

### Normalize legal refs into OSCAL props

```bash
from opengov_oscal_pyprivacy.sdm_catalog import PrivacyCatalog

pc = PrivacyCatalog(cat)
pc.normalize_legal_from_text("GOV-01", "Art. 5 Abs. 2 DSGVO")
```

## Development

Run tests:
```bash
pytest
```

## License

GPL-3.0-only
