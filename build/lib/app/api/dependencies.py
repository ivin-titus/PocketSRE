from fastapi import Request

from app.actions.service import ActionService
from app.incidents.service import IncidentService
from app.shared.audit import AuditLog


def incidents(request: Request) -> IncidentService:
    return request.app.state.incidents


def actions(request: Request) -> ActionService:
    return request.app.state.actions


def audit_log(request: Request) -> AuditLog:
    return request.app.state.audit_log
