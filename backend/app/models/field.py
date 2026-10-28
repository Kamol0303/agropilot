import uuid
from datetime import datetime
from sqlalchemy import String, Numeric, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from geoalchemy2 import Geometry

from app.models.base import Base


class Field(Base):
    """Fermer dalasi (poligon)."""
    __tablename__ = "fields"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    crop_type: Mapped[str | None] = mapped_column(String(50))     # masalan: cotton, wheat
    region: Mapped[str | None] = mapped_column(String(100))       # SuvRadar uchun hudud nomi
    geom = mapped_column(Geometry("POLYGON", srid=4326), nullable=False)
    # centroid va area_ha DB trigger orqali to'ldiriladi (init.sql)
    centroid = mapped_column(Geometry("POINT", srid=4326), nullable=True)
    area_ha: Mapped[float | None] = mapped_column(Numeric(12, 3), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="fields")
    measurements: Mapped[list["DailyMeasurement"]] = relationship(back_populates="field", cascade="all, delete-orphan")
    recommendations: Mapped[list["Recommendation"]] = relationship(back_populates="field", cascade="all, delete-orphan")
