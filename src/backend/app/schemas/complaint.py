from datetime import datetime

from pydantic import BaseModel, Field


class ComplaintCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=5)
    issue_type: str
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class ComplaintResponse(BaseModel):
    id: int
    title: str
    description: str
    issue_type: str
    latitude: float
    longitude: float
    status: str
    priority: str
    reported_at: datetime

    class Config:
        from_attributes = True