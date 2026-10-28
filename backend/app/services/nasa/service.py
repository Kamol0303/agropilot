"""Asosiy kirish nuqtasi."""
from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import date

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.services.nasa import cache, gee, mock, power
from app.services.nasa.types import DailyRecord, NasaDataError, merge_series

log = logging.getLogger(__name__)
MAX_SPAN_DAYS = 366


def _validate(lat: float, lon: float, start: date, end: date) -> None:
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        raise ValueError("lat/lon diapazondan tashqarida")
    if start > end:
        raise ValueError("start end'dan keyin bo'lishi mumkin emas")
    if (end - start).days + 1 > MAX_SPAN_DAYS:
        raise ValueError(f"oraliq {MAX_SPAN_DAYS} kundan oshmasin")


def get_daily_series(
    lat: float, lon: float, start: date, end: date,
    *, db: Session | None = None, settings: Settings | None = None,
) -> list[DailyRecord]:
    s = settings or get_settings()
    _validate(lat, lon, start, end)

    if s.use_mock_data:
        return [r for _, r in sorted(mock.generate_mock_daily(lat, lon, start, end).items())]

    ttl = cache.ttl_for_range(end)
    fallback = mock.generate_mock_daily(lat, lon, start, end) if s.nasa_fallback_to_mock else None

    def run(name: str, fn: Callable[[], dict[date, DailyRecord]]) -> dict[date, DailyRecord]:
        key = cache.make_key(name, lat, lon, start, end)
        try:
            return cache.cached_fetch(db, key, ttl, fn)
        except NasaDataError as e:
            if fallback is None:
                raise
            log.warning("%s uchun live ma'lumot yo'q (%s) -> mock", name, e)
            return {}

    power_s = run("power", lambda: power.fetch_power_daily(lat, lon, start, end))
    smap_s = run("smap", lambda: gee.fetch_smap_daily(lat, lon, start, end))
    ndvi_s = run("ndvi", lambda: gee.fetch_ndvi_daily(lat, lon, start, end))
    merged = merge_series(power_s, smap_s, ndvi_s)

    if fallback is not None:
        for d, mrec in fallback.items():
            rec = merged.setdefault(d, DailyRecord(obs_date=d))
            before = {n: getattr(rec, n) for n in ("t2m_mean", "soil_moisture_surface", "ndvi")}
            rec.fill_from(mrec)
            if before["t2m_mean"] is None:
                rec.sources["power"] = "mock"
            if before["soil_moisture_surface"] is None:
                rec.sources["smap"] = "mock"
            if before["ndvi"] is None:
                rec.sources["ndvi"] = "mock"
            rec.is_mock = any(v == "mock" for v in rec.sources.values())
    return [r for _, r in sorted(merged.items())]
