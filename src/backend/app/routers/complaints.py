from math import radians, sin, cos, sqrt, atan2

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import (
    Authority,
    BoundaryVersion,
    Complaint,
    Jurisdiction,
    RoutingDecision,
)
from app.schemas.complaint import ComplaintCreate
from app.services.routing_service import route_complaint


router = APIRouter(
    prefix="/api/complaints",
    tags=["Complaints"],
)


def calculate_distance_meters(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> float:
    """
    Calculate approximate distance between two GPS coordinates.
    Uses the Haversine formula.
    """

    earth_radius = 6371000

    lat1 = radians(lat1)
    lat2 = radians(lat2)

    delta_lat = radians(lat2 - lat1)
    delta_lon = radians(lon2 - radians(lon1))

    a = (
        sin(delta_lat / 2) ** 2
        + cos(lat1)
        * cos(lat2)
        * sin(delta_lon / 2) ** 2
    )

    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return earth_radius * c


def find_duplicate(
    db: Session,
    complaint_data: ComplaintCreate,
):
    complaints = (
        db.query(Complaint)
        .filter(
            Complaint.issue_type == complaint_data.issue_type
        )
        .all()
    )

    for existing in complaints:

        distance = calculate_distance_meters(
            existing.latitude,
            existing.longitude,
            complaint_data.latitude,
            complaint_data.longitude,
        )

        if distance <= 100:
            return {
                "duplicate": True,
                "existing_complaint_id": existing.id,
                "distance_meters": round(distance, 2),
                "reason": (
                    "A complaint with the same issue type "
                    "was already reported within 100 meters."
                ),
            }

    return {
        "duplicate": False,
    }


@router.post("/")
def create_complaint(
    complaint_data: ComplaintCreate,
    db: Session = Depends(get_db),
):

    # Check for possible duplicate
    duplicate_check = find_duplicate(
        db,
        complaint_data,
    )

    # Create complaint
    complaint = Complaint(
        title=complaint_data.title,
        description=complaint_data.description,
        issue_type=complaint_data.issue_type,
        latitude=complaint_data.latitude,
        longitude=complaint_data.longitude,
    )

    # Mark possible duplicate without rejecting the report
    if duplicate_check["duplicate"]:
        complaint.status = "possible_duplicate"

    db.add(complaint)
    db.commit()
    db.refresh(complaint)

    # Only route normally if it is not a duplicate
    routing = None

    if not duplicate_check["duplicate"]:
        routing = route_complaint(
            db,
            complaint,
        )

    return {
        "complaint": {
            "id": complaint.id,
            "title": complaint.title,
            "description": complaint.description,
            "issue_type": complaint.issue_type,
            "latitude": complaint.latitude,
            "longitude": complaint.longitude,
            "status": complaint.status,
            "priority": complaint.priority,
            "reported_at": complaint.reported_at,
        },
        "duplicate_check": duplicate_check,
        "routing": routing,
    }

@router.patch("/{complaint_id}/status")
def update_complaint_status(
    complaint_id: int,
    status: str,
    db: Session = Depends(get_db),
):
    allowed_statuses = {
        "submitted",
        "routed",
        "in_progress",
        "resolved",
    }

    if status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid status. Allowed values: "
                "submitted, routed, in_progress, resolved"
            ),
        )

    complaint = (
        db.query(Complaint)
        .filter(Complaint.id == complaint_id)
        .first()
    )

    if not complaint:
        raise HTTPException(
            status_code=404,
            detail="Complaint not found",
        )

    complaint.status = status

    db.commit()
    db.refresh(complaint)

    return {
        "id": complaint.id,
        "status": complaint.status,
        "message": "Complaint status updated successfully",
    }

@router.get("/")
def get_complaints(
    db: Session = Depends(get_db),
):
    complaints = (
        db.query(Complaint)
        .order_by(Complaint.reported_at.desc())
        .all()
    )

    results = []

    for complaint in complaints:
        routing = (
            db.query(RoutingDecision)
            .filter(
                RoutingDecision.complaint_id == complaint.id
            )
            .order_by(RoutingDecision.created_at.desc())
            .first()
        )

        authority = None
        jurisdiction = None
        boundary_version = None

        if routing:
            authority = (
                db.query(Authority)
                .filter(Authority.id == routing.authority_id)
                .first()
            )

            jurisdiction = (
                db.query(Jurisdiction)
                .filter(Jurisdiction.id == routing.jurisdiction_id)
                .first()
            )

            boundary_version = (
                db.query(BoundaryVersion)
                .filter(
                    BoundaryVersion.id
                    == routing.boundary_version_id
                )
                .first()
            )

        results.append(
            {
                "id": complaint.id,
                "title": complaint.title,
                "description": complaint.description,
                "issue_type": complaint.issue_type,
                "latitude": complaint.latitude,
                "longitude": complaint.longitude,
                "status": complaint.status,
                "priority": complaint.priority,
                "reported_at": complaint.reported_at,
                "routing": (
                    {
                        "authority": authority.name
                        if authority
                        else None,
                        "authority_type": authority.authority_type
                        if authority
                        else None,
                        "jurisdiction": jurisdiction.name
                        if jurisdiction
                        else None,
                        "boundary_version": (
                            boundary_version.version_name
                            if boundary_version
                            else None
                        ),
                        "confidence": routing.confidence,
                        "reason": routing.reason,
                    }
                    if routing
                    else None
                ),
            }
        )

    return results


@router.post("/{complaint_id}/route")
def route_existing_complaint(
    complaint_id: int,
    db: Session = Depends(get_db),
):
    complaint = (
        db.query(Complaint)
        .filter(Complaint.id == complaint_id)
        .first()
    )

    if not complaint:
        raise HTTPException(
            status_code=404,
            detail="Complaint not found",
        )

    routing = route_complaint(
        db,
        complaint,
    )

    if not routing:
        raise HTTPException(
            status_code=422,
            detail="Could not determine jurisdiction for this location",
        )

    return {
        "complaint_id": complaint.id,
        "status": "routed",
        "routing": routing,
    }