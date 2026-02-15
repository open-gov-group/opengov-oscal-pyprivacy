from __future__ import annotations

import csv
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Set

from .codelist import CodelistRegistry


@dataclass(frozen=True)
class Vocab:
    """Vocabulary with keys and bilingual labels.

    .. deprecated::
        Use :class:`CodelistRegistry` instead. Will be removed in v2.0.0.
    """

    keys: Set[str]
    labels_de: Dict[str, str]
    labels_en: Dict[str, str]


# Mapping: PrivacyVocabs attribute name -> JSON codelist list_id
_VOCAB_TO_CODELIST = {
    "assurance_goals": "assurance-goals",
    "measures": "measure-types",
    "evidence_types": "evidence-types",
    "maturity_domains": "maturity-domains",
    "maturity_levels": "maturity-levels",
    "mapping_schemes": "mapping-schemes",
}


def _codelist_to_vocab(registry: CodelistRegistry, list_id: str) -> Vocab:
    """Convert a JSON codelist to a legacy Vocab object."""
    cl = registry.get_list(list_id)
    keys: Set[str] = set()
    labels_de: Dict[str, str] = {}
    labels_en: Dict[str, str] = {}
    for entry in cl.entries:
        if entry.deprecated:
            continue
        keys.add(entry.code)
        labels_en[entry.code] = entry.get_label("en")
        labels_de[entry.code] = entry.get_label("de")
    return Vocab(keys=keys, labels_de=labels_de, labels_en=labels_en)


def load_vocab_csv(path: Path, delimiter: str = ";") -> Vocab:
    """Load a vocabulary from a CSV file.

    .. deprecated::
        Use :class:`CodelistRegistry` instead. Will be removed in v2.0.0.
    """
    warnings.warn(
        "load_vocab_csv() is deprecated. Use CodelistRegistry.load_defaults() instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    # Still load from CSV for backward compatibility with custom CSV files
    keys: Set[str] = set()
    labels_de: Dict[str, str] = {}
    labels_en: Dict[str, str] = {}
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        for row in reader:
            key = (row.get("key") or "").strip()
            if not key:
                continue
            keys.add(key)
            if "label_de" in row and row["label_de"]:
                labels_de[key] = row["label_de"].strip()
            if "label_en" in row and row["label_en"]:
                labels_en[key] = row["label_en"].strip()
    return Vocab(keys=keys, labels_de=labels_de, labels_en=labels_en)


@dataclass
class PrivacyVocabs:
    """Container for all privacy vocabularies.

    .. deprecated::
        Use :class:`CodelistRegistry` instead. Will be removed in v2.0.0.
    """

    assurance_goals: Vocab
    measures: Vocab
    evidence_types: Vocab
    maturity_domains: Vocab
    maturity_levels: Vocab
    mapping_schemes: Vocab


def load_privacy_vocabs(data_dir: Path) -> PrivacyVocabs:
    """Load vocabs from a data directory.

    .. deprecated::
        Use :func:`CodelistRegistry.load_defaults` instead. Will be removed in v2.0.0.

    The *data_dir* argument is ignored; data is always loaded from the
    packaged JSON codelists via :class:`CodelistRegistry`.
    """
    warnings.warn(
        "load_privacy_vocabs() is deprecated. Use CodelistRegistry.load_defaults() instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    registry = CodelistRegistry.load_defaults()
    return PrivacyVocabs(
        **{
            attr: _codelist_to_vocab(registry, list_id)
            for attr, list_id in _VOCAB_TO_CODELIST.items()
        }
    )


from importlib.resources import files


def default_data_dir() -> Path:
    """Return the packaged data directory (CSV vocabularies).

    .. deprecated::
        Use :func:`CodelistRegistry.load_defaults` instead.
    """
    return Path(str(files("opengov_oscal_pyprivacy"))) / "data"


def load_default_privacy_vocabs() -> PrivacyVocabs:
    """Load vocabs from the packaged JSON codelists.

    .. deprecated::
        Use :func:`CodelistRegistry.load_defaults` instead. Will be removed in v2.0.0.
    """
    warnings.warn(
        "load_default_privacy_vocabs() is deprecated. "
        "Use CodelistRegistry.load_defaults() instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    registry = CodelistRegistry.load_defaults()
    return PrivacyVocabs(
        **{
            attr: _codelist_to_vocab(registry, list_id)
            for attr, list_id in _VOCAB_TO_CODELIST.items()
        }
    )
