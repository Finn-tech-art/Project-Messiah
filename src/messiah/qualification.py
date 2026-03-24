# To decide whether a normalized job is worth pursuing.
# classify job as service_line and job_type
# reject or caution on vague, risky, low-margin, or weakly provable work
# build a successful profile so later steps can favor jobs with high acceptance probability.
# set operator review when the job might be viable but still needs human judgement.

"""Qualification rules for Project Messiah."""

from __future__ import annotations

from messiah.models import (
    AcceptanceCriterion,
    Deliverable,
    EvidenceItem,
    EvidenceKind,
    JobBrief,
    JobStatus,
    JobType,
    MessiahState,
    QualificationResult,
    RiskFlag,
    ServiceLine,
    SuccessProfile,
)


def _combined_text(job: JobBrief) -> str:
    parts = [
        job.title,
        job.summary,
        job.requested_outcome,
        job.raw_request,
        " ".join(job.inputs),
        " ".join(job.constraints),
        " ".join(note for note in job.operator_notes),
    ]
    return " ".join(part for part in parts if part).lower()


def _detect_service_line(job: JobBrief) -> ServiceLine | None:
    if job.service_line_hint is not None:
        return job.service_line_hint

    text = _combined_text(job)

    keyword_groups = [
        (
            ServiceLine.TECHNICAL_DELIVERY,
            [
                "bug",
                "deploy",
                "deployment",
                "ci",
                "api",
                "webhook",
                "repo",
                "repository",
                "integration",
                "automation",
                "test",
                "debug",
                "fix",
                "code",
            ],
        ),
        (
            ServiceLine.RESEARCH_BRIEF,
            [
                "research",
                "competitor",
                "market",
                "vendor",
                "shortlist",
                "brief",
                "comparison",
                "landscape",
                "sources",
            ],
        ),
        (
            ServiceLine.DATA_CLEANUP,
            [
                "spreadsheet",
                "csv",
                "deduplicate",
                "dedupe",
                "normalize",
                "cleanup",
                "clean up",
                "crm export",
                "messy data",
                "lead list",
            ],
        ),
        (
            ServiceLine.STRUCTURED_CONTENT,
            [
                "landing page",
                "faq",
                "email sequence",
                "rewrite",
                "content",
                "copy",
                "help center",
                "product description",
            ],
        ),
        (
            ServiceLine.OPS_ADMIN_EXECUTION,
            [
                "sop",
                "inbox",
                "triage",
                "admin",
                "reporting",
                "weekly report",
                "document conversion",
                "data entry",
            ],
        ),
        (
            ServiceLine.SALES_ENABLEMENT,
            [
                "icp",
                "proposal",
                "lead qualification",
                "outreach",
                "sales",
                "prospect",
                "dossier",
                "follow-up",
            ],
        ),
        (
            ServiceLine.SUPPORT_OPS,
            [
                "ticket",
                "support",
                "escalation",
                "canned response",
                "knowledge base",
                "churn",
                "call transcript",
            ],
        ),
    ]

    best_match: ServiceLine | None = None
    best_score = 0
    for service_line, keywords in keyword_groups:
        score = sum(1 for keyword in keywords if keyword in text)
        if score > best_score:
            best_score = score
            best_match = service_line

    return best_match


def _detect_job_type(job: JobBrief, service_line: ServiceLine | None) -> JobType | None:
    if job.job_type_hint is not None:
        return job.job_type_hint

    text = _combined_text(job)

    if service_line == ServiceLine.TECHNICAL_DELIVERY:
        if "audit" in text or "health" in text:
            return JobType.CODEBASE_HEALTH_AUDIT
        if "deploy" in text or "pipeline" in text or "ci" in text:
            return JobType.CI_DEPLOY_RECOVERY
        if "qa" in text and "ai" in text:
            return JobType.AI_OUTPUT_QA
        if "automation" in text:
            return JobType.AUTOMATION_SPRINT
        if "bug" in text or "fix" in text or "debug" in text:
            return JobType.BUG_RESCUE

    if service_line == ServiceLine.RESEARCH_BRIEF:
        if "competitor" in text:
            return JobType.COMPETITOR_RESEARCH
        if "comparison" in text or "compare" in text or "shortlist" in text:
            return JobType.TOOL_COMPARISON
        return JobType.RESEARCH_BRIEF_SPRINT

    if service_line == ServiceLine.DATA_CLEANUP:
        if "crm" in text:
            return JobType.CRM_DATA_CLEANUP
        if "lead" in text and ("enrich" in text or "enrichment" in text):
            return JobType.LEAD_LIST_ENRICHMENT
        return JobType.DATA_CLEANUP_SPRINT

    if service_line == ServiceLine.STRUCTURED_CONTENT:
        if "landing page" in text:
            return JobType.LANDING_PAGE_REWRITE
        if "faq" in text:
            return JobType.FAQ_GENERATION
        if "help center" in text:
            return JobType.HELP_CENTER_DRAFTING
        return JobType.CONTENT_SYSTEM_PACK

    if service_line == ServiceLine.OPS_ADMIN_EXECUTION:
        if "sop" in text:
            return JobType.SOP_FORMATTING
        return JobType.REPORTING_PACK

    if service_line == ServiceLine.SALES_ENABLEMENT:
        if "proposal" in text:
            return JobType.PROPOSAL_DRAFTING
        return JobType.SALES_RESEARCH_DOSSIER

    if service_line == ServiceLine.SUPPORT_OPS:
        if "ticket" in text or "classification" in text:
            return JobType.TICKET_CLASSIFICATION
        return JobType.HELP_CENTER_DRAFTING

    return None


def _deliverable_names(deliverables: list[Deliverable]) -> list[str]:
    return [item.name.lower() for item in deliverables]


def _acceptance_text(criteria: list[AcceptanceCriterion]) -> str:
    return " ".join(item.description.lower() for item in criteria)


def _derive_risk_flags(job: JobBrief, service_line: ServiceLine | None) -> list[RiskFlag]:
    text = _combined_text(job)
    flags: list[RiskFlag] = []

    if len(job.summary.strip()) < 25 and not job.acceptance_criteria:
        flags.append(RiskFlag.VAGUE_SCOPE)

    if not job.acceptance_criteria:
        flags.append(RiskFlag.MISSING_ACCEPTANCE_CRITERIA)

    if not job.deliverables:
        flags.append(RiskFlag.LOW_CONFIDENCE)

    subjective_markers = ["creative", "viral", "make it amazing", "make it better", "opinion"]
    if any(marker in text for marker in subjective_markers):
        flags.append(RiskFlag.SUBJECTIVE_OUTPUT)

    if any(marker in text for marker in ["legal", "medical", "diagnosis", "lawsuit", "tax advice"]):
        flags.append(RiskFlag.REGULATED_DOMAIN)

    if any(marker in text for marker in ["bypass", "fake account", "impersonate", "evade"]):
        flags.append(RiskFlag.POLICY_RISK)

    if any(marker in text for marker in ["urgent", "asap", "today", "within 1 hour"]):
        flags.append(RiskFlag.TIGHT_DEADLINE)

    if service_line == ServiceLine.TECHNICAL_DELIVERY and not job.inputs:
        flags.append(RiskFlag.MISSING_ACCESS)

    if service_line == ServiceLine.DATA_CLEANUP and not job.inputs:
        flags.append(RiskFlag.DATA_QUALITY_RISK)

    if job.budget_hint and job.budget_hint.maximum <= 30:
        flags.append(RiskFlag.LOW_MARGIN)

    return flags


def _build_success_profile(job: JobBrief, flags: list[RiskFlag]) -> SuccessProfile:
    scope_clarity = min(1.0, 0.35 + (0.2 if job.summary else 0.0) + (0.25 if job.inputs else 0.0))
    acceptance_clarity = min(1.0, 0.3 + 0.25 * len(job.acceptance_criteria))
    evidence_readiness = min(
        1.0,
        0.25
        + (0.25 if job.inputs else 0.0)
        + (0.2 if job.deliverables else 0.0)
        + (0.15 if job.raw_request else 0.0),
    )
    delivery_confidence = min(
        1.0,
        0.3
        + (0.2 if job.inputs else 0.0)
        + (0.2 if job.acceptance_criteria else 0.0)
        + (0.15 if job.deliverables else 0.0),
    )
    margin_fit = 0.6
    if job.budget_hint:
        if job.budget_hint.maximum >= 150:
            margin_fit = 0.9
        elif job.budget_hint.maximum >= 75:
            margin_fit = 0.75
        elif job.budget_hint.maximum < 40:
            margin_fit = 0.35

    repeatability = min(
        1.0,
        0.35
        + (0.15 if job.service_line_hint is not None else 0.0)
        + (0.15 if job.job_type_hint is not None else 0.0)
        + (0.15 if job.deliverables else 0.0),
    )

    rejection_risk = 0.15 * len(flags)
    if RiskFlag.VAGUE_SCOPE in flags:
        rejection_risk += 0.2
    if RiskFlag.SUBJECTIVE_OUTPUT in flags:
        rejection_risk += 0.2
    if RiskFlag.REGULATED_DOMAIN in flags or RiskFlag.POLICY_RISK in flags:
        rejection_risk += 0.25
    rejection_risk = min(1.0, rejection_risk)

    notes: list[str] = []
    if scope_clarity >= 0.7:
        notes.append("Scope is concrete enough for a narrow delivery plan.")
    if acceptance_clarity < 0.5:
        notes.append("Acceptance criteria need strengthening before commitment.")
    if evidence_readiness >= 0.6:
        notes.append("Input material is sufficient for proof-oriented delivery.")
    if margin_fit < 0.5:
        notes.append("Budget looks weak for the likely handling cost.")

    return SuccessProfile(
        scope_clarity=scope_clarity,
        acceptance_clarity=acceptance_clarity,
        evidence_readiness=evidence_readiness,
        delivery_confidence=delivery_confidence,
        margin_fit=margin_fit,
        rejection_risk=rejection_risk,
        repeatability=repeatability,
        notes=notes,
    )


def _qualification_confidence(
    service_line: ServiceLine | None,
    job_type: JobType | None,
    flags: list[RiskFlag],
) -> float:
    confidence = 0.35
    if service_line is not None:
        confidence += 0.2
    if job_type is not None:
        confidence += 0.2
    confidence -= 0.08 * len(flags)
    return max(0.0, min(1.0, confidence))


def _is_qualified(flags: list[RiskFlag], profile: SuccessProfile) -> bool:
    hard_reject = {
        RiskFlag.REGULATED_DOMAIN,
        RiskFlag.POLICY_RISK,
    }
    if any(flag in hard_reject for flag in flags):
        return False

    if profile.scope_clarity < 0.4:
        return False
    if profile.delivery_confidence < 0.4:
        return False
    if profile.rejection_risk >= 0.75:
        return False

    if RiskFlag.VAGUE_SCOPE in flags and RiskFlag.MISSING_ACCEPTANCE_CRITERIA in flags:
        return False

    return True


def _operator_approval_required(
    qualified: bool,
    profile: SuccessProfile,
    flags: list[RiskFlag],
) -> bool:
    if not qualified:
        return False

    caution_flags = {
        RiskFlag.LOW_MARGIN,
        RiskFlag.TIGHT_DEADLINE,
        RiskFlag.MISSING_ACCESS,
        RiskFlag.DATA_QUALITY_RISK,
        RiskFlag.LOW_CONFIDENCE,
    }
    if any(flag in caution_flags for flag in flags):
        return True

    if profile.margin_fit < 0.55:
        return True
    if profile.acceptance_clarity < 0.55:
        return True
    if profile.rejection_risk >= 0.45:
        return True

    return False


def _missing_information(job: JobBrief, flags: list[RiskFlag]) -> list[str]:
    missing: list[str] = []

    if RiskFlag.MISSING_ACCEPTANCE_CRITERIA in flags:
        missing.append("Explicit acceptance criteria are missing.")
    if not job.deliverables:
        missing.append("Expected deliverables are not clearly stated.")
    if RiskFlag.MISSING_ACCESS in flags:
        missing.append("Required access, files, or environment details are missing.")
    if not job.inputs:
        missing.append("Source materials or working inputs are missing.")

    return missing


def qualify_job_brief(job: JobBrief) -> QualificationResult:
    service_line = _detect_service_line(job)
    job_type = _detect_job_type(job, service_line)
    flags = _derive_risk_flags(job, service_line)
    profile = _build_success_profile(job, flags)
    confidence = _qualification_confidence(service_line, job_type, flags)
    qualified = _is_qualified(flags, profile)
    approval_required = _operator_approval_required(qualified, profile, flags)

    rationale_parts = []
    if service_line is not None:
        rationale_parts.append(f"Detected service line: {service_line.value}.")
    if job_type is not None:
        rationale_parts.append(f"Detected job type: {job_type.value}.")
    if qualified:
        rationale_parts.append("Job appears narrow enough for scoped delivery.")
    else:
        rationale_parts.append("Job does not currently meet scope or risk thresholds.")
    if approval_required:
        rationale_parts.append("Operator review is required before commitment.")

    evidence = [
        EvidenceItem(
            kind=EvidenceKind.VALIDATION_NOTE,
            summary="Qualification completed using rule-based service-line and risk scoring.",
            source="system",
        )
    ]

    return QualificationResult(
        qualified=qualified,
        service_line=service_line,
        job_type=job_type,
        rationale=" ".join(rationale_parts),
        success_profile=profile,
        confidence=confidence,
        risk_flags=flags,
        missing_information=_missing_information(job, flags),
        extracted_acceptance_criteria=job.acceptance_criteria,
        extracted_deliverables=job.deliverables,
        operator_approval_required=approval_required,
        evidence=evidence,
    )


def qualification_step(state: MessiahState) -> MessiahState:
    job_brief = state.get("job_brief")
    if job_brief is None:
        raise ValueError("state must contain 'job_brief' before qualification")

    result = qualify_job_brief(job_brief)
    next_status = JobStatus.QUALIFIED if result.qualified else JobStatus.REJECTED
    if result.qualified and result.operator_approval_required:
        next_status = JobStatus.AWAITING_OPERATOR_APPROVAL

    return {
        "qualification": result,
        "job_status": next_status,
        "messages": [
            *state.get("messages", []),
            f"Qualification completed with status: {next_status.value}.",
        ],
    }


__all__ = ["qualification_step", "qualify_job_brief"]
