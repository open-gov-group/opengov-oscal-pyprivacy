# API Reference — v1.0.0

## opengov_oscal_pycore

### Models

| Model | Key Fields |
|-------|-----------|
| `Catalog` | `uuid`, `metadata: OscalMetadata`, `groups: List[Group]`, `back_matter: Optional[BackMatter]` |
| `Group` | `id`, `title`, `class_` (alias `class`), `controls: List[Control]`, `groups: List[Group]`, `props: List[Property]`, `parts: List[Part]` |
| `Control` | `id`, `title`, `class_` (alias `class`), `props: List[Property]`, `parts: List[Part]`, `links: List[Link]`, `params: List[Parameter]`, `controls: List[Control]` |
| `Property` | `name`, `value`, `ns`, `class_` (alias `class`), `group` |
| `Part` | `id`, `name`, `class_` (alias `class`), `title`, `prose`, `props: List[Property]`, `links: List[Link]`, `parts: List[Part]` (recursive) |
| `Link` | `href`, `rel`, `text` |
| `Parameter` | `id`, `label`, `class_` (alias `class`), `usage`, `values: List[str]`, `select`, `constraints`, `guidelines`, `props: List[Property]`, `links: List[Link]` |
| `OscalMetadata` | `title`, `last_modified` (alias `last-modified`), `version`, `oscal_version` (alias `oscal-version`), `roles: List[Role]`, `parties: List[Party]` |
| `BackMatter` | `resources: List[Resource]` |
| `Resource` | `uuid`, `title`, `description`, `rlinks: List[Rlink]` |
| `Rlink` | `href`, `media_type` (alias `media-type`) |
| `Role` | `id`, `title`, `description` |
| `Party` | `uuid`, `type`, `name` |
| `Profile` | `uuid`, `metadata: OscalMetadata`, `imports: List[ImportRef]`, `modify: Optional[Modify]` |
| `ImportRef` | `href`, `include_controls`, `exclude_controls` |
| `Modify` | `set_parameters`, `alters` |
| `ComponentDefinition` | `uuid`, `metadata: OscalMetadata`, `components: List[Component]`, `capabilities: List[Capability]` |
| `Component` | `uuid`, `type`, `title`, `description`, `control_implementations: List[ControlImplementation]` |
| `Capability` | `uuid`, `name`, `description` |
| `ControlImplementation` | `uuid`, `source`, `description`, `implemented_requirements: List[ImplementedRequirement]` |
| `ImplementedRequirement` | `uuid`, `control_id` (alias `control-id`), `description` |
| `SystemSecurityPlan` | `uuid`, `metadata: OscalMetadata`, `import_profile: ImportProfile`, `system_characteristics: SystemCharacteristics`, `control_implementation: SspControlImplementation` |
| `SspControlImplementation` | `description`, `implemented_requirements: List[SspImplementedRequirement]` |
| `SspImplementedRequirement` | `uuid`, `control_id` (alias `control-id`), `description`, `statements` |
| `SystemCharacteristics` | `system_name` (alias `system-name`), `description`, `security_sensitivity_level` (alias `security-sensitivity-level`) |
| `ImportProfile` | `href` |

All models inherit from `OscalBaseModel` with `extra="allow"` for round-trip safety.

### Catalog CRUD

**`iter_controls(cat: Catalog) -> Iterator[Control]`**
Iterate over all controls in all top-level groups.

**`iter_controls_with_group(cat: Catalog) -> Iterator[tuple[Control, Group]]`**
Yield `(control, parent_group)` pairs for all controls.

**`find_control(cat: Catalog, control_id: str) -> Optional[Control]`**
Find a control by ID across all groups.

**`find_group(cat: Catalog, group_id: str) -> Optional[Group]`**
Find a group by ID, searching recursively in nested groups.

**`find_controls_by_prop(cat, *, prop_name, prop_value=None, prop_class=None) -> list[Control]`**
Find all controls having a property matching the given criteria.

**`add_control(cat: Catalog, group_id: str, control: Control) -> None`**
Add a control to a specific group. Raises `ValueError` if group not found.

**`delete_control(cat: Catalog, control_id: str) -> bool`**
Delete a control by ID. Returns True if deleted.

**`set_control_prop(cat: Catalog, control_id: str, prop: Property) -> None`**
Upsert a property on a specific control.

**`add_group(cat: Catalog, group: Group) -> None`**
Add a new top-level group to the catalog.

**`delete_group(cat: Catalog, group_id: str) -> bool`**
Delete a group and all its contents. Returns True if deleted.

**`update_group_title(cat: Catalog, group_id: str, title: str) -> None`**
Update the title of an existing group.

**`move_control(cat: Catalog, control_id: str, target_group_id: str) -> None`**
Move a control from its current group to a different group.

### Props CRUD

**`list_props(props: Sequence[Property] | None) -> List[Property]`**
Return a shallow copy of the props list.

**`find_props(props, *, name=None, ns=None, group=None, class_=None, value=None) -> List[Property]`**
Filter properties by any combination of criteria.

**`get_prop(props, name, *, class_=None, ns=None, group=None, value=None) -> Optional[Property]`**
Get the first matching property (exported as `get_prop_v2`).

**`upsert_prop(props: List[Property], prop: Property, *, key=("name", "class")) -> Property`**
Insert or update a property in-place.

**`remove_props(props: List[Property], *, name=None, ns=None, class_=None) -> int`**
Remove matching properties. Returns count removed.

### Parts CRUD (Mixed-Mode)

**`parts_ref(owner) -> List[Part]`**
Get the parts list from a Control/Group (handles both Part models and dicts).

**`find_part(owner, name: str) -> Optional[Part]`**
Find a top-level part by name.

**`ensure_part_container(owner, name: str, **defaults) -> Part`**
Get or create a part container by name.

**`remove_part(owner, name: str) -> bool`**
Remove a top-level part. Returns True if removed.

**`list_child_parts(parent_part) -> List[Part]`**
List nested child parts.

**`add_child_part(parent_part, child: Part) -> None`**
Add a child part to a parent.

**`update_child_part(parent_part, child_id: str, **updates) -> bool`**
Update a child part by ID. Returns True if updated.

**`delete_child_part(parent_part, child_id: str) -> bool`**
Delete a child part by ID. Returns True if deleted.

### Links CRUD

**`list_links(links: Sequence[Link] | None) -> List[Link]`**
Return a shallow copy of the links list.

**`find_links(links, *, rel=None, href=None) -> List[Link]`**
Filter links by rel and/or href.

**`get_link(links, rel: str, *, href=None) -> Optional[Link]`**
Get the first matching link.

**`upsert_link(links: List[Link], link: Link, *, key=("rel", "href")) -> Link`**
Insert or update a link in-place.

**`remove_links(links: List[Link], *, rel=None, href=None) -> int`**
Remove matching links. Returns count removed.

### Params CRUD

**`list_params(params: Sequence[Parameter] | None) -> List[Parameter]`**
Return a shallow copy of the params list.

**`find_params(params, *, param_id=None, label=None) -> List[Parameter]`**
Filter parameters by id and/or label.

**`get_param(params, param_id: str) -> Optional[Parameter]`**
Get a single parameter by ID (exported as `get_param_value`).

**`upsert_param(params: List[Parameter], param: Parameter) -> Parameter`**
Insert or update a parameter. Matches by id.

**`remove_param(params: List[Parameter], param_id: str) -> None`**
Remove a parameter by ID. No-op if not found.

### BackMatter CRUD

**`find_resource(back_matter: BackMatter, uuid: str) -> Optional[Resource]`**
Find a resource by UUID.

**`add_resource(back_matter: BackMatter, resource: Resource) -> None`**
Add a resource. Raises `ValueError` if UUID already exists.

**`remove_resource(back_matter: BackMatter, uuid: str) -> bool`**
Remove a resource by UUID. Returns True if removed.

### Validation

**`validate_catalog(cat: Catalog) -> list[ValidationIssue]`**
Validate a full catalog (metadata + unique IDs + controls).

**`validate_metadata(metadata: OscalMetadata) -> list[ValidationIssue]`**
Validate metadata fields (title required, version/oscal-version recommended).

**`validate_unique_ids(cat: Catalog) -> list[ValidationIssue]`**
Check for duplicate control IDs across all groups.

**`validate_control(control: Control, path: str) -> list[ValidationIssue]`**
Validate a single control (title check).

`ValidationIssue` dataclass: `severity` ("error" | "warning"), `path`, `message`.

### Schema Validation

**`validate_against_oscal_schema(data: dict, oscal_type: OscalType, *, schema_path=None) -> SchemaValidationResult`**
Validate an OSCAL document dict against the official NIST JSON Schema. Requires `jsonschema` package.

`OscalType`: `"catalog"` | `"profile"` | `"component-definition"` | `"system-security-plan"`

`SchemaValidationResult`: `valid: bool`, `issues: List[SchemaValidationIssue]`, `schema_version: str`

`SchemaValidationIssue`: `path: str`, `message: str`, `schema_path: str`

### Diff

**`diff_oscal(old: dict, new: dict, *, ignore_paths=None) -> OscalDiffResult`**
Diff two OSCAL dicts. Uses deepdiff if available, otherwise simple recursive comparison.

**`diff_catalogs(old: Catalog, new: Catalog, *, ignore_paths=None) -> OscalDiffResult`**
Diff two Catalog models.

**`diff_controls(old: Control, new: Control) -> OscalDiffResult`**
Diff two Control models.

`OscalDiffResult`: `summary: DiffSummary`, `changes: List[DiffChange]`

`DiffSummary`: `added: int`, `changed: int`, `removed: int`

`DiffChange`: `path: str`, `change_type: Literal["added", "changed", "removed"]`, `old_value`, `new_value`

### Export

**`to_dict(model: OscalBaseModel, *, oscal_root_key=None, exclude_none=True, by_alias=True) -> dict`**
Serialize an OSCAL model to a dict with OSCAL-conformant field names.

**`to_json(model: OscalBaseModel, *, oscal_root_key=None, indent=2, ensure_ascii=False, exclude_none=True) -> str`**
Serialize an OSCAL model to a JSON string.

### Versioning

**`touch_metadata(metadata: OscalMetadata) -> None`**
Set `last_modified` to current UTC time.

**`bump_version(metadata: OscalMetadata, new_version: str) -> None`**
Set version and update `last_modified`.

### Repository

**`OscalRepository[T](path: Path, model_cls: Type[T])`**
Generic file-based I/O for OSCAL documents.

- `load() -> T` — Load and validate from JSON file.
- `save(model: T) -> None` — Serialize and write to JSON file.

---

## opengov_oscal_pyprivacy

### Privacy Control Domain

**`extract_legal_articles(control: Control) -> list[str]`**
Extract legal article references from control props.

**`extract_tom_id(control: Control) -> Optional[str]`**
Extract the TOM identifier.

**`extract_statement(control: Control) -> Optional[str]`**
Extract the statement prose from the `statement` part.

**`extract_risk_hint(control: Control) -> Optional[str]`**
Extract the risk hint text.

**`extract_risk_scenarios(control: Control) -> list[dict]`**
Extract risk scenario descriptions.

**`extract_maturity_level_texts(control: Control) -> dict[int, str]`**
Extract maturity level texts as `{level: text}` mapping.

**`extract_evidence_artifacts(control: Control) -> list[str]`**
Extract evidence artifact values.

**`extract_maturity_domain(control: Control) -> Optional[str]`**
Extract the maturity domain classification.

**`extract_maturity_requirement(control: Control) -> Optional[int]`**
Extract the maturity requirement level as int.

**`extract_measure_category(control: Control) -> Optional[str]`**
Extract the measure category classification.

**`list_typical_measures(control: Control) -> list[dict]`**
List all typical measure sub-parts.

**`add_typical_measure(control: Control, measure_id: str, prose: str) -> None`**
Add a new typical measure.

**`update_typical_measure(control: Control, measure_id: str, prose: str) -> bool`**
Update an existing typical measure.

**`delete_typical_measure(control: Control, measure_id: str) -> bool`**
Delete a typical measure by ID.

**`list_assessment_questions(control: Control) -> list[dict]`**
List all assessment question sub-parts.

**`add_assessment_question(control: Control, question_id: str, prose: str) -> None`**
Add a new assessment question.

**`update_assessment_question(control: Control, question_id: str, prose: str) -> bool`**
Update an existing assessment question.

**`delete_assessment_question(control: Control, question_id: str) -> bool`**
Delete an assessment question by ID.

**`set_statement(control: Control, prose: str) -> None`**
Set the statement prose.

**`set_risk_hint(control: Control, prose: str) -> None`**
Set the risk hint text.

**`replace_risk_scenarios(control: Control, scenarios: list[dict]) -> None`**
Replace all risk scenarios.

**`set_maturity_level_text(control: Control, level: int, prose: str) -> None`**
Set text for a specific maturity level.

**`get_maturity_level_text(control: Control, level: int) -> Optional[str]`**
Get text for a specific maturity level.

**`list_dp_goals(control: Control) -> list[str]`**
List data protection goals.

**`replace_dp_goals(control: Control, goals: list[str]) -> None`**
Replace all data protection goals.

### Risk Guidance

**`get_risk_impact_scenarios(control: Control) -> dict`**
Get risk impact scenarios (normal/moderate/high).

**`upsert_risk_impact_scenario(control: Control, level: str, prose: str) -> None`**
Insert or update a risk impact scenario.

**`delete_risk_impact_scenario(control: Control, level: str) -> bool`**
Delete a risk impact scenario.

### SDM Catalog Domain

**`extract_sdm_module(control: Control) -> Optional[str]`**
Extract the SDM module identifier.

**`extract_sdm_goals(control: Control) -> list[str]`**
Extract SDM protection goals.

**`extract_dsgvo_articles(control: Control) -> list[str]`**
Extract DSGVO article references.

**`extract_implementation_level(control: Control) -> Optional[str]`**
Extract the implementation level.

**`extract_dp_risk_impact(control: Control) -> Optional[str]`**
Extract the data protection risk impact level.

**`extract_related_mappings(control: Control) -> list[dict]`**
Extract related standard mappings.

**`set_implementation_level(control: Control, level: str) -> None`**
Set the implementation level.

**`set_dp_risk_impact(control: Control, impact: str) -> None`**
Set the data protection risk impact.

**`replace_related_mappings(control: Control, mappings: list[dict]) -> None`**
Replace all related standard mappings.

**`extract_sdm_tom_description(control: Control) -> Optional[str]`**
Extract the SDM-TOM description.

**`extract_sdm_tom_implementation_hints(control: Control) -> Optional[str]`**
Extract SDM-TOM implementation hints.

**`set_sdm_tom_description(control: Control, prose: str) -> None`**
Set the SDM-TOM description.

**`set_sdm_tom_implementation_hints(control: Control, prose: str) -> None`**
Set SDM-TOM implementation hints.

### Resilience Catalog Domain

**`extract_domain(control: Control) -> Optional[str]`**
Extract the resilience domain.

**`extract_objective(control: Control) -> Optional[str]`**
Extract the resilience objective.

**`extract_description(control: Control) -> Optional[str]`**
Extract the resilience description.

**`set_domain(control: Control, domain: str) -> None`**
Set the resilience domain.

**`set_objective(control: Control, objective: str) -> None`**
Set the resilience objective.

**`set_description(control: Control, description: str) -> None`**
Set the resilience description.

### Profile Domain

**`resolve_profile_imports(profile: Profile, *, catalog_loader: Callable) -> Catalog`**
Resolve profile imports into a flat catalog using the provided loader callback.

**`build_profile_from_controls(catalog: Catalog, control_ids: list[str], *, title: str, version: str) -> Profile`**
Build a new profile selecting specific controls from a catalog.

**`add_profile_import(profile: Profile, href: str, include_controls: list[str]) -> None`**
Add an import entry to a profile.

### SSP Domain

**`generate_implemented_requirements(catalog: Catalog) -> list[SspImplementedRequirement]`**
Generate IR stubs for all controls in a resolved catalog.

**`attach_evidence_to_ssp(ssp: SystemSecurityPlan, resource: Resource, statement_control_id: str) -> None`**
Attach evidence to a specific SSP control statement.

**`get_import_profile_href(ssp: SystemSecurityPlan) -> str`**
Get the profile href from an SSP.

### Mapping Domain

**`list_mappings(mapping_data: dict) -> list[dict]`**
List all mappings from mapping data.

**`get_mapping(mapping_data: dict, mapping_id: str) -> Optional[dict]`**
Get a single mapping by ID.

**`upsert_mapping(mapping_data: dict, mapping: dict) -> None`**
Insert or update a mapping.

**`delete_mapping(mapping_data: dict, mapping_id: str) -> bool`**
Delete a mapping by ID.

**`calculate_mapping_coverage(catalog: Catalog, mapping_data: dict) -> MappingCoverageResult`**
Calculate mapping coverage for a catalog.

**`resolve_transitive_mappings(mapping_data: dict, source_id: str) -> list[TransitiveMappingPath]`**
Resolve transitive mapping chains.

### Query Helpers

**`find_controls_by_tom_id(cat: Catalog, tom_id: str) -> list[Control]`**
Find controls by TOM identifier.

**`find_controls_by_implementation_level(cat: Catalog, level: str) -> list[Control]`**
Find controls by implementation level.

**`find_controls_by_legal_article(cat: Catalog, article: str) -> list[Control]`**
Find controls referencing a specific legal article.

**`find_controls_by_evidence(cat: Catalog, evidence_value: str) -> list[Control]`**
Find controls with a specific evidence artifact.

**`find_controls_by_maturity_domain(cat: Catalog, domain: str) -> list[Control]`**
Find controls by maturity domain.

### Converters

Control-level converters:

| Function | Returns |
|----------|---------|
| `control_to_privacy_summary(control, *, group_id=None)` | `PrivacyControlSummary` |
| `control_to_privacy_detail(control, *, group_id=None)` | `PrivacyControlDetail` |
| `control_to_sdm_summary(control, *, group_id=None)` | `SdmControlSummary` |
| `control_to_sdm_detail(control, *, group_id=None)` | `SdmControlDetail` |
| `control_to_sdm_tom_summary(control, *, group_id=None)` | `SdmTomControlSummary` |
| `control_to_sdm_tom_detail(control, *, group_id=None)` | `SdmTomControlDetail` |
| `control_to_security_control(control, *, group_id=None)` | `SecurityControl` |
| `control_to_ropa_summary(control, *, group_id=None)` | `RopaControlSummary` |
| `control_to_ropa_detail(control, *, group_id=None)` | `RopaControlDetail` |
| `control_to_dpia_summary(control, *, group_id=None)` | `DpiaControlSummary` |
| `control_to_dpia_detail(control, *, group_id=None)` | `DpiaControlDetail` |

Group-level converters:

| Function | Returns |
|----------|---------|
| `group_to_privacy_summary(group)` | `PrivacyGroupSummary` |
| `group_to_privacy_detail(group)` | `PrivacyGroupDetail` |
| `group_to_sdm_summary(group)` | `SdmGroupSummary` |
| `group_to_sdm_detail(group)` | `SdmGroupDetail` |
| `group_to_resilience_summary(group)` | `ResilienceGroupSummary` |
| `group_to_resilience_detail(group)` | `ResilienceGroupDetail` |
| `group_to_ropa_summary(group)` | `RopaGroupSummary` |
| `group_to_ropa_detail(group)` | `RopaGroupDetail` |
| `group_to_dpia_summary(group)` | `DpiaGroupSummary` |
| `group_to_dpia_detail(group)` | `DpiaGroupDetail` |

### Codelist Engine

**`CodelistRegistry`** — Central registry for standardized vocabularies.

- `CodelistRegistry.load_defaults() -> CodelistRegistry` — Load all built-in codelists.
- `registry.validate_code(codelist_name: str, code: str) -> bool` — Check if a code is valid.
- `registry.get_label(codelist_name: str, code: str, lang: str = "en") -> Optional[str]` — Get localized label.
- `registry.search(codelist_name: str, query: str) -> list[CodeEntry]` — Search codes by text.
- `registry.list_codes(codelist_name: str) -> list[CodeEntry]` — List all entries.

**`CascadeService`** — Cascading compliance impact evaluation.

- `CascadeService.load_defaults() -> CascadeService` — Load default cascade rules.
- `cascade.evaluate_impact(data_category: str, current_protection_level: str) -> list` — Evaluate compliance impacts.
- `cascade.suggest_changes(old_category: str, new_category: str) -> list` — Suggest protection changes.

**`TranslationOverlay`** — Multilingual label resolution.

- `TranslationOverlay.load_defaults() -> TranslationOverlay` — Load EN/DE/FR overlays.
- `overlay.get_label(codelist_name: str, code: str, lang: str) -> Optional[str]` — Get translated label.

**`export_genericode(codelist: Codelist) -> str`**
Export a Codelist to Genericode 1.0 XML.

**`import_genericode(xml_str: str) -> Codelist`**
Import a Codelist from Genericode 1.0 XML.

**`validate_codelist_props(catalog: Catalog, registry: CodelistRegistry) -> list`**
Validate that all codelist-referencing props in a catalog use valid codes.

**`create_codelist_prop(codelist_name: str, code: str) -> Property`**
Create an OSCAL Property for a codelist code.

### DiffService

**`OscalDiffService(*, ignore_paths: list[str] = None)`**
High-level diff service with file and catalog support.

- `svc.diff_files(old_path: Path, new_path: Path) -> OscalDiffResult` — Diff two JSON files.
- `svc.diff_catalogs(old: Catalog, new: Catalog) -> OscalDiffResult` — Diff two catalogs.
- `svc.format_diff_summary(result: OscalDiffResult) -> str` — Human-readable summary.

### DTOs

All DTOs inherit from `DtoBaseModel` with `ConfigDict(populate_by_name=True)` — snake_case fields + camelCase aliases. Use `model_dump(by_alias=True)` for JSON output.

| DTO | Module |
|-----|--------|
| `PrivacyControlSummary`, `PrivacyControlDetail` | `dto/privacy.py` |
| `PrivacyGroupSummary`, `PrivacyGroupDetail` | `dto/privacy.py` |
| `SdmControlSummary`, `SdmControlDetail` | `dto/sdm.py` |
| `SdmGroupSummary`, `SdmGroupDetail` | `dto/sdm.py` |
| `SdmTomControlSummary`, `SdmTomControlDetail` | `dto/sdm_tom.py` |
| `SecurityControl`, `SecurityControlUpdateRequest` | `dto/resilience.py` |
| `ResilienceGroupSummary`, `ResilienceGroupDetail` | `dto/resilience.py` |
| `SecurityControlRef`, `MappingStandards`, `SdmSecurityMapping` | `dto/mapping_workbench.py` |
| `RopaControlSummary`, `RopaControlDetail` | `dto/ropa.py` |
| `RopaGroupSummary`, `RopaGroupDetail` | `dto/ropa.py` |
| `DpiaControlSummary`, `DpiaControlDetail` | `dto/dpia.py` |
| `DpiaGroupSummary`, `DpiaGroupDetail` | `dto/dpia.py` |
| `MappingCoverageResult`, `TransitiveMappingPath` | `dto/mapping_coverage.py` |

### Legal Adapter

**`normalize_legal_from_text(control: Control, text: str) -> None`**
Parse and normalize a legal reference text into OSCAL props.

**`add_legal_id(control: Control, legal_id: str) -> None`**
Add a normalized legal ID property.

**`add_or_update_legal(control: Control, legal_id: str, **kwargs) -> None`**
Add or update a legal reference.

`LegalPropSpec` — Configuration for legal property mapping.
