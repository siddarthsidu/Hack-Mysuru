from datetime import datetime

from pydantic import BaseModel


class EvidenceResponse(BaseModel):
    id: int
    complaint_id: int
    file_name: str
    content_type: str
    file_size: int
    sha256_hash: str
    ai_issue_type: str | None
    ai_confidence: float | None
    is_suspicious: bool
    suspicious_reason: str | None
    uploaded_at: datetime

    class Config:
        from_attributes = True