import os
import sys
import secrets

# Allow imports from the backend root
sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
        )
    ),
)

from app.database import SessionLocal
from app.models import Authority, User
from app.services.auth_service import hash_password


def generate_password():
    """
    Generate a secure temporary authority password.
    """
    return secrets.token_urlsafe(12)


def seed_authority_users():
    db = SessionLocal()

    try:
        authorities = (
            db.query(Authority)
            .filter(Authority.is_active.is_(True))
            .all()
        )

        if not authorities:
            print("No active authorities found.")
            print("Run the normal seed_data.py first.")
            return

        print("\n========================================")
        print(" CIVICROUTE AUTHORITY ACCOUNTS")
        print("========================================\n")

        for authority in authorities:

            # Generate a predictable system email
            email = (
                f"{authority.authority_type.lower()}"
                f"@civicroute.local"
            )

            existing_user = (
                db.query(User)
                .filter(User.email == email)
                .first()
            )

            if existing_user:
                print(
                    f"[EXISTS] {authority.name}"
                )
                print(
                    f"Email: {existing_user.email}"
                )
                print()
                continue

            password = generate_password()

            user = User(
                name=f"{authority.name} Officer",
                email=email,
                password_hash=hash_password(password),
                role="AUTHORITY",
                phone=authority.phone,
                authority_id=authority.id,
                is_active=True,
            )

            db.add(user)
            db.commit()
            db.refresh(user)

            print("----------------------------------------")
            print(f"Authority : {authority.name}")
            print(f"Email     : {email}")
            print(f"Password  : {password}")
            print(f"Authority ID: {authority.id}")
            print("----------------------------------------")
            print()

        print("Authority account setup completed.")

    finally:
        db.close()


if __name__ == "__main__":
    seed_authority_users()