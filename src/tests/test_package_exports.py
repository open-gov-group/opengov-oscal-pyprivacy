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


def test_pycore_exports_complete():
    """All pycore public API functions and classes are importable from the top-level package."""
    import opengov_oscal_pycore as pycore

    # Models
    assert hasattr(pycore, "Catalog")
    assert hasattr(pycore, "Group")
    assert hasattr(pycore, "Control")
    assert hasattr(pycore, "Property")
    assert hasattr(pycore, "Link")
    assert hasattr(pycore, "Part")
    assert hasattr(pycore, "OscalMetadata")
    assert hasattr(pycore, "Role")
    assert hasattr(pycore, "Party")
    assert hasattr(pycore, "BackMatter")
    assert hasattr(pycore, "Resource")
    assert hasattr(pycore, "Rlink")

    # Repository
    assert hasattr(pycore, "OscalRepository")

    # Catalog CRUD (existing + new)
    assert hasattr(pycore, "iter_controls")
    assert hasattr(pycore, "iter_controls_with_group")
    assert hasattr(pycore, "find_controls_by_prop")
    assert hasattr(pycore, "find_control")
    assert hasattr(pycore, "find_group")
    assert hasattr(pycore, "add_control")
    assert hasattr(pycore, "delete_control")
    assert hasattr(pycore, "set_control_prop")
    assert hasattr(pycore, "add_group")
    assert hasattr(pycore, "delete_group")
    assert hasattr(pycore, "update_group_title")
    assert hasattr(pycore, "move_control")

    # Props CRUD
    assert hasattr(pycore, "list_props")
    assert hasattr(pycore, "find_props")
    assert hasattr(pycore, "get_prop_v2")
    assert hasattr(pycore, "upsert_prop")
    assert hasattr(pycore, "remove_props")

    # Parts CRUD
    assert hasattr(pycore, "parts_ref")
    assert hasattr(pycore, "find_part")
    assert hasattr(pycore, "ensure_part_container")
    assert hasattr(pycore, "remove_part")
    assert hasattr(pycore, "list_child_parts")
    assert hasattr(pycore, "add_child_part")
    assert hasattr(pycore, "update_child_part")
    assert hasattr(pycore, "delete_child_part")

    # Links CRUD
    assert hasattr(pycore, "list_links")
    assert hasattr(pycore, "find_links")
    assert hasattr(pycore, "get_link")
    assert hasattr(pycore, "upsert_link")
    assert hasattr(pycore, "remove_links")

    # Back-matter CRUD
    assert hasattr(pycore, "find_resource")
    assert hasattr(pycore, "add_resource")
    assert hasattr(pycore, "remove_resource")

    # Versioning
    assert hasattr(pycore, "touch_metadata")
    assert hasattr(pycore, "bump_version")

    # Validation
    assert hasattr(pycore, "ValidationIssue")
    assert hasattr(pycore, "validate_catalog")
    assert hasattr(pycore, "validate_metadata")
    assert hasattr(pycore, "validate_unique_ids")
    assert hasattr(pycore, "validate_control")

    # Verify __all__ is complete
    for name in pycore.__all__:
        assert hasattr(pycore, name), f"{name} in __all__ but not importable"
