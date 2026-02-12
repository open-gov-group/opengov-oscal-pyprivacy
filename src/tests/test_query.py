import json
from pathlib import Path
import pytest
from opengov_oscal_pycore.models import Catalog, Control, Group, Property
from opengov_oscal_pycore.crud_catalog import iter_controls_with_group, find_controls_by_prop

FIXTURE_FILE = Path(__file__).parent / "data" / "open_privacy_catalog_risk.json"

@pytest.fixture
def catalog():
    data = json.loads(FIXTURE_FILE.read_text(encoding="utf-8"))
    return Catalog.model_validate(data)

@pytest.fixture
def simple_catalog():
    return Catalog(
        uuid="test",
        metadata={"title": "Test"},
        groups=[
            Group(id="g1", title="G1", controls=[
                Control(id="c1", title="C1", props=[Property(name="level", value="full")]),
                Control(id="c2", title="C2", props=[Property(name="level", value="partial")]),
            ]),
            Group(id="g2", title="G2", controls=[
                Control(id="c3", title="C3", props=[Property(name="level", value="full")]),
            ]),
        ],
    )

class TestIterControlsWithGroup:
    def test_yields_all_controls(self, simple_catalog):
        pairs = list(iter_controls_with_group(simple_catalog))
        assert len(pairs) == 3

    def test_group_association(self, simple_catalog):
        pairs = list(iter_controls_with_group(simple_catalog))
        assert pairs[0][1].id == "g1"
        assert pairs[2][1].id == "g2"

class TestFindControlsByProp:
    def test_find_by_name(self, simple_catalog):
        found = find_controls_by_prop(simple_catalog, prop_name="level")
        assert len(found) == 3

    def test_find_by_name_and_value(self, simple_catalog):
        found = find_controls_by_prop(simple_catalog, prop_name="level", prop_value="full")
        assert len(found) == 2
        assert {c.id for c in found} == {"c1", "c3"}

    def test_find_no_match(self, simple_catalog):
        found = find_controls_by_prop(simple_catalog, prop_name="nonexistent")
        assert found == []

    def test_find_by_class(self, simple_catalog):
        found = find_controls_by_prop(simple_catalog, prop_name="level", prop_class="some_class")
        assert found == []


from opengov_oscal_pyprivacy.domain.query import (
    find_controls_by_tom_id,
    find_controls_by_implementation_level,
    find_controls_by_legal_article,
    find_controls_by_evidence,
    find_controls_by_maturity_domain,
)

class TestDomainQueryHelpers:
    def test_find_by_tom_id(self, catalog):
        # catalog fixture should have SDM building blocks
        found = find_controls_by_tom_id(catalog, "nonexistent-tom")
        assert found == []

    def test_find_by_implementation_level(self, simple_catalog):
        # simple catalog doesn't have impl level, expect empty
        found = find_controls_by_implementation_level(simple_catalog, "full")
        assert found == []

    def test_find_by_legal_article(self, catalog):
        found = find_controls_by_legal_article(catalog, "nonexistent-article")
        assert found == []


class TestNewQueryHelpers:
    def test_find_by_evidence_existing(self, catalog):
        found = find_controls_by_evidence(catalog, "record-of-processing")
        assert len(found) > 0
        assert any(c.id.startswith("REG") for c in found)

    def test_find_by_evidence_nonexistent(self, catalog):
        found = find_controls_by_evidence(catalog, "nonexistent")
        assert found == []

    def test_find_by_maturity_domain_existing(self, catalog):
        found = find_controls_by_maturity_domain(catalog, "records-of-processing")
        assert len(found) > 0

    def test_find_by_maturity_domain_risk_management(self, catalog):
        found = find_controls_by_maturity_domain(catalog, "risk-management")
        assert len(found) > 0
        assert any(c.id.startswith("DPIA") for c in found)

    def test_find_by_evidence_dpia_report(self, catalog):
        found = find_controls_by_evidence(catalog, "dpia-report")
        assert len(found) > 0
        assert any(c.id.startswith("DPIA") for c in found)

    def test_find_by_maturity_domain_nonexistent(self, catalog):
        found = find_controls_by_maturity_domain(catalog, "nonexistent-domain")
        assert found == []
