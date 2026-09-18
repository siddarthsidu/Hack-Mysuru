from datetime import datetime

from sqlalchemy import DateTime, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Complaint(Base):
    __tablename__ = "complaints"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    issue_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    latitude: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    longitude: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="submitted",
        nullable=False,
    )

    priority: Mapped[str] = mapped_column(
        String(20),
        default="normal",
        nullable=False,
    )

    reported_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )