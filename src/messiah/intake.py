# Turn raw inbound work into a normalised JobBrief
# Accept fixture-style dictionaries or JSON files
# Normalize the fields you already care about into the models from models.py
# preserve raw input for operator review
# it should just clean and structure.

"""Inbound job normalization for Project Messiah."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from .models import (
    AcceptanceCriterion,
    Deliverable,
    EvidenceItem,
    EvidenceKind,
    JobBrief,
    JobStatus,
    JobType,
    MessiahState,
    PriceBand,
    ServiceLine,
)


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _clean_list(values: Any) -> list[str]:
    if values is None:
        return []
    if isinstance(values, str):
        text = values.strip()
        return [text] if text else []
    if isinstance(values, Iterable) and not isinstance(values, (str, bytes, dict)):
        return [str(item).strip() for item in values if str(item).strip()]
    return [str(values).strip()]


def _parse_service_line(value: str | None) -> ServiceLine | None:
    if not value:
        return None

    normalized = value.strip().lower()
    aliases = {
        "technical": ServiceLine.TECHNICAL_DELIVERY,
        "technical_delivery": ServiceLine.TECHNICAL_DELIVERY,
        "research": ServiceLine.RESEARCH_BRIEF,
        "research_brief": ServiceLine.RESEARCH_BRIEF,
        "data": ServiceLine.DATA_CLEANUP,
        "data_cleanup": ServiceLine.DATA_CLEANUP,
        "content": ServiceLine.STRUCTURED_CONTENT,
        "structured_content": ServiceLine.STRUCTURED_CONTENT,
        "ops": ServiceLine.OPS_ADMIN_EXECUTION,
        "ops_admin_execution": ServiceLine.OPS_ADMIN_EXECUTION,
        "sales": ServiceLine.SALES_ENABLEMENT,
        "sales_enablement": ServiceLine.SALES_ENABLEMENT,
        "support": ServiceLine.SUPPORT_OPS,
        "support_ops": ServiceLine.SUPPORT_OPS,
    }
    return aliases.get(normalized)


def _parse_job_type(value: str | None) -> JobType | None:
    if not value:
        return None

    normalized = value.strip().lower()
    for member in JobType:
        if normalized == member.value:
            return member
    return None


def _parse_acceptance_criteria(values: Any) -> list[AcceptanceCriterion]:
    items: list[AcceptanceCriterion] = []

    if values is None:
        return items

    if isinstance(values, str):
        values = [values]

    for value in values:
        if isinstance(value, dict):
            description = _clean_text(value.get("description"))
            if not description:
                continue
            items.append(
                AcceptanceCriterion(
                    description=description,
                    measurable=bool(value.get("measurable", True)),
                    source=_clean_text(value.get("source")) or None,
                )
            )
            continue

        description = _clean_text(value)
        if description:
            items.append(AcceptanceCriterion(description=description))

    return items


def _parse_deliverables(values: Any) -> list[Deliverable]:
    items: list[Deliverable] = []

    if values is None:
        return items

    if isinstance(values, str):
        values = [values]

    for value in values:
        if isinstance(value, dict):
            name = _clean_text(value.get("name"))
            description = _clean_text(value.get("description")) or name
            fmt = _clean_text(value.get("format")) or "unspecified"
            if not name and not description:
                continue
            items.append(
                Deliverable(
                    name=name or description,
                    description=description,
                    format=fmt,
                    required=bool(value.get("required", True)),
                )
            )
            continue

        text = _clean_text(value)
        if text:
            items.append(
                Deliverable(
                    name=text,
                    description=text,
                    format="unspecified",
                )
            )

    return items


def _parse_budget_hint(data: dict[str, Any]) -> PriceBand | None:
    budget = data.get("budget_hint")
    if isinstance(budget, dict):
        minimum = float(budget.get("minimum", 0))
        maximum = float(budget.get("maximum", minimum))
        return PriceBand(
            minimum=minimum,
            maximum=maximum,
            currency=_clean_text(budget.get("currency")) or "USD",
            rationale=_clean_text(budget.get("rationale")),
        )

    min_value = data.get("budget_min")
    max_value = data.get("budget_max")
    if min_value is None and max_value is None:
        return None

    minimum = float(min_value or 0)
    maximum = float(max_value or minimum)
    return PriceBand(
        minimum=minimum,
        maximum=maximum,
        currency=_clean_text(data.get("budget_currency")) or "USD",
        rationale=_clean_text(data.get("budget_note")),
    )


def build_job_brief(data: dict[str, Any]) -> JobBrief:
    job_id = _clean_text(data.get("job_id") or data.get("id") or "job-draft")
    title = _clean_text(data.get("title") or "Untitled job")
    summary = _clean_text(data.get("summary") or data.get("brief") or data.get("description"))
    requested_outcome = _clean_text(
        data.get("requested_outcome") or data.get("outcome") or summary or title
    )
    source_channel = _clean_text(data.get("source_channel") or data.get("source") or "unknown")

    evidence = []
    raw_request = _clean_text(data.get("raw_request"))
    if raw_request:
        evidence.append(
            EvidenceItem(
                kind=EvidenceKind.CLIENT_INPUT,
                summary="Original inbound request preserved during intake.",
                source="fixture",
                reference=raw_request,
            )
        )

    return JobBrief(
        job_id=job_id,
        title=title,
        summary=summary,
        requested_outcome=requested_outcome,
        source_channel=source_channel,
        raw_request=raw_request,
        service_line_hint=_parse_service_line(_clean_text(data.get("service_line_hint"))),
        job_type_hint=_parse_job_type(_clean_text(data.get("job_type_hint"))),
        inputs=_clean_list(data.get("inputs")),
        constraints=_clean_list(data.get("constraints")),
        acceptance_criteria=_parse_acceptance_criteria(data.get("acceptance_criteria")),
        deliverables=_parse_deliverables(data.get("deliverables")),
        budget_hint=_parse_budget_hint(data),
        operator_notes=_clean_list(data.get("operator_notes")),
        evidence=evidence,
    )


def load_job_brief(path: str | Path) -> JobBrief:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return build_job_brief(payload)


def intake_job(state: MessiahState) -> MessiahState:
    if "job_brief" in state:
        return {
            "job_status": JobStatus.INTAKE,
            "messages": [*state.get("messages", []), "Job brief already present in state."],
        }

    input_path = state.get("input_path")
    if not input_path:
        raise ValueError("state must include either 'job_brief' or 'input_path' for intake")

    job_brief = load_job_brief(input_path)
    return {
        "job_brief": job_brief,
        "job_status": JobStatus.INTAKE,
        "messages": [*state.get("messages", []), f"Loaded job brief from {input_path}."],
    }


__all__ = ["build_job_brief", "intake_job", "load_job_brief"]
