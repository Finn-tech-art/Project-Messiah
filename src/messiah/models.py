#Defines the business language for the whole system.

# What it should do.
# Model multi-service jobs, not just coding tasks
# Encode sellable, low ambiguity work: service line, job type, status, risks.
# Carry the fields that matter commercially: acceptance criteria, deliverables, priceband, confidence, evidence,operator approval
# add a success selection layer so later nodes can prefer jobs with clear scope, strong proof and lower rejection risk
"""Core domain models for Project Messiah's scoped-work workflow."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Literal, TypedDict


def _validate_score(name: str, value: float) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be between 0.0 and 1.0; got {value!r}")


class ServiceLine(StrEnum):
    TECHNICAL_DELIVERY = "technical_delivery"
    RESEARCH_BRIEF = "research_brief"
    DATA_CLEANUP = "data_cleanup"
    STRUCTURED_CONTENT = "structured_content"
    OPS_ADMIN_EXECUTION = "ops_admin_execution"
    SALES_ENABLEMENT = "sales_enablement"
    SUPPORT_OPS = "support_ops"


class JobType(StrEnum):
    BUG_RESCUE = "bug_rescue"
    CODEBASE_HEALTH_AUDIT = "codebase_health_audit"
    CI_DEPLOY_RECOVERY = "ci_deploy_recovery"
    AUTOMATION_SPRINT = "automation_sprint"
    AI_OUTPUT_QA = "ai_output_qa"
    RESEARCH_BRIEF_SPRINT = "research_brief_sprint"
    COMPETITOR_RESEARCH = "competitor_research"
    TOOL_COMPARISON = "tool_comparison"
    DATA_CLEANUP_SPRINT = "data_cleanup_sprint"
    CRM_DATA_CLEANUP = "crm_data_cleanup"
    LEAD_LIST_ENRICHMENT = "lead_list_enrichment"
    CONTENT_SYSTEM_PACK = "content_system_pack"
    LANDING_PAGE_REWRITE = "landing_page_rewrite"
    FAQ_GENERATION = "faq_generation"
    HELP_CENTER_DRAFTING = "help_center_drafting"
    TICKET_CLASSIFICATION = "ticket_classification"
    SALES_RESEARCH_DOSSIER = "sales_research_dossier"
    PROPOSAL_DRAFTING = "proposal_drafting"
    REPORTING_PACK = "reporting_pack"
    SOP_FORMATTING = "sop_formatting"


class JobStatus(StrEnum):
    DRAFT = "draft"
    INTAKE = "intake"
    UNDER_REVIEW = "under_review"
    QUALIFIED = "qualified"
    REJECTED = "rejected"
    AWAITING_OPERATOR_APPROVAL = "awaiting_operator_approval"
    APPROVED = "approved"
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    READY_FOR_DELIVERY = "ready_for_delivery"
    DELIVERED = "delivered"


class RiskFlag(StrEnum):
    VAGUE_SCOPE = "vague_scope"
    MISSING_ACCEPTANCE_CRITERIA = "missing_acceptance_criteria"
    SUBJECTIVE_OUTPUT = "subjective_output"
    LOW_MARGIN = "low_margin"
    MISSING_ACCESS = "missing_access"
    TIGHT_DEADLINE = "tight_deadline"
    REGULATED_DOMAIN = "regulated_domain"
    POLICY_RISK = "policy_risk"
    DATA_QUALITY_RISK = "data_quality_risk"
    DEPENDENCY_RISK = "dependency_risk"
    CONTESTED_MARKET = "contested_market"
    LOW_CONFIDENCE = "low_confidence"


class EvidenceKind(StrEnum):
    CLIENT_INPUT = "client_input"
    SOURCE_MATERIAL = "source_material"
    VALIDATION_NOTE = "validation_note"
    DELIVERY_ARTIFACT = "delivery_artifact"
    METRIC = "metric"
    OPERATOR_NOTE = "operator_note"


class ApprovalDecision(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class EffortTier(StrEnum):
    TINY = "tiny"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


EvidenceSource = Literal["fixture", "form", "operator", "model", "system", "external"]


@dataclass(slots=True, kw_only=True)
class AcceptanceCriterion:
    description: str
    measurable: bool = True
    source: str | None = None


@dataclass(slots=True, kw_only=True)
class Deliverable:
    name: str
    description: str
    format: str
    required: bool = True


@dataclass(slots=True, kw_only=True)
class PriceBand:
    minimum: float
    maximum: float
    currency: str = "USD"
    rationale: str = ""

    def __post_init__(self) -> None:
        if self.minimum < 0 or self.maximum < 0:
            raise ValueError("price values must be non-negative")
        if self.minimum > self.maximum:
            raise ValueError("minimum price cannot exceed maximum price")


@dataclass(slots=True, kw_only=True)
class EvidenceItem:
    kind: EvidenceKind
    summary: str
    source: EvidenceSource
    reference: str | None = None
    confidence: float = 1.0

    def __post_init__(self) -> None:
        _validate_score("confidence", self.confidence)


@dataclass(slots=True, kw_only=True)
class OperatorApproval:
    decision: ApprovalDecision = ApprovalDecision.PENDING
    required: bool = False
    reviewer: str | None = None
    note: str = ""
    timestamp: datetime | None = None


@dataclass(slots=True, kw_only=True)
class SuccessProfile:
    """Selection signals for whether a job is worth pursuing."""

    scope_clarity: float
    acceptance_clarity: float
    evidence_readiness: float
    delivery_confidence: float
    margin_fit: float
    rejection_risk: float
    repeatability: float
    notes: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        _validate_score("scope_clarity", self.scope_clarity)
        _validate_score("acceptance_clarity", self.acceptance_clarity)
        _validate_score("evidence_readiness", self.evidence_readiness)
        _validate_score("delivery_confidence", self.delivery_confidence)
        _validate_score("margin_fit", self.margin_fit)
        _validate_score("rejection_risk", self.rejection_risk)
        _validate_score("repeatability", self.repeatability)


@dataclass(slots=True, kw_only=True)
class JobBrief:
    job_id: str
    title: str
    summary: str
    requested_outcome: str
    source_channel: str
    raw_request: str = ""
    service_line_hint: ServiceLine | None = None
    job_type_hint: JobType | None = None
    inputs: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    acceptance_criteria: list[AcceptanceCriterion] = field(default_factory=list)
    deliverables: list[Deliverable] = field(default_factory=list)
    budget_hint: PriceBand | None = None
    deadline: datetime | None = None
    operator_notes: list[str] = field(default_factory=list)
    evidence: list[EvidenceItem] = field(default_factory=list)


@dataclass(slots=True, kw_only=True)
class QualificationResult:
    qualified: bool
    service_line: ServiceLine | None
    job_type: JobType | None
    rationale: str
    success_profile: SuccessProfile
    confidence: float
    risk_flags: list[RiskFlag] = field(default_factory=list)
    missing_information: list[str] = field(default_factory=list)
    extracted_acceptance_criteria: list[AcceptanceCriterion] = field(default_factory=list)
    extracted_deliverables: list[Deliverable] = field(default_factory=list)
    operator_approval_required: bool = False
    evidence: list[EvidenceItem] = field(default_factory=list)

    def __post_init__(self) -> None:
        _validate_score("confidence", self.confidence)


@dataclass(slots=True, kw_only=True)
class Estimate:
    price_band: PriceBand
    estimated_hours_low: float
    estimated_hours_high: float
    effort_tier: EffortTier
    confidence: float
    assumptions: list[str] = field(default_factory=list)
    likely_margin_note: str = ""
    evidence: list[EvidenceItem] = field(default_factory=list)
    operator_approval_required: bool = False

    def __post_init__(self) -> None:
        _validate_score("confidence", self.confidence)
        if self.estimated_hours_low < 0 or self.estimated_hours_high < 0:
            raise ValueError("estimated hours must be non-negative")
        if self.estimated_hours_low > self.estimated_hours_high:
            raise ValueError("estimated_hours_low cannot exceed estimated_hours_high")


@dataclass(slots=True, kw_only=True)
class PlanStep:
    step_id: str
    title: str
    description: str
    owner: Literal["agent", "operator"] = "agent"
    required_inputs: list[str] = field(default_factory=list)
    expected_outputs: list[str] = field(default_factory=list)
    evidence_requirements: list[str] = field(default_factory=list)
    requires_operator_approval: bool = False


@dataclass(slots=True, kw_only=True)
class ExecutionPlan:
    summary: str
    objectives: list[str]
    steps: list[PlanStep]
    delivery_artifacts: list[str]
    approval_gates: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    evidence_requirements: list[str] = field(default_factory=list)
    confidence: float = 1.0
    operator_approval_required: bool = False

    def __post_init__(self) -> None:
        _validate_score("confidence", self.confidence)


@dataclass(slots=True, kw_only=True)
class ChecklistItem:
    item: str
    linked_acceptance_criterion: str | None = None
    proof_note: str = ""
    required: bool = True
    completed: bool = False


@dataclass(slots=True, kw_only=True)
class DeliveryChecklist:
    items: list[ChecklistItem]
    required_deliverables: list[str]
    final_validation_notes: list[str] = field(default_factory=list)
    confidence: float = 1.0
    evidence: list[EvidenceItem] = field(default_factory=list)
    operator_signoff_required: bool = False

    def __post_init__(self) -> None:
        _validate_score("confidence", self.confidence)


class MessiahState(TypedDict, total=False):
    """Shared LangGraph state for the dry-run delivery workflow."""

    run_id: str
    job_status: JobStatus
    job_brief: JobBrief
    qualification: QualificationResult
    estimate: Estimate
    execution_plan: ExecutionPlan
    delivery_checklist: DeliveryChecklist
    operator_approval: OperatorApproval
    evidence: list[EvidenceItem]
    output_artifacts: list[str]
    messages: list[str]
    errors: list[str]


__all__ = [
    "AcceptanceCriterion",
    "ApprovalDecision",
    "ChecklistItem",
    "Deliverable",
    "DeliveryChecklist",
    "EffortTier",
    "Estimate",
    "EvidenceItem",
    "EvidenceKind",
    "ExecutionPlan",
    "JobBrief",
    "JobStatus",
    "JobType",
    "MessiahState",
    "OperatorApproval",
    "PlanStep",
    "PriceBand",
    "QualificationResult",
    "RiskFlag",
    "ServiceLine",
    "SuccessProfile",
]
