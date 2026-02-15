"""
Tests for opengov_oscal_pyprivacy.vocab — privacy vocabulary loading.
"""

import warnings
from pathlib import Path

import pytest

from opengov_oscal_pyprivacy.vocab import (
    load_default_privacy_vocabs,
    load_privacy_vocabs,
    PrivacyVocabs,
    Vocab,
)


@pytest.fixture(scope="module")
def vocabs() -> PrivacyVocabs:
    """Load the default privacy vocabs once for all tests in this module."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        return load_default_privacy_vocabs()


# ---------------------------------------------------------------------------
# Structural checks
# ---------------------------------------------------------------------------

class TestLoadDefaultPrivacyVocabs:
    """Verify that load_default_privacy_vocabs returns a fully populated object."""

    def test_load_default_privacy_vocabs(self, vocabs: PrivacyVocabs):
        """All six vocab sets must be loaded and non-None."""
        assert isinstance(vocabs, PrivacyVocabs)
        assert isinstance(vocabs.assurance_goals, Vocab)
        assert isinstance(vocabs.measures, Vocab)
        assert isinstance(vocabs.evidence_types, Vocab)
        assert isinstance(vocabs.maturity_domains, Vocab)
        assert isinstance(vocabs.maturity_levels, Vocab)
        assert isinstance(vocabs.mapping_schemes, Vocab)


# ---------------------------------------------------------------------------
# assurance_goals
# ---------------------------------------------------------------------------

class TestAssuranceGoalsVocab:

    def test_assurance_goals_vocab_has_keys(self, vocabs: PrivacyVocabs):
        """assurance_goals must have a non-empty keys set."""
        ag = vocabs.assurance_goals
        assert len(ag.keys) > 0

    def test_assurance_goals_expected_keys(self, vocabs: PrivacyVocabs):
        """Spot-check known SDM assurance goals."""
        expected = {"transparency", "intervenability", "unlinkability",
                    "confidentiality", "integrity", "availability"}
        assert expected.issubset(vocabs.assurance_goals.keys)

    def test_assurance_goals_has_de_labels(self, vocabs: PrivacyVocabs):
        """German labels should be present for all assurance goals."""
        ag = vocabs.assurance_goals
        assert len(ag.labels_de) == len(ag.keys)

    def test_assurance_goals_has_en_labels(self, vocabs: PrivacyVocabs):
        """English labels should be present for all assurance goals."""
        ag = vocabs.assurance_goals
        assert len(ag.labels_en) == len(ag.keys)


# ---------------------------------------------------------------------------
# measures
# ---------------------------------------------------------------------------

class TestMeasuresVocab:

    def test_measures_vocab_has_labels(self, vocabs: PrivacyVocabs):
        """measures must have non-empty keys and German labels."""
        m = vocabs.measures
        assert len(m.keys) > 0
        assert len(m.labels_de) > 0

    def test_measures_expected_keys(self, vocabs: PrivacyVocabs):
        """Spot-check known measure types."""
        expected = {"organizational", "technical"}
        assert expected.issubset(vocabs.measures.keys)


# ---------------------------------------------------------------------------
# maturity_domains
# ---------------------------------------------------------------------------

class TestMaturityDomainsVocab:

    def test_maturity_domains_loaded(self, vocabs: PrivacyVocabs):
        """maturity_domains must be non-empty."""
        md = vocabs.maturity_domains
        assert len(md.keys) > 0
        assert len(md.labels_de) > 0

    def test_maturity_domains_expected_keys(self, vocabs: PrivacyVocabs):
        """Spot-check known maturity domains."""
        expected = {"governance", "risk", "process"}
        assert expected.issubset(vocabs.maturity_domains.keys)


# ---------------------------------------------------------------------------
# maturity_levels
# ---------------------------------------------------------------------------

class TestMaturityLevelsVocab:

    def test_maturity_levels_loaded(self, vocabs: PrivacyVocabs):
        """maturity_levels must be non-empty."""
        ml = vocabs.maturity_levels
        assert len(ml.keys) > 0
        assert len(ml.labels_de) > 0

    def test_maturity_levels_five_levels(self, vocabs: PrivacyVocabs):
        """There should be exactly 5 maturity levels (1-5)."""
        ml = vocabs.maturity_levels
        expected = {"1", "2", "3", "4", "5"}
        assert ml.keys == expected


# ---------------------------------------------------------------------------
# evidence_types
# ---------------------------------------------------------------------------

class TestEvidenceTypesVocab:

    def test_evidence_types_loaded(self, vocabs: PrivacyVocabs):
        """evidence_types must be non-empty."""
        et = vocabs.evidence_types
        assert len(et.keys) > 0
        assert len(et.labels_de) > 0

    def test_evidence_types_expected_keys(self, vocabs: PrivacyVocabs):
        """Spot-check known evidence types."""
        expected = {"policy", "procedure", "record", "report"}
        assert expected.issubset(vocabs.evidence_types.keys)


# ---------------------------------------------------------------------------
# mapping_schemes
# ---------------------------------------------------------------------------

class TestMappingSchemesVocab:

    def test_mapping_schemes_loaded(self, vocabs: PrivacyVocabs):
        """mapping_schemes must be non-empty with both de and en labels."""
        ms = vocabs.mapping_schemes
        assert len(ms.keys) > 0
        assert len(ms.labels_de) > 0
        assert len(ms.labels_en) > 0

    def test_mapping_schemes_expected_keys(self, vocabs: PrivacyVocabs):
        """Spot-check known mapping schemes."""
        expected = {"sdm", "iso27001"}
        assert expected.issubset(vocabs.mapping_schemes.keys)


# ---------------------------------------------------------------------------
# Deprecation warnings
# ---------------------------------------------------------------------------

class TestDeprecationWarnings:
    """Verify that deprecated functions emit DeprecationWarning."""

    def test_load_default_emits_warning(self):
        with pytest.warns(DeprecationWarning, match="deprecated"):
            load_default_privacy_vocabs()

    def test_load_privacy_vocabs_emits_warning(self):
        with pytest.warns(DeprecationWarning, match="deprecated"):
            load_privacy_vocabs(Path("dummy"))

    def test_codelist_registry_equivalent(self, vocabs: PrivacyVocabs):
        """Verify CodelistRegistry provides same data as PrivacyVocabs."""
        from opengov_oscal_pyprivacy.codelist import CodelistRegistry

        registry = CodelistRegistry.load_defaults()
        # assurance_goals keys should match
        cl = registry.get_list("assurance-goals")
        cl_keys = {e.code for e in cl.entries if not e.deprecated}
        assert vocabs.assurance_goals.keys == cl_keys
