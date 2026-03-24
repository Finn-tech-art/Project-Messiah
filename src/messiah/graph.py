# Defines workflow control.

#What it should do.
# Write the node order for the MVP pipeline
# Stop the flow when a job is rejected, blocked, or waiting on human approval.
# support Langgraph 
# still let you run the workflow locally with plain python funcions before the rest of the implementation exists.

"""Workflow orchestration for Project Messiah's dry-run pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping, TypeAlias, cast

from .models import ApprovalDecision, JobStatus, MessiahState

try:
    from langgraph.graph import END as LANGGRAPH_END
    from langgraph.graph import START as LANGGRAPH_START
    from langgraph.graph import StateGraph

    LANGGRAPH_AVAILABLE = True
except ImportError:  # pragma: no cover
    LANGGRAPH_AVAILABLE = False
    LANGGRAPH_END = "__end__"
    LANGGRAPH_START = "__start__"
    StateGraph = None


NODE_INTAKE = "intake"
NODE_QUALIFICATION = "qualification"
NODE_ESTIMATION = "estimation"
NODE_EXECUTION_PLAN = "execution_plan"
NODE_DELIVERY_CHECKLIST = "delivery_checklist"
FLOW_END = "__end__"

StateUpdate: TypeAlias = Mapping[str, Any] | MessiahState | None
StateNode: TypeAlias = Callable[[MessiahState], StateUpdate]


@dataclass(slots=True, kw_only=True)
class WorkflowNodes:
    intake: StateNode
    qualification: StateNode
    estimation: StateNode
    execution_plan: StateNode
    delivery_checklist: StateNode


def _merge_state(state: MessiahState, update: StateUpdate) -> MessiahState:
    next_state = dict(state)
    if update:
        next_state.update(update)
    return cast(MessiahState, next_state)


def _has_terminal_status(state: MessiahState) -> bool:
    status = state.get("job_status")
    return status in {JobStatus.REJECTED, JobStatus.BLOCKED, JobStatus.DELIVERED}


def _approval_pending(state: MessiahState) -> bool:
    approval = state.get("operator_approval")
    if approval is None:
        return False
    return approval.decision == ApprovalDecision.PENDING


def _approval_rejected(state: MessiahState) -> bool:
    approval = state.get("operator_approval")
    if approval is None:
        return False
    return approval.decision == ApprovalDecision.REJECTED


def _qualification_failed(state: MessiahState) -> bool:
    qualification = state.get("qualification")
    if qualification is None:
        return False
    return not qualification.qualified


def _approval_required_after_qualification(state: MessiahState) -> bool:
    qualification = state.get("qualification")
    if qualification is None:
        return False
    return qualification.operator_approval_required and _approval_pending(state)


def _approval_required_after_estimation(state: MessiahState) -> bool:
    estimate = state.get("estimate")
    if estimate is None:
        return False
    return estimate.operator_approval_required and _approval_pending(state)


def route_after_intake(state: MessiahState) -> str:
    if _has_terminal_status(state) or _approval_rejected(state):
        return FLOW_END
    return NODE_QUALIFICATION


def route_after_qualification(state: MessiahState) -> str:
    if _has_terminal_status(state) or _approval_rejected(state) or _qualification_failed(state):
        return FLOW_END
    if _approval_required_after_qualification(state):
        return FLOW_END
    return NODE_ESTIMATION


def route_after_estimation(state: MessiahState) -> str:
    if _has_terminal_status(state) or _approval_rejected(state):
        return FLOW_END
    if _approval_required_after_estimation(state):
        return FLOW_END
    return NODE_EXECUTION_PLAN


def route_after_execution_plan(state: MessiahState) -> str:
    if _has_terminal_status(state) or _approval_rejected(state):
        return FLOW_END
    return NODE_DELIVERY_CHECKLIST


def route_after_delivery_checklist(state: MessiahState) -> str:
    return FLOW_END


def run_workflow(initial_state: MessiahState, nodes: WorkflowNodes) -> MessiahState:
    """Runs the workflow locally without requiring LangGraph to be installed."""

    state = cast(MessiahState, dict(initial_state))

    state = _merge_state(state, nodes.intake(state))
    if route_after_intake(state) == FLOW_END:
        return state

    state = _merge_state(state, nodes.qualification(state))
    if route_after_qualification(state) == FLOW_END:
        return state

    state = _merge_state(state, nodes.estimation(state))
    if route_after_estimation(state) == FLOW_END:
        return state

    state = _merge_state(state, nodes.execution_plan(state))
    if route_after_execution_plan(state) == FLOW_END:
        return state

    state = _merge_state(state, nodes.delivery_checklist(state))
    return state


def build_graph(nodes: WorkflowNodes):
    """Builds a compiled LangGraph workflow once the dependency is installed."""

    if not LANGGRAPH_AVAILABLE or StateGraph is None:
        raise RuntimeError(
            "langgraph is not installed; use run_workflow() for local dry runs until it is added"
        )

    graph = StateGraph(MessiahState)
    graph.add_node(NODE_INTAKE, nodes.intake)
    graph.add_node(NODE_QUALIFICATION, nodes.qualification)
    graph.add_node(NODE_ESTIMATION, nodes.estimation)
    graph.add_node(NODE_EXECUTION_PLAN, nodes.execution_plan)
    graph.add_node(NODE_DELIVERY_CHECKLIST, nodes.delivery_checklist)

    graph.add_edge(LANGGRAPH_START, NODE_INTAKE)
    graph.add_conditional_edges(
        NODE_INTAKE,
        route_after_intake,
        {
            NODE_QUALIFICATION: NODE_QUALIFICATION,
            FLOW_END: LANGGRAPH_END,
        },
    )
    graph.add_conditional_edges(
        NODE_QUALIFICATION,
        route_after_qualification,
        {
            NODE_ESTIMATION: NODE_ESTIMATION,
            FLOW_END: LANGGRAPH_END,
        },
    )
    graph.add_conditional_edges(
        NODE_ESTIMATION,
        route_after_estimation,
        {
            NODE_EXECUTION_PLAN: NODE_EXECUTION_PLAN,
            FLOW_END: LANGGRAPH_END,
        },
    )
    graph.add_conditional_edges(
        NODE_EXECUTION_PLAN,
        route_after_execution_plan,
        {
            NODE_DELIVERY_CHECKLIST: NODE_DELIVERY_CHECKLIST,
            FLOW_END: LANGGRAPH_END,
        },
    )
    graph.add_conditional_edges(
        NODE_DELIVERY_CHECKLIST,
        route_after_delivery_checklist,
        {FLOW_END: LANGGRAPH_END},
    )

    return graph.compile()


__all__ = [
    "FLOW_END",
    "LANGGRAPH_AVAILABLE",
    "NODE_DELIVERY_CHECKLIST",
    "NODE_ESTIMATION",
    "NODE_EXECUTION_PLAN",
    "NODE_INTAKE",
    "NODE_QUALIFICATION",
    "WorkflowNodes",
    "build_graph",
    "route_after_delivery_checklist",
    "route_after_estimation",
    "route_after_execution_plan",
    "route_after_intake",
    "route_after_qualification",
    "run_workflow",
]

