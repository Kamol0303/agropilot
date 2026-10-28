"""daily_measurements ga saqlash (upsert) va dala uchun sinxronlash."""
from __future__ import annotations

import uuid
from datetime import date, timedelta

from sqlalchemy import func, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models import DailyMeasurement
from app.services.nasa.service import get_daily_series
from app.services.nasa.types import VALUE_COLS, DailyRecord

CHUNK = 500


def upsert_measurements(db: Session, field_id: uuid.UUID | str, records: list[DailyRecord]) -> int:
    """Qatorlarni (field_id, obs_date) bo'yicha yozadi.

    Mavjud qiymat yangi NULL bilan o'chirilmaydi (COALESCE); sources JSONB birlashtiriladi;
    is_mock yangi yozuvdagi qiymatga yangilanadi (real ma'lumot mock'ni almashtiradi).
    """
    if not records:
        return 0
    t = DailyMeasurement.__table__
    for i in range(0, len(records), CHUNK):
        part = records[i:i + CHUNK]
        rows = [
            {"field_id": field_id, "obs_date": r.obs_date, "is_mock": r.is_mock, "sources": r.sources,
             **{c: getattr(r, c) for c in VALUE_COLS}}
            for r in part
        ]
        stmt = insert(t).values(rows)
        set_ = {c: func.coalesce(stmt.excluded[c], t.c[c]) for c in VALUE_COLS}
        set_["is_mock"] = stmt.excluded.is_mock
        set_["sources"] = t.c.sources.op("||")(stmt.excluded.sources)
        db.execute(stmt.on_conflict_do_update(constraint="uq_measurement_field_date", set_=set_))
    db.commit()
    return len(records)


def get_field_centroid(db: Session, field_id: uuid.UUID | str) -> tuple[float, float] | None:
    """(lat, lon) — dala poligonining markazi."""
    row = db.execute(
        text("SELECT ST_Y(centroid), ST_X(centroid) FROM fields WHERE id = :id"),
        {"id": str(field_id)},
    ).first()
    return (float(row[0]), float(row[1])) if row and row[0] is not None else None


def sync_field_measurements(
    db: Session, field_id: uuid.UUID | str, start: date | None = None, end: date | None = None,
) -> dict:
    """Dala markazi uchun NASA ma'lumotini olib DB ga yozadi. Standart: oxirgi 14 kun."""
    end = end or date.today()
    start = start or end - timedelta(days=13)
    pos = get_field_centroid(db, field_id)
    if pos is None:
        raise LookupError(f"dala topilmadi: {field_id}")
    records = get_daily_series(pos[0], pos[1], start, end, db=db)
    n = upsert_measurements(db, field_id, records)
    return {
        "field_id": str(field_id), "start": start.isoformat(), "end": end.isoformat(), "rows": n,
        "mock_rows": sum(1 for r in records if r.is_mock),
    }
