"""Tests for DTO models: SDM-TOM (#5), Resilience (#6), Mapping Workbench (#6)."""

import pytest

from opengov_oscal_pyprivacy.dto import (
    # SDM-TOM (#5)
    SdmTomControlSummary,
    SdmTomControlDetail,
    # Resilience (#6)
    SecurityControl,
    SecurityControlUpdateRequest,
    # Mapping Workbench (#6)
    SecurityControlRef,
    MappingStandards,
    SdmSecurityMapping,
)


# ---------------------------------------------------------------------------
# SDM-TOM DTOs (#5)
# ---------------------------------------------------------------------------

class TestSdmTomControlSummary:

    def test_sdm_tom_summary_defaults(self):
        """SdmTomControlSummary with only id+title must have correct defaults."""
        obj = SdmTomControlSummary(id="tom-1", title="Verschluesselung")

        assert obj.id == "tom-1"
        assert obj.title == "Verschluesselung"
        assert obj.sdm_module is None
        assert obj.sdm_goals == []
        assert obj.dsgvo_articles == []

    def test_sdm_tom_summary_full(self):
        """SdmTomControlSummary with all fields populated."""
        obj = SdmTomControlSummary(
            id="tom-2",
            title="Pseudonymisierung",
            sdm_module="Datenminimierung",
            sdm_goals=["Vertraulichkeit", "Integritaet"],
            dsgvo_articles=["Art. 25", "Art. 32"],
        )

        assert obj.id == "tom-2"
        assert obj.title == "Pseudonymisierung"
        assert obj.sdm_module == "Datenminimierung"
        assert obj.sdm_goals == ["Vertraulichkeit", "Integritaet"]
        assert obj.dsgvo_articles == ["Art. 25", "Art. 32"]


class TestSdmTomControlDetail:

    def test_sdm_tom_detail_inherits_summary(self):
        """SdmTomControlDetail must inherit all fields from SdmTomControlSummary."""
        assert issubclass(SdmTomControlDetail, SdmTomControlSummary)

        obj = SdmTomControlDetail(
            id="tom-3",
            title="Zutrittskontrolle",
            sdm_module="Verfuegbarkeit",
            sdm_goals=["Verfuegbarkeit"],
            dsgvo_articles=["Art. 32"],
            description="Beschreibung der Zutrittskontrolle",
            implementation_hints="Empfohlene Umsetzung",
        )

        # Summary fields
        assert obj.id == "tom-3"
        assert obj.title == "Zutrittskontrolle"
        assert obj.sdm_module == "Verfuegbarkeit"
        assert obj.sdm_goals == ["Verfuegbarkeit"]
        assert obj.dsgvo_articles == ["Art. 32"]

        # Detail-only fields
        assert obj.description == "Beschreibung der Zutrittskontrolle"
        assert obj.implementation_hints == "Empfohlene Umsetzung"

    def test_sdm_tom_detail_defaults(self):
        """Detail-only fields must default to None."""
        obj = SdmTomControlDetail(id="tom-4", title="Minimal")

        assert obj.description is None
        assert obj.implementation_hints is None

    def test_sdm_tom_detail_serialization(self):
        """Roundtrip: model_dump -> model_validate must yield equal object."""
        original = SdmTomControlDetail(
            id="tom-5",
            title="Eingabekontrolle",
            sdm_module="Transparenz",
            sdm_goals=["Transparenz", "Intervenierbarkeit"],
            dsgvo_articles=["Art. 5", "Art. 25"],
            description="Protokollierung aller Eingaben",
            implementation_hints="Logging-Framework nutzen",
        )

        data = original.model_dump()
        restored = SdmTomControlDetail.model_validate(data)

        assert restored == original
        assert restored.model_dump() == data


# ---------------------------------------------------------------------------
# Resilience DTOs (#6)
# ---------------------------------------------------------------------------

class TestSecurityControl:

    def test_security_control_minimal(self):
        """SecurityControl with only id+title must have correct defaults."""
        obj = SecurityControl(id="sc-1", title="Firewall")

        assert obj.id == "sc-1"
        assert obj.title == "Firewall"
        assert obj.class_ is None
        assert obj.domain is None
        assert obj.objective is None
        assert obj.description is None

    def test_security_control_full(self):
        """SecurityControl with all fields populated."""
        obj = SecurityControl(
            id="sc-2",
            title="Intrusion Detection",
            class_="technical",
            domain="network",
            objective="Detect unauthorized access",
            description="Monitor network traffic for suspicious activity",
        )

        assert obj.id == "sc-2"
        assert obj.title == "Intrusion Detection"
        assert obj.class_ == "technical"
        assert obj.domain == "network"
        assert obj.objective == "Detect unauthorized access"
        assert obj.description == "Monitor network traffic for suspicious activity"

    def test_security_control_serialization(self):
        """Roundtrip: model_dump -> model_validate must yield equal object."""
        original = SecurityControl(
            id="sc-3",
            title="Access Control",
            class_="organizational",
            domain="identity",
            objective="Restrict system access",
            description="Role-based access control implementation",
        )

        data = original.model_dump()
        restored = SecurityControl.model_validate(data)

        assert restored == original


class TestSecurityControlUpdateRequest:

    def test_security_control_update_request_all_none(self):
        """All fields must be optional and default to None."""
        obj = SecurityControlUpdateRequest()

        assert obj.title is None
        assert obj.domain is None
        assert obj.objective is None
        assert obj.description is None

    def test_security_control_update_request_partial(self):
        """Partial update: only some fields set."""
        obj = SecurityControlUpdateRequest(
            title="Updated Title",
            domain="updated-domain",
        )

        assert obj.title == "Updated Title"
        assert obj.domain == "updated-domain"
        assert obj.objective is None
        assert obj.description is None

    def test_security_control_update_request_exclude_unset(self):
        """model_dump(exclude_unset=True) should only contain explicitly set fields."""
        obj = SecurityControlUpdateRequest(title="Only Title")
        data = obj.model_dump(exclude_unset=True)

        assert data == {"title": "Only Title"}


# ---------------------------------------------------------------------------
# Mapping Workbench DTOs (#6)
# ---------------------------------------------------------------------------

class TestSecurityControlRef:

    def test_security_control_ref(self):
        """SecurityControlRef must carry catalogId and controlId."""
        ref = SecurityControlRef(catalogId="cat-bsi", controlId="bsi-001")

        assert ref.catalogId == "cat-bsi"
        assert ref.controlId == "bsi-001"

    def test_security_control_ref_serialization(self):
        """Roundtrip for SecurityControlRef."""
        original = SecurityControlRef(catalogId="cat-iso", controlId="iso-042")
        data = original.model_dump()

        assert data == {"catalogId": "cat-iso", "controlId": "iso-042"}
        assert SecurityControlRef.model_validate(data) == original


class TestMappingStandards:

    def test_mapping_standards_defaults(self):
        """All fields must default to None."""
        obj = MappingStandards()

        assert obj.bsi is None
        assert obj.iso27001 is None
        assert obj.iso27701 is None

    def test_mapping_standards_full(self):
        """MappingStandards with all fields populated."""
        obj = MappingStandards(
            bsi=["BSI-100", "BSI-200"],
            iso27001=["A.5.1", "A.6.1"],
            iso27701=["6.2.1"],
        )

        assert obj.bsi == ["BSI-100", "BSI-200"]
        assert obj.iso27001 == ["A.5.1", "A.6.1"]
        assert obj.iso27701 == ["6.2.1"]

    def test_mapping_standards_serialization(self):
        """Roundtrip for MappingStandards."""
        original = MappingStandards(
            bsi=["BSI-300"],
            iso27001=None,
            iso27701=["7.1.1", "7.2.1"],
        )

        data = original.model_dump()
        restored = MappingStandards.model_validate(data)

        assert restored == original


class TestSdmSecurityMapping:

    def test_sdm_security_mapping_defaults(self):
        """SdmSecurityMapping with only required fields."""
        obj = SdmSecurityMapping(
            sdmControlId="sdm-1",
            sdmTitle="Verschluesselung",
        )

        assert obj.sdmControlId == "sdm-1"
        assert obj.sdmTitle == "Verschluesselung"
        assert obj.securityControls == []
        assert obj.standards == MappingStandards()
        assert obj.notes is None

    def test_sdm_security_mapping_full(self):
        """SdmSecurityMapping with all fields populated."""
        refs = [
            SecurityControlRef(catalogId="cat-bsi", controlId="bsi-001"),
            SecurityControlRef(catalogId="cat-iso", controlId="iso-042"),
        ]
        standards = MappingStandards(
            bsi=["BSI-100"],
            iso27001=["A.5.1"],
            iso27701=["6.2.1"],
        )

        obj = SdmSecurityMapping(
            sdmControlId="sdm-2",
            sdmTitle="Zugriffskontrolle",
            securityControls=refs,
            standards=standards,
            notes="Besondere Hinweise",
        )

        assert obj.sdmControlId == "sdm-2"
        assert obj.sdmTitle == "Zugriffskontrolle"
        assert len(obj.securityControls) == 2
        assert obj.securityControls[0].catalogId == "cat-bsi"
        assert obj.securityControls[1].controlId == "iso-042"
        assert obj.standards.bsi == ["BSI-100"]
        assert obj.notes == "Besondere Hinweise"

    def test_sdm_security_mapping_serialization(self):
        """Roundtrip: model_dump -> model_validate must yield equal object."""
        original = SdmSecurityMapping(
            sdmControlId="sdm-3",
            sdmTitle="Protokollierung",
            securityControls=[
                SecurityControlRef(catalogId="cat-nist", controlId="nist-au-2"),
            ],
            standards=MappingStandards(
                bsi=["BSI-OPS.1.1"],
                iso27001=["A.12.4"],
                iso27701=None,
            ),
            notes="Audit-Log-Anforderung",
        )

        data = original.model_dump()
        restored = SdmSecurityMapping.model_validate(data)

        assert restored == original
        assert restored.model_dump() == data
