from typing import List

from .schemas import (
    OrchestrateCommand,
    OrchestrateRequest,
    OrchestrateResponse,
    OrchestrationStatus,
    OrchestrationStep,
)


def decide_next(request: OrchestrateRequest) -> OrchestrateResponse:
    commands: List[OrchestrateCommand] = []
    compensated: List[str] = []
    notes = None

    step = request.current_step
    status = request.status

    if step == OrchestrationStep.use_case:
        if status == OrchestrationStatus.pending:
            commands = [
                OrchestrateCommand(
                    name="run_use_case", params={"case_id": request.case_id}
                )
            ]
            return OrchestrateResponse(
                next_step=OrchestrationStep.use_case,
                action="execute",
                commands=commands,
                compensated=compensated,
            )
        if status == OrchestrationStatus.success:
            commands = [
                OrchestrateCommand(
                    name="run_risk_classifier",
                    params={
                        "case_id": request.case_id,
                        "use_case": request.last_result or {},
                    },
                )
            ]
            return OrchestrateResponse(
                next_step=OrchestrationStep.risk_class,
                action="execute",
                commands=commands,
                compensated=compensated,
            )
        if status == OrchestrationStatus.failed:
            commands = [
                OrchestrateCommand(
                    name="emit_case_failed",
                    params={"case_id": request.case_id, "failed_step": "use_case"},
                )
            ]
            return OrchestrateResponse(
                next_step=OrchestrationStep.complete,
                action="finalize",
                commands=commands,
                compensated=compensated,
                notes="Initial step failed; no compensation necessary",
            )

    if step == OrchestrationStep.risk_class:
        if status == OrchestrationStatus.pending:
            commands = [
                OrchestrateCommand(
                    name="run_risk_classifier", params={"case_id": request.case_id}
                )
            ]
            return OrchestrateResponse(
                next_step=OrchestrationStep.risk_class,
                action="execute",
                commands=commands,
                compensated=compensated,
            )
        if status == OrchestrationStatus.success:
            commands = [
                OrchestrateCommand(
                    name="run_fria",
                    params={
                        "case_id": request.case_id,
                        "risk_class": request.last_result or {},
                    },
                )
            ]
            return OrchestrateResponse(
                next_step=OrchestrationStep.fria,
                action="execute",
                commands=commands,
                compensated=compensated,
            )
        if status == OrchestrationStatus.failed:
            compensated.append("use_case")
            commands = [
                OrchestrateCommand(
                    name="compensate_use_case", params={"case_id": request.case_id}
                ),
                OrchestrateCommand(
                    name="emit_case_failed",
                    params={"case_id": request.case_id, "failed_step": "risk_class"},
                ),
            ]
            return OrchestrateResponse(
                next_step=OrchestrationStep.complete,
                action="finalize",
                commands=commands,
                compensated=compensated,
                notes="Risk classification failed; compensated prior step",
            )

    if step == OrchestrationStep.fria:
        if status == OrchestrationStatus.pending:
            commands = [
                OrchestrateCommand(name="run_fria", params={"case_id": request.case_id})
            ]
            return OrchestrateResponse(
                next_step=OrchestrationStep.fria,
                action="execute",
                commands=commands,
                compensated=compensated,
            )
        if status == OrchestrationStatus.success:
            commands = [
                OrchestrateCommand(
                    name="emit_case_completed",
                    params={"case_id": request.case_id, "fria": request.last_result or {}},
                )
            ]
            return OrchestrateResponse(
                next_step=OrchestrationStep.complete,
                action="finalize",
                commands=commands,
                compensated=compensated,
            )
        if status == OrchestrationStatus.failed:
            compensated.append("risk_class")
            commands = [
                OrchestrateCommand(
                    name="compensate_risk_class", params={"case_id": request.case_id}
                ),
                OrchestrateCommand(
                    name="emit_case_failed",
                    params={"case_id": request.case_id, "failed_step": "fria"},
                ),
            ]
            return OrchestrateResponse(
                next_step=OrchestrationStep.complete,
                action="finalize",
                commands=commands,
                compensated=compensated,
                notes="FRIA failed; compensated risk classification",
            )

    # Complete or unknown states: finalize
    commands = [
        OrchestrateCommand(name="noop", params={"case_id": request.case_id})
    ]
    return OrchestrateResponse(
        next_step=OrchestrationStep.complete,
        action="finalize",
        commands=commands,
        compensated=compensated,
        notes=notes or "Completed or unrecognized state",
    )

