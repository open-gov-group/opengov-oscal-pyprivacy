from enum import Enum





class DpGoal(str, Enum):
    CONFIDENTIALITY = "confidentiality"
    INTEGRITY = "integrity"
    AVAILABILITY = "availability"
    TRANSPARENCY = "transparency"
    INTERVENABILITY = "intervenability"
    UNLINKABILITY = "unlinkability"
    


class SdmModule(str, Enum):
    ORGANIZATIONAL = "organizational"
    TECHNICAL = "technical"
    PHYSICAL = "physical"
    PERSONNEL = "personnel"
    

class ImplementationLevel(str, Enum):
    NOT_APPLICABLE = "n/a"
    PLANNED = "planned"
    PARTIAL = "partial"
    IMPLEMENTED = "implemented"
    OPTIMIZED = "optimized"


class RiskLevel(str, Enum):
    VERY_LOW = "very-low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very-high"
