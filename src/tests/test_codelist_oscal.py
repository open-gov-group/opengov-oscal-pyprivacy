from __future__ import annotations

import pytest

from opengov_oscal_pycore.models import Catalog, Control, Group, Property
from opengov_oscal_pycore.validation import ValidationIssue
from opengov_oscal_pyprivacy.codelist.registry import CodelistRegistry
from opengov_oscal_pyprivacy.codelist.export.oscal import (
    CODELIST_NAMESPACE,
    create_codelist_prop,
    extract_codelist_codes,
    validate_codelist_props,
)


@pytest.fixture
def registry() -> CodelistRegistry:
    return CodelistRegistry.load_defaults()


def _make_catalog(*controls_with_props) -> Catalog:
    """Helper to create a catalog with controls for testing."""
    controls = []
    for ctrl_id, props in controls_with_props:
        controls.append(Control(id=ctrl_id, title=f"Control {ctrl_id}", props=props))
    return Catalog(
        uuid="test-uuid",
        metadata={"title": "Test Catalog"},
        groups=[Group(id="test-group", title="Test Group", controls=controls)],
    )


# ---------------------------------------------------------------------------
# TestCreateCodelistProp
# ---------------------------------------------------------------------------
class TestCreateCodelistProp:
    def test_create_prop_defaults(self):
        """Creates prop with ns=CODELIST_NAMESPACE, class_=list_id."""
        prop = create_codelist_prop("data-categories", "master-data")
        assert prop.ns == CODELIST_NAMESPACE
        assert prop.class_ == "data-categories"
        assert prop.name == "data-categories"
        assert prop.value == "master-data"

    def test_create_prop_custom_name(self):
        """prop_name overrides name."""
        prop = create_codelist_prop("data-categories", "master-data", prop_name="category")
        assert prop.name == "category"
        assert prop.class_ == "data-categories"

    def test_create_prop_value(self):
        """value set correctly."""
        prop = create_codelist_prop("measure-types", "technical")
        assert prop.value == "technical"
        assert isinstance(prop, Property)


# ---------------------------------------------------------------------------
# TestExtractCodelistCodes
# ---------------------------------------------------------------------------
class TestExtractCodelistCodes:
    def test_extract_from_control_with_codelist_props(self):
        """control has 2 codelist props for 'data-categories', extract returns both."""
        control = Control(
            id="ctrl-1",
            title="Test",
            props=[
                Property(
                    name="data-categories",
                    value="master-data",
                    ns=CODELIST_NAMESPACE,
                    class_="data-categories",
                ),
                Property(
                    name="data-categories",
                    value="contact-data",
                    ns=CODELIST_NAMESPACE,
                    class_="data-categories",
                ),
            ],
        )
        codes = extract_codelist_codes(control, "data-categories")
        assert codes == ["master-data", "contact-data"]

    def test_extract_from_control_without_codelist_props(self):
        """returns empty list."""
        control = Control(id="ctrl-1", title="Test", props=[])
        codes = extract_codelist_codes(control, "data-categories")
        assert codes == []

    def test_extract_ignores_other_namespaces(self):
        """prop with different ns is ignored."""
        control = Control(
            id="ctrl-1",
            title="Test",
            props=[
                Property(
                    name="data-categories",
                    value="master-data",
                    ns="https://other-namespace.example.com",
                    class_="data-categories",
                ),
            ],
        )
        codes = extract_codelist_codes(control, "data-categories")
        assert codes == []

    def test_extract_filters_by_list_id(self):
        """only returns codes for the requested list_id."""
        control = Control(
            id="ctrl-1",
            title="Test",
            props=[
                Property(
                    name="data-categories",
                    value="master-data",
                    ns=CODELIST_NAMESPACE,
                    class_="data-categories",
                ),
                Property(
                    name="measure-types",
                    value="technical",
                    ns=CODELIST_NAMESPACE,
                    class_="measure-types",
                ),
            ],
        )
        codes = extract_codelist_codes(control, "data-categories")
        assert codes == ["master-data"]


# ---------------------------------------------------------------------------
# TestValidateCodelistProps
# ---------------------------------------------------------------------------
class TestValidateCodelistProps:
    def test_valid_props_no_issues(self, registry):
        """catalog with valid codelist props returns no issues."""
        catalog = _make_catalog(
            (
                "ctrl-1",
                [
                    Property(
                        name="data-categories",
                        value="master-data",
                        ns=CODELIST_NAMESPACE,
                        class_="data-categories",
                    ),
                ],
            ),
        )
        issues = validate_codelist_props(catalog, registry)
        assert issues == []

    def test_invalid_code_returns_error(self, registry):
        """prop with invalid code value returns error."""
        catalog = _make_catalog(
            (
                "ctrl-1",
                [
                    Property(
                        name="data-categories",
                        value="nonexistent-code",
                        ns=CODELIST_NAMESPACE,
                        class_="data-categories",
                    ),
                ],
            ),
        )
        issues = validate_codelist_props(catalog, registry)
        assert len(issues) == 1
        assert issues[0].severity == "error"
        assert "Invalid code" in issues[0].message
        assert "nonexistent-code" in issues[0].message

    def test_unknown_codelist_returns_warning(self, registry):
        """prop with unknown class_ returns warning."""
        catalog = _make_catalog(
            (
                "ctrl-1",
                [
                    Property(
                        name="unknown-list",
                        value="some-code",
                        ns=CODELIST_NAMESPACE,
                        class_="unknown-list-id",
                    ),
                ],
            ),
        )
        issues = validate_codelist_props(catalog, registry)
        assert len(issues) == 1
        assert issues[0].severity == "warning"
        assert "Unknown codelist" in issues[0].message

    def test_missing_class_returns_error(self, registry):
        """prop with ns=CODELIST_NAMESPACE but no class_ returns error."""
        catalog = _make_catalog(
            (
                "ctrl-1",
                [
                    Property(
                        name="some-prop",
                        value="some-value",
                        ns=CODELIST_NAMESPACE,
                    ),
                ],
            ),
        )
        issues = validate_codelist_props(catalog, registry)
        assert len(issues) == 1
        assert issues[0].severity == "error"
        assert "missing class_" in issues[0].message

    def test_non_codelist_props_ignored(self, registry):
        """props without CODELIST_NAMESPACE are not checked."""
        catalog = _make_catalog(
            (
                "ctrl-1",
                [
                    Property(name="label", value="some-label"),
                    Property(name="status", value="active", ns="https://example.com"),
                ],
            ),
        )
        issues = validate_codelist_props(catalog, registry)
        assert issues == []

    def test_empty_catalog_no_issues(self, registry):
        """catalog with no controls returns empty list."""
        catalog = Catalog(
            uuid="test-uuid",
            metadata={"title": "Empty Catalog"},
            groups=[Group(id="empty-group", title="Empty")],
        )
        issues = validate_codelist_props(catalog, registry)
        assert issues == []


# ---------------------------------------------------------------------------
# TestNamespaceConstant
# ---------------------------------------------------------------------------
class TestNamespaceConstant:
    def test_namespace_is_string(self):
        """CODELIST_NAMESPACE is a str."""
        assert isinstance(CODELIST_NAMESPACE, str)

    def test_namespace_is_url(self):
        """starts with 'https://'."""
        assert CODELIST_NAMESPACE.startswith("https://")
