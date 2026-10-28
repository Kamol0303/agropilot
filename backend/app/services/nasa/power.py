"""NASA POWER (daily, point) klienti.

Haqiqiy javob formati (JSON):
{
  "type": "Feature",
  "geometry": {"type": "Point", "coordinates": [lon, lat, elev]},
  "properties": {"parameter": {"T2M": {"20260101": 1.2, ...}, "PRECTOTCORR": {...}, ...}},
  "parameters": {"T2M": {"units": "C", ...}, "ALLSKY_SFC_SW_DWN": {"units": "MJ/m^2/day", ...}},
  ...
}
Ma'lumot yo'q kunlar -999 bilan to'ldirilgan (fill value). POWER odatda 2-3 kun kechikadi.
"""
from __future__ import annotations

import logging
import time
from datetime import date, datetime

import httpx

from app.core.config import get_settings
from app.services.nasa.types import DailyRecord, NasaDataError

log = logging.getLogger(__name__)

POWER_PARAMS = ["T2M", "T2M_MAX", "T2M_MIN", "PRECTOTCORR", "ALLSKY_SFC_SW_DWN"]
FILL_VALUE = -999.0


def _clean(v) -> float | None:
    if v is None:
        return None
    v = float(v)
    return None if v <= FILL_VALUE + 1e-6 else v


def parse_power_response(payload: dict) -> dict[date, DailyRecord]:
    """POWER JSON javobini {sana: DailyRecord} ga aylantiradi."""
    try:
        par = payload["properties"]["parameter"]
    except (KeyError, TypeError) as e:
        raise NasaDataError(f"POWER javob formati kutilmagan: {e}") from e

    # AG hamjamiyatida radiatsiya MJ/m²/kun; kWh/m²/kun ga o'tkazamiz.
    # Birlik javobning "parameters" bo'limidan o'qiladi; yo'q bo'lsa MJ deb olinadi (AG default).
    units = ((payload.get("parameters") or {}).get("ALLSKY_SFC_SW_DWN") or {}).get("units", "MJ/m^2/day")
    solar_factor = 1 / 3.6 if "MJ" in units.upper() else 1.0

    all_days: set[str] = set()
    for series in par.values():
        all_days.update(series.keys())

    out: dict[date, DailyRecord] = {}
    for key in sorted(all_days):
        d = datetime.strptime(key, "%Y%m%d").date()
        solar = _clean(par.get("ALLSKY_SFC_SW_DWN", {}).get(key))
        rec = DailyRecord(
            obs_date=d,
            t2m_mean=_clean(par.get("T2M", {}).get(key)),
            t2m_max=_clean(par.get("T2M_MAX", {}).get(key)),
            t2m_min=_clean(par.get("T2M_MIN", {}).get(key)),
            precip_mm=_clean(par.get("PRECTOTCORR", {}).get(key)),
            solar_kwh_m2=None if solar is None else round(solar * solar_factor, 3),
            sources={"power": "NASA POWER daily (AG)"},
        )
        # hamma o'lchov bo'sh kunni qoldirmaymiz
        if any(getattr(rec, n) is not None for n in ("t2m_mean", "precip_mm", "solar_kwh_m2")):
            out[d] = rec
    return out


def fetch_power_daily(
    lat: float, lon: float, start: date, end: date,
    *, client: httpx.Client | None = None, retries: int = 3,
) -> dict[date, DailyRecord]:
    """Berilgan koordinata uchun [start, end] oralig'ida kunlik POWER ma'lumotlarini tortadi."""
    s = get_settings()
    params = {
        "parameters": ",".join(POWER_PARAMS),
        "community": "AG",
        "longitude": f"{lon:.4f}",
        "latitude": f"{lat:.4f}",
        "start": start.strftime("%Y%m%d"),
        "end": end.strftime("%Y%m%d"),
        "format": "JSON",
    }
    own = client is None
    client = client or httpx.Client(timeout=s.nasa_timeout_s)
    try:
        last_err: Exception | None = None
        for attempt in range(1, retries + 1):
            try:
                r = client.get(s.nasa_power_url, params=params)
                if r.status_code >= 500 or r.status_code == 429:
                    raise httpx.HTTPStatusError("server busy", request=r.request, response=r)
                r.raise_for_status()
                return parse_power_response(r.json())
            except (httpx.TransportError, httpx.HTTPStatusError) as e:
                last_err = e
                log.warning("POWER urinish %s/%s xato: %s", attempt, retries, e)
                time.sleep(min(2 ** attempt, 8))
        raise NasaDataError(f"NASA POWER javob bermadi: {last_err}")
    finally:
        if own:
            client.close()
