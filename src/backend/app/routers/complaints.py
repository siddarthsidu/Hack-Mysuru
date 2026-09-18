from datetime import date
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
    User,
    Notification,
)

from app.schemas.complaint import ComplaintCreate

from app.schemas.complaint_ai import (
    ComplaintAnalysisRequest,
    ComplaintAnalysisResponse,
)

from app.services.routing_service import (
    find_route,
    route_complaint,
)

from app.services.ai.complaint_service import (
    analyze_complaint,
)

from app.dependencies.auth import (
    get_current_user,
    require_authority_user,
    require_public_user,
)


router = APIRouter(
    prefix="/api/complaints",
    tags=["Complaints"],
)


# =========================================================
# DISTANCE CALCULATION
# =========================================================

def calculate_distance_meters(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> float:
    """
    Calculate approximate distance between two GPS coordinates
    using the Haversine formula.
    """

    earth_radius = 6371000

    lat1_rad = radians(lat1)
    lat2_rad = radians(lat2)

    delta_lat = lat2_rad - lat1_rad
    delta_lon = radians(lon2 - lon1)

    a = (
        sin(delta_lat / 2) ** 2
        + cos(lat1_rad)
        * cos(lat2_rad)
        * sin(delta_lon / 2) ** 2
    )

    c = 2 * atan2(
        sqrt(a),
        sqrt(1 - a),
    )

    return earth_radius * c


# =========================================================
# DUPLICATE DETECTION
# =========================================================

def find_duplicate(
    db: Session,
    complaint_data: ComplaintCreate,
):
    """
    Detect whether a similar complaint already exists
    within 100 meters.
    """

    complaints = (
        db.query(Complaint)
        .filter(
            Complaint.issue_type
            == complaint_data.issue_type
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
                "distance_meters": round(
                    distance,
                    2,
                ),
                "reason": (
                    "A complaint with the same issue type "
                    "was already reported within 100 meters."
                ),
            }

    return {
        "duplicate": False,
    }


# =========================================================
# CREATE COMPLAINT
# PUBLIC USERS ONLY
# =========================================================

@router.post("/")
def create_complaint(
    complaint_data: ComplaintCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_public_user),
):
    """
    Create a civic complaint.

    Only authenticated public users can create complaints.

    The user_id is taken directly from the authenticated
    JWT user and cannot be supplied by the frontend.
    """

    # -----------------------------------------------------
    # Check duplicate
    # -----------------------------------------------------

    duplicate_check = find_duplicate(
        db,
        complaint_data,
    )

    if duplicate_check["duplicate"]:

        raise HTTPException(
            status_code=409,
            detail={
                "message": (
                    "Possible duplicate complaint detected."
                ),
                "duplicate_complaint_id": (
                    duplicate_check[
                        "existing_complaint_id"
                    ]
                ),
                "distance_meters": (
                    duplicate_check[
                        "distance_meters"
                    ]
                ),
                "reason": (
                    duplicate_check[
                        "reason"
                    ]
                ),
            },
        )

    # -----------------------------------------------------
    # Create complaint
    # -----------------------------------------------------

    complaint = Complaint(
        user_id=current_user.id,
        title=complaint_data.title,
        description=complaint_data.description,
        issue_type=complaint_data.issue_type,
        latitude=complaint_data.latitude,
        longitude=complaint_data.longitude,
    )

    db.add(complaint)
    db.commit()
    db.refresh(complaint)

    # -----------------------------------------------------
    # Automatically route complaint
    # -----------------------------------------------------

    routing = route_complaint(
        db,
        complaint,
    )

    return {
        "complaint": {
            "id": complaint.id,
            "user_id": complaint.user_id,
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


# =========================================================
# GET COMPLAINTS
# ROLE-BASED ACCESS
# =========================================================

@router.get("/")
def get_complaints(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return complaints according to the authenticated user.

    PUBLIC_USER:
        Only complaints submitted by that user.

    AUTHORITY:
        Only complaints routed to that authority.
    """

    # =====================================================
    # PUBLIC USER
    # =====================================================

    if current_user.role == "PUBLIC_USER":

        complaints = (
            db.query(Complaint)
            .filter(
                Complaint.user_id
                == current_user.id
            )
            .order_by(
                Complaint.reported_at.desc()
            )
            .all()
        )

    # =====================================================
    # AUTHORITY
    # =====================================================

    elif current_user.role == "AUTHORITY":

        if current_user.authority_id is None:

            raise HTTPException(
                status_code=403,
                detail=(
                    "Authority account is not linked "
                    "to an authority."
                ),
            )

        routing_decisions = (
            db.query(RoutingDecision)
            .filter(
                RoutingDecision.authority_id
                == current_user.authority_id
            )
            .all()
        )

        complaint_ids = list(
            {
                decision.complaint_id
                for decision in routing_decisions
            }
        )

        if not complaint_ids:
            return []

        complaints = (
            db.query(Complaint)
            .filter(
                Complaint.id.in_(complaint_ids)
            )
            .order_by(
                Complaint.reported_at.desc()
            )
            .all()
        )

    else:

        raise HTTPException(
            status_code=403,
            detail="Invalid user role.",
        )

    # =====================================================
    # BUILD RESPONSE
    # =====================================================

    results = []

    for complaint in complaints:

        routing = (
            db.query(RoutingDecision)
            .filter(
                RoutingDecision.complaint_id
                == complaint.id
            )
            .order_by(
                RoutingDecision.created_at.desc()
            )
            .first()
        )

        authority = None
        jurisdiction = None
        boundary_version = None

        if routing:

            authority = (
                db.query(Authority)
                .filter(
                    Authority.id
                    == routing.authority_id
                )
                .first()
            )

            jurisdiction = (
                db.query(Jurisdiction)
                .filter(
                    Jurisdiction.id
                    == routing.jurisdiction_id
                )
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
                "user_id": complaint.user_id,
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
                        "authority": (
                            authority.name
                            if authority
                            else None
                        ),
                        "authority_type": (
                            authority.authority_type
                            if authority
                            else None
                        ),
                        "jurisdiction": (
                            jurisdiction.name
                            if jurisdiction
                            else None
                        ),
                        "boundary_version": (
                            boundary_version.version_name
                            if boundary_version
                            else None
                        ),
                        "confidence": (
                            routing.confidence
                        ),
                        "reason": (
                            routing.reason
                        ),
                    }
                    if routing
                    else None
                ),
            }
        )

    return results


# =========================================================
# ROUTE PREVIEW
# PUBLIC
# =========================================================

@router.get("/route-preview")
def route_preview(
    latitude: float,
    longitude: float,
    report_date: date,
    db: Session = Depends(get_db),
):
    """
    Preview which authority would be responsible
    for a location based on a specific date.

    This does not create a complaint or routing decision.
    """

    # -----------------------------------------------------
    # Validate latitude
    # -----------------------------------------------------

    if not -90 <= latitude <= 90:

        raise HTTPException(
            status_code=422,
            detail="Invalid latitude.",
        )

    # -----------------------------------------------------
    # Validate longitude
    # -----------------------------------------------------

    if not -180 <= longitude <= 180:

        raise HTTPException(
            status_code=422,
            detail="Invalid longitude.",
        )

    # -----------------------------------------------------
    # Find route
    # -----------------------------------------------------

    routing = find_route(
        db,
        latitude,
        longitude,
        report_date,
    )

    if not routing:

        raise HTTPException(
            status_code=422,
            detail=(
                "No jurisdiction found for this "
                "location and date."
            ),
        )

    return {
        "latitude": latitude,
        "longitude": longitude,
        "report_date": report_date,
        "routing": routing,
    }


# =========================================================
# AI COMPLAINT ANALYSIS
# PUBLIC ENDPOINT
# =========================================================

@router.post(
    "/analyze",
    response_model=ComplaintAnalysisResponse,
)
def analyze_complaint_text(
    data: ComplaintAnalysisRequest,
):
    """
    Analyze a citizen's complaint description before
    the complaint is submitted.

    Returns:
        - issue type
        - severity
        - urgency
        - duration
        - summary
        - suggested action
        - confidence
    """

    try:

        return analyze_complaint(
            data.text
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


# =========================================================
# GET SINGLE COMPLAINT
# =========================================================

@router.get("/{complaint_id}")
def get_complaint(
    complaint_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get a single complaint.

    PUBLIC_USER:
        Can only access their own complaint.

    AUTHORITY:
        Can only access complaints assigned
        to their authority.
    """

    complaint = (
        db.query(Complaint)
        .filter(
            Complaint.id == complaint_id
        )
        .first()
    )

    if not complaint:

        raise HTTPException(
            status_code=404,
            detail="Complaint not found.",
        )

    # =====================================================
    # PUBLIC USER
    # =====================================================

    if current_user.role == "PUBLIC_USER":

        if complaint.user_id != current_user.id:

            raise HTTPException(
                status_code=403,
                detail=(
                    "You can only access "
                    "your own complaints."
                ),
            )

    # =====================================================
    # AUTHORITY
    # =====================================================

    elif current_user.role == "AUTHORITY":

        if current_user.authority_id is None:

            raise HTTPException(
                status_code=403,
                detail=(
                    "Authority account is not linked "
                    "to an authority."
                ),
            )

        routing = (
            db.query(RoutingDecision)
            .filter(
                RoutingDecision.complaint_id
                == complaint.id,
                RoutingDecision.authority_id
                == current_user.authority_id,
            )
            .order_by(
                RoutingDecision.created_at.desc()
            )
            .first()
        )

        if not routing:

            raise HTTPException(
                status_code=403,
                detail=(
                    "This complaint is not assigned "
                    "to your authority."
                ),
            )

    else:

        raise HTTPException(
            status_code=403,
            detail="Invalid user role.",
        )

    return {
        "id": complaint.id,
        "user_id": complaint.user_id,
        "title": complaint.title,
        "description": complaint.description,
        "issue_type": complaint.issue_type,
        "latitude": complaint.latitude,
        "longitude": complaint.longitude,
        "status": complaint.status,
        "priority": complaint.priority,
        "reported_at": complaint.reported_at,
    }


# =========================================================
# UPDATE STATUS
# AUTHORITY ONLY
# =========================================================

@router.patch("/{complaint_id}/status")
def update_complaint_status(
    complaint_id: int,
    status: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authority_user),
):
    """
    Update the workflow status of a complaint.

    Only the authority responsible for the complaint
    can update its status.

    When a complaint moves to IN_PROGRESS or RESOLVED,
    the citizen receives an in-app notification.
    """

    # -----------------------------------------------------
    # Allowed statuses
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # Find complaint
    # -----------------------------------------------------

    complaint = (
        db.query(Complaint)
        .filter(
            Complaint.id == complaint_id
        )
        .first()
    )

    if not complaint:

        raise HTTPException(
            status_code=404,
            detail="Complaint not found.",
        )

    # -----------------------------------------------------
    # Verify authority ownership
    # -----------------------------------------------------

    routing = (
        db.query(RoutingDecision)
        .filter(
            RoutingDecision.complaint_id
            == complaint.id,
            RoutingDecision.authority_id
            == current_user.authority_id,
        )
        .order_by(
            RoutingDecision.created_at.desc()
        )
        .first()
    )

    if not routing:

        raise HTTPException(
            status_code=403,
            detail=(
                "This complaint is not assigned "
                "to your authority."
            ),
        )

    # -----------------------------------------------------
    # Prevent duplicate status updates
    # -----------------------------------------------------

    old_status = complaint.status

    if old_status == status:

        return {
            "id": complaint.id,
            "old_status": old_status,
            "status": complaint.status,
            "notification_created": False,
            "message": (
                "Complaint already has this status."
            ),
        }

    # -----------------------------------------------------
    # Update complaint status
    # -----------------------------------------------------

    complaint.status = status

    notification_created = False

    # -----------------------------------------------------
    # Create citizen notification
    # -----------------------------------------------------

    if (
        complaint.user_id is not None
        and status in {
            "in_progress",
            "resolved",
        }
    ):

        if status == "in_progress":

            message = (
                f"Your complaint #{complaint.id} "
                "is now being handled by the "
                "responsible authority."
            )

        else:

            message = (
                f"Your complaint #{complaint.id} "
                "has been resolved by the "
                "responsible authority."
            )

        notification = Notification(
            user_id=complaint.user_id,
            complaint_id=complaint.id,
            message=message,
            is_read=False,
        )

        db.add(notification)

        notification_created = True

    # -----------------------------------------------------
    # Save changes
    # -----------------------------------------------------

    db.commit()
    db.refresh(complaint)

    return {
        "id": complaint.id,
        "old_status": old_status,
        "status": complaint.status,
        "notification_created": notification_created,
        "message": (
            "Complaint status updated successfully."
        ),
    }


# =========================================================
# MANUAL ROUTING
# AUTHORITY ONLY
# =========================================================

@router.post("/{complaint_id}/route")
def route_existing_complaint(
    complaint_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authority_user),
):
    """
    Manually route an existing complaint.

    Only an authenticated authority can perform this action.
    """

    # -----------------------------------------------------
    # Find complaint
    # -----------------------------------------------------

    complaint = (
        db.query(Complaint)
        .filter(
            Complaint.id == complaint_id
        )
        .first()
    )

    if not complaint:

        raise HTTPException(
            status_code=404,
            detail="Complaint not found.",
        )

    # -----------------------------------------------------
    # Calculate routing
    # -----------------------------------------------------

    routing = route_complaint(
        db,
        complaint,
    )

    if not routing:

        raise HTTPException(
            status_code=422,
            detail=(
                "Could not determine jurisdiction "
                "for this location."
            ),
        )

    # -----------------------------------------------------
    # Security check
    # -----------------------------------------------------

    latest_routing = (
        db.query(RoutingDecision)
        .filter(
            RoutingDecision.complaint_id
            == complaint.id
        )
        .order_by(
            RoutingDecision.created_at.desc()
        )
        .first()
    )

    if (
        latest_routing
        and latest_routing.authority_id
        != current_user.authority_id
    ):

        raise HTTPException(
            status_code=403,
            detail=(
                "This complaint routes to a different "
                "authority."
            ),
        )

    return {
        "complaint_id": complaint.id,
        "status": "routed",
        "routing": routing,
    }