from pydantic import BaseModel


class ComplaintAnalysisRequest(BaseModel):
    text: str


class ComplaintAnalysisResponse(BaseModel):
    success: bool
    engine: str
    issue_type: str
    severity: str
    urgency: str
    confidence: float
    duration: str | None
    summary: str
    suggested_action: str