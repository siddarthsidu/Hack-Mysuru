from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class BoundaryVersion(Base):
    __tablename__ = "boundary_versions"

    id: Mapped[int] = mapped_column(primary_key=True)

    version_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    effective_from: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    effective_to: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )