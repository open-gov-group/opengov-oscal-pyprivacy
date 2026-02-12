from opengov_oscal_pycore.models import Catalog, Group, Control, Property
from opengov_oscal_pyprivacy.legal_adapter import (
    add_legal_id,
    add_or_update_legal,
    list_normalized_legal_ids,
    normalize_legal_from_text,
    LegalPropSpec,
)


def test_normalize_legal_from_text_adds_props():
    cat = Catalog(
        uuid="u",
        metadata={"title": "t", "version": "0.1", "oscal_version": "1.0.0"},
        groups=[Group(id="g", title="G", controls=[Control(id="c1", title="C1")])],
    )
    c = cat.groups[0].controls[0]

    # Uses the default registry shipped with opengov-pylegal-utils
    added = normalize_legal_from_text(c, "Art. 5 Abs. 2 DSGVO")

    assert len(added) >= 1
    assert any(p.name == "legal" for p in c.props)


# ---------------------------------------------------------------------------
# Extended test coverage (Issue #13)
# ---------------------------------------------------------------------------

def _fresh_control() -> Control:
    """Helper: a control with no props."""
    return Control(id="ctl-test", title="Test Control")


def test_add_legal_id():
    """add_legal_id appends a legal prop to the control."""
    c = _fresh_control()
    add_legal_id(c, "EU:REG:GDPR:ART-5_ABS-2")

    assert len(c.props) == 1
    p = c.props[0]
    assert p.name == "legal"
    assert p.value == "EU:REG:GDPR:ART-5_ABS-2"
    assert p.ns == "de"
    assert p.group == "reference"
    assert p.class_ == "proof"


def test_add_legal_id_with_label():
    """add_legal_id stores the human-readable label in remarks."""
    c = _fresh_control()
    add_legal_id(c, "EU:REG:GDPR:ART-24", label="Art. 24 DS-GVO")

    assert len(c.props) == 1
    assert c.props[0].remarks == "Art. 24 DS-GVO"


def test_add_legal_id_no_duplicate():
    """Adding the same norm_id twice must not create a duplicate property."""
    c = _fresh_control()
    add_legal_id(c, "EU:REG:GDPR:ART-5_ABS-2")
    add_legal_id(c, "EU:REG:GDPR:ART-5_ABS-2")

    assert len(c.props) == 1


def test_add_legal_id_updates_label_on_duplicate():
    """If a duplicate is added with a new label, the label is updated."""
    c = _fresh_control()
    add_legal_id(c, "EU:REG:GDPR:ART-5_ABS-2", label="Old Label")
    add_legal_id(c, "EU:REG:GDPR:ART-5_ABS-2", label="New Label")

    assert len(c.props) == 1
    assert c.props[0].remarks == "New Label"


def test_add_or_update_legal():
    """add_or_update_legal is a backwards-compatible alias for add_legal_id."""
    c = _fresh_control()
    add_or_update_legal(c, "EU:REG:GDPR:ART-6", human_label="Art. 6 DS-GVO")

    assert len(c.props) == 1
    p = c.props[0]
    assert p.name == "legal"
    assert p.value == "EU:REG:GDPR:ART-6"
    assert p.remarks == "Art. 6 DS-GVO"


def test_list_normalized_legal_ids_empty():
    """A control with no props returns an empty list of legal IDs."""
    c = _fresh_control()
    ids = list_normalized_legal_ids(c)
    assert ids == []


def test_list_normalized_legal_ids_populated():
    """A control with legal props returns all their values."""
    c = _fresh_control()
    add_legal_id(c, "EU:REG:GDPR:ART-5_ABS-2")
    add_legal_id(c, "EU:REG:GDPR:ART-24")

    ids = list_normalized_legal_ids(c)
    assert len(ids) == 2
    assert "EU:REG:GDPR:ART-5_ABS-2" in ids
    assert "EU:REG:GDPR:ART-24" in ids


def test_list_normalized_legal_ids_ignores_non_legal_props():
    """list_normalized_legal_ids only returns props named 'legal'."""
    c = _fresh_control()
    add_legal_id(c, "EU:REG:GDPR:ART-5_ABS-2")
    # Manually add a non-legal prop
    c.props.append(Property(name="custom", value="something"))

    ids = list_normalized_legal_ids(c)
    assert ids == ["EU:REG:GDPR:ART-5_ABS-2"]
