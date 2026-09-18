from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Jurisdiction(Base):
    __tablename__ = "jurisdictions"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    authority_id: Mapped[int] = mapped_column(
        ForeignKey("authorities.id"),
        nullable=False,
    )

    boundary_version_id: Mapped[int] = mapped_column(
        ForeignKey("boundary_versions.id"),
        nullable=False,
    )

    min_latitude: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    max_latitude: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    min_longitude: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    max_longitude: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    def contains(self, latitude: float, longitude: float) -> bool:
        return (
            self.min_latitude <= latitude <= self.max_latitude
            and self.min_longitude <= longitude <= self.max_longitude
        )