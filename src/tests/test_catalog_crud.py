from pathlib import Path

import pytest

from opengov_oscal_pycore.models import Catalog, Control, Group
from opengov_oscal_pycore.repo import OscalRepository
from opengov_oscal_pycore.crud_catalog import (
    add_control,
    delete_control,
    find_control,
    find_group,
    iter_controls,
    set_control_prop,
)


def test_add_and_delete_control(tmp_path: Path):
    # Minimaler Catalog
    cat = Catalog(
        uuid="test-uuid",
        metadata={"title": "Test Catalog", "version": "0.1", "oscal_version": "1.0.0"},
        groups=[
            Group(
                id="grp-1",
                title="Test Group",
                controls=[],
            )
        ],
    )

    control = Control(
        id="ctl-1",
        title="Test Control",
    )

    add_control(cat, "grp-1", control)
    assert find_control(cat, "ctl-1") is not None

    deleted = delete_control(cat, "ctl-1")
    assert deleted is True
    assert find_control(cat, "ctl-1") is None


def test_set_control_prop(tmp_path: Path):
    cat = Catalog(
        uuid="test-uuid",
        metadata={"title": "Test Catalog", "version": "0.1", "oscal_version": "1.0.0"},
        groups=[
            Group(
                id="grp-1",
                title="Test Group",
                controls=[
                    Control(id="ctl-1", title="Test Control", props=[]),
                ],
            )
        ],
    )

    set_control_prop(cat, "ctl-1", "sdm-goal", "availability", cls="sdm")
    control = find_control(cat, "ctl-1")
    assert control is not None
    assert any(p.name == "sdm-goal" and p.value == "availability" for p in control.props)


# ---------------------------------------------------------------------------
# Extended test coverage (Issue #13)
# ---------------------------------------------------------------------------

def _multi_group_catalog() -> Catalog:
    """Helper: catalog with 2 groups and 3 controls total."""
    return Catalog(
        uuid="multi-uuid",
        metadata={"title": "Multi", "version": "0.1", "oscal_version": "1.0.0"},
        groups=[
            Group(
                id="grp-a",
                title="Group A",
                controls=[
                    Control(id="ctl-a1", title="A1"),
                    Control(id="ctl-a2", title="A2"),
                ],
            ),
            Group(
                id="grp-b",
                title="Group B",
                controls=[
                    Control(id="ctl-b1", title="B1"),
                ],
            ),
        ],
    )


def test_iter_controls_yields_all():
    """iter_controls yields every control across all groups."""
    cat = _multi_group_catalog()
    ids = [c.id for c in iter_controls(cat)]
    assert set(ids) == {"ctl-a1", "ctl-a2", "ctl-b1"}
    assert len(ids) == 3


def test_find_group_found():
    """find_group returns the correct group when it exists."""
    cat = _multi_group_catalog()
    grp = find_group(cat, "grp-b")
    assert grp is not None
    assert grp.id == "grp-b"
    assert grp.title == "Group B"


def test_find_group_not_found():
    """find_group returns None for a non-existent group id."""
    cat = _multi_group_catalog()
    assert find_group(cat, "nonexistent") is None


def test_find_control_not_found():
    """find_control returns None for a non-existent control id."""
    cat = _multi_group_catalog()
    assert find_control(cat, "no-such-control") is None


def test_add_control_group_not_found_raises():
    """add_control raises ValueError when the target group does not exist."""
    cat = _multi_group_catalog()
    with pytest.raises(ValueError, match="not found"):
        add_control(cat, "nonexistent-group", Control(id="x", title="X"))


def test_delete_control_not_found_returns_false():
    """delete_control returns False when no control matches."""
    cat = _multi_group_catalog()
    result = delete_control(cat, "no-such-control")
    assert result is False


def test_set_control_prop_not_found_raises():
    """set_control_prop raises ValueError when the control does not exist."""
    cat = _multi_group_catalog()
    with pytest.raises(ValueError, match="not found"):
        set_control_prop(cat, "no-such-control", "key", "val")
