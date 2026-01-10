from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Dict


# ---------- Data model for localized texts ----------

@dataclass(frozen=True)
class LocalizedGoalText:
    """
    Localized texts for a single assurance goal in one language.
    """
    name: str
    objective: str


@dataclass(frozen=True)
class DataPrivacy_AssuranceGoalDefinition:
    """
    Language-independent metadata for a data protection assurance goal.
    """
    key: str                      # technical identifier (stable, ASCII)
    legal_basis: str              # e.g. GDPR articles
    texts_by_language: Dict[str, LocalizedGoalText]  # "en", "de", ...


    def get_text(self, language: str) -> LocalizedGoalText:
        """
        Return localized text for the given ISO language code.

        Falls back to English ("en") if the requested language is not available.
        """
        if language in self.texts_by_language:
            return self.texts_by_language[language]

        # Fallback to English if available, otherwise raise a clear error
        if "en" in self.texts_by_language:
            return self.texts_by_language["en"]

        raise KeyError(
            f"No localized text for language '{language}' "
            f"and no English fallback for goal '{self.key}'."
        )


# ---------- Abstract interface for assurance goals ----------

class DataPrivacy_AssuranceGoalBase(ABC):
    """
    Abstract interface for all assurance goals.

    This makes the public API explicit and type-safe.
    """

    @property
    @abstractmethod
    def key(self) -> str:
        """Technical identifier for the assurance goal (stable)."""
        raise NotImplementedError

    @property
    @abstractmethod
    def legal_basis(self) -> str:
        """Legal basis of the assurance goal (e.g. GDPR articles)."""
        raise NotImplementedError

    @abstractmethod
    def get_name(self, language: str = "en") -> str:
        """Return the localized name for the given language."""
        raise NotImplementedError

    @abstractmethod
    def get_objective(self, language: str = "en") -> str:
        """Return the localized objective/description for the given language."""
        raise NotImplementedError


# ---------- Enum implementation of assurance goals ----------

class AssuranceGoal(DataPrivacy_AssuranceGoalBase, Enum):
    """
    Enum of GDPR-related assurance goals used in data protection.

    Each member holds a strongly typed definition object with
    multilingual texts and a legal basis.
    """

    CONFIDENTIALITY = DataPrivacy_AssuranceGoalDefinition(
        key="confidentiality",
        legal_basis="GDPR Art. 5(1)(f), Art. 32",
        texts_by_language={
            "en": LocalizedGoalText(
                name="Confidentiality",
                objective="Prevent unauthorized disclosure of personal data."
            ),
            "de": LocalizedGoalText(
                name="Vertraulichkeit",
                objective="Unbefugte Offenlegung personenbezogener Daten verhindern."
            ),
        },
    )

    INTEGRITY = DataPrivacy_AssuranceGoalDefinition(
        key="integrity",
        legal_basis="GDPR Art. 5(1)(d), (1)(f), Art. 32",
        texts_by_language={
            "en": LocalizedGoalText(
                name="Integrity",
                objective="Ensure that personal data is accurate and protected "
                          "against unauthorized modification or destruction."
            ),
            "de": LocalizedGoalText(
                name="Integrität",
                objective="Sicherstellen, dass personenbezogene Daten korrekt sind "
                          "und vor unbefugter Veränderung oder Vernichtung geschützt werden."
            ),
        },
    )

    AVAILABILITY = DataPrivacy_AssuranceGoalDefinition(
        key="availability",
        legal_basis="GDPR Art. 5(1)(f), Art. 32(1)(b)",
        texts_by_language={
            "en": LocalizedGoalText(
                name="Availability",
                objective="Ensure that personal data is accessible and usable "
                          "when required for the intended processing."
            ),
            "de": LocalizedGoalText(
                name="Verfügbarkeit",
                objective="Sicherstellen, dass personenbezogene Daten bei Bedarf "
                          "für die vorgesehene Verarbeitung verfügbar und nutzbar sind."
            ),
        },
    )

    TRANSPARENCY = DataPrivacy_AssuranceGoalDefinition(
        key="transparency",
        legal_basis="GDPR Art. 5(1)(a), Art. 12–14",
        texts_by_language={
            "en": LocalizedGoalText(
                name="Transparency",
                objective="Provide data subjects with clear, accessible and "
                          "comprehensible information about the processing of their data."
            ),
            "de": LocalizedGoalText(
                name="Transparenz",
                objective="Betroffenen klare, zugängliche und verständliche Informationen "
                          "über die Verarbeitung ihrer Daten bereitstellen."
            ),
        },
    )

    UNLINKABILITY = DataPrivacy_AssuranceGoalDefinition(
        key="unlinkability",
        legal_basis="GDPR Art. 5(1)(c), (1)(e), Art. 25",
        texts_by_language={
            "en": LocalizedGoalText(
                name="Unlinkability",
                objective="Prevent unnecessary or unintended linking of personal data "
                          "across different processing contexts."
            ),
            "de": LocalizedGoalText(
                name="Nicht-Verkettung",
                objective="Unnötige oder unbeabsichtigte Verknüpfung personenbezogener "
                          "Daten über verschiedene Verarbeitungskontexte hinweg verhindern."
            ),
        },
    )

    INTERVENABILITY = DataPrivacy_AssuranceGoalDefinition(
        key="intervenability",
        legal_basis="GDPR Art. 16–18, Art. 21, Art. 25",
        texts_by_language={
            "en": LocalizedGoalText(
                name="Intervenability",
                objective="Enable data subjects and controllers to intervene in the "
                          "processing (e.g. rectification, erasure, restriction)."
            ),
            "de": LocalizedGoalText(
                name="Intervenierbarkeit",
                objective="Betroffenen und Verantwortlichen ermöglichen, in die "
                          "Verarbeitung einzugreifen (z. B. Berichtigung, Löschung, Einschränkung)."
            ),
        },
    )

    # --- strongly typed accessors delegating to the underlying definition ---

    @property
    def definition(self) -> DataPrivacy_AssuranceGoalDefinition:
        """
        Strongly typed access to the underlying definition object.

        Use this if you need full access to all metadata and translations.
        """
        return self.value

    @property
    def key(self) -> str:
        """Technical identifier for the assurance goal (stable)."""
        return self.definition.key

    @property
    def legal_basis(self) -> str:
        """Legal basis of the assurance goal (e.g. GDPR articles)."""
        return self.definition.legal_basis

    def get_name(self, language: str = "en") -> str:
        """Return the localized name for the given language (default: English)."""
        return self.definition.get_text(language).name

    def get_objective(self, language: str = "en") -> str:
        """Return the localized objective for the given language (default: English)."""
        return self.definition.get_text(language).objective
