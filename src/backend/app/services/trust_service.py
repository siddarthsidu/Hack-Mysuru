import hashlib
from pathlib import Path

from sqlalchemy.orm import Session

from app.models import Evidence


def calculate_sha256(file_path: str) -> str:
    """
    Calculate SHA-256 hash for an evidence file.
    """

    sha256 = hashlib.sha256()

    with open(file_path, "rb") as file:
        while True:
            chunk = file.read(1024 * 1024)

            if not chunk:
                break

            sha256.update(chunk)

    return sha256.hexdigest()


def check_reused_evidence(
    db: Session,
    sha256_hash: str,
):
    """
    Check whether exactly the same evidence file
    has already been uploaded.
    """

    existing = (
        db.query(Evidence)
        .filter(
            Evidence.sha256_hash == sha256_hash
        )
        .first()
    )

    if existing:
        return {
            "reused": True,
            "existing_evidence_id": existing.id,
            "existing_complaint_id": existing.complaint_id,
            "reason": (
                "The exact same evidence file has "
                "already been submitted."
            ),
        }

    return {
        "reused": False,
    }


def validate_evidence(
    file_path: str,
    content_type: str,
    file_size: int,
):
    """
    Basic evidence integrity checks.
    """

    path = Path(file_path)

    if not path.exists():
        return {
            "valid": False,
            "reason": "Evidence file does not exist.",
        }

    if file_size <= 0:
        return {
            "valid": False,
            "reason": "Evidence file is empty.",
        }

    if file_size > 10 * 1024 * 1024:
        return {
            "valid": False,
            "reason": "Evidence file exceeds the 10 MB limit.",
        }

    allowed_types = {
        "image/jpeg",
        "image/png",
        "image/webp",
    }

    if content_type not in allowed_types:
        return {
            "valid": False,
            "reason": (
                "Only JPEG, PNG and WEBP images "
                "are supported."
            ),
        }

    return {
        "valid": True,
        "reason": None,
    }