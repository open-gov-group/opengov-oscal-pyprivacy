from opengov_oscal_pycore.models import Catalog, Group, Control
from opengov_oscal_pyprivacy.legal_adapter import normalize_legal_from_text


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
