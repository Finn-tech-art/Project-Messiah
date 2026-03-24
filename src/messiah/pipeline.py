# Connect the pieces already built into one dry-run workflow and fill the gap between estimation and dashboard
# define the execution plan step and the delivery checklist step
# provide the default set of workflow nodes using intake, qualification and estimation
# expose one run_pipeline entry point that can use Langgraph or the plain python fallback from graph.py

"""Dry-run pipeline assembly for Project Messiah."""

from __future__ import annotations

from messiah.estimation import estimation_step
from messiah.graph import LANGGRAPH_AVAILABLE, WorkflowNodes, build_graph, run_workflow
from messiah.intake import intake_job
from messiah.models import (
    ChecklistItem,
    DeliveryChecklist,
    EvidenceItem,
    EvidenceKind,
    ExecutionPlan,
    JobBrief,
    JobStatus,
    JobType,
    MessiahState,
    PlanStep,
    QualificationResult,
    ServiceLine,
)
from .qualification import qualification_step


def _default_objectives(job: JobBrief, qualification: QualificationResult) -> list[str]:
    objectives = [f"Deliver the scoped outcome: {job.requested_outcome}"]

    if qualification.service_line == ServiceLine.TECHNICAL_DELIVERY:
        objectives.append("Produce an objective technical result with proof of completion.")
    elif qualification.service_line == ServiceLine.RESEARCH_BRIEF:
        objectives.append("Produce a decision-ready brief with sources and a clear recommendation.")
    elif qualification.service_line == ServiceLine.DATA_CLEANUP:
        objectives.append("Produce a cleaned dataset with clear handling rules.")
    elif qualification.service_line == ServiceLine.STRUCTURED_CONTENT:
        objectives.append("Produce business-ready content assets tied to source material.")
    elif qualification.service_line == ServiceLine.OPS_ADMIN_EXECUTION:
        objectives.append("Produce a completed operational output with a repeatable structure.")
    elif qualification.service_line == ServiceLine.SALES_ENABLEMENT:
        objectives.append("Produce sales-ready materials that support outreach or qualification.")
    elif qualification.service_line == ServiceLine.SUPPORT_OPS:
        objectives.append("Produce support-ready outputs that are easy to review and reuse.")

    if job.acceptance_criteria:
        objectives.append("Match the stated acceptance criteria closely enough for clean review.")

    return objectives


def _execution_step_title(job_type: JobType | None, service_line: ServiceLine | None) -> str:
    if job_type == JobType.BUG_RESCUE:
        return "Resolve the reproducible bug"
    if job_type == JobType.CODEBASE_HEALTH_AUDIT:
        return "Review the codebase and prepare the audit findings"
    if job_type == JobType.CI_DEPLOY_RECOVERY:
        return "Restore the failing deploy or pipeline path"
    if job_type == JobType.AUTOMATION_SPRINT:
        return "Implement the scoped automation workflow"
    if job_type == JobType.AI_OUTPUT_QA:
        return "Review and harden the AI-generated output"
    if job_type in {JobType.RESEARCH_BRIEF_SPRINT, JobType.COMPETITOR_RESEARCH, JobType.TOOL_COMPARISON}:
        return "Research, compare, and synthesize the requested findings"
    if job_type in {JobType.DATA_CLEANUP_SPRINT, JobType.CRM_DATA_CLEANUP, JobType.LEAD_LIST_ENRICHMENT}:
        return "Clean, normalize, and validate the working dataset"
    if job_type in {JobType.CONTENT_SYSTEM_PACK, JobType.LANDING_PAGE_REWRITE, JobType.FAQ_GENERATION}:
        return "Draft and structure the requested content assets"
    if job_type in {JobType.HELP_CENTER_DRAFTING, JobType.TICKET_CLASSIFICATION}:
        return "Prepare the requested support operations output"
    if job_type in {JobType.SALES_RESEARCH_DOSSIER, JobType.PROPOSAL_DRAFTING}:
        return "Assemble the requested sales enablement materials"
    if job_type in {JobType.REPORTING_PACK, JobType.SOP_FORMATTING}:
        return "Produce the requested operations/admin deliverable"

    if service_line == ServiceLine.TECHNICAL_DELIVERY:
        return "Execute the scoped technical delivery"
    if service_line == ServiceLine.RESEARCH_BRIEF:
        return "Assemble the scoped research brief"
    if service_line == ServiceLine.DATA_CLEANUP:
        return "Complete the scoped data cleanup"
    if service_line == ServiceLine.STRUCTURED_CONTENT:
        return "Produce the scoped structured content"
    if service_line == ServiceLine.OPS_ADMIN_EXECUTION:
        return "Complete the scoped ops/admin task"
    if service_line == ServiceLine.SALES_ENABLEMENT:
        return "Produce the scoped sales enablement output"
    if service_line == ServiceLine.SUPPORT_OPS:
        return "Produce the scoped support operations output"

    return "Execute the scoped work"


def _default_delivery_artifacts(job: JobBrief, qualification: QualificationResult) -> list[str]:
    if job.deliverables:
        return [item.name for item in job.deliverables]

    if qualification.service_line == ServiceLine.TECHNICAL_DELIVERY:
        return ["Root cause summary", "Fix or patch notes", "Validation note"]
    if qualification.service_line == ServiceLine.RESEARCH_BRIEF:
        return ["Summary memo", "Comparison table", "Source list"]
    if qualification.service_line == ServiceLine.DATA_CLEANUP:
        return ["Cleaned dataset", "Cleanup rules", "Issue summary"]
    if qualification.service_line == ServiceLine.STRUCTURED_CONTENT:
        return ["Final content draft", "Source-to-output mapping", "Revision notes"]
    if qualification.service_line == ServiceLine.OPS_ADMIN_EXECUTION:
        return ["Completed output", "Processing notes", "Operator handoff note"]
    if qualification.service_line == ServiceLine.SALES_ENABLEMENT:
        return ["Sales asset pack", "Research notes", "Usage guidance"]
    if qualification.service_line == ServiceLine.SUPPORT_OPS:
        return ["Support-ready asset", "Classification or drafting notes", "Review guidance"]

    return ["Final deliverable", "Validation summary"]


def build_execution_plan(
    job: JobBrief,
    qualification: QualificationResult,
) -> ExecutionPlan:
    delivery_artifacts = _default_delivery_artifacts(job, qualification)

    steps = [
        PlanStep(
            step_id="review_scope",
            title="Review scope and source materials",
            description=(
                "Confirm the requested outcome, working inputs, constraints, and acceptance criteria "
                "before starting the main execution pass."
            ),
            required_inputs=["job brief", *job.inputs],
            expected_outputs=["scope confirmation", "execution assumptions"],
            evidence_requirements=["Preserve brief details and any important source references."],
            requires_operator_approval=False,
        ),
        PlanStep(
            step_id="execute_work",
            title=_execution_step_title(qualification.job_type, qualification.service_line),
            description=(
                "Perform the main scoped work with emphasis on narrow execution, objective proof, "
                "and minimal unnecessary expansion of scope."
            ),
            required_inputs=["confirmed scope", *job.inputs],
            expected_outputs=delivery_artifacts,
            evidence_requirements=["Capture notes or artifacts that prove the work was completed."],
            requires_operator_approval=qualification.operator_approval_required,
        ),
        PlanStep(
            step_id="validate_output",
            title="Validate against acceptance criteria",
            description=(
                "Check the produced output against the stated or extracted acceptance criteria and "
                "record anything that still needs clarification."
            ),
            required_inputs=delivery_artifacts,
            expected_outputs=["validation notes", "acceptance check"],
            evidence_requirements=["Tie validation notes to acceptance criteria where possible."],
            requires_operator_approval=False,
        ),
        PlanStep(
            step_id="package_delivery",
            title="Package the delivery for review",
            description=(
                "Prepare the buyer-facing output with the deliverables, proof notes, and any next-step "
                "guidance needed for clean handoff."
            ),
            required_inputs=["validated outputs", "validation notes"],
            expected_outputs=["delivery bundle"],
            evidence_requirements=["Include proof-oriented notes suitable for operator review."],
            requires_operator_approval=True,
        ),
    ]

    approval_gates = []
    if qualification.operator_approval_required:
        approval_gates.append("Operator approval required before execution commitment.")
    approval_gates.append("Final operator review before delivery handoff.")

    return ExecutionPlan(
        summary="Dry-run execution plan for a scoped, proof-oriented delivery.",
        objectives=_default_objectives(job, qualification),
        steps=steps,
        delivery_artifacts=delivery_artifacts,
        approval_gates=approval_gates,
        dependencies=job.inputs.copy(),
        evidence_requirements=[
            "Retain proof of completion.",
            "Retain notes that map outputs back to scope and acceptance criteria.",
        ],
        confidence=qualification.success_profile.delivery_confidence,
        operator_approval_required=True,
    )


def build_delivery_checklist(
    job: JobBrief,
    plan: ExecutionPlan,
) -> DeliveryChecklist:
    items: list[ChecklistItem] = []

    for criterion in job.acceptance_criteria:
        items.append(
            ChecklistItem(
                item=f"Confirm acceptance criterion: {criterion.description}",
                linked_acceptance_criterion=criterion.description,
                proof_note="Validation note should state how this criterion was met.",
            )
        )

    if job.deliverables:
        for deliverable in job.deliverables:
            items.append(
                ChecklistItem(
                    item=f"Prepare deliverable: {deliverable.name}",
                    proof_note=f"Provide or reference the final {deliverable.format} output.",
                )
            )
    else:
        for artifact in plan.delivery_artifacts:
            items.append(
                ChecklistItem(
                    item=f"Prepare delivery artifact: {artifact}",
                    proof_note="Include the artifact in the final delivery bundle.",
                )
            )

    items.extend(
        [
            ChecklistItem(
                item="Attach validation notes",
                proof_note="Summarize checks run against scope and acceptance criteria.",
            ),
            ChecklistItem(
                item="Attach proof-oriented summary",
                proof_note="Show what was completed, what was checked, and any remaining caveats.",
            ),
            ChecklistItem(
                item="Operator reviews final delivery bundle",
                proof_note="Human review is required before external delivery.",
            ),
        ]
    )

    evidence = [
        EvidenceItem(
            kind=EvidenceKind.DELIVERY_ARTIFACT,
            summary="Delivery checklist generated from the execution plan and acceptance criteria.",
            source="system",
        )
    ]

    return DeliveryChecklist(
        items=items,
        required_deliverables=plan.delivery_artifacts,
        final_validation_notes=[
            "Verify that the final bundle stays within scope.",
            "Verify that proof and acceptance notes are understandable to a buyer.",
        ],
        confidence=plan.confidence,
        evidence=evidence,
        operator_signoff_required=True,
    )


def execution_plan_step(state: MessiahState) -> MessiahState:
    job_brief = state.get("job_brief")
    qualification = state.get("qualification")
    estimate = state.get("estimate")

    if job_brief is None:
        raise ValueError("state must contain 'job_brief' before execution planning")
    if qualification is None:
        raise ValueError("state must contain 'qualification' before execution planning")
    if estimate is None:
        raise ValueError("state must contain 'estimate' before execution planning")

    plan = build_execution_plan(job_brief, qualification)
    return {
        "execution_plan": plan,
        "job_status": JobStatus.PLANNED,
        "messages": [
            *state.get("messages", []),
            f"Execution plan generated with {len(plan.steps)} steps.",
        ],
    }


def delivery_checklist_step(state: MessiahState) -> MessiahState:
    job_brief = state.get("job_brief")
    execution_plan = state.get("execution_plan")

    if job_brief is None:
        raise ValueError("state must contain 'job_brief' before checklist generation")
    if execution_plan is None:
        raise ValueError("state must contain 'execution_plan' before checklist generation")

    checklist = build_delivery_checklist(job_brief, execution_plan)
    return {
        "delivery_checklist": checklist,
        "job_status": JobStatus.READY_FOR_DELIVERY,
        "messages": [
            *state.get("messages", []),
            f"Delivery checklist generated with {len(checklist.items)} items.",
        ],
    }


def default_workflow_nodes() -> WorkflowNodes:
    return WorkflowNodes(
        intake=intake_job,
        qualification=qualification_step,
        estimation=estimation_step,
        execution_plan=execution_plan_step,
        delivery_checklist=delivery_checklist_step,
    )


def run_pipeline(initial_state: MessiahState, *, prefer_langgraph: bool = True) -> MessiahState:
    nodes = default_workflow_nodes()

    if prefer_langgraph and LANGGRAPH_AVAILABLE:
        graph = build_graph(nodes)
        result = graph.invoke(dict(initial_state))
        return result

    return run_workflow(initial_state, nodes)


__all__ = [
    "build_delivery_checklist",
    "build_execution_plan",
    "default_workflow_nodes",
    "delivery_checklist_step",
    "execution_plan_step",
    "run_pipeline",
]
