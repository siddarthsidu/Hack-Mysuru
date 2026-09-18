from datetime import date

from app.database import SessionLocal
from app.models import Authority, BoundaryVersion, Jurisdiction


def add_boundary_v2():
    db = SessionLocal()

    try:
        # Check whether version 2 already exists
        existing = (
            db.query(BoundaryVersion)
            .filter(
                BoundaryVersion.version_name
                == "Mysuru Demo Boundary v2"
            )
            .first()
        )

        if existing:
            print("Boundary v2 already exists.")
            return

        # Close version 1
        boundary_v1 = (
            db.query(BoundaryVersion)
            .filter(
                BoundaryVersion.version_name
                == "Mysuru Demo Boundary v1"
            )
            .first()
        )

        if boundary_v1:
            boundary_v1.effective_to = date(2026, 8, 31)

        # Get authorities
        mcc = (
            db.query(Authority)
            .filter(Authority.authority_type == "MCC")
            .first()
        )

        tp = (
            db.query(Authority)
            .filter(Authority.authority_type == "TP")
            .first()
        )

        if not mcc or not tp:
            raise Exception(
                "Required MCC or TP authority not found."
            )

        # Create new boundary version
        boundary_v2 = BoundaryVersion(
            version_name="Mysuru Demo Boundary v2",
            effective_from=date(2026, 9, 1),
            effective_to=None,
            is_active=True,
        )

        db.add(boundary_v2)
        db.flush()

        # MCC area - northern section
        mcc_north = Jurisdiction(
            name="Demo MCC Zone v2 North",
            authority_id=mcc.id,
            boundary_version_id=boundary_v2.id,
            min_latitude=12.30,
            max_latitude=12.40,
            min_longitude=76.55,
            max_longitude=76.70,
        )

        # MCC area - southern/western section
        mcc_south = Jurisdiction(
            name="Demo MCC Zone v2 South",
            authority_id=mcc.id,
            boundary_version_id=boundary_v2.id,
            min_latitude=12.25,
            max_latitude=12.30,
            min_longitude=76.55,
            max_longitude=76.62,
        )

        # Area reassigned to Town Panchayat
        tp_reassigned = Jurisdiction(
            name="Demo Town Panchayat Zone v2",
            authority_id=tp.id,
            boundary_version_id=boundary_v2.id,
            min_latitude=12.25,
            max_latitude=12.30,
            min_longitude=76.62,
            max_longitude=76.70,
        )

        db.add_all(
            [
                mcc_north,
                mcc_south,
                tp_reassigned,
            ]
        )

        db.commit()

        print("✅ Boundary v2 created successfully.")
        print(
            "Version 1 effective until: 2026-08-31"
        )
        print(
            "Version 2 effective from: 2026-09-01"
        )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    add_boundary_v2()