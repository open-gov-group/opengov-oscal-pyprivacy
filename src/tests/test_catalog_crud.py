from pathlib import Path

import pytest

from opengov_oscal_pycore.models import Catalog, Control, Group
from opengov_oscal_pycore.repo import OscalRepository
from opengov_oscal_pycore.crud_catalog import (
    add_control,
    delete_control,
    find_control,
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
