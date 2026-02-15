"""
Validate OSCAL documents against official NIST OSCAL JSON Schemas.

Design: Schemas are downloaded lazily from GitHub and cached locally in
``~/.cache/opengov-oscal/schemas/``.  Callers can also supply a local
schema file via the *schema_path* parameter to avoid network access
(recommended for tests and CI).

``jsonschema`` is an *optional* dependency -- a clear error message is
raised at validation time if it is not installed.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Literal, Optional
from urllib.request import urlopen

OSCAL_SCHEMA_BASE_URL = (
    "https://raw.githubusercontent.com/usnistgov/OSCAL/main/json/schema"
)

OSCAL_SCHEMA_FILES = {
    "catalog": "oscal_catalog_schema.json",
    "profile": "oscal_profile_schema.json",
    "component-definition": "oscal_component_schema.json",
    "system-security-plan": "oscal_ssp_schema.json",
}

OscalType = Literal[
    "catalog", "profile", "component-definition", "system-security-plan"
]


@dataclass
class SchemaValidationIssue:
    """A single JSON-Schema validation finding."""

    path: str
    message: str
    schema_path: str = ""


@dataclass
class SchemaValidationResult:
    """Aggregated result of a JSON-Schema validation run."""

    valid: bool
    issues: List[SchemaValidationIssue] = field(default_factory=list)
    schema_version: str = ""


# ---------------------------------------------------------------------------
# Schema loading helpers
# ---------------------------------------------------------------------------

def _get_cache_dir() -> Path:
    """Return the cache directory for OSCAL schemas."""
    cache = Path.home() / ".cache" / "opengov-oscal" / "schemas"
    cache.mkdir(parents=True, exist_ok=True)
    return cache


def _download_schema(oscal_type: OscalType, cache_dir: Optional[Path] = None) -> dict:
    """Download and cache an OSCAL JSON schema.

    If the schema already exists in *cache_dir* it is loaded from disk.
    """
    if cache_dir is None:
        cache_dir = _get_cache_dir()

    filename = OSCAL_SCHEMA_FILES[oscal_type]
    cache_file = cache_dir / filename

    if cache_file.exists():
        return json.loads(cache_file.read_text(encoding="utf-8"))

    url = f"{OSCAL_SCHEMA_BASE_URL}/{filename}"
    try:
        with urlopen(url, timeout=30) as resp:  # noqa: S310
            data = resp.read().decode("utf-8")
        cache_file.write_text(data, encoding="utf-8")
        return json.loads(data)
    except Exception as exc:
        raise RuntimeError(
            f"Failed to download OSCAL schema from {url}: {exc}. "
            f"You can manually place the schema at {cache_file}"
        ) from exc


def _load_schema(
    oscal_type: OscalType,
    *,
    schema_path: Optional[Path] = None,
) -> dict:
    """Load an OSCAL schema from a local path or download it."""
    if schema_path is not None:
        return json.loads(schema_path.read_text(encoding="utf-8"))
    return _download_schema(oscal_type)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def validate_against_oscal_schema(
    data: dict,
    oscal_type: OscalType,
    *,
    schema_path: Optional[Path] = None,
) -> SchemaValidationResult:
    """Validate an OSCAL document dict against the official JSON Schema.

    Args:
        data: The OSCAL document as a dict (with or without root wrapper).
        oscal_type: One of ``"catalog"``, ``"profile"``,
            ``"component-definition"``, ``"system-security-plan"``.
        schema_path: Optional path to a local schema file (skips download).

    Returns:
        A :class:`SchemaValidationResult` with a *valid* flag, a list of
        :class:`SchemaValidationIssue` objects, and the *schema_version*
        extracted from the schema ``$id``.
    """
    try:
        import jsonschema  # noqa: F811
    except ImportError:
        raise ImportError(
            "jsonschema is required for schema validation. "
            "Install it with: pip install jsonschema>=4.0"
        )

    schema = _load_schema(oscal_type, schema_path=schema_path)
    schema_version = schema.get("$id", "unknown")

    # Auto-detect the correct validator class for the schema draft
    validator_cls = jsonschema.validators.validator_for(schema)
    validator = validator_cls(schema)

    issues: List[SchemaValidationIssue] = []

    for error in sorted(validator.iter_errors(data), key=lambda e: list(e.path)):
        path = ".".join(str(p) for p in error.absolute_path) or "$"
        schema_p = ".".join(str(p) for p in error.absolute_schema_path) or "$"
        issues.append(
            SchemaValidationIssue(
                path=path,
                message=error.message,
                schema_path=schema_p,
            )
        )

    return SchemaValidationResult(
        valid=len(issues) == 0,
        issues=issues,
        schema_version=schema_version,
    )
