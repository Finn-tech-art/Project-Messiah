# The local human control panel

# show the current job state in a way the operator can review quickly
# surface the commercially important fields: service-line, status, price-band, confidence,risks, approval need
# display the execution plan and delivery checklist clearly
# stay local and simple for the MVP.

"""Local operator dashboard for Project Messiah."""

from __future__ import annotations

import sys
from typing import Iterable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from .models import MessiahState


def _join_lines(values: Iterable[str], empty: str = "None") -> str:
    items = [value for value in values if value]
    return "\n".join(items) if items else empty


def _format_price_band(state: MessiahState) -> str:
    estimate = state.get("estimate")
    if estimate is None:
        return "Not estimated"
    band = estimate.price_band
    return f"{band.currency} {band.minimum:.2f} - {band.maximum:.2f}"


def _format_confidence(state: MessiahState) -> str:
    qualification = state.get("qualification")
    estimate = state.get("estimate")

    parts: list[str] = []
    if qualification is not None:
        parts.append(f"qualification {qualification.confidence:.2f}")
    if estimate is not None:
        parts.append(f"estimate {estimate.confidence:.2f}")
    return " | ".join(parts) if parts else "Not scored"


def _format_operator_status(state: MessiahState) -> str:
    approval = state.get("operator_approval")
    if approval is None:
        return "No operator decision recorded"
    note = approval.note.strip()
    if note:
        return f"{approval.decision.value} | {note}"
    return approval.decision.value


class DashboardWindow(QMainWindow):
    def __init__(self, state: MessiahState | None = None) -> None:
        super().__init__()
        self.setWindowTitle("Project Messiah Dashboard")
        self.resize(1100, 820)

        self._summary_labels: dict[str, QLabel] = {}
        self._brief_text = QPlainTextEdit()
        self._qualification_text = QPlainTextEdit()
        self._estimate_text = QPlainTextEdit()
        self._messages_text = QPlainTextEdit()
        self._plan_list = QListWidget()
        self._checklist_list = QListWidget()

        self._brief_text.setReadOnly(True)
        self._qualification_text.setReadOnly(True)
        self._estimate_text.setReadOnly(True)
        self._messages_text.setReadOnly(True)

        self._build_ui()
        self.load_state(state or {})

    def _build_ui(self) -> None:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        layout.addWidget(self._build_summary_box())

        content = QHBoxLayout()
        content.setSpacing(12)
        content.addWidget(self._build_left_column(), 1)
        content.addWidget(self._build_right_column(), 1)
        layout.addLayout(content)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(container)
        self.setCentralWidget(scroll)

    def _build_summary_box(self) -> QGroupBox:
        box = QGroupBox("Overview")
        form = QFormLayout(box)

        for key in [
            "job_id",
            "title",
            "service_line",
            "job_type",
            "status",
            "price_band",
            "confidence",
            "operator",
        ]:
            label = QLabel("-")
            label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            self._summary_labels[key] = label
            form.addRow(key.replace("_", " ").title(), label)

        return box

    def _build_left_column(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)

        brief_box = QGroupBox("Job Brief")
        brief_layout = QVBoxLayout(brief_box)
        brief_layout.addWidget(self._brief_text)

        qualification_box = QGroupBox("Qualification")
        qualification_layout = QVBoxLayout(qualification_box)
        qualification_layout.addWidget(self._qualification_text)

        estimate_box = QGroupBox("Estimate")
        estimate_layout = QVBoxLayout(estimate_box)
        estimate_layout.addWidget(self._estimate_text)

        layout.addWidget(brief_box)
        layout.addWidget(qualification_box)
        layout.addWidget(estimate_box)

        return widget

    def _build_right_column(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)

        plan_box = QGroupBox("Execution Plan")
        plan_layout = QVBoxLayout(plan_box)
        plan_layout.addWidget(self._plan_list)

        checklist_box = QGroupBox("Delivery Checklist")
        checklist_layout = QVBoxLayout(checklist_box)
        checklist_layout.addWidget(self._checklist_list)

        messages_box = QGroupBox("Workflow Messages")
        messages_layout = QVBoxLayout(messages_box)
        messages_layout.addWidget(self._messages_text)

        layout.addWidget(plan_box)
        layout.addWidget(checklist_box)
        layout.addWidget(messages_box)

        return widget

    def load_state(self, state: MessiahState) -> None:
        job = state.get("job_brief")
        qualification = state.get("qualification")
        estimate = state.get("estimate")
        execution_plan = state.get("execution_plan")
        checklist = state.get("delivery_checklist")

        self._summary_labels["job_id"].setText(job.job_id if job else "-")
        self._summary_labels["title"].setText(job.title if job else "No job loaded")
        self._summary_labels["service_line"].setText(
            qualification.service_line.value if qualification and qualification.service_line else "-"
        )
        self._summary_labels["job_type"].setText(
            qualification.job_type.value if qualification and qualification.job_type else "-"
        )
        self._summary_labels["status"].setText(
            state.get("job_status").value if state.get("job_status") else "-"
        )
        self._summary_labels["price_band"].setText(_format_price_band(state))
        self._summary_labels["confidence"].setText(_format_confidence(state))
        self._summary_labels["operator"].setText(_format_operator_status(state))

        self._brief_text.setPlainText(self._render_brief(state))
        self._qualification_text.setPlainText(self._render_qualification(state))
        self._estimate_text.setPlainText(self._render_estimate(state))
        self._messages_text.setPlainText(_join_lines(state.get("messages", []), empty="No messages"))

        self._plan_list.clear()
        if execution_plan is not None:
            for step in execution_plan.steps:
                prefix = "[Operator]" if step.owner == "operator" else "[Agent]"
                gate = " | approval required" if step.requires_operator_approval else ""
                self._plan_list.addItem(f"{prefix} {step.title}{gate}")
                self._plan_list.addItem(f"  {step.description}")
        else:
            self._plan_list.addItem("No execution plan generated")

        self._checklist_list.clear()
        if checklist is not None:
            for item in checklist.items:
                status = "done" if item.completed else "open"
                self._checklist_list.addItem(f"[{status}] {item.item}")
                if item.proof_note:
                    self._checklist_list.addItem(f"  proof: {item.proof_note}")
        else:
            self._checklist_list.addItem("No delivery checklist generated")

    def _render_brief(self, state: MessiahState) -> str:
        job = state.get("job_brief")
        if job is None:
            return "No job brief loaded."

        parts = [
            f"Title: {job.title}",
            f"Summary: {job.summary or 'None'}",
            f"Requested outcome: {job.requested_outcome or 'None'}",
            f"Source channel: {job.source_channel}",
            "",
            "Inputs:",
            _join_lines(job.inputs),
            "",
            "Constraints:",
            _join_lines(job.constraints),
            "",
            "Acceptance criteria:",
            _join_lines([item.description for item in job.acceptance_criteria]),
            "",
            "Deliverables:",
            _join_lines([item.name for item in job.deliverables]),
            "",
            "Operator notes:",
            _join_lines(job.operator_notes),
        ]
        return "\n".join(parts)

    def _render_qualification(self, state: MessiahState) -> str:
        qualification = state.get("qualification")
        if qualification is None:
            return "No qualification result yet."

        parts = [
            f"Qualified: {qualification.qualified}",
            f"Rationale: {qualification.rationale}",
            f"Confidence: {qualification.confidence:.2f}",
            "",
            "Risk flags:",
            _join_lines([flag.value for flag in qualification.risk_flags]),
            "",
            "Missing information:",
            _join_lines(qualification.missing_information),
            "",
            "Success profile:",
            f"scope_clarity={qualification.success_profile.scope_clarity:.2f}",
            f"acceptance_clarity={qualification.success_profile.acceptance_clarity:.2f}",
            f"evidence_readiness={qualification.success_profile.evidence_readiness:.2f}",
            f"delivery_confidence={qualification.success_profile.delivery_confidence:.2f}",
            f"margin_fit={qualification.success_profile.margin_fit:.2f}",
            f"rejection_risk={qualification.success_profile.rejection_risk:.2f}",
            f"repeatability={qualification.success_profile.repeatability:.2f}",
            "",
            "Notes:",
            _join_lines(qualification.success_profile.notes),
        ]
        return "\n".join(parts)

    def _render_estimate(self, state: MessiahState) -> str:
        estimate = state.get("estimate")
        if estimate is None:
            return "No estimate generated."

        parts = [
            f"Price band: {_format_price_band(state)}",
            f"Hours: {estimate.estimated_hours_low:.1f} - {estimate.estimated_hours_high:.1f}",
            f"Effort tier: {estimate.effort_tier.value}",
            f"Confidence: {estimate.confidence:.2f}",
            f"Operator approval required: {estimate.operator_approval_required}",
            "",
            "Assumptions:",
            _join_lines(estimate.assumptions),
            "",
            f"Margin note: {estimate.likely_margin_note}",
            f"Pricing rationale: {estimate.price_band.rationale}",
        ]
        return "\n".join(parts)


def launch_dashboard(state: MessiahState | None = None) -> int:
    app = QApplication.instance()
    owns_app = app is None
    if app is None:
        app = QApplication(sys.argv)

    window = DashboardWindow(state=state)
    window.show()

    if owns_app:
        return app.exec()
    return 0


def main() -> None:
    try:
        raise SystemExit(launch_dashboard())
    except Exception as exc:  # pragma: no cover
        app = QApplication.instance() or QApplication(sys.argv)
        QMessageBox.critical(None, "Dashboard Error", str(exc))
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
