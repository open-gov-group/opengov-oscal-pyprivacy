"""
Comprehensive tests for opengov_oscal_pycore models and CRUD modules.

Covers:
  - Part/Link model round-trips, recursion, extra-field preservation (#1)
  - Link CRUD operations (#2)
  - Parts mixed-mode (model vs dict) operations (#8)
"""

from __future__ import annotations

import json

import pytest

from opengov_oscal_pycore.models import (
    Catalog,
    Control,
    Group,
    Link,
    Part,
    Property,
)
from opengov_oscal_pycore.crud.links import (
    find_links,
    get_link,
    list_links,
    remove_links,
    upsert_link,
)
from opengov_oscal_pycore.crud.parts import (
    add_child_part,
    delete_child_part,
    ensure_part_container,
    find_part,
    parts_ref,
    update_child_part,
)


# ============================================================================
# Part / Link Models (#1)
# ============================================================================


class TestLinkRoundtrip:
    """Link erstellen, model_dump(by_alias=True), JSON, zurueck laden."""

    def test_link_roundtrip(self):
        link = Link(href="https://example.com/policy", rel="reference", text="Privacy Policy")

        dumped = link.model_dump(by_alias=True)
        assert dumped["href"] == "https://example.com/policy"
        assert dumped["rel"] == "reference"
        assert dumped["text"] == "Privacy Policy"

        json_str = json.dumps(dumped)
        loaded_data = json.loads(json_str)
        restored = Link(**loaded_data)

        assert restored.href == link.href, "href must survive round-trip"
        assert restored.rel == link.rel, "rel must survive round-trip"
        assert restored.text == link.text, "text must survive round-trip"

    def test_link_minimal_roundtrip(self):
        """Link with only href (rel and text are optional)."""
        link = Link(href="#ctrl-1")
        dumped = link.model_dump(by_alias=True)
        restored = Link(**json.loads(json.dumps(dumped)))
        assert restored.href == "#ctrl-1"
        assert restored.rel is None
        assert restored.text is None


class TestPartRecursive:
    """Part mit verschachtelten Parts erstellen, verifizieren."""

    def test_part_recursive(self):
        inner = Part(name="sub-item", prose="Nested prose")
        middle = Part(name="section", parts=[inner], prose="Middle prose")
        outer = Part(name="statement", parts=[middle])

        assert len(outer.parts) == 1, "outer should have one child part"
        assert outer.parts[0].name == "section"
        assert len(outer.parts[0].parts) == 1, "middle should have one child part"
        assert outer.parts[0].parts[0].name == "sub-item"
        assert outer.parts[0].parts[0].prose == "Nested prose"

    def test_part_recursive_roundtrip(self):
        inner = Part(name="leaf", id="leaf-1", prose="leaf prose")
        root = Part(name="root", parts=[Part(name="branch", parts=[inner])])

        dumped = root.model_dump(by_alias=True)
        json_str = json.dumps(dumped)
        restored = Part(**json.loads(json_str))

        assert restored.parts[0].parts[0].name == "leaf"
        assert restored.parts[0].parts[0].prose == "leaf prose"


class TestPartExtraFieldsPreserved:
    """Part mit unbekannten Feldern laden, sicherstellen sie ueberleben."""

    def test_part_extra_fields_preserved(self):
        raw = {
            "name": "statement",
            "prose": "Some prose",
            "custom-workbench-field": "wb-value-123",
            "x-annotation": {"key": "val"},
        }
        part = Part(**raw)

        assert part.name == "statement"
        assert part.prose == "Some prose"

        dumped = part.model_dump(by_alias=True)
        assert dumped["custom-workbench-field"] == "wb-value-123", (
            "Extra field 'custom-workbench-field' must survive round-trip"
        )
        assert dumped["x-annotation"] == {"key": "val"}, (
            "Extra field 'x-annotation' must survive round-trip"
        )

    def test_link_extra_fields_preserved(self):
        raw = {"href": "#ref", "rel": "related", "media-type": "application/json"}
        link = Link(**raw)
        dumped = link.model_dump(by_alias=True)
        assert dumped["media-type"] == "application/json"


class TestControlWithPartsLinks:
    """Control mit parts/links erstellen, serialisieren, deserialisieren."""

    def test_control_with_parts_links(self):
        ctrl = Control(
            id="ctrl-1",
            title="Access Control",
            parts=[
                Part(name="statement", prose="Implement access control"),
                Part(name="guidance", prose="See ISO 27001"),
            ],
            links=[
                Link(href="#policy-1", rel="reference", text="Policy ref"),
                Link(href="https://example.com", rel="related"),
            ],
        )

        assert len(ctrl.parts) == 2
        assert len(ctrl.links) == 2
        assert ctrl.parts[0].name == "statement"
        assert ctrl.links[1].href == "https://example.com"

        # Serialize and deserialize
        dumped = ctrl.model_dump(by_alias=True)
        json_str = json.dumps(dumped)
        restored = Control(**json.loads(json_str))

        assert restored.id == "ctrl-1"
        assert len(restored.parts) == 2
        assert len(restored.links) == 2
        assert restored.parts[1].prose == "See ISO 27001"
        assert restored.links[0].text == "Policy ref"


class TestControlNestedControls:
    """Control mit verschachtelten controls."""

    def test_control_nested_controls(self):
        child = Control(id="ctrl-1.1", title="Sub-Control A")
        parent = Control(
            id="ctrl-1",
            title="Parent Control",
            controls=[child],
        )

        assert len(parent.controls) == 1
        assert parent.controls[0].id == "ctrl-1.1"
        assert parent.controls[0].title == "Sub-Control A"

    def test_control_nested_controls_roundtrip(self):
        parent = Control(
            id="ctrl-1",
            title="Parent",
            controls=[
                Control(id="ctrl-1.a", title="Enhancement A"),
                Control(id="ctrl-1.b", title="Enhancement B"),
            ],
        )

        dumped = parent.model_dump(by_alias=True)
        restored = Control(**json.loads(json.dumps(dumped)))

        assert len(restored.controls) == 2
        assert restored.controls[0].id == "ctrl-1.a"
        assert restored.controls[1].title == "Enhancement B"


class TestGroupWithGroupsPartProps:
    """Group mit groups/parts/props."""

    def test_group_with_groups_parts_props(self):
        grp = Group(
            id="grp-1",
            title="Privacy Controls",
            props=[
                Property(name="label", value="PR"),
                Property(name="sort-id", value="pr-01"),
            ],
            parts=[
                Part(name="overview", prose="Overview of privacy controls"),
            ],
            groups=[
                Group(
                    id="grp-1.1",
                    title="Sub-Group",
                    controls=[
                        Control(id="ctrl-sub-1", title="Sub Control"),
                    ],
                ),
            ],
        )

        assert grp.id == "grp-1"
        assert len(grp.props) == 2
        assert grp.props[0].name == "label"
        assert len(grp.parts) == 1
        assert grp.parts[0].prose == "Overview of privacy controls"
        assert len(grp.groups) == 1
        assert grp.groups[0].id == "grp-1.1"
        assert len(grp.groups[0].controls) == 1

    def test_group_roundtrip(self):
        grp = Group(
            id="grp-2",
            title="Risk Management",
            groups=[
                Group(id="grp-2.1", title="Risk Assessment"),
            ],
            parts=[Part(name="objective", prose="Minimize risk")],
            props=[Property(name="category", value="risk")],
        )

        dumped = grp.model_dump(by_alias=True)
        restored = Group(**json.loads(json.dumps(dumped)))

        assert restored.id == "grp-2"
        assert len(restored.groups) == 1
        assert restored.groups[0].title == "Risk Assessment"
        assert restored.parts[0].prose == "Minimize risk"
        assert restored.props[0].value == "risk"


# ============================================================================
# Link CRUD (#2)
# ============================================================================


class TestListLinks:
    """test_list_links: leere Liste, Liste mit Links."""

    def test_list_links_empty(self):
        result = list_links(None)
        assert result == [], "None should produce empty list"

        result = list_links([])
        assert result == [], "Empty list should stay empty"

    def test_list_links_with_items(self):
        links = [
            Link(href="#a", rel="related"),
            Link(href="#b", rel="reference"),
        ]
        result = list_links(links)
        assert len(result) == 2
        assert result[0].href == "#a"
        assert result[1].href == "#b"

    def test_list_links_returns_new_list(self):
        """list_links should return a new list, not the same object."""
        original = [Link(href="#x")]
        result = list_links(original)
        assert result is not original


class TestFindLinks:
    """test_find_links: Filter nach rel, href, beides."""

    def _sample_links(self) -> list[Link]:
        return [
            Link(href="#policy-1", rel="reference", text="Policy 1"),
            Link(href="#policy-2", rel="reference", text="Policy 2"),
            Link(href="https://example.com", rel="related", text="Example"),
            Link(href="#policy-1", rel="related", text="Also ref policy 1"),
        ]

    def test_find_links_by_rel(self):
        links = self._sample_links()
        result = find_links(links, rel="reference")
        assert len(result) == 2, "Should find 2 links with rel='reference'"
        assert all(l.rel == "reference" for l in result)

    def test_find_links_by_href(self):
        links = self._sample_links()
        result = find_links(links, href="#policy-1")
        assert len(result) == 2, "Should find 2 links with href='#policy-1'"
        assert all(l.href == "#policy-1" for l in result)

    def test_find_links_by_rel_and_href(self):
        links = self._sample_links()
        result = find_links(links, rel="reference", href="#policy-1")
        assert len(result) == 1
        assert result[0].text == "Policy 1"

    def test_find_links_no_match(self):
        links = self._sample_links()
        result = find_links(links, rel="nonexistent")
        assert result == []

    def test_find_links_none_input(self):
        result = find_links(None, rel="reference")
        assert result == []


class TestGetLink:
    """test_get_link: gefunden, nicht gefunden."""

    def test_get_link_found(self):
        links = [
            Link(href="#a", rel="related"),
            Link(href="#b", rel="reference"),
        ]
        result = get_link(links, "reference")
        assert result is not None
        assert result.href == "#b"

    def test_get_link_not_found(self):
        links = [Link(href="#a", rel="related")]
        result = get_link(links, "nonexistent")
        assert result is None

    def test_get_link_with_href_filter(self):
        links = [
            Link(href="#a", rel="reference"),
            Link(href="#b", rel="reference"),
        ]
        result = get_link(links, "reference", href="#b")
        assert result is not None
        assert result.href == "#b"

    def test_get_link_empty_list(self):
        result = get_link([], "reference")
        assert result is None

    def test_get_link_none_list(self):
        result = get_link(None, "reference")
        assert result is None


class TestUpsertLinkInsert:
    """test_upsert_link_insert: neuen Link einfuegen."""

    def test_upsert_link_insert(self):
        links: list[Link] = []
        new_link = Link(href="#doc-1", rel="reference", text="Doc 1")

        result = upsert_link(links, new_link)

        assert len(links) == 1, "Link should be appended"
        assert result is new_link, "Returned link should be the inserted one"
        assert links[0].href == "#doc-1"

    def test_upsert_link_insert_into_existing(self):
        links = [Link(href="#existing", rel="related")]
        new_link = Link(href="#new", rel="reference", text="New")

        upsert_link(links, new_link)

        assert len(links) == 2
        assert links[1].href == "#new"


class TestUpsertLinkUpdate:
    """test_upsert_link_update: bestehenden Link aktualisieren (text aendern)."""

    def test_upsert_link_update(self):
        original = Link(href="#doc-1", rel="reference", text="Old text")
        links = [original]

        updated_link = Link(href="#doc-1", rel="reference", text="New text")
        result = upsert_link(links, updated_link)

        assert len(links) == 1, "Should not add a duplicate"
        assert result is original, "Should return the existing (updated) link object"
        assert result.text == "New text", "Text should be updated in-place"

    def test_upsert_link_update_custom_key(self):
        """Update matching only on rel (ignoring href)."""
        original = Link(href="#old-href", rel="reference", text="Old")
        links = [original]

        updated = Link(href="#new-href", rel="reference", text="Updated")
        result = upsert_link(links, updated, key=("rel",))

        assert len(links) == 1
        assert result.href == "#new-href", "href should be updated"
        assert result.text == "Updated"


class TestRemoveLinks:
    """test_remove_links: nach rel, nach href, beides."""

    def test_remove_links_by_rel(self):
        links = [
            Link(href="#a", rel="reference"),
            Link(href="#b", rel="related"),
            Link(href="#c", rel="reference"),
        ]
        remove_links(links, rel="reference")
        assert len(links) == 1
        assert links[0].rel == "related"

    def test_remove_links_by_href(self):
        links = [
            Link(href="#target", rel="reference"),
            Link(href="#other", rel="related"),
            Link(href="#target", rel="related"),
        ]
        remove_links(links, href="#target")
        assert len(links) == 1
        assert links[0].href == "#other"

    def test_remove_links_by_rel_and_href(self):
        links = [
            Link(href="#a", rel="reference"),
            Link(href="#a", rel="related"),
            Link(href="#b", rel="reference"),
        ]
        remove_links(links, rel="reference", href="#a")
        assert len(links) == 2
        # Only the one matching both rel AND href was removed
        remaining_hrefs = {l.href for l in links}
        assert "#a" in remaining_hrefs, "Link with href=#a but rel=related should remain"
        assert "#b" in remaining_hrefs

    def test_remove_links_no_match(self):
        links = [Link(href="#a", rel="reference")]
        remove_links(links, rel="nonexistent")
        assert len(links) == 1, "No links should be removed"

    def test_remove_links_mutates_in_place(self):
        links = [Link(href="#a", rel="reference")]
        original_id = id(links)
        remove_links(links, rel="reference")
        assert id(links) == original_id, "Should mutate the list in-place"
        assert len(links) == 0


# ============================================================================
# Parts Mixed-Mode (#8)
# ============================================================================


class TestPartsRefControlModel:
    """test_parts_ref_control_model: parts_ref auf Control (typed parts Feld)."""

    def test_parts_ref_control_model(self):
        ctrl = Control(id="ctrl-1", title="Test")
        ref = parts_ref(ctrl)

        assert isinstance(ref, list)
        assert len(ref) == 0

        # Mutating ref should mutate the control's parts
        ref.append(Part(name="statement", prose="test"))
        assert len(ctrl.parts) == 1
        assert ctrl.parts[0].name == "statement"

    def test_parts_ref_control_with_existing_parts(self):
        ctrl = Control(
            id="ctrl-1",
            parts=[Part(name="overview", prose="existing")],
        )
        ref = parts_ref(ctrl)
        assert len(ref) == 1
        assert ref[0].name == "overview"


class TestPartsRefDict:
    """test_parts_ref_dict: parts_ref auf dict (wie bisher)."""

    def test_parts_ref_dict_existing(self):
        obj = {"parts": [{"name": "item", "prose": "dict item"}]}
        ref = parts_ref(obj)

        assert isinstance(ref, list)
        assert len(ref) == 1
        assert ref[0]["name"] == "item"

    def test_parts_ref_dict_missing(self):
        obj: dict = {}
        ref = parts_ref(obj)

        assert isinstance(ref, list)
        assert len(ref) == 0
        assert "parts" in obj, "parts key should be created on the dict"

    def test_parts_ref_dict_not_list(self):
        obj = {"parts": "invalid"}
        ref = parts_ref(obj)

        assert isinstance(ref, list)
        assert len(ref) == 0


class TestFindPartModel:
    """test_find_part_model: find_part mit Part-Objekten."""

    def test_find_part_by_name(self):
        parts = [
            Part(name="statement", prose="A"),
            Part(name="guidance", prose="B"),
        ]
        result = find_part(parts, name="guidance")
        assert result is not None
        assert result.prose == "B"

    def test_find_part_by_id(self):
        parts = [
            Part(name="item", id="p-1", prose="first"),
            Part(name="item", id="p-2", prose="second"),
        ]
        result = find_part(parts, part_id="p-2")
        assert result is not None
        assert result.prose == "second"

    def test_find_part_by_name_and_id(self):
        parts = [
            Part(name="item", id="p-1"),
            Part(name="item", id="p-2"),
            Part(name="other", id="p-1"),
        ]
        result = find_part(parts, name="item", part_id="p-2")
        assert result is not None
        assert result.id == "p-2"
        assert result.name == "item"

    def test_find_part_not_found(self):
        parts = [Part(name="statement")]
        result = find_part(parts, name="nonexistent")
        assert result is None

    def test_find_part_empty_list(self):
        result = find_part([], name="anything")
        assert result is None

    def test_find_part_dict_mode(self):
        parts = [
            {"name": "statement", "id": "s-1", "prose": "dict part"},
        ]
        result = find_part(parts, name="statement")
        assert result is not None
        assert result["prose"] == "dict part"


class TestEnsurePartContainerCreatesModel:
    """test_ensure_part_container_creates_model: Container auf Control erzeugt Part-Objekt."""

    def test_ensure_part_container_creates_model(self):
        ctrl = Control(id="ctrl-1", title="Test Control")
        assert len(ctrl.parts) == 0

        container = ensure_part_container(ctrl, "statement", prose="Initial prose")

        assert len(ctrl.parts) == 1, "Control should have one part now"
        assert isinstance(ctrl.parts[0], Part), "Part should be a Part model instance"
        assert container.name == "statement"
        assert container.prose == "Initial prose"

    def test_ensure_part_container_idempotent(self):
        ctrl = Control(id="ctrl-1")
        ensure_part_container(ctrl, "statement", prose="v1")
        ensure_part_container(ctrl, "statement", prose="v2")

        assert len(ctrl.parts) == 1, "Should not create a duplicate"
        assert ctrl.parts[0].prose == "v2", "Prose should be updated"

    def test_ensure_part_container_on_dict(self):
        obj: dict = {}
        container = ensure_part_container(obj, "statement")

        assert "parts" in obj
        assert len(obj["parts"]) == 1
        assert isinstance(container, dict), "Dict parent should produce dict parts"
        assert container["name"] == "statement"

    def test_ensure_part_container_on_group(self):
        grp = Group(id="grp-1", title="Group")
        container = ensure_part_container(grp, "overview", prose="Group overview")

        assert len(grp.parts) == 1
        assert isinstance(grp.parts[0], Part)
        assert container.prose == "Group overview"


class TestAddChildPartToModelContainer:
    """test_add_child_part_to_model_container: add_child_part auf Part-Container erzeugt Part."""

    def test_add_child_part_to_model_container(self):
        container = Part(name="statement", parts=[])

        child = add_child_part(
            container,
            name="item",
            prose="Child prose",
            part_id="item-1",
        )

        assert len(container.parts) == 1
        assert isinstance(child, Part), "Child should be a Part model"
        assert child.name == "item"
        assert child.prose == "Child prose"
        assert child.id == "item-1"

    def test_add_child_part_multiple(self):
        container = Part(name="statement")

        add_child_part(container, name="item-a", part_id="a")
        add_child_part(container, name="item-b", part_id="b")

        assert len(container.parts) == 2
        assert container.parts[0].id == "a"
        assert container.parts[1].id == "b"

    def test_add_child_part_with_props_and_links(self):
        container = Part(name="root")
        props = [Property(name="label", value="X")]
        links = [Link(href="#ref", rel="reference")]

        child = add_child_part(
            container,
            name="enriched",
            part_id="e-1",
            props=props,
            links=links,
        )

        assert isinstance(child, Part)
        assert len(child.props) == 1
        assert child.props[0].value == "X"
        assert len(child.links) == 1
        assert child.links[0].href == "#ref"

    def test_add_child_part_to_dict_container(self):
        container = {"name": "statement", "parts": []}

        child = add_child_part(container, name="sub-item", prose="dict child")

        assert len(container["parts"]) == 1
        assert isinstance(child, dict), "Dict container should produce dict children"
        assert child["name"] == "sub-item"
        assert child["prose"] == "dict child"


class TestUpdateChildPartModel:
    """test_update_child_part_model: update_child_part auf Part-Objekt."""

    def test_update_child_part_model(self):
        container = Part(
            name="statement",
            parts=[
                Part(name="item", id="item-1", prose="Original"),
                Part(name="item", id="item-2", prose="Untouched"),
            ],
        )

        updated = update_child_part(container, "item-1", prose="Updated prose")

        assert updated.prose == "Updated prose"
        assert container.parts[0].prose == "Updated prose"
        assert container.parts[1].prose == "Untouched", "Other child should be unchanged"

    def test_update_child_part_title(self):
        container = Part(
            name="root",
            parts=[Part(name="item", id="ch-1", title="Old Title")],
        )
        update_child_part(container, "ch-1", title="New Title")
        assert container.parts[0].title == "New Title"

    def test_update_child_part_props_and_links(self):
        container = Part(
            name="root",
            parts=[Part(name="item", id="ch-1")],
        )
        new_props = [Property(name="status", value="active")]
        new_links = [Link(href="#ref", rel="related")]

        update_child_part(container, "ch-1", props=new_props, links=new_links)

        assert len(container.parts[0].props) == 1
        assert container.parts[0].props[0].value == "active"
        assert len(container.parts[0].links) == 1

    def test_update_child_part_not_found(self):
        container = Part(name="root", parts=[Part(name="item", id="ch-1")])

        with pytest.raises(ValueError, match="part child not found"):
            update_child_part(container, "nonexistent", prose="fail")

    def test_update_child_part_dict_mode(self):
        container = {
            "name": "root",
            "parts": [{"name": "item", "id": "ch-1", "prose": "Old"}],
        }
        updated = update_child_part(container, "ch-1", prose="New")
        assert updated["prose"] == "New"


class TestDeleteChildPartModel:
    """test_delete_child_part_model: delete_child_part auf Part-Objekt."""

    def test_delete_child_part_model(self):
        container = Part(
            name="statement",
            parts=[
                Part(name="item", id="item-1", prose="Delete me"),
                Part(name="item", id="item-2", prose="Keep me"),
            ],
        )

        delete_child_part(container, "item-1")

        assert len(container.parts) == 1
        assert container.parts[0].id == "item-2"

    def test_delete_child_part_not_found(self):
        container = Part(name="root", parts=[Part(name="item", id="ch-1")])

        with pytest.raises(ValueError, match="part child not found"):
            delete_child_part(container, "nonexistent")

    def test_delete_child_part_last_child(self):
        container = Part(
            name="root",
            parts=[Part(name="only-child", id="ch-1")],
        )
        delete_child_part(container, "ch-1")
        assert len(container.parts) == 0

    def test_delete_child_part_dict_mode(self):
        container = {
            "name": "root",
            "parts": [
                {"name": "item", "id": "d-1"},
                {"name": "item", "id": "d-2"},
            ],
        }
        delete_child_part(container, "d-1")
        assert len(container["parts"]) == 1
        assert container["parts"][0]["id"] == "d-2"

    def test_delete_child_part_empty_parts(self):
        container = Part(name="root", parts=[])
        with pytest.raises(ValueError, match="part child not found"):
            delete_child_part(container, "ghost")
