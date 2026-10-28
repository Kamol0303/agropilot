from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def liveness():
    """Server tirikmi (DB'siz)."""
    s = get_settings()
    return {"status": "ok", "service": "agropilot", "env": s.app_env, "mock_data": s.use_mock_data}


@router.get("/db")
def db_check(db: Session = Depends(get_db)):
    """DB va PostGIS ishlayaptimi."""
    version = db.execute(text("SELECT PostGIS_Version()")).scalar()
    tables = db.execute(text(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema='public' ORDER BY table_name"
    )).scalars().all()
    return {"status": "ok", "postgis": version, "tables": [t for t in tables if t != "spatial_ref_sys"]}
