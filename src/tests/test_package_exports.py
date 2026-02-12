"""Test that all public APIs are accessible from package-level imports (#17)."""
from __future__ import annotations


def test_domain_init_exports():
    """All domain functions importable from opengov_oscal_pyprivacy.domain."""
    from opengov_oscal_pyprivacy import domain

    expected = [
        "list_typical_measures", "add_typical_measure", "update_typical_measure", "delete_typical_measure",
        "list_assessment_questions", "add_assessment_question", "update_assessment_question", "delete_assessment_question",
        "set_statement", "set_risk_hint", "replace_risk_scenarios",
        "set_maturity_level_text", "get_maturity_level_text",
        "list_dp_goals", "replace_dp_goals",
        "extract_legal_articles", "extract_tom_id", "extract_statement",
        "extract_risk_hint", "extract_risk_scenarios", "extract_maturity_level_texts",
        "get_risk_impact_scenarios", "upsert_risk_impact_scenario", "delete_risk_impact_scenario",
        "extract_sdm_module", "extract_sdm_goals", "extract_dsgvo_articles",
        "extract_implementation_level", "extract_dp_risk_impact", "extract_related_mappings",
        "set_implementation_level", "set_dp_risk_impact", "replace_related_mappings",
        "extract_sdm_tom_description", "extract_sdm_tom_implementation_hints",
        "set_sdm_tom_description", "set_sdm_tom_implementation_hints",
        "extract_domain", "extract_objective", "extract_description",
        "set_domain", "set_objective", "set_description",
    ]
    for name in expected:
        assert hasattr(domain, name), f"domain.{name} not exported"


def test_converters_init_exports():
    """All converter functions importable from opengov_oscal_pyprivacy.converters."""
    from opengov_oscal_pyprivacy import converters

    expected = [
        "control_to_privacy_summary", "control_to_privacy_detail",
        "group_to_privacy_summary", "group_to_privacy_detail",
        "control_to_sdm_summary", "control_to_sdm_detail",
        "control_to_sdm_tom_summary", "control_to_sdm_tom_detail",
        "control_to_security_control",
    ]
    for name in expected:
        assert hasattr(converters, name), f"converters.{name} not exported"


def test_top_level_exports_converters():
    """Converter functions importable from top-level opengov_oscal_pyprivacy."""
    import opengov_oscal_pyprivacy as pkg

    expected = [
        "control_to_privacy_summary", "control_to_privacy_detail",
        "group_to_privacy_summary", "group_to_privacy_detail",
        "control_to_sdm_summary", "control_to_sdm_detail",
        "control_to_sdm_tom_summary", "control_to_sdm_tom_detail",
        "control_to_security_control",
    ]
    for name in expected:
        assert hasattr(pkg, name), f"opengov_oscal_pyprivacy.{name} not exported"
        assert name in pkg.__all__, f"{name} not in __all__"
