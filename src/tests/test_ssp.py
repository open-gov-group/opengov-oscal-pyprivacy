from __future__ import annotations

"""
Tests for OSCAL System Security Plan (SSP) model and domain operations (Issue #44).

Covers:
  - SystemSecurityPlan / SspImplementedRequirement / SspControlImplementation model
  - Root-unwrapping validator
  - Alias handling for hyphenated OSCAL keys
  - ImportProfile, SystemCharacteristics access
  - generate_implemented_requirements
  - attach_evidence_to_ssp
  - get_import_profile_href
  - Extra-field round-trip safety
  - Empty defaults
"""

import json
from pathlib import Path

import pytest

from opengov_oscal_pycore.models import (
    Catalog,
    OscalMetadata,
    BackMatter,
    Resource,
    Rlink,
    Property,
    Link,
)
from opengov_oscal_pycore.models_ssp import (
    SystemSecurityPlan,
    SspImplementedRequirement,
    SspControlImplementation,
    SystemCharacteristics,
    ImportProfile,
)

from opengov_oscal_pyprivacy.domain.ssp import (
    generate_implemented_requirements,
    attach_evidence_to_ssp,
    get_import_profile_href,
)

DATA_DIR = Path(__file__).parent / "data"


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture(scope="module")
def ssp_json() -> dict:
    """Load the raw SSP JSON fixture."""
    return json.loads((DATA_DIR / "test_ssp.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def ssp(ssp_json: dict) -> SystemSecurityPlan:
    """Parse the SSP fixture into a SystemSecurityPlan model."""
    return SystemSecurityPlan.model_validate(ssp_json)


@pytest.fixture(scope="module")
def catalog() -> Catalog:
    """Load the privacy catalog fixture."""
    with open(DATA_DIR / "open_privacy_catalog_risk.json") as f:
        return Catalog(**json.load(f))


# ============================================================================
# Load test
# ============================================================================


class TestSspLoad:
    """Loading SSP from JSON fixture."""

    def test_load_from_fixture(self, ssp: SystemSecurityPlan) -> None:
        """SSP loads correctly from the test fixture."""
        assert ssp.uuid == "d1e2f3a4-b5c6-7890-d1e2-f3a4b5c67890"
        assert ssp.metadata.title == "Test Privacy SSP"

    def test_metadata_is_typed(self, ssp: SystemSecurityPlan) -> None:
        """Metadata is OscalMetadata, not a plain dict."""
        assert isinstance(ssp.metadata, OscalMetadata)
        assert ssp.metadata.version == "1.0.0"
        assert ssp.metadata.oscal_version == "1.1.2"
        assert ssp.metadata.last_modified == "2026-01-01T00:00:00Z"


# ============================================================================
# Round-trip test
# ============================================================================


class TestSspRoundTrip:
    """Serialize to dict (by_alias) and reload -- values must survive."""

    def test_dump_and_reload(self, ssp: SystemSecurityPlan) -> None:
        """Dict round-trip preserves data."""
        dumped = ssp.model_dump(by_alias=True)
        reloaded = SystemSecurityPlan.model_validate(dumped)
        assert reloaded.uuid == ssp.uuid
        assert reloaded.metadata.title == ssp.metadata.title
        assert reloaded.import_profile.href == ssp.import_profile.href
        assert (
            len(reloaded.control_implementation.implemented_requirements)
            == len(ssp.control_implementation.implemented_requirements)
        )

    def test_json_round_trip(self, ssp: SystemSecurityPlan) -> None:
        """JSON string round-trip preserves data."""
        json_str = ssp.model_dump_json(by_alias=True)
        reloaded = SystemSecurityPlan.model_validate_json(json_str)
        assert reloaded.uuid == ssp.uuid
        assert reloaded.system_characteristics.system_name == ssp.system_characteristics.system_name


# ============================================================================
# Unwrap root test
# ============================================================================


class TestUnwrapRoot:
    """Root-unwrapping validator for SSP."""

    def test_wrapped_form(self, ssp_json: dict) -> None:
        """{'system-security-plan': {...}} is unwrapped automatically."""
        assert "system-security-plan" in ssp_json
        parsed = SystemSecurityPlan.model_validate(ssp_json)
        assert parsed.uuid == "d1e2f3a4-b5c6-7890-d1e2-f3a4b5c67890"

    def test_bare_form(self, ssp_json: dict) -> None:
        """Bare form (without wrapper key) also works."""
        inner = ssp_json["system-security-plan"]
        parsed = SystemSecurityPlan.model_validate(inner)
        assert parsed.uuid == "d1e2f3a4-b5c6-7890-d1e2-f3a4b5c67890"


# ============================================================================
# Alias tests
# ============================================================================


class TestAliases:
    """Verify that hyphenated OSCAL aliases work correctly."""

    def test_import_profile_alias(self, ssp: SystemSecurityPlan) -> None:
        """import-profile alias serializes correctly."""
        dumped = ssp.model_dump(by_alias=True)
        assert "import-profile" in dumped
        assert "import_profile" not in dumped

    def test_system_characteristics_alias(self, ssp: SystemSecurityPlan) -> None:
        """system-characteristics alias serializes correctly."""
        dumped = ssp.model_dump(by_alias=True)
        assert "system-characteristics" in dumped
        assert "system_characteristics" not in dumped

    def test_control_implementation_alias(self, ssp: SystemSecurityPlan) -> None:
        """control-implementation alias serializes correctly."""
        dumped = ssp.model_dump(by_alias=True)
        assert "control-implementation" in dumped
        assert "control_implementation" not in dumped

    def test_implemented_requirements_alias(self, ssp: SystemSecurityPlan) -> None:
        """implemented-requirements alias serializes correctly."""
        dumped = ssp.model_dump(by_alias=True)
        ci = dumped["control-implementation"]
        assert "implemented-requirements" in ci
        assert "implemented_requirements" not in ci

    def test_control_id_alias(self) -> None:
        """SspImplementedRequirement accepts 'control-id' alias."""
        ir = SspImplementedRequirement.model_validate({
            "uuid": "test",
            "control-id": "AC-01",
        })
        assert ir.control_id == "AC-01"

    def test_system_name_alias(self, ssp: SystemSecurityPlan) -> None:
        """system-name alias serializes correctly."""
        dumped = ssp.system_characteristics.model_dump(by_alias=True)
        assert "system-name" in dumped
        assert "system_name" not in dumped

    def test_security_sensitivity_level_alias(self, ssp: SystemSecurityPlan) -> None:
        """security-sensitivity-level alias serializes correctly."""
        dumped = ssp.system_characteristics.model_dump(by_alias=True)
        assert "security-sensitivity-level" in dumped
        assert "security_sensitivity_level" not in dumped

    def test_back_matter_alias(self, ssp: SystemSecurityPlan) -> None:
        """back-matter alias serializes correctly."""
        dumped = ssp.model_dump(by_alias=True)
        assert "back-matter" in dumped
        assert "back_matter" not in dumped


# ============================================================================
# ImportProfile access
# ============================================================================


class TestImportProfileAccess:
    """ImportProfile field access."""

    def test_href_accessible(self, ssp: SystemSecurityPlan) -> None:
        """ImportProfile href is accessible."""
        assert isinstance(ssp.import_profile, ImportProfile)
        assert ssp.import_profile.href == "profiles/privacy-profile.json"


# ============================================================================
# SystemCharacteristics access
# ============================================================================


class TestSystemCharacteristicsAccess:
    """SystemCharacteristics field access."""

    def test_system_name(self, ssp: SystemSecurityPlan) -> None:
        """system_name is accessible."""
        assert ssp.system_characteristics.system_name == "Privacy Management System"

    def test_description(self, ssp: SystemSecurityPlan) -> None:
        """description is accessible."""
        assert ssp.system_characteristics.description == "System for managing privacy controls"

    def test_security_sensitivity_level(self, ssp: SystemSecurityPlan) -> None:
        """security_sensitivity_level is accessible."""
        assert ssp.system_characteristics.security_sensitivity_level == "moderate"

    def test_system_ids(self, ssp: SystemSecurityPlan) -> None:
        """system_ids are accessible."""
        assert len(ssp.system_characteristics.system_ids) == 1
        assert ssp.system_characteristics.system_ids[0]["id"] == "PMS-001"

    def test_props(self, ssp: SystemSecurityPlan) -> None:
        """Props are accessible as Property objects."""
        assert len(ssp.system_characteristics.props) == 1
        assert ssp.system_characteristics.props[0].name == "deployment-model"
        assert ssp.system_characteristics.props[0].value == "on-premise"


# ============================================================================
# ControlImplementation access
# ============================================================================


class TestControlImplementationAccess:
    """SspControlImplementation field access."""

    def test_implemented_requirements_count(self, ssp: SystemSecurityPlan) -> None:
        """implemented_requirements list is accessible."""
        assert ssp.control_implementation is not None
        assert len(ssp.control_implementation.implemented_requirements) == 2

    def test_description(self, ssp: SystemSecurityPlan) -> None:
        """description is accessible."""
        assert ssp.control_implementation.description == "Privacy control implementations"


# ============================================================================
# SspImplementedRequirement access
# ============================================================================


class TestSspImplementedRequirementAccess:
    """SspImplementedRequirement field access."""

    def test_control_id(self, ssp: SystemSecurityPlan) -> None:
        """control_id is accessible."""
        ir = ssp.control_implementation.implemented_requirements[0]
        assert ir.control_id == "GOV-01"

    def test_uuid(self, ssp: SystemSecurityPlan) -> None:
        """uuid is accessible."""
        ir = ssp.control_implementation.implemented_requirements[0]
        assert ir.uuid == "e2f3a4b5-c6d7-8901-e2f3-a4b5c6d78901"

    def test_props(self, ssp: SystemSecurityPlan) -> None:
        """Props are accessible as Property objects."""
        ir = ssp.control_implementation.implemented_requirements[0]
        assert len(ir.props) == 1
        assert ir.props[0].name == "implementation-status"
        assert ir.props[0].value == "implemented"

    def test_statements(self, ssp: SystemSecurityPlan) -> None:
        """Statements are accessible."""
        ir = ssp.control_implementation.implemented_requirements[1]
        assert len(ir.statements) == 1
        assert ir.statements[0]["statement-id"] == "GOV-02.a"

    def test_links_default_empty(self) -> None:
        """IR with no links has an empty list."""
        ir = SspImplementedRequirement(uuid="x", control_id="AC-01")
        assert ir.links == []


# ============================================================================
# generate_implemented_requirements
# ============================================================================


class TestGenerateImplementedRequirements:
    """Tests for generate_implemented_requirements."""

    def test_generates_for_all_controls(self, catalog: Catalog) -> None:
        """One IR stub per control in the catalog."""
        from opengov_oscal_pycore.crud_catalog import iter_controls

        expected_ids = [c.id for c in iter_controls(catalog)]
        reqs = generate_implemented_requirements(catalog)

        generated_ids = [r.control_id for r in reqs]
        assert len(reqs) == len(expected_ids)
        for cid in expected_ids:
            assert cid in generated_ids

    def test_uuids_are_deterministic(self, catalog: Catalog) -> None:
        """Same catalog produces same UUIDs each time."""
        reqs1 = generate_implemented_requirements(catalog)
        reqs2 = generate_implemented_requirements(catalog)
        for r1, r2 in zip(reqs1, reqs2):
            assert r1.uuid == r2.uuid

    def test_uuids_are_valid(self, catalog: Catalog) -> None:
        """Generated UUIDs are valid UUID strings."""
        import uuid

        reqs = generate_implemented_requirements(catalog)
        for r in reqs:
            parsed = uuid.UUID(r.uuid)
            assert str(parsed) == r.uuid

    def test_descriptions_are_empty(self, catalog: Catalog) -> None:
        """Generated stubs have empty description (to be filled by implementer)."""
        reqs = generate_implemented_requirements(catalog)
        for r in reqs:
            assert r.description == ""


# ============================================================================
# attach_evidence_to_ssp
# ============================================================================


class TestAttachEvidenceToSsp:
    """Tests for attach_evidence_to_ssp."""

    def _make_ssp(self) -> SystemSecurityPlan:
        """Create a minimal SSP for testing."""
        return SystemSecurityPlan(
            uuid="test-ssp",
            metadata=OscalMetadata(title="Test"),
            import_profile=ImportProfile(href="profile.json"),
            control_implementation=SspControlImplementation(
                description="Test CI",
                implemented_requirements=[
                    SspImplementedRequirement(
                        uuid="ir-1",
                        control_id="GOV-01",
                        description="Test IR",
                    ),
                ],
            ),
        )

    def test_adds_resource_to_back_matter(self) -> None:
        """Resource is added to SSP's back_matter."""
        ssp = self._make_ssp()
        resource = Resource(
            uuid="evidence-1",
            title="Test Evidence",
            rlinks=[Rlink(href="evidence/test.pdf", media_type="application/pdf")],
        )

        attach_evidence_to_ssp(ssp, resource)

        assert ssp.back_matter is not None
        assert len(ssp.back_matter.resources) == 1
        assert ssp.back_matter.resources[0].uuid == "evidence-1"

    def test_creates_back_matter_if_none(self) -> None:
        """back_matter is created if it does not exist."""
        ssp = self._make_ssp()
        assert ssp.back_matter is None

        resource = Resource(uuid="ev-1", title="E1")
        attach_evidence_to_ssp(ssp, resource)

        assert ssp.back_matter is not None

    def test_links_resource_to_matching_ir(self) -> None:
        """When statement_control_id is given, a link is added to the matching IR."""
        ssp = self._make_ssp()
        resource = Resource(uuid="ev-2", title="E2")

        attach_evidence_to_ssp(ssp, resource, statement_control_id="GOV-01")

        ir = ssp.control_implementation.implemented_requirements[0]
        assert len(ir.links) == 1
        assert ir.links[0].href == "#ev-2"
        assert ir.links[0].rel == "evidence"

    def test_no_link_when_control_id_not_found(self) -> None:
        """No link is added when control ID does not match any IR."""
        ssp = self._make_ssp()
        resource = Resource(uuid="ev-3", title="E3")

        attach_evidence_to_ssp(ssp, resource, statement_control_id="NONEXISTENT")

        ir = ssp.control_implementation.implemented_requirements[0]
        assert len(ir.links) == 0

    def test_no_link_when_no_control_id(self) -> None:
        """No link is added when statement_control_id is not given."""
        ssp = self._make_ssp()
        resource = Resource(uuid="ev-4", title="E4")

        attach_evidence_to_ssp(ssp, resource)

        ir = ssp.control_implementation.implemented_requirements[0]
        assert len(ir.links) == 0


# ============================================================================
# get_import_profile_href
# ============================================================================


class TestGetImportProfileHref:
    """Tests for get_import_profile_href."""

    def test_returns_href(self, ssp: SystemSecurityPlan) -> None:
        """Returns the profile href from the SSP."""
        assert get_import_profile_href(ssp) == "profiles/privacy-profile.json"


# ============================================================================
# Extra fields (round-trip safety)
# ============================================================================


class TestExtraFields:
    """OscalBaseModel extra='allow' preserves unknown fields."""

    def test_ssp_extra_fields(self) -> None:
        """Unknown fields on SystemSecurityPlan survive round-trip."""
        data = {
            "uuid": "extra-test",
            "metadata": {"title": "Extra Test"},
            "import-profile": {"href": "test.json"},
            "custom-extension": {"foo": "bar"},
        }
        parsed = SystemSecurityPlan.model_validate(data)
        dumped = parsed.model_dump(by_alias=True)
        assert dumped["custom-extension"] == {"foo": "bar"}

    def test_ir_extra_fields(self) -> None:
        """Unknown fields on SspImplementedRequirement survive round-trip."""
        data = {
            "uuid": "ir-extra",
            "control-id": "AC-01",
            "responsible-roles": [{"role-id": "admin"}],
        }
        ir = SspImplementedRequirement.model_validate(data)
        dumped = ir.model_dump(by_alias=True)
        assert dumped["responsible-roles"] == [{"role-id": "admin"}]

    def test_import_profile_extra_fields(self) -> None:
        """Unknown fields on ImportProfile survive round-trip."""
        data = {
            "href": "profile.json",
            "x-custom": True,
        }
        ip = ImportProfile.model_validate(data)
        dumped = ip.model_dump(by_alias=True)
        assert dumped["x-custom"] is True


# ============================================================================
# Empty defaults
# ============================================================================


class TestEmptyDefaults:
    """SSP with minimal fields uses correct defaults."""

    def test_minimal_ssp(self) -> None:
        """SSP with only required fields has correct defaults."""
        ssp = SystemSecurityPlan(
            uuid="minimal",
            metadata=OscalMetadata(title="Minimal"),
            import_profile=ImportProfile(href="p.json"),
        )
        assert ssp.system_characteristics is None
        assert ssp.control_implementation is None
        assert ssp.back_matter is None

    def test_empty_control_implementation(self) -> None:
        """SspControlImplementation with no IRs has empty list."""
        ci = SspControlImplementation()
        assert ci.implemented_requirements == []
        assert ci.description is None

    def test_empty_system_characteristics(self) -> None:
        """SystemCharacteristics with no fields has correct defaults."""
        sc = SystemCharacteristics()
        assert sc.system_name is None
        assert sc.description is None
        assert sc.security_sensitivity_level is None
        assert sc.system_ids == []
        assert sc.props == []
