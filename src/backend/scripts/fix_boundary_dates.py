from datetime import date

from app.database import SessionLocal
from app.models import BoundaryVersion


def fix_boundary_dates():
    db = SessionLocal()

    try:
        v1 = (
            db.query(BoundaryVersion)
            .filter(
                BoundaryVersion.version_name
                == "Mysuru Demo Boundary v1"
            )
            .first()
        )

        v2 = (
            db.query(BoundaryVersion)
            .filter(
                BoundaryVersion.version_name
                == "Mysuru Demo Boundary v2"
            )
            .first()
        )

        if not v1:
            raise Exception("Boundary v1 not found.")

        if not v2:
            raise Exception("Boundary v2 not found.")

        # Close version 1 at the end of August
        v1.effective_from = date(2026, 1, 1)
        v1.effective_to = date(2026, 8, 31)
        v1.is_active = True

        # Start version 2 from September
        v2.effective_from = date(2026, 9, 1)
        v2.effective_to = None
        v2.is_active = True

        db.commit()

        print("✅ Boundary dates fixed successfully.")
        print()
        print(
            f"V1: {v1.version_name} | "
            f"{v1.effective_from} → {v1.effective_to}"
        )
        print(
            f"V2: {v2.version_name} | "
            f"{v2.effective_from} → ongoing"
        )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    fix_boundary_dates()