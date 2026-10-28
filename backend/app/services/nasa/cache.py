"""nasa_cache jadvali orqali keshlash (PostgreSQL JSONB)."""
from __future__ import annotations

import json
import logging
from collections.abc import Callable
from datetime import date, timedelta

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.services.nasa.types import DailyRecord, records_from_json, records_to_json

log = logging.getLogger(__name__)


def make_key(source: str, lat: float, lon: float, start: date, end: date) -> str:
    # 3 xona ~ 110 m: POWER (50 km), SMAP (9 km), MODIS (250 m) uchun yetarli
    return f"{source}:{lat:.3f}:{lon:.3f}:{start:%Y%m%d}:{end:%Y%m%d}"


def ttl_for_range(end: date, today: date | None = None) -> int:
    """So'nggi 7 kunni qamragan so'rovlar tez eskiradi (ma'lumot hali yangilanadi)."""
    s = get_settings()
    today = today or date.today()
    return s.cache_ttl_recent_s if end >= today - timedelta(days=7) else s.cache_ttl_history_s


def cache_get(db: Session, key: str) -> dict[date, DailyRecord] | None:
    row = db.execute(
        text("SELECT payload FROM nasa_cache WHERE cache_key = :k AND expires_at > now()"),
        {"k": key},
    ).first()
    return records_from_json(row[0]) if row else None


def cache_set(db: Session, key: str, series: dict[date, DailyRecord], ttl_s: int) -> None:
    db.execute(
        text("""
            INSERT INTO nasa_cache (cache_key, payload, fetched_at, expires_at)
            VALUES (:k, CAST(:p AS jsonb), now(), now() + :ttl * interval '1 second')
            ON CONFLICT (cache_key) DO UPDATE
               SET payload = EXCLUDED.payload, fetched_at = now(), expires_at = EXCLUDED.expires_at
        """),
        {"k": key, "p": json.dumps(records_to_json(series)), "ttl": ttl_s},
    )
    db.commit()


def cached_fetch(
    db: Session | None, key: str, ttl_s: int, fn: Callable[[], dict[date, DailyRecord]],
) -> dict[date, DailyRecord]:
    """Keshdan o'qiydi, bo'lmasa fn() ni chaqirib saqlaydi. Kesh xatosi asosiy oqimni buzmaydi."""
    if db is not None:
        try:
            hit = cache_get(db, key)
            if hit is not None:
                return hit
        except Exception as e:  # noqa: BLE001
            db.rollback()
            log.warning("kesh o'qishda xato: %s", e)
    series = fn()
    if db is not None and series:
        try:
            cache_set(db, key, series, ttl_s)
        except Exception as e:  # noqa: BLE001
            db.rollback()
            log.warning("kesh yozishda xato: %s", e)
    return series


def purge_expired(db: Session) -> int:
    n = db.execute(text("DELETE FROM nasa_cache WHERE expires_at <= now()")).rowcount
    db.commit()
    return n
