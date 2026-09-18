from datetime import date

from app.database import Base, SessionLocal, engine
from app.models import Authority, BoundaryVersion, Jurisdiction


def seed_data():
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        # Prevent duplicate seed data
        if db.query(Authority).count() > 0:
            print("Seed data already exists.")
            return

        # -------------------------
        # Authorities
        # -------------------------

        mcc = Authority(
            name="Mysuru City Corporation",
            authority_type="MCC",
            contact_email="mcc@example.com",
            phone="0821-XXXXXXX",
        )

        town_panchayat = Authority(
            name="Demo Town Panchayat",
            authority_type="TP",
            contact_email="tp@example.com",
            phone="0821-XXXXXXX",
        )

        gram_panchayat = Authority(
            name="Demo Gram Panchayat",
            authority_type="GP",
            contact_email="gp@example.com",
            phone="0821-XXXXXXX",
        )

        db.add_all([mcc, town_panchayat, gram_panchayat])
        db.flush()

        # -------------------------
        # Boundary Version
        # -------------------------

        boundary = BoundaryVersion(
            version_name="Mysuru Demo Boundary v1",
            effective_from=date(2026, 1, 1),
            effective_to=None,
            is_active=True,
        )

        db.add(boundary)
        db.flush()

        # -------------------------
        # Demo Jurisdictions
        # -------------------------
        #
        # IMPORTANT:
        # These are demo bounding boxes for the MVP.
        # They are NOT official administrative boundaries.
        #

        jurisdictions = [
            Jurisdiction(
                name="Demo MCC Zone",
                authority_id=mcc.id,
                boundary_version_id=boundary.id,
                min_latitude=12.25,
                max_latitude=12.40,
                min_longitude=76.55,
                max_longitude=76.70,
            ),
            Jurisdiction(
                name="Demo Town Panchayat Zone",
                authority_id=town_panchayat.id,
                boundary_version_id=boundary.id,
                min_latitude=12.20,
                max_latitude=12.25,
                min_longitude=76.55,
                max_longitude=76.70,
            ),
            Jurisdiction(
                name="Demo Gram Panchayat Zone",
                authority_id=gram_panchayat.id,
                boundary_version_id=boundary.id,
                min_latitude=12.15,
                max_latitude=12.20,
                min_longitude=76.55,
                max_longitude=76.70,
            ),
        ]

        db.add_all(jurisdictions)

        db.commit()

        print("✅ Demo seed data created successfully.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_data()