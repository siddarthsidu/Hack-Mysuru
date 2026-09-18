from fastapi import FastAPI

from app.database import Base, engine
from app.models import (
    Authority,
    BoundaryVersion,
    Jurisdiction,
    Complaint,
    RoutingDecision,
)
from app.routers.complaints import router as complaints_router


app = FastAPI(
    title="HackMysuru CivicRoute API",
    description="Civic complaint routing system for Mysuru",
    version="1.0.0",
)

Base.metadata.create_all(bind=engine)

app.include_router(complaints_router)


@app.get("/")
def root():
    return {
        "message": "CivicRoute API is running",
        "status": "ok",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
    }