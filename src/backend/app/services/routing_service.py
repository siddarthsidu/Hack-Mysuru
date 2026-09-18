from sqlalchemy.orm import Session

from app.models import (
    Authority,
    BoundaryVersion,
    Complaint,
    Jurisdiction,
    RoutingDecision,
)


def find_route(
    db: Session,
    latitude: float,
    longitude: float,
    complaint_date,
):
    """
    Determine the responsible authority for a location
    using the boundary version effective on the complaint date.
    """

    # Find the boundary version that was active on the complaint date
    boundary = (
        db.query(BoundaryVersion)
        .filter(
            BoundaryVersion.effective_from <= complaint_date,
            BoundaryVersion.is_active.is_(True),
        )
        .filter(
            (BoundaryVersion.effective_to.is_(None))
            | (BoundaryVersion.effective_to >= complaint_date)
        )
        .order_by(
            BoundaryVersion.effective_from.desc()
        )
        .first()
    )

    if not boundary:
        return None

    # Get jurisdictions belonging to that boundary version
    jurisdictions = (
        db.query(Jurisdiction)
        .filter(
            Jurisdiction.boundary_version_id == boundary.id
        )
        .all()
    )

    matched_jurisdiction = None

    # Find the jurisdiction containing the coordinates
    for jurisdiction in jurisdictions:
        if jurisdiction.contains(
            latitude,
            longitude,
        ):
            matched_jurisdiction = jurisdiction
            break

    if not matched_jurisdiction:
        return None

    # Find the responsible authority
    authority = (
        db.query(Authority)
        .filter(
            Authority.id == matched_jurisdiction.authority_id,
            Authority.is_active.is_(True),
        )
        .first()
    )

    if not authority:
        return None

    return {
        "authority": authority.name,
        "authority_type": authority.authority_type,
        "jurisdiction": matched_jurisdiction.name,
        "boundary_version": boundary.version_name,
        "confidence": 0.95,
        "reason": (
            f"Location matched "
            f"{matched_jurisdiction.name} "
            f"using boundary version "
            f"{boundary.version_name}."
        ),
    }


def route_complaint(
    db: Session,
    complaint: Complaint,
):
    """
    Route a saved complaint and persist the routing decision.
    """

    complaint_date = complaint.reported_at.date()

    routing = find_route(
        db,
        complaint.latitude,
        complaint.longitude,
        complaint_date,
    )

    if not routing:
        return None

    # Find the exact boundary version
    boundary = (
        db.query(BoundaryVersion)
        .filter(
            BoundaryVersion.version_name
            == routing["boundary_version"]
        )
        .first()
    )

    if not boundary:
        return None

    # Find the exact jurisdiction
    jurisdiction = (
        db.query(Jurisdiction)
        .filter(
            Jurisdiction.name
            == routing["jurisdiction"],
            Jurisdiction.boundary_version_id
            == boundary.id,
        )
        .first()
    )

    if not jurisdiction:
        return None

    # Find the authority
    authority = (
        db.query(Authority)
        .filter(
            Authority.name == routing["authority"]
        )
        .first()
    )

    if not authority:
        return None

    # Store routing decision
    decision = RoutingDecision(
        complaint_id=complaint.id,
        authority_id=authority.id,
        jurisdiction_id=jurisdiction.id,
        boundary_version_id=boundary.id,
        confidence=routing["confidence"],
        reason=routing["reason"],
    )

    db.add(decision)

    complaint.status = "routed"

    db.commit()
    db.refresh(decision)

    return routing