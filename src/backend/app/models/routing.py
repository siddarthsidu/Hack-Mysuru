from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class RoutingDecision(Base):
    __tablename__ = "routing_decisions"

    id: Mapped[int] = mapped_column(primary_key=True)

    complaint_id: Mapped[int] = mapped_column(
        ForeignKey("complaints.id"),
        nullable=False,
    )

    authority_id: Mapped[int] = mapped_column(
        ForeignKey("authorities.id"),
        nullable=False,
    )

    jurisdiction_id: Mapped[int] = mapped_column(
        ForeignKey("jurisdictions.id"),
        nullable=False,
    )

    boundary_version_id: Mapped[int] = mapped_column(
        ForeignKey("boundary_versions.id"),
        nullable=False,
    )

    confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )