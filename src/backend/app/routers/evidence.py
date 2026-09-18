import os
import shutil
import uuid
from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from sqlalchemy.orm import Session

from app.database import get_db

from app.dependencies.auth import (
    get_current_user,
    require_public_user,
)

from app.models import (
    Complaint,
    Evidence,
    User,
)

from app.schemas.evidence import EvidenceResponse

from app.services.ai.vision_service import (
    analyze_image,
)

from app.services.trust_service import (
    calculate_sha256,
    check_reused_evidence,
    validate_evidence,
)


router = APIRouter(
    prefix="/api/evidence",
    tags=["Evidence & Trust"],
)


UPLOAD_DIR = Path(
    "uploads/evidence"
)

UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


ALLOWED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
}


# =========================================================
# UPLOAD AND ANALYZE EVIDENCE
# =========================================================

@router.post(
    "/complaints/{complaint_id}/upload",
)
async def upload_evidence(
    complaint_id: int,
    file: UploadFile = File(...),
    description: str = Form(""),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_public_user),
):
    """
    Upload evidence for a citizen complaint.

    Performs:
    - file validation
    - SHA-256 hashing
    - reused-image detection
    - basic image validation
    - AI analysis
    - suspicious evidence flagging
    """

    # -----------------------------------------------------
    # Find complaint
    # -----------------------------------------------------

    complaint = (
        db.query(Complaint)
        .filter(
            Complaint.id == complaint_id,
            Complaint.user_id == current_user.id,
        )
        .first()
    )

    if not complaint:
        raise HTTPException(
            status_code=404,
            detail=(
                "Complaint not found or you do not "
                "have access to it."
            ),
        )

    # -----------------------------------------------------
    # Validate filename
    # -----------------------------------------------------

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No file was provided.",
        )

    extension = Path(
        file.filename
    ).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported image format. "
                "Use JPG, JPEG, PNG or WEBP."
            ),
        )

    # -----------------------------------------------------
    # Generate unique storage name
    # -----------------------------------------------------

    stored_file_name = (
        f"{uuid.uuid4().hex}{extension}"
    )

    file_path = (
        UPLOAD_DIR /
        stored_file_name
    )

    try:

        # -------------------------------------------------
        # Save file
        # -------------------------------------------------

        with file_path.open("wb") as buffer:

            shutil.copyfileobj(
                file.file,
                buffer,
            )

        file_size = file_path.stat().st_size

        # -------------------------------------------------
        # Validate evidence
        # -------------------------------------------------

        validation = validate_evidence(
            file_path=str(file_path),
            content_type=file.content_type or "",
            file_size=file_size,
        )

        if not validation["valid"]:

            raise HTTPException(
                status_code=400,
                detail=validation["reason"],
            )

        # -------------------------------------------------
        # Calculate SHA-256
        # -------------------------------------------------

        sha256_hash = calculate_sha256(
            str(file_path)
        )

        # -------------------------------------------------
        # Check reused evidence
        # -------------------------------------------------

        reused_check = check_reused_evidence(
            db,
            sha256_hash,
        )

        is_suspicious = False
        suspicious_reason = None

        if reused_check["reused"]:

            is_suspicious = True

            suspicious_reason = (
                reused_check["reason"]
            )

        # -------------------------------------------------
        # AI analysis
        # -------------------------------------------------

        ai_result = analyze_image(
            image_path=str(file_path),
            description=description,
        )

        # -------------------------------------------------
        # Store evidence
        # -------------------------------------------------

        evidence = Evidence(
            complaint_id=complaint.id,
            file_name=file.filename,
            stored_file_name=stored_file_name,
            content_type=file.content_type or "",
            file_size=file_size,
            sha256_hash=sha256_hash,
            ai_issue_type=ai_result.get(
                "issue_type"
            ),
            ai_confidence=ai_result.get(
                "confidence"
            ),
            is_suspicious=is_suspicious,
            suspicious_reason=suspicious_reason,
        )

        db.add(evidence)
        db.commit()
        db.refresh(evidence)

        # -------------------------------------------------
        # Return trust result
        # -------------------------------------------------

        return {
            "success": True,
            "evidence": {
                "id": evidence.id,
                "complaint_id": evidence.complaint_id,
                "file_name": evidence.file_name,
                "content_type": evidence.content_type,
                "file_size": evidence.file_size,
                "sha256_hash": evidence.sha256_hash,
                "is_suspicious": evidence.is_suspicious,
                "suspicious_reason": (
                    evidence.suspicious_reason
                ),
            },
            "trust": {
                "reused_evidence": (
                    reused_check["reused"]
                ),
                "status": (
                    "needs_review"
                    if is_suspicious
                    else "trusted"
                ),
            },
            "ai_analysis": ai_result,
        }

    except HTTPException:
        raise

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Evidence processing failed: {exc}"
            ),
        )

    finally:

        # -------------------------------------------------
        # Delete physical file after processing.
        #
        # The current MVP stores evidence metadata/hash.
        # We will add persistent evidence storage later.
        # -------------------------------------------------

        if file_path.exists():

            try:
                os.remove(file_path)

            except OSError:
                pass


# =========================================================
# GET COMPLAINT EVIDENCE
# =========================================================

@router.get(
    "/complaints/{complaint_id}",
)
def get_complaint_evidence(
    complaint_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return evidence associated with a complaint.

    Public users can only access their own complaint.
    Authorities can access complaints routed to them.
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

    # -----------------------------------------------------
    # Public user security
    # -----------------------------------------------------

    if current_user.role == "PUBLIC_USER":

        if complaint.user_id != current_user.id:

            raise HTTPException(
                status_code=403,
                detail=(
                    "You can only access evidence "
                    "for your own complaints."
                ),
            )

    # -----------------------------------------------------
    # Authority access
    # -----------------------------------------------------

    elif current_user.role == "AUTHORITY":

        from app.models import RoutingDecision

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

    evidence_items = (
        db.query(Evidence)
        .filter(
            Evidence.complaint_id
            == complaint.id
        )
        .order_by(
            Evidence.uploaded_at.desc()
        )
        .all()
    )

    return {
        "complaint_id": complaint.id,
        "evidence": [
            {
                "id": item.id,
                "file_name": item.file_name,
                "content_type": item.content_type,
                "file_size": item.file_size,
                "sha256_hash": item.sha256_hash,
                "ai_issue_type": item.ai_issue_type,
                "ai_confidence": item.ai_confidence,
                "is_suspicious": item.is_suspicious,
                "suspicious_reason": (
                    item.suspicious_reason
                ),
                "uploaded_at": item.uploaded_at,
            }
            for item in evidence_items
        ],
    }