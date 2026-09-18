from pydantic import BaseModel, Field


class PriorityAnalysisRequest(BaseModel):
    issue_type: str
    severity: str | None = None
    urgency: str | None = None
    description: str | None = None
    is_duplicate: bool = False
    routing_confidence: float | None = Field(
        default=None,
        ge=0,
        le=1,
    )


class PriorityAnalysisResponse(BaseModel):
    priority: str
    score: int
    reasons: list[str]
    recommended_action: str