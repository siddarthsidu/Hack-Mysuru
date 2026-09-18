from fastapi import APIRouter

from app.schemas.priority import (
    PriorityAnalysisRequest,
    PriorityAnalysisResponse,
)
from app.services.priority_service import calculate_priority


router = APIRouter(
    prefix="/api/priority",
    tags=["Priority Engine"],
)


@router.post(
    "/analyze",
    response_model=PriorityAnalysisResponse,
)
def analyze_priority(
    data: PriorityAnalysisRequest,
):
    return calculate_priority(
        issue_type=data.issue_type,
        severity=data.severity,
        urgency=data.urgency,
        description=data.description,
        is_duplicate=data.is_duplicate,
        routing_confidence=data.routing_confidence,
    )