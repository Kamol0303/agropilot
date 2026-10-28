"""Ilova sozlamalari (.env dan o'qiladi)."""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "dev"
    database_url: str = "postgresql+psycopg2://agropilot:agropilot@localhost:5432/agropilot"
    cors_origins: str = "http://localhost:3000"

    # --- NASA ma'lumotlari ---
    use_mock_data: bool = True            # True: NASA'ga umuman murojaat qilmaydi (offline demo)
    nasa_fallback_to_mock: bool = True    # live manba xato bersa, mock bilan to'ldiradi (is_mock=True)
    nasa_power_url: str = "https://power.larc.nasa.gov/api/temporal/daily/point"
    nasa_timeout_s: float = 30.0
    cache_ttl_recent_s: int = 6 * 3600        # oxirgi 7 kunni qamragan so'rovlar uchun
    cache_ttl_history_s: int = 30 * 86400     # to'liq o'tgan davr uchun

    # Google Earth Engine (SMAP, MODIS NDVI)
    gee_service_account: str = ""
    gee_key_file: str = ""
    gee_project: str = ""
    smap_collection: str = "NASA/SMAP/SPL4SMGP/007"
    ndvi_collection: str = "MODIS/061/MOD13Q1"

    earthdata_username: str = ""
    earthdata_password: str = ""
    telegram_bot_token: str = ""
    llm_api_key: str = ""

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
