from .legal_adapter import LegalPropSpec, add_legal_id, add_or_update_legal, normalize_legal_from_text
from .domain.privacy_control import (
    get_risk_impact_scenarios,
    upsert_risk_impact_scenario,
    delete_risk_impact_scenario,

    list_typical_measures,
    add_typical_measure,
    update_typical_measure,
    delete_typical_measure,
    list_assessment_questions,
    add_assessment_question,
    update_assessment_question,
    delete_assessment_question,
    set_statement,
    set_risk_hint,
    replace_risk_scenarios,
    set_maturity_level_text,
    get_maturity_level_text,
    list_dp_goals,
    replace_dp_goals,

    # extract helpers (#7)
    extract_legal_articles,
    extract_tom_id,
    extract_statement,
    extract_risk_hint,
    extract_risk_scenarios,
    extract_maturity_level_texts,

    # extract helpers (#27)
    extract_evidence_artifacts,
    extract_maturity_domain,
    extract_maturity_requirement,
    extract_measure_category,
)
from .domain.sdm_catalog import (
    extract_sdm_module,
    extract_sdm_goals,
    extract_dsgvo_articles,
    extract_implementation_level,
    extract_dp_risk_impact,
    extract_related_mappings,
    set_implementation_level,
    set_dp_risk_impact,
    replace_related_mappings,
    extract_sdm_tom_description,
    extract_sdm_tom_implementation_hints,
    set_sdm_tom_description,
    set_sdm_tom_implementation_hints,
)
from .domain.query import (
    find_controls_by_tom_id,
    find_controls_by_implementation_level,
    find_controls_by_legal_article,
    find_controls_by_evidence,
    find_controls_by_maturity_domain,
)
from .domain.resilience_catalog import (
    extract_domain,
    extract_objective,
    extract_description,
    set_domain,
    set_objective,
    set_description,
)
from .converters import (
    control_to_privacy_summary,
    control_to_privacy_detail,
    group_to_privacy_summary,
    group_to_privacy_detail,
    control_to_sdm_summary,
    control_to_sdm_detail,
    control_to_sdm_tom_summary,
    control_to_sdm_tom_detail,
    control_to_security_control,
    control_to_ropa_summary,
    control_to_ropa_detail,
    group_to_ropa_summary,
    group_to_ropa_detail,
    control_to_dpia_summary,
    control_to_dpia_detail,
    group_to_dpia_summary,
    group_to_dpia_detail,
)
# Profile domain (#42)
from .domain.profile import (
    resolve_profile_imports,
    build_profile_from_controls,
    add_profile_import,
)
# SSP domain (#44)
from .domain.ssp import (
    generate_implemented_requirements,
    attach_evidence_to_ssp,
    get_import_profile_href,
)
# Mapping domain (#43)
from .domain.mapping import (
    list_mappings,
    get_mapping,
    upsert_mapping,
    delete_mapping,
    calculate_mapping_coverage,
    resolve_transitive_mappings,
)
# DiffService (#46)
from .services.diff_service import OscalDiffService

__all__ = [
    "LegalPropSpec",
    "add_legal_id",
    "add_or_update_legal",
    "normalize_legal_from_text",
    # parts field-sets
    "list_typical_measures",
    "add_typical_measure",
    "update_typical_measure",
    "delete_typical_measure",
    "list_assessment_questions",
    "add_assessment_question",
    "update_assessment_question",
    "delete_assessment_question",
    "set_statement",
    "set_risk_hint",
    "replace_risk_scenarios",
    "set_maturity_level_text",
    "get_maturity_level_text",
    # props field-sets
    "list_dp_goals",
    "replace_dp_goals",
    # risk guidance
    "get_risk_impact_scenarios",
    "upsert_risk_impact_scenario",
    "delete_risk_impact_scenario",
    # extract helpers (#7)
    "extract_legal_articles",
    "extract_tom_id",
    "extract_statement",
    "extract_risk_hint",
    "extract_risk_scenarios",
    "extract_maturity_level_texts",
    # extract helpers (#27)
    "extract_evidence_artifacts",
    "extract_maturity_domain",
    "extract_maturity_requirement",
    "extract_measure_category",
    # SDM catalog domain (#3)
    "extract_sdm_module",
    "extract_sdm_goals",
    "extract_dsgvo_articles",
    "extract_implementation_level",
    "extract_dp_risk_impact",
    "extract_related_mappings",
    "set_implementation_level",
    "set_dp_risk_impact",
    "replace_related_mappings",
    "extract_sdm_tom_description",
    "extract_sdm_tom_implementation_hints",
    "set_sdm_tom_description",
    "set_sdm_tom_implementation_hints",
    # resilience catalog domain (#4)
    "extract_domain",
    "extract_objective",
    "extract_description",
    "set_domain",
    "set_objective",
    "set_description",
    # query helpers (#18)
    "find_controls_by_tom_id",
    "find_controls_by_implementation_level",
    "find_controls_by_legal_article",
    # query helpers (#30)
    "find_controls_by_evidence",
    "find_controls_by_maturity_domain",
    # converters (#14-#16)
    "control_to_privacy_summary",
    "control_to_privacy_detail",
    "group_to_privacy_summary",
    "group_to_privacy_detail",
    "control_to_sdm_summary",
    "control_to_sdm_detail",
    "control_to_sdm_tom_summary",
    "control_to_sdm_tom_detail",
    "control_to_security_control",
    # ROPA converters (#28)
    "control_to_ropa_summary",
    "control_to_ropa_detail",
    "group_to_ropa_summary",
    "group_to_ropa_detail",
    # DPIA converters (#29)
    "control_to_dpia_summary",
    "control_to_dpia_detail",
    "group_to_dpia_summary",
    "group_to_dpia_detail",
    # Profile domain (#42)
    "resolve_profile_imports",
    "build_profile_from_controls",
    "add_profile_import",
    # SSP domain (#44)
    "generate_implemented_requirements",
    "attach_evidence_to_ssp",
    "get_import_profile_href",
    # Mapping domain (#43)
    "list_mappings",
    "get_mapping",
    "upsert_mapping",
    "delete_mapping",
    "calculate_mapping_coverage",
    "resolve_transitive_mappings",
    # DiffService (#46)
    "OscalDiffService",
]
