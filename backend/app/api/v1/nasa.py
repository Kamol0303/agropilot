"""NASA ma'lumotlarini ko'rish endpointlari."""
import uuid
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.nasa import NasaDataError, get_daily_series, sync_field_measurements

router = APIRouter(prefix="/nasa", tags=["nasa"])


@router.get("/daily")
def preview_daily(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    start: date = Query(default_factory=lambda: date.today() - timedelta(days=6)),
    end: date = Query(default_factory=date.today),
    db: Session = Depends(get_db),
):
    try:
        recs = get_daily_series(lat, lon, start, end, db=db)
    except ValueError as e:
        raise HTTPException(422, str(e)) from e
    except NasaDataError as e:
        raise HTTPException(502, str(e)) from e
    return {"lat": lat, "lon": lon, "count": len(recs), "days": [r.to_json() for r in recs]}
