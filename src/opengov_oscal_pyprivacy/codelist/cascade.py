from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from .models import CascadeRule, CodeEntry
from .registry import CodelistRegistry


@dataclass
class CascadeImpact:
    """Result of evaluating a cascade rule."""

    rule_id: str
    description: str
    source_code: str
    target_list: str
    target_field: str
    current_value: Optional[str]
    required_value: str
    is_violation: bool
    severity: str  # "error", "warning", "info"


class CascadeService:
    """Evaluates cascade rules to determine compliance impacts.

    The service loads declarative rules from JSON files and evaluates them
    against codelist entries to determine what changes are required when
    data categories, protection levels, or recipients change.
    """

    def __init__(
        self,
        registry: CodelistRegistry,
        rules: Optional[List[CascadeRule]] = None,
    ) -> None:
        self._registry = registry
        self._rules: List[CascadeRule] = rules or []
        # Sort by priority (lower number = higher priority)
        self._rules.sort(key=lambda r: r.priority)

    @classmethod
    def load_defaults(
        cls, registry: Optional[CodelistRegistry] = None
    ) -> CascadeService:
        """Load default cascade rules from packaged data."""
        if registry is None:
            registry = CodelistRegistry.load_defaults()

        from importlib.resources import files

        rules_dir = (
            Path(str(files("opengov_oscal_pyprivacy")))
            / "data"
            / "cascade_rules"
        )

        rules: List[CascadeRule] = []
        if rules_dir.exists():
            for path in sorted(rules_dir.glob("*.json")):
                data = json.loads(path.read_text(encoding="utf-8"))
                for rule_data in data:
                    rules.append(CascadeRule.model_validate(rule_data))

        return cls(registry, rules)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_field_value(
        self, entry: CodeEntry, field_path: str
    ) -> Optional[str]:
        """Extract a field value from a CodeEntry using dot notation."""
        if field_path == "code":
            return entry.code
        if field_path.startswith("metadata."):
            attr = field_path.split(".", 1)[1]
            # Try direct attribute first, then extra dict
            val = getattr(entry.metadata, attr, None)
            if val is None:
                val = entry.metadata.extra.get(attr)
            return val
        return getattr(entry, field_path, None)

    def _matches_condition(
        self, value: Optional[str], condition: str
    ) -> bool:
        """Evaluate a simple condition string against a value."""
        if value is None:
            return False
        condition = condition.strip()
        if condition.startswith("== "):
            expected = condition[3:].strip().strip("'\"")
            return value == expected
        if condition.startswith("!= "):
            expected = condition[3:].strip().strip("'\"")
            return value != expected
        if condition.startswith("in "):
            # e.g. "in ['special', 'criminal']"
            items_str = condition[3:].strip().strip("[]")
            items = [i.strip().strip("'\"") for i in items_str.split(",")]
            return value in items
        return False

    def _check_violation(
        self, effect, current_protection_level: Optional[str]
    ) -> bool:
        """Check if current state violates a requirement."""
        if (
            effect.target_list == "protection-levels"
            and current_protection_level
        ):
            levels = ["baseline", "standard", "enhanced"]
            try:
                current_idx = levels.index(current_protection_level)
                required_idx = levels.index(effect.value)
                return current_idx < required_idx
            except ValueError:
                return False
        return False

    def _get_effective_level(
        self, impacts: List[CascadeImpact], current: Optional[str]
    ) -> Optional[str]:
        """Determine the effective protection level after applying impacts."""
        levels = ["baseline", "standard", "enhanced"]
        max_idx = -1
        if current and current in levels:
            max_idx = levels.index(current)
        for impact in impacts:
            if (
                impact.target_list == "protection-levels"
                and impact.required_value in levels
            ):
                idx = levels.index(impact.required_value)
                if idx > max_idx:
                    max_idx = idx
        return levels[max_idx] if max_idx >= 0 else None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def evaluate_impact(
        self,
        data_category: str,
        *,
        current_protection_level: Optional[str] = None,
        current_recipients: Optional[List[str]] = None,
    ) -> List[CascadeImpact]:
        """Evaluate all cascade impacts for a given data category.

        Parameters
        ----------
        data_category:
            Code of the data category to evaluate (e.g. ``"health-data"``).
        current_protection_level:
            Optional current protection level code for violation detection.
        current_recipients:
            Optional list of recipient codes to trigger transfer rules.

        Returns
        -------
        List[CascadeImpact]
            All impacts triggered by the data category, effective protection
            level, and recipients.
        """
        impacts: List[CascadeImpact] = []

        # --- Evaluate data-category rules ---
        try:
            cat_entry = self._registry.resolve_code(
                "data-categories", data_category
            )
        except KeyError:
            return impacts

        for rule in self._rules:
            if rule.source_list != "data-categories":
                continue
            field_val = self._get_field_value(cat_entry, rule.source_field)
            if not self._matches_condition(field_val, rule.condition):
                continue

            for effect in rule.effects:
                impacts.append(
                    CascadeImpact(
                        rule_id=rule.rule_id,
                        description=effect.description.get("en"),
                        source_code=data_category,
                        target_list=effect.target_list,
                        target_field=effect.target_field,
                        current_value=(
                            current_protection_level
                            if effect.target_list == "protection-levels"
                            else None
                        ),
                        required_value=effect.value,
                        is_violation=self._check_violation(
                            effect, current_protection_level
                        ),
                        severity=(
                            "error"
                            if effect.operator == "require"
                            else "warning"
                        ),
                    )
                )

        # --- Evaluate protection-level rules (cascaded) ---
        effective_level = self._get_effective_level(
            impacts, current_protection_level
        )
        if effective_level:
            try:
                level_entry = self._registry.resolve_code(
                    "protection-levels", effective_level
                )
            except KeyError:
                level_entry = None

            if level_entry:
                for rule in self._rules:
                    if rule.source_list != "protection-levels":
                        continue
                    field_val = self._get_field_value(
                        level_entry, rule.source_field
                    )
                    if not self._matches_condition(field_val, rule.condition):
                        continue
                    for effect in rule.effects:
                        impacts.append(
                            CascadeImpact(
                                rule_id=rule.rule_id,
                                description=effect.description.get("en"),
                                source_code=effective_level,
                                target_list=effect.target_list,
                                target_field=effect.target_field,
                                current_value=None,
                                required_value=effect.value,
                                is_violation=False,
                                severity="warning",
                            )
                        )

        # --- Evaluate recipient / transfer rules ---
        if current_recipients:
            for recipient in current_recipients:
                try:
                    rec_entry = self._registry.resolve_code(
                        "recipients", recipient
                    )
                except KeyError:
                    continue
                for rule in self._rules:
                    if rule.source_list != "recipients":
                        continue
                    field_val = self._get_field_value(
                        rec_entry, rule.source_field
                    )
                    if not self._matches_condition(field_val, rule.condition):
                        continue
                    for effect in rule.effects:
                        impacts.append(
                            CascadeImpact(
                                rule_id=rule.rule_id,
                                description=effect.description.get("en"),
                                source_code=recipient,
                                target_list=effect.target_list,
                                target_field=effect.target_field,
                                current_value=None,
                                required_value=effect.value,
                                is_violation=False,
                                severity=(
                                    "error"
                                    if effect.operator == "require"
                                    else "warning"
                                ),
                            )
                        )

        return impacts

    def suggest_changes(
        self,
        old_data_category: str,
        new_data_category: str,
    ) -> List[CascadeImpact]:
        """Suggest required changes when data category changes.

        Returns only NEW impacts that were not already required by the
        old data category.
        """
        old_impacts = self.evaluate_impact(old_data_category)
        new_impacts = self.evaluate_impact(new_data_category)

        old_rules = {
            (i.rule_id, i.target_list, i.required_value) for i in old_impacts
        }
        return [
            i
            for i in new_impacts
            if (i.rule_id, i.target_list, i.required_value) not in old_rules
        ]
