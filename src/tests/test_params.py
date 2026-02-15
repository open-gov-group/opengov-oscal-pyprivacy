"""Tests for the typed Parameter model and params CRUD operations (#49)."""
from __future__ import annotations

import pytest

from opengov_oscal_pycore.models import Parameter, Control, Property, Link
from opengov_oscal_pycore.crud.params import (
    list_params,
    find_params,
    get_param,
    upsert_param,
    remove_param,
)


# ---------------------------------------------------------------------------
# Parameter model tests
# ---------------------------------------------------------------------------


class TestParameterModel:
    """Tests for the Parameter Pydantic model."""

    def test_parameter_all_fields(self):
        """Create a Parameter with all fields and verify access."""
        p = Parameter(
            id="p-1",
            label="Frequency",
            class_="sp800-53",
            usage="Select one value",
            values=["daily", "weekly"],
            select={"how-many": "one", "choice": ["daily", "weekly", "monthly"]},
            constraints=[{"description": "Must be a valid period"}],
            guidelines=[{"prose": "Choose the frequency of scans."}],
            props=[Property(name="sort-id", value="01")],
            links=[Link(href="#ref-1", rel="reference")],
        )
        assert p.id == "p-1"
        assert p.label == "Frequency"
        assert p.class_ == "sp800-53"
        assert p.usage == "Select one value"
        assert p.values == ["daily", "weekly"]
        assert p.select == {"how-many": "one", "choice": ["daily", "weekly", "monthly"]}
        assert len(p.constraints) == 1
        assert len(p.guidelines) == 1
        assert len(p.props) == 1
        assert p.props[0].name == "sort-id"
        assert len(p.links) == 1
        assert p.links[0].href == "#ref-1"

    def test_parameter_alias_class(self):
        """The class_ field uses alias 'class' for OSCAL JSON compatibility."""
        data = {"id": "p-alias", "class": "privacy"}
        p = Parameter.model_validate(data)
        assert p.class_ == "privacy"
        # Serialization by alias should produce "class"
        dumped = p.model_dump(by_alias=True)
        assert "class" in dumped
        assert dumped["class"] == "privacy"

    def test_parameter_extra_fields_roundtrip(self):
        """Unknown fields survive round-trip thanks to extra='allow'."""
        data = {"id": "p-extra", "custom_field": "custom_value", "another": 42}
        p = Parameter.model_validate(data)
        assert p.id == "p-extra"
        dumped = p.model_dump()
        assert dumped["custom_field"] == "custom_value"
        assert dumped["another"] == 42

    def test_parameter_minimal(self):
        """Only 'id' is required; all other fields have defaults."""
        p = Parameter(id="p-min")
        assert p.id == "p-min"
        assert p.label is None
        assert p.class_ is None
        assert p.usage is None
        assert p.values == []
        assert p.select is None
        assert p.constraints == []
        assert p.guidelines == []
        assert p.props == []
        assert p.links == []


# ---------------------------------------------------------------------------
# Control.params typed tests
# ---------------------------------------------------------------------------


class TestControlParamsTyped:
    """Tests for Control.params using the typed Parameter list."""

    def test_control_with_typed_params(self):
        """Control with typed Parameter list."""
        ctrl = Control(
            id="ctrl-1",
            params=[Parameter(id="p-1", label="L1"), Parameter(id="p-2", label="L2")],
        )
        assert len(ctrl.params) == 2
        assert isinstance(ctrl.params[0], Parameter)
        assert ctrl.params[0].id == "p-1"
        assert ctrl.params[1].label == "L2"

    def test_control_params_from_dict(self):
        """Control loaded from dict with params as raw dicts auto-converts to Parameter."""
        data = {
            "id": "ctrl-dict",
            "params": [
                {"id": "p-a", "label": "Alpha"},
                {"id": "p-b", "label": "Beta", "values": ["x", "y"]},
            ],
        }
        ctrl = Control.model_validate(data)
        assert len(ctrl.params) == 2
        assert isinstance(ctrl.params[0], Parameter)
        assert ctrl.params[0].id == "p-a"
        assert ctrl.params[0].label == "Alpha"
        assert isinstance(ctrl.params[1], Parameter)
        assert ctrl.params[1].values == ["x", "y"]

    def test_control_roundtrip_with_params(self):
        """Dump and reload preserves params."""
        ctrl = Control(
            id="ctrl-rt",
            title="Round-trip Test",
            params=[
                Parameter(
                    id="p-rt",
                    label="RT Param",
                    values=["v1"],
                    select={"how-many": "one", "choice": ["v1", "v2"]},
                ),
            ],
        )
        dumped = ctrl.model_dump(by_alias=True)
        reloaded = Control.model_validate(dumped)
        assert len(reloaded.params) == 1
        assert isinstance(reloaded.params[0], Parameter)
        assert reloaded.params[0].id == "p-rt"
        assert reloaded.params[0].label == "RT Param"
        assert reloaded.params[0].values == ["v1"]
        assert reloaded.params[0].select == {"how-many": "one", "choice": ["v1", "v2"]}


# ---------------------------------------------------------------------------
# list_params tests
# ---------------------------------------------------------------------------


class TestListParams:
    """Tests for list_params."""

    def test_list_params_empty(self):
        assert list_params([]) == []

    def test_list_params_none(self):
        assert list_params(None) == []

    def test_list_params_non_empty(self):
        params = [Parameter(id="a"), Parameter(id="b")]
        result = list_params(params)
        assert len(result) == 2
        assert result[0].id == "a"
        # Should be a copy, not the same list object
        assert result is not params


# ---------------------------------------------------------------------------
# find_params tests
# ---------------------------------------------------------------------------


class TestFindParams:
    """Tests for find_params."""

    def test_find_params_by_id_found(self):
        params = [Parameter(id="x", label="X"), Parameter(id="y", label="Y")]
        result = find_params(params, param_id="x")
        assert len(result) == 1
        assert result[0].id == "x"

    def test_find_params_by_id_not_found(self):
        params = [Parameter(id="x")]
        result = find_params(params, param_id="z")
        assert result == []

    def test_find_params_by_label_found(self):
        params = [
            Parameter(id="a", label="Alpha"),
            Parameter(id="b", label="Beta"),
            Parameter(id="c", label="Alpha"),
        ]
        result = find_params(params, label="Alpha")
        assert len(result) == 2
        assert {p.id for p in result} == {"a", "c"}

    def test_find_params_by_label_not_found(self):
        params = [Parameter(id="a", label="Alpha")]
        result = find_params(params, label="Gamma")
        assert result == []

    def test_find_params_by_id_and_label(self):
        params = [
            Parameter(id="a", label="Alpha"),
            Parameter(id="b", label="Alpha"),
        ]
        result = find_params(params, param_id="a", label="Alpha")
        assert len(result) == 1
        assert result[0].id == "a"

    def test_find_params_none_input(self):
        assert find_params(None, param_id="x") == []


# ---------------------------------------------------------------------------
# get_param tests
# ---------------------------------------------------------------------------


class TestGetParam:
    """Tests for get_param."""

    def test_get_param_found(self):
        params = [Parameter(id="p1", label="P1"), Parameter(id="p2", label="P2")]
        result = get_param(params, "p1")
        assert result is not None
        assert result.id == "p1"
        assert result.label == "P1"

    def test_get_param_not_found(self):
        params = [Parameter(id="p1")]
        result = get_param(params, "missing")
        assert result is None

    def test_get_param_none_input(self):
        result = get_param(None, "anything")
        assert result is None


# ---------------------------------------------------------------------------
# upsert_param tests
# ---------------------------------------------------------------------------


class TestUpsertParam:
    """Tests for upsert_param."""

    def test_upsert_param_insert(self):
        """New param is appended when no matching id exists."""
        params: list[Parameter] = [Parameter(id="existing")]
        new_param = Parameter(id="new-one", label="New")
        result = upsert_param(params, new_param)
        assert len(params) == 2
        assert params[1].id == "new-one"
        assert result is new_param

    def test_upsert_param_update(self):
        """Existing param is replaced when matching id exists."""
        params: list[Parameter] = [
            Parameter(id="p1", label="Old"),
            Parameter(id="p2", label="Other"),
        ]
        updated = Parameter(id="p1", label="Updated", usage="New usage")
        result = upsert_param(params, updated)
        assert len(params) == 2
        assert params[0].id == "p1"
        assert params[0].label == "Updated"
        assert params[0].usage == "New usage"
        assert result is updated


# ---------------------------------------------------------------------------
# remove_param tests
# ---------------------------------------------------------------------------


class TestRemoveParam:
    """Tests for remove_param."""

    def test_remove_param_existing(self):
        params: list[Parameter] = [Parameter(id="a"), Parameter(id="b"), Parameter(id="c")]
        remove_param(params, "b")
        assert len(params) == 2
        assert [p.id for p in params] == ["a", "c"]

    def test_remove_param_not_found(self):
        """Removing a non-existing param is a no-op."""
        params: list[Parameter] = [Parameter(id="a")]
        remove_param(params, "missing")
        assert len(params) == 1
        assert params[0].id == "a"


# ---------------------------------------------------------------------------
# Integration test
# ---------------------------------------------------------------------------


class TestParamsIntegration:
    """End-to-end integration: Control with params + CRUD operations."""

    def test_full_workflow(self):
        """Create Control with params, upsert, remove, and verify."""
        ctrl = Control(
            id="ctrl-int",
            params=[
                Parameter(id="p1", label="First"),
                Parameter(id="p2", label="Second"),
            ],
        )

        # Verify initial state
        assert len(ctrl.params) == 2

        # List
        all_params = list_params(ctrl.params)
        assert len(all_params) == 2

        # Find
        found = find_params(ctrl.params, param_id="p1")
        assert len(found) == 1

        # Get
        p = get_param(ctrl.params, "p2")
        assert p is not None
        assert p.label == "Second"

        # Upsert (update existing)
        upsert_param(ctrl.params, Parameter(id="p1", label="First Updated", values=["v1"]))
        assert ctrl.params[0].label == "First Updated"
        assert ctrl.params[0].values == ["v1"]
        assert len(ctrl.params) == 2

        # Upsert (insert new)
        upsert_param(ctrl.params, Parameter(id="p3", label="Third"))
        assert len(ctrl.params) == 3
        assert ctrl.params[2].id == "p3"

        # Remove
        remove_param(ctrl.params, "p2")
        assert len(ctrl.params) == 2
        assert [p.id for p in ctrl.params] == ["p1", "p3"]

        # Round-trip the whole control
        dumped = ctrl.model_dump(by_alias=True)
        reloaded = Control.model_validate(dumped)
        assert len(reloaded.params) == 2
        assert reloaded.params[0].id == "p1"
        assert reloaded.params[0].label == "First Updated"
        assert reloaded.params[1].id == "p3"


class TestParamsPackageExports:
    """Verify params CRUD is accessible from the top-level pycore package."""

    def test_parameter_model_exported(self):
        import opengov_oscal_pycore as pycore
        assert hasattr(pycore, "Parameter")
        assert "Parameter" in pycore.__all__

    def test_params_crud_exported(self):
        import opengov_oscal_pycore as pycore
        for name in ["list_params", "find_params", "get_param_value", "upsert_param", "remove_param"]:
            assert hasattr(pycore, name), f"{name} not exported"
            assert name in pycore.__all__, f"{name} not in __all__"
