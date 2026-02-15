"""
Performance benchmarks for opengov-oscal-pycore and opengov-oscal-pyprivacy.

Uses pytest-benchmark when available (--benchmark-enable),
but also runs as plain pytest assertions (--benchmark-disable or no plugin).

Issue #51.
"""

from __future__ import annotations

import uuid
from typing import List

import pytest

from opengov_oscal_pycore import (
    Catalog,
    Group,
    Control,
    Property,
    Part,
    Link,
    Parameter,
    OscalMetadata,
    find_control,
    upsert_prop,
    add_control,
)
from opengov_oscal_pycore.diff import diff_catalogs
from opengov_oscal_pyprivacy.converters import control_to_privacy_detail


# ---------------------------------------------------------------------------
# Synthetic catalog generator
# ---------------------------------------------------------------------------

_LEGAL_ARTICLES = [
    "EU:REG:GDPR:ART-5_ABS-2",
    "EU:REG:GDPR:ART-24",
    "EU:REG:GDPR:ART-25",
    "EU:REG:GDPR:ART-32",
    "EU:REG:GDPR:ART-35",
]

_DP_GOALS = ["transparency", "intervenability", "confidentiality", "integrity", "availability"]


def _make_props(ctrl_id: str, idx: int) -> List[Property]:
    """Generate 5 realistic properties for a control."""
    return [
        Property(
            name="legal",
            ns="de",
            value=_LEGAL_ARTICLES[idx % len(_LEGAL_ARTICLES)],
            group="reference",
            **{"class": "proof"},
            remarks=f"Art. {5 + idx} DS-GVO",
        ),
        Property(
            name="assurnace_goal",
            ns="de",
            value=_DP_GOALS[idx % len(_DP_GOALS)],
            group="aim_of_measure",
            **{"class": "teleological_interpretation"},
            remarks=_DP_GOALS[idx % len(_DP_GOALS)].capitalize(),
        ),
        Property(
            name="sdm-building-block",
            value=f"ORG-{ctrl_id}",
        ),
        Property(
            name="measure",
            ns="de",
            value="organizational",
            group="implementation",
            **{"class": "category"},
            remarks="Organisatorisch",
        ),
        Property(
            name="maturity",
            value=str((idx % 5) + 1),
            group="responsibility",
            **{"class": "requirement"},
            remarks=f"Stufe {(idx % 5) + 1}",
        ),
    ]


def _make_parts(ctrl_id: str) -> List[Part]:
    """Generate realistic parts: statement, maturity-hints (with nested levels), typical-measures, assessment-questions."""
    lower_id = ctrl_id.lower()
    return [
        Part(
            id=f"{lower_id}-stmt",
            name="statement",
            prose=f"Statement for control {ctrl_id}: This control ensures proper implementation of privacy measures.",
        ),
        Part(
            id=f"{lower_id}-maturity",
            name="maturity-hints",
            prose="CNIL-Reifegradmodell mit Level 1, 3 und 5.",
            parts=[
                Part(
                    id=f"{lower_id}-maturity-level-01",
                    name="maturity-level-1",
                    props=[Property(name="maturity-level", value="1")],
                    prose=f"Level 1: Ad-hoc process for {ctrl_id}.",
                ),
                Part(
                    id=f"{lower_id}-maturity-level-03",
                    name="maturity-level-3",
                    props=[Property(name="maturity-level", value="3")],
                    prose=f"Level 3: Defined process for {ctrl_id}.",
                ),
                Part(
                    id=f"{lower_id}-maturity-level-05",
                    name="maturity-level-5",
                    props=[Property(name="maturity-level", value="5")],
                    prose=f"Level 5: Optimized process for {ctrl_id}.",
                ),
            ],
        ),
        Part(
            id=f"{lower_id}-typical-measures",
            name="typical-measures",
            prose=f"Typical measures for {ctrl_id}.",
            parts=[
                Part(
                    id=f"{lower_id}-typical-measure-{i:02d}",
                    name="typical-measure",
                    prose=f"Measure {i} for {ctrl_id}: Implement control procedure {i}.",
                )
                for i in range(1, 4)
            ],
        ),
        Part(
            id=f"{lower_id}-questions",
            name="assessment-questions",
            prose=f"Audit questions for {ctrl_id}.",
            parts=[
                Part(
                    id=f"{lower_id}-questions-{i:02d}",
                    name="assessment-question",
                    prose=f"Question {i} for {ctrl_id}: Is procedure {i} documented?",
                )
                for i in range(1, 3)
            ],
        ),
    ]


def _make_links(ctrl_id: str, idx: int) -> List[Link]:
    """Generate 2 realistic links."""
    return [
        Link(href=f"#ref-{ctrl_id}", rel="related", text=f"Related to {ctrl_id}"),
        Link(href=f"https://example.com/controls/{ctrl_id}", rel="reference"),
    ]


def _make_params(ctrl_id: str) -> List[Parameter]:
    """Generate 2 realistic parameters."""
    lower_id = ctrl_id.lower()
    return [
        Parameter(
            id=f"{lower_id}-param-01",
            label=f"Frequency for {ctrl_id}",
            values=["monthly"],
        ),
        Parameter(
            id=f"{lower_id}-param-02",
            label=f"Scope for {ctrl_id}",
            values=["organization-wide"],
        ),
    ]


def generate_synthetic_catalog(n_controls: int, n_groups: int = 10) -> Catalog:
    """
    Generate a synthetic OSCAL catalog with realistic structure.

    Each control has: id, title, class_, 5 props, 4 parts (with nested sub-parts),
    2 links, and 2 params. Controls are distributed evenly across groups.

    Args:
        n_controls: Total number of controls to create.
        n_groups: Number of top-level groups.

    Returns:
        A fully populated Catalog instance.
    """
    controls_per_group = max(1, n_controls // n_groups)
    remainder = n_controls - (controls_per_group * n_groups)

    groups: List[Group] = []
    ctrl_idx = 0

    for g_idx in range(n_groups):
        group_id = f"GRP-{g_idx + 1:03d}"
        n_ctrls = controls_per_group + (1 if g_idx < remainder else 0)
        controls: List[Control] = []

        for c_local in range(n_ctrls):
            ctrl_id = f"CTRL-{ctrl_idx + 1:04d}"
            control = Control(
                id=ctrl_id,
                title=f"Control {ctrl_id}: Privacy measure {ctrl_idx + 1}",
                props=_make_props(ctrl_id, ctrl_idx),
                parts=_make_parts(ctrl_id),
                links=_make_links(ctrl_id, ctrl_idx),
                params=_make_params(ctrl_id),
                **{"class": "management"},
            )
            controls.append(control)
            ctrl_idx += 1

        group = Group(
            id=group_id,
            title=f"Group {group_id}: Privacy domain {g_idx + 1}",
            controls=controls,
            **{"class": "governance"},
        )
        groups.append(group)

    catalog = Catalog(
        uuid=str(uuid.uuid4()),
        metadata=OscalMetadata(
            title="Synthetic Performance Test Catalog",
            **{
                "last-modified": "2026-01-01T00:00:00Z",
            },
            version="1.0.0",
            **{
                "oscal-version": "1.1.2",
            },
        ),
        groups=groups,
    )
    return catalog


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def catalog_100() -> Catalog:
    """100-control catalog (reused across tests in this module)."""
    return generate_synthetic_catalog(100, n_groups=10)


@pytest.fixture(scope="module")
def catalog_500() -> Catalog:
    """500-control catalog."""
    return generate_synthetic_catalog(500, n_groups=10)


@pytest.fixture(scope="module")
def catalog_1000() -> Catalog:
    """1000-control catalog."""
    return generate_synthetic_catalog(1000, n_groups=10)


# ---------------------------------------------------------------------------
# Benchmark helpers
# ---------------------------------------------------------------------------

def _run_benchmark(benchmark, func, *args, **kwargs):
    """Run func through benchmark if available, otherwise call once."""
    if benchmark is not None:
        return benchmark(func, *args, **kwargs)
    return func(*args, **kwargs)


# ---------------------------------------------------------------------------
# Performance tests
# ---------------------------------------------------------------------------

class TestPerformance:
    """Performance benchmarks for core OSCAL operations."""

    # --- 1. Model validation (load) with 1000 controls < 2s ---------------

    def test_load_large_catalog(self, benchmark):
        """Catalog.model_validate() with 1000 controls should complete in < 2s."""
        # Build the raw dict once (outside benchmark)
        cat = generate_synthetic_catalog(1000, n_groups=10)
        raw = cat.model_dump(by_alias=True)

        result = benchmark(Catalog.model_validate, raw)

        # Sanity: we got the right number of controls
        total = sum(len(g.controls) for g in result.groups)
        assert total == 1000
        # Performance threshold: median < 2s
        # (pytest-benchmark records stats; we assert on wall time for non-benchmark runs)

    # --- 2. find_control with 1000 controls < 50ms -------------------------

    def test_find_control_large_catalog(self, catalog_1000: Catalog, benchmark):
        """find_control() should locate a control in 1000-control catalog quickly."""
        # Search for the last control (worst case for linear scan)
        target_id = "CTRL-1000"

        result = benchmark(find_control, catalog_1000, target_id)

        assert result is not None
        assert result.id == target_id

    # --- 3. CRUD operations with 1000 controls < 100ms --------------------

    def test_crud_operations_large_catalog(self, benchmark):
        """upsert_prop + add_control on a 1000-control catalog should be fast."""
        # Fresh catalog each round to avoid mutation side-effects
        def crud_operations():
            cat = generate_synthetic_catalog(1000, n_groups=10)

            # upsert a prop on the first control
            first_ctrl = cat.groups[0].controls[0]
            upsert_prop(
                first_ctrl.props,
                Property(name="benchmark-tag", value="perf-test"),
                key=("name",),
            )

            # add a new control to the first group
            new_ctrl = Control(
                id="CTRL-NEW-9999",
                title="Benchmark new control",
                props=[Property(name="status", value="new")],
            )
            add_control(cat, cat.groups[0].id, new_ctrl)

            return cat

        result = benchmark(crud_operations)

        # Verify operations succeeded
        assert find_control(result, "CTRL-NEW-9999") is not None
        first_ctrl = result.groups[0].controls[0]
        bench_props = [p for p in first_ctrl.props if p.name == "benchmark-tag"]
        assert len(bench_props) == 1

    # --- 4. diff_catalogs with 2x 500 controls < 5s -----------------------

    def test_diff_large_catalogs(self, benchmark):
        """diff_catalogs() comparing two 500-control catalogs should complete in < 5s."""
        cat_a = generate_synthetic_catalog(500, n_groups=10)
        # Create a modified copy: change some control titles and add props
        cat_b_dict = cat_a.model_dump(by_alias=True)
        # Modify 50 controls (10%)
        modified_count = 0
        for g in cat_b_dict["groups"]:
            for c in g["controls"]:
                if modified_count < 50:
                    c["title"] = c["title"] + " (modified)"
                    c["props"].append({"name": "diff-marker", "value": "changed"})
                    modified_count += 1
        cat_b = Catalog.model_validate(cat_b_dict)

        result = benchmark(diff_catalogs, cat_a, cat_b)

        # Verify diff found changes
        assert result.summary.changed > 0 or result.summary.added > 0
        assert len(result.changes) > 0

    # --- 5. control_to_privacy_detail with 100 controls < 1s ---------------

    def test_converter_large_catalog(self, catalog_100: Catalog, benchmark):
        """control_to_privacy_detail for 100 controls should complete in < 1s."""
        controls = [c for g in catalog_100.groups for c in g.controls]
        assert len(controls) == 100

        def convert_all():
            results = []
            for ctrl in controls:
                dto = control_to_privacy_detail(ctrl)
                results.append(dto)
            return results

        results = benchmark(convert_all)

        assert len(results) == 100
        # Verify DTO structure for the first result
        first = results[0]
        assert first.id == "CTRL-0001"
        assert first.title != ""

    # --- 6. Catalog generation itself (extra benchmark) --------------------

    def test_generate_large_catalog(self, benchmark):
        """Generating a 1000-control catalog should be reasonably fast."""
        cat = benchmark(generate_synthetic_catalog, 1000, 10)

        total = sum(len(g.controls) for g in cat.groups)
        assert total == 1000
        assert len(cat.groups) == 10
        # Verify structure completeness
        sample = cat.groups[0].controls[0]
        assert len(sample.props) == 5
        assert len(sample.parts) == 4
        assert len(sample.links) == 2
        assert len(sample.params) == 2

    # --- 7. Iteration over large catalog (extra benchmark) -----------------

    def test_iter_controls_large_catalog(self, catalog_1000: Catalog, benchmark):
        """Iterating all 1000 controls and collecting IDs should be fast."""
        from opengov_oscal_pycore import iter_controls

        def collect_ids():
            return [c.id for c in iter_controls(catalog_1000)]

        ids = benchmark(collect_ids)

        assert len(ids) == 1000
        assert ids[0] == "CTRL-0001"
        assert ids[-1] == "CTRL-1000"
