# Changelog

## [0.8.0] - 2026-02-14

Phase 1.5: Standardisierte Codelisten-Engine — Pydantic v2 Models, CodelistRegistry, XÖV-VVT Import, i18n, Cascade Engine, OSCAL Integration.

### Added

- Codelist Models: `Codelist`, `CodeEntry`, `CodeLabel`, `CascadeRule`, `CascadeEffect`, `CodeEntryMetadata` with strict validation (`extra="forbid"`) (#33)
- `CodelistRegistry` with JSON Loader: `load_defaults()`, `validate_code()`, `get_label()`, `search()`, `list_codes()` (#34)
- CSV → JSON Migration: 6 bestehende Vocabularies (assurance-goals, measure-types, evidence-types, maturity-domains, maturity-levels, mapping-schemes) als JSON (#34)
- XÖV-VVT Import: 12 Listen (data-categories, data-subjects, recipients, legal-instruments, crypto-methods, auth-methods, availability-classes, storage-locations, protocols, operating-models, data-flow-directions, document-types) + protection-levels (#35)
- i18n: `TranslationOverlay` mit EN/DE inline + FR Overlay-Dateien, Fallback-Chain (#36)
- Genericode Export: `export_genericode()` für XÖV-Kompatibilität (Roundtrip) (#37)
- Cascade Engine: `CascadeService` mit `evaluate_impact()`, `suggest_changes()`, 3 Regel-Sets (#38)
- OSCAL Integration: `validate_codelist_props()`, `create_codelist_prop()`, `extract_codelist_codes()` (#39)

### Quality Gate (#40)

- 423 tests, 97% coverage (up from 295 tests / 97%)
- New: codelist/ subpackage with models, registry, loader, i18n, cascade, export/
- 19 JSON codelist files, 3 cascade rule sets, FR overlay
- Python 3.10-3.14 compatible

## [0.7.0] - 2026-02-12

Phase 4: ROPA + DPIA Domains — Extract functions, DTOs, Converters, Query helpers.

### Added

- Extract: `extract_evidence_artifacts`, `extract_maturity_domain`, `extract_maturity_requirement`, `extract_measure_category` in `privacy_control.py` (#27)
- DTOs: `RopaControlSummary`, `RopaControlDetail`, `RopaGroupSummary`, `RopaGroupDetail` in `dto/ropa.py` (#28)
- DTOs: `DpiaControlSummary`, `DpiaControlDetail`, `DpiaGroupSummary`, `DpiaGroupDetail` in `dto/dpia.py` (#29)
- Converter: `control_to_ropa_summary`, `control_to_ropa_detail`, `group_to_ropa_summary`, `group_to_ropa_detail` (#28)
- Converter: `control_to_dpia_summary`, `control_to_dpia_detail`, `group_to_dpia_summary`, `group_to_dpia_detail` (#29)
- Query: `find_controls_by_evidence`, `find_controls_by_maturity_domain` in `domain/query.py` (#30)
- Exports: All ROPA/DPIA DTOs, converters, extract/query functions added to package exports (#30)

### Quality Gate (#31)

- 295 tests, 97% coverage (up from 257 tests / 97%)
- New test files: test_ropa, test_dpia
- Python 3.10-3.14 compatible

## [0.6.0] - 2026-02-12

Phase 3: Workbench-Readiness — Typed Metadata, BackMatter, Group CRUD, Validation.

### Added

- Models: `OscalMetadata`, `Role`, `Party` with typed fields and alias support (`last-modified` -> `last_modified`) (#21)
- Models: `BackMatter`, `Resource`, `Rlink` with `Catalog.back_matter` field (#22)
- CRUD: `add_group`, `delete_group`, `update_group_title`, `move_control` in `crud_catalog.py` (#23)
- CRUD: `find_resource`, `add_resource`, `remove_resource` in `crud/back_matter.py` (#22)
- Validation: `validate_catalog`, `validate_metadata`, `validate_unique_ids`, `validate_control` with `ValidationIssue` dataclass (#24)
- Exports: pycore `__init__.py` now exports all 50+ public functions and classes (#25)

### Changed

- **BREAKING**: `Catalog.metadata` changed from `Dict[str, Any]` to `OscalMetadata` Pydantic model (#21)
- `find_group` now searches recursively in nested groups (#23)
- `versioning.py`: fixed bug where `last_modified` (underscore) did not match OSCAL `last-modified` (hyphen) (#21)

### Quality Gate (#26)

- 257 tests, 97% coverage (up from 220 tests / 97%)
- New test files: test_back_matter, test_validation
- Python 3.10-3.14 compatible

## [0.5.0] - 2026-02-12

Phase 2: Converter-Layer — DTO-Factories, Naming-Standardisierung, Query-Helpers.

### Added

- Converter: `control_to_privacy_summary`, `control_to_privacy_detail`, `group_to_privacy_summary`, `group_to_privacy_detail` (#14)
- Converter: `control_to_sdm_summary`, `control_to_sdm_detail` (#15)
- Converter: `control_to_sdm_tom_summary`, `control_to_sdm_tom_detail`, `control_to_security_control` (#16)
- Replaces 15+ manual extract calls per control with a single converter call
- Query: `find_controls_by_prop`, `iter_controls_with_group` in `crud_catalog.py` (#18)
- Query: `find_controls_by_tom_id`, `find_controls_by_implementation_level`, `find_controls_by_legal_article` in `domain/query.py` (#18)
- Exports: `domain/__init__.py` exports all 55+ domain functions, `converters/__init__.py` exports all 9 converters (#17)

### Changed

- DTO naming: `DtoBaseModel` with `ConfigDict(populate_by_name=True)`, all fields snake_case with camelCase aliases (#11)
- DTO naming: `dto/sdm.py` `groupId` -> `group_id`, `dto/mapping_workbench.py` `catalogId` -> `catalog_id`, etc. (#11)
- Legacy cleanup: removed deprecated root-level `sdm_catalog.py` (`PrivacyCatalog` class) (#12)
- Legacy cleanup: `DeprecationWarning` in `props_parts.py`, `crud_catalog.py` migrated to `crud.props` (#12)

### Quality Gate (#20)

- 220 tests, 97% coverage (up from 129 tests / 90%)
- New test files: test_pycore_infrastructure, test_vocab, test_converters_*, test_query, test_integration_workflow, test_package_exports
- Python 3.10-3.14 compatible

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
