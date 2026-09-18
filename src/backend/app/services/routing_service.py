from sqlalchemy.orm import Session

from app.models import (
    Authority,
    BoundaryVersion,
    Complaint,
    Jurisdiction,
    RoutingDecision,
)


def route_complaint(db: Session, complaint: Complaint):

    complaint_date = complaint.reported_at.date()

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
        .order_by(BoundaryVersion.effective_from.desc())
        .first()
    )

    if not boundary:
        return None

    jurisdictions = (
        db.query(Jurisdiction)
        .filter(
            Jurisdiction.boundary_version_id == boundary.id
        )
        .all()
    )

    matched_jurisdiction = None

    for jurisdiction in jurisdictions:
        if jurisdiction.contains(
            complaint.latitude,
            complaint.longitude,
        ):
            matched_jurisdiction = jurisdiction
            break

    if not matched_jurisdiction:
        return None

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

    decision = RoutingDecision(
        complaint_id=complaint.id,
        authority_id=authority.id,
        jurisdiction_id=matched_jurisdiction.id,
        boundary_version_id=boundary.id,
        confidence=0.95,
        reason=(
            f"Location matched {matched_jurisdiction.name} "
            f"using boundary version {boundary.version_name}."
        ),
    )

    db.add(decision)

    complaint.status = "routed"

    db.commit()
    db.refresh(decision)

    return {
        "authority": authority.name,
        "authority_type": authority.authority_type,
        "jurisdiction": matched_jurisdiction.name,
        "boundary_version": boundary.version_name,
        "confidence": decision.confidence,
        "reason": decision.reason,
    }