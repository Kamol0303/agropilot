"""NASA servislari uchun umumiy ma'lumot turlari."""
from __future__ import annotations

from dataclasses import dataclass, field, fields as dc_fields
from datetime import date

VALUE_COLS = (
    "t2m_mean", "t2m_max", "t2m_min", "precip_mm", "solar_kwh_m2",
    "soil_moisture_surface", "soil_moisture_rootzone", "ndvi", "lst_k",
)


class NasaDataError(RuntimeError):
    """Live NASA manbasidan ma'lumot olib bo'lmadi."""


@dataclass
class DailyRecord:
    obs_date: date
    t2m_mean: float | None = None
    t2m_max: float | None = None
    t2m_min: float | None = None
    precip_mm: float | None = None
    solar_kwh_m2: float | None = None
    soil_moisture_surface: float | None = None
    soil_moisture_rootzone: float | None = None
    ndvi: float | None = None
    lst_k: float | None = None
    is_mock: bool = False
    sources: dict = field(default_factory=dict)

    def to_json(self) -> dict:
        d = {f.name: getattr(self, f.name) for f in dc_fields(self)}
        d["obs_date"] = self.obs_date.isoformat()
        return d

    @classmethod
    def from_json(cls, d: dict) -> "DailyRecord":
        d = dict(d)
        d["obs_date"] = date.fromisoformat(d["obs_date"])
        return cls(**d)

    def fill_from(self, other: "DailyRecord") -> None:
        for name in VALUE_COLS:
            if getattr(self, name) is None and getattr(other, name) is not None:
                setattr(self, name, getattr(other, name))
        for k, v in other.sources.items():
            self.sources.setdefault(k, v)
        self.is_mock = self.is_mock or other.is_mock


def merge_series(*series: dict[date, DailyRecord]) -> dict[date, DailyRecord]:
    out: dict[date, DailyRecord] = {}
    for s in series:
        for d, rec in s.items():
            if d in out:
                out[d].fill_from(rec)
            else:
                out[d] = rec
    return out


def records_to_json(series: dict[date, DailyRecord]) -> list[dict]:
    return [series[d].to_json() for d in sorted(series)]


def records_from_json(rows: list[dict]) -> dict[date, DailyRecord]:
    recs = [DailyRecord.from_json(r) for r in rows]
    return {r.obs_date: r for r in recs}
