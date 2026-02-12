from pathlib import Path

import pytest

from opengov_oscal_pycore.models import Catalog, Control, Group
from opengov_oscal_pycore.repo import OscalRepository
from opengov_oscal_pycore.crud_catalog import (
    add_control,
    add_group,
    delete_control,
    delete_group,
    find_control,
    find_group,
    iter_controls,
    move_control,
    set_control_prop,
    update_group_title,
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


# ---------------------------------------------------------------------------
# Group CRUD operations (Issue #23)
# ---------------------------------------------------------------------------

class TestGroupCrud:
    """Tests for Group CRUD operations."""

    def _make_catalog(self):
        return Catalog(
            uuid="test-uuid",
            metadata={"title": "Test", "version": "0.1", "oscal_version": "1.0.0"},
            groups=[
                Group(id="g1", title="Group 1", controls=[
                    Control(id="c1", title="Control 1"),
                    Control(id="c2", title="Control 2"),
                ]),
                Group(id="g2", title="Group 2", controls=[
                    Control(id="c3", title="Control 3"),
                ]),
            ],
        )

    def test_add_group(self):
        cat = self._make_catalog()
        add_group(cat, Group(id="g3", title="Group 3"))
        assert len(cat.groups) == 3
        assert find_group(cat, "g3") is not None

    def test_add_group_duplicate_raises(self):
        cat = self._make_catalog()
        with pytest.raises(ValueError):
            add_group(cat, Group(id="g1", title="Duplicate"))

    def test_delete_group(self):
        cat = self._make_catalog()
        assert delete_group(cat, "g1") is True
        assert len(cat.groups) == 1
        assert find_group(cat, "g1") is None

    def test_delete_group_not_found(self):
        cat = self._make_catalog()
        assert delete_group(cat, "nonexistent") is False

    def test_update_group_title(self):
        cat = self._make_catalog()
        update_group_title(cat, "g1", "New Title")
        assert find_group(cat, "g1").title == "New Title"

    def test_update_group_title_not_found(self):
        cat = self._make_catalog()
        with pytest.raises(ValueError):
            update_group_title(cat, "nonexistent", "Title")

    def test_move_control(self):
        cat = self._make_catalog()
        assert move_control(cat, "c1", "g2") is True
        # c1 moved from g1 to g2
        assert len(find_group(cat, "g1").controls) == 1
        assert len(find_group(cat, "g2").controls) == 2
        assert any(c.id == "c1" for c in find_group(cat, "g2").controls)

    def test_move_control_not_found(self):
        cat = self._make_catalog()
        assert move_control(cat, "nonexistent", "g2") is False

    def test_move_control_target_not_found(self):
        cat = self._make_catalog()
        with pytest.raises(ValueError):
            move_control(cat, "c1", "nonexistent")

    def test_find_group_recursive(self):
        """find_group should search nested groups."""
        cat = self._make_catalog()
        nested = Group(id="g1-sub", title="Sub Group")
        find_group(cat, "g1").groups.append(nested)
        assert find_group(cat, "g1-sub") is not None
        assert find_group(cat, "g1-sub").title == "Sub Group"
