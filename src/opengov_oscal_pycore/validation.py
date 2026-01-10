"""
Validation-Helper für OSCAL-Objekte.

In v1 kann das ein Stub sein; später:
- JSON-Schema-Validation
- evtl. Custom-Checks (z.B. ID-Konventionen)
"""

from __future__ import annotations
from pydantic import BaseModel


def validate_oscal(model: BaseModel) -> None:
    """
    Platzhalter-Funktion.

    Später:
    - Schema-Validierung gegen offizielle OSCAL-Schemas.
    - Raise aussagekräftige Exceptions bei Fehlern.
    """
    # TODO: implement
    return
