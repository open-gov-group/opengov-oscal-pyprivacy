from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Iterable, List

from opengov_oscal_pycore.models import Catalog, Control
from opengov_oscal_pycore.crud_catalog import find_control, iter_controls
from opengov_oscal_pycore.props_parts import get_prop, set_prop, remove_prop

from . import catalog_keys as K
from .vocab import PrivacyVocabs
from .legal_adapter import normalize_legal_from_text, add_legal_id, list_normalized_legal_ids


@dataclass
class ControlView:
    control: Control
    assurance_goal: Optional[str] = None
    measure: Optional[str] = None
    sdm_building_block: Optional[str] = None
    maturity_domain: Optional[str] = None
    maturity_requirement: Optional[str] = None


class PrivacyCatalog:
    def __init__(self, catalog: Catalog, vocabs: Optional[PrivacyVocabs] = None, strict: bool = False):
        self.catalog = catalog
        self.vocabs = vocabs
        self.strict = strict

    def iter_controls(self) -> Iterable[Control]:
        return iter_controls(self.catalog)

    def get_control(self, control_id: str) -> Control:
        c = find_control(self.catalog, control_id)
        if not c:
            raise KeyError(f"Control not found: {control_id}")
        return c

    def view(self, control_id: str) -> ControlView:
        c = self.get_control(control_id)
        props = c.props or []

        def val(name: str, cls: Optional[str] = None, group: Optional[str] = None) -> Optional[str]:
            # we need a slightly richer lookup than core.get_prop (which matches only name+class)
            for p in props:
                if p.name != name:
                    continue
                if cls is not None and p.class_ != cls:
                    continue
                if group is not None and p.group != group:
                    continue
                return p.value
            return None

        return ControlView(
            control=c,
            assurance_goal=val(K.ASSURANCE_GOAL, cls=K.CLASS_TELEOLOGICAL, group=K.GROUP_AIM),
            measure=val(K.MEASURE, cls=K.CLASS_CATEGORY, group=K.GROUP_IMPLEMENTATION),
            sdm_building_block=val(K.SDM_BUILDING_BLOCK),
            maturity_domain=val(K.MATURITY, cls=K.CLASS_MATURITY_DOMAIN),
            maturity_requirement=val(K.MATURITY, cls=K.CLASS_MATURITY_REQUIREMENT),
        )

    # ---------- setters with CSV-backed validation ----------
    def _validate(self, vocab_name: str, value: Optional[str]) -> None:
        if not self.strict or not self.vocabs or value is None:
            return
        vocab = getattr(self.vocabs, vocab_name)
        if value not in vocab.keys:
            raise ValueError(f"Value '{value}' not allowed for {vocab_name}")

    def set_assurance_goal(self, control_id: str, goal: Optional[str]) -> None:
        self._validate("assurance_goals", goal)
        c = self.get_control(control_id)
        set_prop(c.props, K.ASSURANCE_GOAL, goal or "", cls=K.CLASS_TELEOLOGICAL, ns=None)
        # ensure group matches your catalog convention
        p = next(p for p in c.props if p.name == K.ASSURANCE_GOAL and p.class_ == K.CLASS_TELEOLOGICAL)
        p.group = K.GROUP_AIM
        if goal is None:
            remove_prop(c.props, K.ASSURANCE_GOAL, cls=K.CLASS_TELEOLOGICAL)

    def set_measure(self, control_id: str, measure: Optional[str]) -> None:
        self._validate("measures", measure)
        c = self.get_control(control_id)
        if measure is None:
            # remove all 'measure' props
            c.props[:] = [p for p in c.props if p.name != K.MEASURE]
            return
        c.props.append(
            type(c.props[0])(
                name=K.MEASURE,
                value=measure,
                group=K.GROUP_IMPLEMENTATION,
                class_=K.CLASS_CATEGORY,
            )
        )

# ---------- legal references ----------
def add_legal_id(self, control_id: str, norm_id: str, label: Optional[str] = None) -> None:
    c = self.get_control(control_id)
    add_legal_id(c, norm_id, label=label)

def normalize_legal_from_text(self, control_id: str, text: str) -> List[str]:
    c = self.get_control(control_id)
    return normalize_legal_from_text(c, text)

def list_legal_ids(self, control_id: str) -> List[str]:
    c = self.get_control(control_id)
    return list_normalized_legal_ids(c)

