# Changelog

## [0.4.0] - 2026-02-12

Phase 1: Fundament — vollstaendige Implementierung aller 10 Issues.

### Added

#### pycore: Models (#1)
- `Link` Pydantic v2 model (`href`, `rel`, `text`) with `extra="allow"`
- `Part` Pydantic v2 model (recursive: `id`, `name`, `class_`, `title`, `prose`, `props`, `links`, `parts`)
- `Control` extended: `+parts`, `+links`, `+params`, `+controls` (nested)
- `Group` extended: `+parts`, `+props`, `+groups` (nested)

#### pycore: Link CRUD (#2)
- `crud/links.py`: `list_links`, `find_links`, `get_link`, `upsert_link`, `remove_links`
- Same interface pattern as `crud/props.py`

#### pycore: Parts Mixed-Mode (#8)
- `crud/parts.py` now supports both `Part` model objects and plain dicts transparently
- Internal helpers: `_get()`, `_set()`, `_is_part_model()`, `_container_uses_part_models()`
- All existing API signatures remain stable

#### pyprivacy: SDM Catalog domain (#3)
- `domain/sdm_catalog.py`: 13 functions for SDM-specific property extraction and mutation
- `extract_sdm_module`, `extract_sdm_goals`, `extract_dsgvo_articles`
- `extract_implementation_level`, `extract_dp_risk_impact`, `extract_related_mappings`
- `set_implementation_level`, `set_dp_risk_impact`, `replace_related_mappings`
- `extract_sdm_tom_description`, `extract_sdm_tom_implementation_hints`
- `set_sdm_tom_description`, `set_sdm_tom_implementation_hints`

#### pyprivacy: Resilience Catalog domain (#4)
- `domain/resilience_catalog.py`: `extract_domain`, `extract_objective`, `extract_description`
- `set_domain`, `set_objective`, `set_description`

#### pyprivacy: SDM-TOM DTOs (#5)
- `dto/sdm_tom.py`: `SdmTomControlSummary`, `SdmTomControlDetail`
- Fixes Workbench import errors

#### pyprivacy: Resilience + Mapping DTOs (#6)
- `dto/resilience.py`: `SecurityControl`, `SecurityControlUpdateRequest`
- `dto/mapping_workbench.py`: `SecurityControlRef`, `MappingStandards`, `SdmSecurityMapping`

#### pyprivacy: Extract functions (#7)
- `extract_legal_articles`, `extract_tom_id`, `extract_statement`
- `extract_risk_hint`, `extract_risk_scenarios`, `extract_maturity_level_texts`

### Changed

- `privacy_control.py` and `risk_guidance.py` updated for Mixed-Mode support (Part models + dicts)
- Fixed Pydantic v2.11 deprecation warning (`obj.model_fields` -> `type(obj).model_fields`)

### Quality Gate (#10)
- 129 tests, 90% coverage
- All new domain functions >= 95% coverage
- Python 3.10-3.14 compatible

## [0.3.0] - 2025-11-27

- Initial privacy/SDM catalog support
- CSV-backed vocabularies
- Legal reference integration
- Risk impact scenarios
- Maturity level management
