from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers.auth import router as auth_router
from app.routers import notifications
from app.routers import evidence
from app.database import Base, engine
from app.models import (
    Authority,
    BoundaryVersion,
    Jurisdiction,
    Complaint,
    RoutingDecision,
)
from app.routers.complaints import router as complaints_router
from app.routers import priority

app = FastAPI(
    title="HackMysuru CivicRoute API",
    description="Civic complaint routing system for Mysuru",
    version="1.0.0",
)


# Allow the React/Vite frontend to communicate with the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


Base.metadata.create_all(bind=engine)

app.include_router(complaints_router)
app.include_router(auth_router)
app.include_router(notifications.router)
app.include_router(evidence.router)
app.include_router(priority.router)

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