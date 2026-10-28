"""Google Earth Engine orqali SMAP (tuproq namligi) va MODIS NDVI.

earthengine-api ixtiyoriy bog'liqlik: `pip install -r requirements-gee.txt`.
Kirish: `earthengine authenticate` yoki service account (GEE_SERVICE_ACCOUNT + GEE_KEY_FILE).
"""
from __future__ import annotations

import logging
from datetime import date, timedelta

from app.core.config import get_settings
from app.services.nasa.types import DailyRecord, NasaDataError

log = logging.getLogger(__name__)
_ee = None  # lazy import + initialize


def _get_ee():
    global _ee
    if _ee is not None:
        return _ee
    try:
        import ee
    except ImportError as e:
        raise NasaDataError("earthengine-api o'rnatilmagan (requirements-gee.txt)") from e
    s = get_settings()
    try:
        if s.gee_service_account and s.gee_key_file:
            creds = ee.ServiceAccountCredentials(s.gee_service_account, s.gee_key_file)
            ee.Initialize(creds, project=s.gee_project or None)
        else:
            ee.Initialize(project=s.gee_project or None)
    except Exception as e:  # noqa: BLE001
        raise NasaDataError(f"GEE ishga tushmadi: {e}") from e
    _ee = ee
    return ee


def _num(v) -> float | None:
    return None if v is None else float(v)


def parse_smap_features(features: list[dict]) -> dict[date, DailyRecord]:
    """GEE FeatureCollection.getInfo()['features'] -> {sana: DailyRecord}."""
    out: dict[date, DailyRecord] = {}
    for f in features:
        p = f.get("properties", {})
        sm_s, sm_r = _num(p.get("sm_surface")), _num(p.get("sm_rootzone"))
        if sm_s is None and sm_r is None:
            continue
        d = date.fromisoformat(p["date"])
        out[d] = DailyRecord(
            obs_date=d, soil_moisture_surface=sm_s, soil_moisture_rootzone=sm_r,
            sources={"smap": "SMAP L4 (GEE)"},
        )
    return out


def fetch_smap_daily(lat: float, lon: float, start: date, end: date) -> dict[date, DailyRecord]:
    """SMAP L4 (3 soatlik, 9 km) -> kunlik o'rtacha sm_surface / sm_rootzone (m³/m³)."""
    ee = _get_ee()
    s = get_settings()
    point = ee.Geometry.Point([lon, lat])
    start_ee = ee.Date(start.isoformat())
    n_days = (end - start).days + 1
    col = (ee.ImageCollection(s.smap_collection)
           .select(["sm_surface", "sm_rootzone"])
           .filterDate(start.isoformat(), (end + timedelta(days=1)).isoformat()))

    def per_day(i):
        d0 = start_ee.advance(ee.Number(i), "day")
        img = col.filterDate(d0, d0.advance(1, "day")).mean()
        vals = img.reduceRegion(ee.Reducer.mean(), point, 9000)
        return ee.Feature(None, vals).set("date", d0.format("YYYY-MM-dd"))

    try:
        fc = ee.FeatureCollection(ee.List.sequence(0, n_days - 1).map(per_day)).getInfo()
    except Exception as e:  # noqa: BLE001
        raise NasaDataError(f"SMAP so'rovi xato: {e}") from e
    return parse_smap_features(fc.get("features", []))


# ---------------- NDVI ----------------
NDVI_SCALE = 0.0001   # MOD13Q1: NDVI butun son * 0.0001
COMPOSITE_DAYS = 16


def forward_fill_composites(
    composites: dict[date, float], start: date, end: date, max_age_days: int = COMPOSITE_DAYS,
) -> dict[date, float]:
    """16 kunlik kompozit qiymatlarini kunlikka yoyadi (oxirgi qiymat max_age_days gacha amal qiladi)."""
    out: dict[date, float] = {}
    keys = sorted(composites)
    d = start
    while d <= end:
        prev = [k for k in keys if k <= d]
        if prev and (d - prev[-1]).days < max_age_days:
            out[d] = composites[prev[-1]]
        d += timedelta(days=1)
    return out


def parse_ndvi_features(features: list[dict]) -> dict[date, float]:
    out: dict[date, float] = {}
    for f in features:
        p = f.get("properties", {})
        raw = p.get("NDVI")
        if raw is None:
            continue
        out[date.fromisoformat(p["date"])] = round(max(-1.0, min(1.0, float(raw) * NDVI_SCALE)), 4)
    return out


def fetch_ndvi_daily(lat: float, lon: float, start: date, end: date) -> dict[date, DailyRecord]:
    """MODIS MOD13Q1 (250 m, 16 kunlik) NDVI -> kunlik qator (forward-fill)."""
    ee = _get_ee()
    s = get_settings()
    point = ee.Geometry.Point([lon, lat])
    col = (ee.ImageCollection(s.ndvi_collection).select("NDVI")
           .filterDate((start - timedelta(days=COMPOSITE_DAYS)).isoformat(),
                       (end + timedelta(days=1)).isoformat()))

    def per_img(img):
        vals = img.reduceRegion(ee.Reducer.mean(), point, 250)
        return ee.Feature(None, vals).set("date", img.date().format("YYYY-MM-dd"))

    try:
        fc = ee.FeatureCollection(col.map(per_img)).getInfo()
    except Exception as e:  # noqa: BLE001
        raise NasaDataError(f"NDVI so'rovi xato: {e}") from e
    daily = forward_fill_composites(parse_ndvi_features(fc.get("features", [])), start, end)
    return {
        d: DailyRecord(obs_date=d, ndvi=round(v, 4), sources={"ndvi": "MODIS MOD13Q1 (GEE)"})
        for d, v in daily.items()
    }
