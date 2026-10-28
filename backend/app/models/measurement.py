from datetime import date, datetime
import uuid
from sqlalchemy import BigInteger, Boolean, Date, DateTime, Float, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class DailyMeasurement(Base):
    """Bitta dala uchun bir kunlik jamlangan NASA o'lchovlari."""
    __tablename__ = "daily_measurements"
    __table_args__ = (UniqueConstraint("field_id", "obs_date", name="uq_measurement_field_date"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    field_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("fields.id", ondelete="CASCADE"), index=True)
    obs_date: Mapped[date] = mapped_column(Date)

    # NASA POWER
    t2m_mean: Mapped[float | None] = mapped_column(Float)        # °C
    t2m_max: Mapped[float | None] = mapped_column(Float)
    t2m_min: Mapped[float | None] = mapped_column(Float)
    precip_mm: Mapped[float | None] = mapped_column(Float)       # mm/kun
    solar_kwh_m2: Mapped[float | None] = mapped_column(Float)    # kWh/m²/kun

    # SMAP
    soil_moisture_surface: Mapped[float | None] = mapped_column(Float)   # m³/m³
    soil_moisture_rootzone: Mapped[float | None] = mapped_column(Float)  # m³/m³

    # MODIS / HLS
    ndvi: Mapped[float | None] = mapped_column(Float)            # -1..1

    # ECOSTRESS
    lst_k: Mapped[float | None] = mapped_column(Float)           # sirt harorati, Kelvin

    is_mock: Mapped[bool] = mapped_column(Boolean, default=False)
    sources: Mapped[dict] = mapped_column(JSONB, default=dict)   # provenance
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    field: Mapped["Field"] = relationship(back_populates="measurements")
