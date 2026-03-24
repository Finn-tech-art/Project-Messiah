# Turns a qualified job into a practical effort and pricing view
# uses jobbrief and qualification result and a price band
# keep estimates practical and conservative especially when scope is weak
# escalate uncertain or weak-margin jobs to operator review instead of pretending the estimate is precise

"""Estimation rules for Project Messiah."""

from __future__ import annotations

from .models import (
    EffortTier,
    Estimate,
    EvidenceItem,
    EvidenceKind,
    JobBrief,
    JobStatus,
    JobType,
    MessiahState,
    PriceBand,
    QualificationResult,
    RiskFlag,
    ServiceLine,
)


def _base_hours_for_job_type(job_type: JobType | None, service_line: ServiceLine | None) -> tuple[float, float]:
    if job_type == JobType.BUG_RESCUE:
        return 1.5, 4.0
    if job_type == JobType.CODEBASE_HEALTH_AUDIT:
        return 2.0, 5.0
    if job_type == JobType.CI_DEPLOY_RECOVERY:
        return 1.5, 4.5
    if job_type == JobType.AUTOMATION_SPRINT:
        return 3.0, 8.0
    if job_type == JobType.AI_OUTPUT_QA:
        return 1.0, 3.0
    if job_type == JobType.RESEARCH_BRIEF_SPRINT:
        return 2.0, 5.0
    if job_type == JobType.COMPETITOR_RESEARCH:
        return 2.0, 6.0
    if job_type == JobType.TOOL_COMPARISON:
        return 2.0, 4.5
    if job_type == JobType.DATA_CLEANUP_SPRINT:
        return 1.5, 4.0
    if job_type == JobType.CRM_DATA_CLEANUP:
        return 2.0, 5.5
    if job_type == JobType.LEAD_LIST_ENRICHMENT:
        return 2.0, 5.0
    if job_type == JobType.CONTENT_SYSTEM_PACK:
        return 2.0, 5.0
    if job_type == JobType.LANDING_PAGE_REWRITE:
        return 2.0, 4.5
    if job_type == JobType.FAQ_GENERATION:
        return 1.5, 3.5
    if job_type == JobType.HELP_CENTER_DRAFTING:
        return 2.0, 5.0
    if job_type == JobType.TICKET_CLASSIFICATION:
        return 1.5, 4.0
    if job_type == JobType.SALES_RESEARCH_DOSSIER:
        return 2.0, 5.0
    if job_type == JobType.PROPOSAL_DRAFTING:
        return 1.5, 3.5
    if job_type == JobType.REPORTING_PACK:
        return 1.5, 4.0
    if job_type == JobType.SOP_FORMATTING:
        return 1.0, 3.0

    if service_line == ServiceLine.TECHNICAL_DELIVERY:
        return 2.0, 5.0
    if service_line == ServiceLine.RESEARCH_BRIEF:
        return 2.0, 5.0
    if service_line == ServiceLine.DATA_CLEANUP:
        return 1.5, 4.5
    if service_line == ServiceLine.STRUCTURED_CONTENT:
        return 1.5, 4.0
    if service_line == ServiceLine.OPS_ADMIN_EXECUTION:
        return 1.5, 4.0
    if service_line == ServiceLine.SALES_ENABLEMENT:
        return 2.0, 4.5
    if service_line == ServiceLine.SUPPORT_OPS:
        return 1.5, 4.0

    return 2.0, 5.0


def _adjust_hours(
    base_low: float,
    base_high: float,
    qualification: QualificationResult,
    job: JobBrief,
) -> tuple[float, float]:
    low = base_low
    high = base_high

    profile = qualification.success_profile
    flags = set(qualification.risk_flags)

    if profile.scope_clarity >= 0.75:
        low -= 0.25
        high -= 0.5
    if profile.scope_clarity < 0.5:
        high += 1.0

    if profile.acceptance_clarity >= 0.75:
        high -= 0.25
    if profile.acceptance_clarity < 0.5:
        high += 0.75

    if not job.inputs:
        high += 1.0
    if len(job.deliverables) >= 3:
        high += 0.5

    if RiskFlag.MISSING_ACCESS in flags:
        high += 1.0
    if RiskFlag.DATA_QUALITY_RISK in flags:
        high += 0.75
    if RiskFlag.TIGHT_DEADLINE in flags:
        high += 0.5
    if RiskFlag.LOW_CONFIDENCE in flags:
        high += 0.75

    low = max(0.5, round(low, 2))
    high = max(low, round(high, 2))
    return low, high


def _effort_tier(low: float, high: float) -> EffortTier:
    if high <= 2.0:
        return EffortTier.TINY
    if high <= 4.0:
        return EffortTier.SMALL
    if high <= 7.0:
        return EffortTier.MEDIUM
    return EffortTier.LARGE


def _hourly_rate(qualification: QualificationResult) -> float:
    service_line = qualification.service_line
    profile = qualification.success_profile

    base_rate = 45.0
    if service_line == ServiceLine.TECHNICAL_DELIVERY:
        base_rate = 70.0
    elif service_line == ServiceLine.RESEARCH_BRIEF:
        base_rate = 50.0
    elif service_line == ServiceLine.DATA_CLEANUP:
        base_rate = 40.0
    elif service_line == ServiceLine.STRUCTURED_CONTENT:
        base_rate = 45.0
    elif service_line == ServiceLine.OPS_ADMIN_EXECUTION:
        base_rate = 40.0
    elif service_line == ServiceLine.SALES_ENABLEMENT:
        base_rate = 50.0
    elif service_line == ServiceLine.SUPPORT_OPS:
        base_rate = 42.0

    if profile.margin_fit >= 0.8:
        base_rate += 10.0
    if profile.rejection_risk >= 0.5:
        base_rate -= 5.0

    return base_rate


def _price_band(
    low_hours: float,
    high_hours: float,
    qualification: QualificationResult,
    job: JobBrief,
) -> PriceBand:
    rate = _hourly_rate(qualification)
    minimum = round(low_hours * rate, 2)
    maximum = round(high_hours * rate, 2)

    if job.budget_hint is not None:
        if job.budget_hint.minimum > minimum:
            minimum = job.budget_hint.minimum
        if job.budget_hint.maximum > 0:
            maximum = min(maximum, job.budget_hint.maximum) if maximum > 0 else job.budget_hint.maximum
            maximum = max(minimum, maximum)

    rationale = (
        f"Estimated from {low_hours:.1f}-{high_hours:.1f} hours "
        f"at an implied service-line rate of ${rate:.0f}/hour."
    )
    return PriceBand(minimum=minimum, maximum=maximum, currency="USD", rationale=rationale)


def _estimate_confidence(qualification: QualificationResult, low: float, high: float) -> float:
    confidence = qualification.confidence
    confidence += 0.1 if high - low <= 2.0 else 0.0
    confidence += 0.1 if qualification.success_profile.scope_clarity >= 0.7 else 0.0
    confidence -= 0.15 if qualification.success_profile.rejection_risk >= 0.5 else 0.0
    return max(0.0, min(1.0, round(confidence, 2)))


def _assumptions(job: JobBrief, qualification: QualificationResult) -> list[str]:
    assumptions = [
        "Scope stays within the current brief and deliverables.",
        "No major hidden dependencies appear after intake.",
    ]

    if not job.inputs:
        assumptions.append("Estimate assumes missing working inputs will be provided before execution.")
    if not job.acceptance_criteria:
        assumptions.append("Estimate assumes acceptance criteria will be clarified before delivery.")
    if qualification.operator_approval_required:
        assumptions.append("Final commitment is subject to operator review.")

    return assumptions


def _margin_note(price_band: PriceBand, high_hours: float) -> str:
    implied_rate = 0.0 if high_hours == 0 else price_band.maximum / high_hours
    if implied_rate >= 60:
        return "Healthy margin if scope remains stable."
    if implied_rate >= 40:
        return "Acceptable margin for a controlled, repeatable job."
    return "Thin margin; keep scope tight or require operator approval."


def estimate_job(job: JobBrief, qualification: QualificationResult) -> Estimate:
    base_low, base_high = _base_hours_for_job_type(qualification.job_type, qualification.service_line)
    low_hours, high_hours = _adjust_hours(base_low, base_high, qualification, job)
    effort_tier = _effort_tier(low_hours, high_hours)
    price_band = _price_band(low_hours, high_hours, qualification, job)
    confidence = _estimate_confidence(qualification, low_hours, high_hours)

    operator_approval_required = qualification.operator_approval_required
    if confidence < 0.6:
        operator_approval_required = True
    if qualification.success_profile.margin_fit < 0.5:
        operator_approval_required = True

    evidence = [
        EvidenceItem(
            kind=EvidenceKind.METRIC,
            summary=(
                f"Estimated effort at {low_hours:.1f}-{high_hours:.1f} hours with "
                f"{effort_tier.value} effort tier."
            ),
            source="system",
        )
    ]

    return Estimate(
        price_band=price_band,
        estimated_hours_low=low_hours,
        estimated_hours_high=high_hours,
        effort_tier=effort_tier,
        confidence=confidence,
        assumptions=_assumptions(job, qualification),
        likely_margin_note=_margin_note(price_band, high_hours),
        evidence=evidence,
        operator_approval_required=operator_approval_required,
    )


def estimation_step(state: MessiahState) -> MessiahState:
    job_brief = state.get("job_brief")
    qualification = state.get("qualification")

    if job_brief is None:
        raise ValueError("state must contain 'job_brief' before estimation")
    if qualification is None:
        raise ValueError("state must contain 'qualification' before estimation")
    if not qualification.qualified:
        raise ValueError("estimation should only run for qualified jobs")

    estimate = estimate_job(job_brief, qualification)
    next_status = JobStatus.PLANNED
    if estimate.operator_approval_required:
        next_status = JobStatus.AWAITING_OPERATOR_APPROVAL

    return {
        "estimate": estimate,
        "job_status": next_status,
        "messages": [
            *state.get("messages", []),
            f"Estimate completed with price band ${estimate.price_band.minimum:.2f}-${estimate.price_band.maximum:.2f}.",
        ],
    }


__all__ = ["estimate_job", "estimation_step"]
