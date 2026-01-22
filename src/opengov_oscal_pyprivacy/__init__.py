from .legal_adapter import LegalPropSpec, add_legal_id, add_or_update_legal, normalize_legal_from_text
from .domain.privacy_control import (
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
)

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
]
