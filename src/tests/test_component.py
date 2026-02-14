from __future__ import annotations

"""Tests for OSCAL ComponentDefinition models (#45)."""

import json
from pathlib import Path

import pytest

from opengov_oscal_pycore.models_component import (
    ComponentDefinition,
    Component,
    Capability,
    ControlImplementation,
    ImplementedRequirement,
)

TEST_DATA_DIR = Path(__file__).parent / "data"
FIXTURE_FILE = TEST_DATA_DIR / "test_component_definition.json"


@pytest.fixture(scope="module")
def comp_def_data() -> dict:
    """Load the raw JSON fixture."""
    return json.loads(FIXTURE_FILE.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def comp_def(comp_def_data: dict) -> ComponentDefinition:
    """Parse the fixture into a ComponentDefinition model."""
    return ComponentDefinition.model_validate(comp_def_data)


# ---------- Load test ----------


class TestComponentDefinitionLoad:
    def test_load_from_fixture(self, comp_def: ComponentDefinition):
        """ComponentDefinition loads successfully from JSON fixture."""
        assert comp_def.uuid == "b2c3d4e5-f6a7-8901-bcde-f12345678901"
        assert comp_def.metadata.title == "Test Privacy Component Definition"

    def test_metadata_fields(self, comp_def: ComponentDefinition):
        """Typed OscalMetadata fields are accessible."""
        assert comp_def.metadata.version == "1.0.0"
        assert comp_def.metadata.oscal_version == "1.1.2"
        assert comp_def.metadata.last_modified == "2026-01-01T00:00:00Z"


# ---------- Round-trip test ----------


class TestComponentDefinitionRoundTrip:
    def test_dump_and_reload(self, comp_def: ComponentDefinition):
        """Serialize to dict (by_alias) and reload — values must survive."""
        dumped = comp_def.model_dump(by_alias=True)
        reloaded = ComponentDefinition.model_validate(dumped)
        assert reloaded.uuid == comp_def.uuid
        assert reloaded.metadata.title == comp_def.metadata.title
        assert len(reloaded.components) == len(comp_def.components)
        assert len(reloaded.capabilities) == len(comp_def.capabilities)

    def test_json_round_trip(self, comp_def: ComponentDefinition):
        """JSON string round-trip preserves data."""
        json_str = comp_def.model_dump_json(by_alias=True)
        reloaded = ComponentDefinition.model_validate_json(json_str)
        assert reloaded.uuid == comp_def.uuid
        assert reloaded.components[0].title == comp_def.components[0].title


# ---------- Unwrap root test ----------


class TestUnwrapRoot:
    def test_wrapped_form(self, comp_def_data: dict):
        """{'component-definition': {...}} is unwrapped automatically."""
        assert "component-definition" in comp_def_data
        cd = ComponentDefinition.model_validate(comp_def_data)
        assert cd.uuid == "b2c3d4e5-f6a7-8901-bcde-f12345678901"

    def test_bare_form(self, comp_def_data: dict):
        """Bare form (without wrapper key) also works."""
        inner = comp_def_data["component-definition"]
        cd = ComponentDefinition.model_validate(inner)
        assert cd.uuid == "b2c3d4e5-f6a7-8901-bcde-f12345678901"


# ---------- Component access ----------


class TestComponentAccess:
    def test_component_count(self, comp_def: ComponentDefinition):
        assert len(comp_def.components) == 1

    def test_component_fields(self, comp_def: ComponentDefinition):
        comp = comp_def.components[0]
        assert comp.uuid == "c3d4e5f6-a7b8-9012-cdef-123456789012"
        assert comp.type == "software"
        assert comp.title == "Privacy Management System"
        assert comp.description == "Software component implementing privacy controls"

    def test_component_props(self, comp_def: ComponentDefinition):
        """Component props are accessible as Property objects."""
        comp = comp_def.components[0]
        assert len(comp.props) == 1
        assert comp.props[0].name == "vendor"
        assert comp.props[0].value == "OpenGov"

    def test_component_links_default_empty(self):
        """Component with no links has an empty list."""
        comp = Component(uuid="x", type="software", title="X")
        assert comp.links == []


# ---------- ControlImplementation access ----------


class TestControlImplementationAccess:
    def test_control_implementations(self, comp_def: ComponentDefinition):
        comp = comp_def.components[0]
        assert len(comp.control_implementations) == 1
        ci = comp.control_implementations[0]
        assert ci.uuid == "d4e5f6a7-b8c9-0123-def0-234567890123"
        assert ci.source == "catalogs/privacy.json"
        assert ci.description == "Privacy control implementations"

    def test_implemented_requirements(self, comp_def: ComponentDefinition):
        ci = comp_def.components[0].control_implementations[0]
        assert len(ci.implemented_requirements) == 2
        ir0 = ci.implemented_requirements[0]
        assert ir0.uuid == "e5f6a7b8-c9d0-1234-ef01-345678901234"
        assert ir0.control_id == "GOV-01"
        assert ir0.description == "Implemented via automated governance workflow"


# ---------- Capability access ----------


class TestCapabilityAccess:
    def test_capability_count(self, comp_def: ComponentDefinition):
        assert len(comp_def.capabilities) == 1

    def test_capability_fields(self, comp_def: ComponentDefinition):
        cap = comp_def.capabilities[0]
        assert cap.uuid == "a7b8c9d0-e1f2-3456-0123-567890123456"
        assert cap.name == "Privacy Compliance"
        assert cap.description == "Provides privacy compliance capabilities"

    def test_capability_props(self, comp_def: ComponentDefinition):
        cap = comp_def.capabilities[0]
        assert len(cap.props) == 1
        assert cap.props[0].name == "scope"
        assert cap.props[0].value == "DSGVO"


# ---------- Alias tests ----------


class TestAliases:
    def test_control_id_alias(self):
        """ImplementedRequirement accepts 'control-id' alias."""
        ir = ImplementedRequirement.model_validate({
            "uuid": "test",
            "control-id": "AC-01",
        })
        assert ir.control_id == "AC-01"

    def test_implemented_requirements_alias(self):
        """ControlImplementation accepts 'implemented-requirements' alias."""
        ci = ControlImplementation.model_validate({
            "uuid": "test",
            "source": "cat.json",
            "implemented-requirements": [
                {"uuid": "ir1", "control-id": "AC-01"}
            ],
        })
        assert len(ci.implemented_requirements) == 1

    def test_control_implementations_alias(self):
        """Component accepts 'control-implementations' alias."""
        comp = Component.model_validate({
            "uuid": "test",
            "type": "software",
            "title": "Test",
            "control-implementations": [
                {"uuid": "ci1", "source": "cat.json"}
            ],
        })
        assert len(comp.control_implementations) == 1

    def test_back_matter_alias(self):
        """ComponentDefinition accepts 'back-matter' alias."""
        cd = ComponentDefinition.model_validate({
            "uuid": "test",
            "metadata": {"title": "Test"},
            "back-matter": {"resources": []},
        })
        assert cd.back_matter is not None
        assert cd.back_matter.resources == []

    def test_aliases_in_dump(self, comp_def: ComponentDefinition):
        """Dumping with by_alias=True produces hyphenated OSCAL keys."""
        dumped = comp_def.model_dump(by_alias=True)
        comp = dumped["components"][0]
        assert "control-implementations" in comp
        ci = comp["control-implementations"][0]
        assert "implemented-requirements" in ci
        ir = ci["implemented-requirements"][0]
        assert "control-id" in ir


# ---------- Empty defaults ----------


class TestEmptyDefaults:
    def test_empty_components_list(self):
        cd = ComponentDefinition.model_validate({
            "uuid": "test",
            "metadata": {"title": "Test"},
        })
        assert cd.components == []
        assert cd.capabilities == []
        assert cd.back_matter is None

    def test_empty_control_implementations(self):
        comp = Component(uuid="x", type="software", title="X")
        assert comp.control_implementations == []

    def test_empty_implemented_requirements(self):
        ci = ControlImplementation(uuid="x", source="cat.json")
        assert ci.implemented_requirements == []


# ---------- Extra fields (round-trip safety) ----------


class TestExtraFields:
    def test_extra_fields_survive_round_trip(self):
        """Unknown fields survive load/dump (extra='allow')."""
        data = {
            "uuid": "test",
            "metadata": {"title": "Test"},
            "custom-extension": {"foo": "bar"},
        }
        cd = ComponentDefinition.model_validate(data)
        dumped = cd.model_dump(by_alias=True)
        assert dumped["custom-extension"] == {"foo": "bar"}

    def test_component_extra_fields(self):
        data = {
            "uuid": "x",
            "type": "software",
            "title": "X",
            "x-custom": 42,
        }
        comp = Component.model_validate(data)
        dumped = comp.model_dump(by_alias=True)
        assert dumped["x-custom"] == 42

    def test_implemented_requirement_extra_fields(self):
        data = {
            "uuid": "ir1",
            "control-id": "AC-01",
            "responsible-roles": [{"role-id": "admin"}],
        }
        ir = ImplementedRequirement.model_validate(data)
        dumped = ir.model_dump(by_alias=True)
        assert dumped["responsible-roles"] == [{"role-id": "admin"}]
