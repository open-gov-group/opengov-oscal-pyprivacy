from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Set, Optional


@dataclass(frozen=True)
class Vocab:
    keys: Set[str]
    labels_de: Dict[str, str]
    labels_en: Dict[str, str]


def load_vocab_csv(path: Path, delimiter: str = ";") -> Vocab:
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
    assurance_goals: Vocab
    measures: Vocab
    evidence_types: Vocab
    maturity_domains: Vocab
    maturity_levels: Vocab
    mapping_schemes: Vocab

def load_privacy_vocabs(data_dir: Path) -> PrivacyVocabs:
    return PrivacyVocabs(
        assurance_goals=load_vocab_csv(data_dir / "assurance_goals.csv"),
        measures=load_vocab_csv(data_dir / "measures.csv"),
        evidence_types=load_vocab_csv(data_dir / "evidence_types.csv"),
        maturity_domains=load_vocab_csv(data_dir / "maturity_domains.csv"),
        maturity_levels=load_vocab_csv(data_dir / "maturity_levels.csv"),
        mapping_schemes=load_vocab_csv(data_dir / "mapping_schemes.csv"),
    )

from importlib.resources import files


def default_data_dir() -> Path:
    """Return the packaged data directory (CSV vocabularies)."""
    return Path(files("opengov_oscal_pyprivacy")) / "data"


def load_default_privacy_vocabs() -> PrivacyVocabs:
    """Load vocabs from the packaged CSV data directory."""
    return load_privacy_vocabs(default_data_dir())
