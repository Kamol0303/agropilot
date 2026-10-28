"""NASA servis va endpointlari uchun unit testlar."""
from datetime import date
from fastapi.testclient import TestClient

from app.main import app
from app.services.nasa import get_daily_series
from app.services.nasa.types import DailyRecord, merge_series

client = TestClient(app)


def test_mock_generation():
    start = date(2026, 7, 1)
    end = date(2026, 7, 3)
    recs = get_daily_series(41.31, 69.24, start, end)
    assert len(recs) == 3
    assert recs[0].obs_date == start
    assert recs[2].obs_date == end
    assert recs[0].is_mock is True
    assert recs[0].t2m_mean is not None


def test_merge_series():
    d = date(2026, 7, 1)
    r1 = {d: DailyRecord(obs_date=d, t2m_mean=25.0)}
    r2 = {d: DailyRecord(obs_date=d, soil_moisture_surface=0.2)}
    merged = merge_series(r1, r2)
    assert merged[d].t2m_mean == 25.0
    assert merged[d].soil_moisture_surface == 0.2


def test_nasa_daily_endpoint():
    r = client.get("/api/v1/nasa/daily?lat=41.31&lon=69.24&start=2026-07-01&end=2026-07-03")
    assert r.status_code == 200
    data = r.json()
    assert data["count"] == 3
    assert len(data["days"]) == 3
    assert data["days"][0]["obs_date"] == "2026-07-01"


def test_nasa_daily_validation():
    r = client.get("/api/v1/nasa/daily?lat=100.0&lon=69.24")
    assert r.status_code == 422
