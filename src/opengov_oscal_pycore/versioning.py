from __future__ import annotations

from datetime import datetime, timezone


def bump_version(metadata, new_version: str) -> None:
    """
    Setzt version und aktualisiert last-modified.
    Erwartet ein metadata-Objekt aus oscal-pydantic (Catalog.metadata o.ä.).
    """
    metadata.version = new_version
    metadata.last_modified = datetime.now(timezone.utc).isoformat()


def touch_metadata(metadata) -> None:
    """
    Aktualisiert nur last-modified.
    """
    metadata.last_modified = datetime.now(timezone.utc).isoformat()
