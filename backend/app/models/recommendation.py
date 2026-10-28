from datetime import date, datetime
import uuid
from sqlalchemy import BigInteger, Boolean, Date, DateTime, ForeignKey, SmallInteger, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Recommendation(Base):
    """Kundalik AI tavsiya (sug'orish, stress, kasallik)."""
    __tablename__ = "recommendations"
    __table_args__ = (UniqueConstraint("field_id", "rec_date", "rec_type", name="uq_reco_field_date_type"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    field_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("fields.id", ondelete="CASCADE"), index=True)
    rec_date: Mapped[date] = mapped_column(Date)
    rec_type: Mapped[str] = mapped_column(String(20))        # irrigation | stress | disease | general
    action: Mapped[str] = mapped_column(String(50))          # irrigate | skip | monitor ...
    severity: Mapped[int] = mapped_column(SmallInteger, default=0)   # 0=ok ... 3=jiddiy
    message_uz: Mapped[str] = mapped_column(Text)
    reasoning: Mapped[dict] = mapped_column(JSONB, default=dict)     # qaror asoslari
    sent_to_telegram: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    field: Mapped["Field"] = relationship(back_populates="recommendations")
