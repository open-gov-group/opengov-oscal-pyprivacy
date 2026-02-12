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

    def test_security_control_ref_snake_case(self):
        """SecurityControlRef must be accessible via snake_case field names."""
        ref = SecurityControlRef(catalog_id="cat-bsi", control_id="bsi-001")

        assert ref.catalog_id == "cat-bsi"
        assert ref.control_id == "bsi-001"

    def test_security_control_ref_camel_case_alias(self):
        """SecurityControlRef must accept camelCase aliases (populate_by_name)."""
        ref = SecurityControlRef(catalogId="cat-bsi", controlId="bsi-001")

        assert ref.catalog_id == "cat-bsi"
        assert ref.control_id == "bsi-001"

    def test_security_control_ref_serialization_by_alias(self):
        """model_dump(by_alias=True) must produce camelCase keys."""
        ref = SecurityControlRef(catalog_id="cat-iso", control_id="iso-042")
        data = ref.model_dump(by_alias=True)

        assert data == {"catalogId": "cat-iso", "controlId": "iso-042"}

    def test_security_control_ref_roundtrip(self):
        """Roundtrip: camelCase dict -> model -> model_dump(by_alias=True) -> back."""
        camel_dict = {"catalogId": "cat-iso", "controlId": "iso-042"}
        obj = SecurityControlRef(**camel_dict)

        assert obj.catalog_id == "cat-iso"
        assert obj.control_id == "iso-042"
        assert obj.model_dump(by_alias=True) == camel_dict

    def test_security_control_ref_serialization_snake(self):
        """model_dump() (default) must produce snake_case keys."""
        ref = SecurityControlRef(catalog_id="cat-iso", control_id="iso-042")
        data = ref.model_dump()

        assert data == {"catalog_id": "cat-iso", "control_id": "iso-042"}
        assert SecurityControlRef.model_validate(data) == ref


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

    def test_sdm_security_mapping_defaults_snake_case(self):
        """SdmSecurityMapping constructed with snake_case field names."""
        obj = SdmSecurityMapping(
            sdm_control_id="sdm-1",
            sdm_title="Verschluesselung",
        )

        assert obj.sdm_control_id == "sdm-1"
        assert obj.sdm_title == "Verschluesselung"
        assert obj.security_controls == []
        assert obj.standards == MappingStandards()
        assert obj.notes is None

    def test_sdm_security_mapping_defaults_camel_case(self):
        """SdmSecurityMapping constructed with camelCase aliases."""
        obj = SdmSecurityMapping(
            sdmControlId="sdm-1",
            sdmTitle="Verschluesselung",
        )

        assert obj.sdm_control_id == "sdm-1"
        assert obj.sdm_title == "Verschluesselung"
        assert obj.security_controls == []
        assert obj.standards == MappingStandards()
        assert obj.notes is None

    def test_sdm_security_mapping_full(self):
        """SdmSecurityMapping with all fields populated."""
        refs = [
            SecurityControlRef(catalog_id="cat-bsi", control_id="bsi-001"),
            SecurityControlRef(catalog_id="cat-iso", control_id="iso-042"),
        ]
        standards = MappingStandards(
            bsi=["BSI-100"],
            iso27001=["A.5.1"],
            iso27701=["6.2.1"],
        )

        obj = SdmSecurityMapping(
            sdm_control_id="sdm-2",
            sdm_title="Zugriffskontrolle",
            security_controls=refs,
            standards=standards,
            notes="Besondere Hinweise",
        )

        assert obj.sdm_control_id == "sdm-2"
        assert obj.sdm_title == "Zugriffskontrolle"
        assert len(obj.security_controls) == 2
        assert obj.security_controls[0].catalog_id == "cat-bsi"
        assert obj.security_controls[1].control_id == "iso-042"
        assert obj.standards.bsi == ["BSI-100"]
        assert obj.notes == "Besondere Hinweise"

    def test_sdm_security_mapping_serialization_by_alias(self):
        """model_dump(by_alias=True) must produce camelCase keys."""
        obj = SdmSecurityMapping(
            sdm_control_id="sdm-3",
            sdm_title="Protokollierung",
            security_controls=[
                SecurityControlRef(catalog_id="cat-nist", control_id="nist-au-2"),
            ],
            standards=MappingStandards(
                bsi=["BSI-OPS.1.1"],
                iso27001=["A.12.4"],
                iso27701=None,
            ),
            notes="Audit-Log-Anforderung",
        )

        data = obj.model_dump(by_alias=True)

        assert "sdmControlId" in data
        assert "sdmTitle" in data
        assert "securityControls" in data
        assert data["sdmControlId"] == "sdm-3"
        assert data["sdmTitle"] == "Protokollierung"
        assert data["securityControls"][0]["catalogId"] == "cat-nist"
        assert data["securityControls"][0]["controlId"] == "nist-au-2"

    def test_sdm_security_mapping_roundtrip(self):
        """Roundtrip: model_dump -> model_validate must yield equal object."""
        original = SdmSecurityMapping(
            sdm_control_id="sdm-3",
            sdm_title="Protokollierung",
            security_controls=[
                SecurityControlRef(catalog_id="cat-nist", control_id="nist-au-2"),
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

    def test_sdm_security_mapping_camel_case_roundtrip(self):
        """Roundtrip: camelCase dict -> model -> model_dump(by_alias=True) -> camelCase dict."""
        camel_dict = {
            "sdmControlId": "sdm-rt",
            "sdmTitle": "Roundtrip Test",
            "securityControls": [
                {"catalogId": "cat-x", "controlId": "ctrl-y"},
            ],
            "standards": {"bsi": None, "iso27001": None, "iso27701": None},
            "notes": None,
        }

        obj = SdmSecurityMapping(**camel_dict)

        assert obj.sdm_control_id == "sdm-rt"
        assert obj.sdm_title == "Roundtrip Test"
        assert obj.security_controls[0].catalog_id == "cat-x"

        dumped = obj.model_dump(by_alias=True)

        assert dumped == camel_dict
