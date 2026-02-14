from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import Field

from .common import DtoBaseModel


class MappingCoverageResult(DtoBaseModel):
    total_controls: int = Field(alias="totalControls")
    mapped_controls: int = Field(alias="mappedControls")
    coverage_percent: float = Field(alias="coveragePercent")
    unmapped_control_ids: List[str] = Field(default_factory=list, alias="unmappedControlIds")
    per_group_coverage: Dict[str, float] = Field(default_factory=dict, alias="perGroupCoverage")


class TransitiveMappingPath(DtoBaseModel):
    source_id: str = Field(alias="sourceId")
    path: List[str] = Field(default_factory=list)
    target_standards: List[str] = Field(default_factory=list, alias="targetStandards")
