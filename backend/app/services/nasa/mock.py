"""Deterministik soxta ma'lumot (O'rta Osiyo iqlimiga yaqin)."""
from __future__ import annotations

import calendar
import math
import random
from datetime import date, timedelta
from functools import lru_cache

from app.services.nasa.types import DailyRecord


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


@lru_cache(maxsize=64)
def _simulate_year(lat_key: float, lon_key: float, year: int) -> dict[date, DailyRecord]:
    rng = random.Random(f"{lat_key:.2f}:{lon_key:.2f}:{year}")
    lat_shift = (40.0 - lat_key) * 0.4
    sm_s, sm_r = 0.22, 0.26
    out: dict[date, DailyRecord] = {}
    n_days = 366 if calendar.isleap(year) else 365
    for i in range(n_days):
        d = date(year, 1, 1) + timedelta(days=i)
        doy = i + 1
        season = math.sin(2 * math.pi * (doy - 105) / 365)
        t_mean = 14 + 15 * season + lat_shift + rng.gauss(0, 2)
        t_max = t_mean + 6 + rng.uniform(0, 3)
        t_min = t_mean - 6 - rng.uniform(0, 3)
        wet = 0.30 if (doy < 150 or doy > 300) else 0.04
        precip = round(rng.expovariate(1 / 6), 1) if rng.random() < wet else 0.0
        solar = max(0.5, 4.8 + 2.6 * season + rng.gauss(0, 0.4)) * (0.45 if precip > 2 else 1.0)
        heat = max(season, 0.0)
        sm_s = _clamp(sm_s - (0.002 + 0.006 * heat) + precip * 0.012, 0.05, 0.45)
        sm_r = _clamp(sm_r + 0.15 * (sm_s - sm_r) - 0.0015 * heat, 0.08, 0.45)
        ndvi = _clamp(0.18 + 0.60 * math.exp(-((doy - 195) / 50) ** 2) + rng.gauss(0, 0.015), 0.05, 0.95)
        out[d] = DailyRecord(
            obs_date=d,
            t2m_mean=round(t_mean, 1), t2m_max=round(t_max, 1), t2m_min=round(t_min, 1),
            precip_mm=precip, solar_kwh_m2=round(solar, 2),
            soil_moisture_surface=round(sm_s, 3), soil_moisture_rootzone=round(sm_r, 3),
            ndvi=round(ndvi, 3), lst_k=round(t_max + 273.15 + 4 + rng.gauss(0, 1.5), 1),
            is_mock=True,
            sources={k: "mock" for k in ("power", "smap", "ndvi", "ecostress")},
        )
    return out


def generate_mock_daily(lat: float, lon: float, start: date, end: date) -> dict[date, DailyRecord]:
    out: dict[date, DailyRecord] = {}
    for year in range(start.year, end.year + 1):
        for d, rec in _simulate_year(round(lat, 2), round(lon, 2), year).items():
            if start <= d <= end:
                out[d] = DailyRecord.from_json(rec.to_json())
    return out
