-- AgroPilot sxemasi (PostgreSQL 16 + PostGIS)
CREATE EXTENSION IF NOT EXISTS postgis;

-- ============ users ============
CREATE TABLE users (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email            VARCHAR(255) UNIQUE,
    full_name        VARCHAR(200) NOT NULL,
    language         VARCHAR(5)   NOT NULL DEFAULT 'uz',
    telegram_chat_id BIGINT UNIQUE,
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT now()
);

-- ============ fields (dala-poligon) ============
CREATE TABLE fields (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id    UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name       VARCHAR(200) NOT NULL,
    crop_type  VARCHAR(50),
    region     VARCHAR(100),
    geom       geometry(Polygon, 4326) NOT NULL,
    centroid   geometry(Point, 4326),
    area_ha    NUMERIC(12,3),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_geom_valid CHECK (ST_IsValid(geom))
);
CREATE INDEX idx_fields_user   ON fields(user_id);
CREATE INDEX idx_fields_geom   ON fields USING GIST (geom);
CREATE INDEX idx_fields_region ON fields(region);

-- centroid va maydonni (gektar) avtomatik hisoblash
CREATE OR REPLACE FUNCTION fields_set_derived() RETURNS trigger AS $$
BEGIN
    NEW.centroid := ST_Centroid(NEW.geom);
    NEW.area_ha  := ROUND((ST_Area(NEW.geom::geography) / 10000.0)::numeric, 3);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_fields_derived
BEFORE INSERT OR UPDATE OF geom ON fields
FOR EACH ROW EXECUTE FUNCTION fields_set_derived();

-- ============ daily_measurements ============
CREATE TABLE daily_measurements (
    id                     BIGSERIAL PRIMARY KEY,
    field_id               UUID NOT NULL REFERENCES fields(id) ON DELETE CASCADE,
    obs_date               DATE NOT NULL,
    -- NASA POWER
    t2m_mean               REAL,
    t2m_max                REAL,
    t2m_min                REAL,
    precip_mm              REAL,
    solar_kwh_m2           REAL,
    -- SMAP
    soil_moisture_surface  REAL,
    soil_moisture_rootzone REAL,
    -- MODIS / HLS
    ndvi                   REAL CHECK (ndvi BETWEEN -1 AND 1),
    -- ECOSTRESS
    lst_k                  REAL,
    is_mock                BOOLEAN NOT NULL DEFAULT FALSE,
    sources                JSONB   NOT NULL DEFAULT '{}'::jsonb,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_measurement_field_date UNIQUE (field_id, obs_date)
);
CREATE INDEX idx_meas_field_date ON daily_measurements(field_id, obs_date DESC);

-- ============ recommendations ============
CREATE TABLE recommendations (
    id               BIGSERIAL PRIMARY KEY,
    field_id         UUID NOT NULL REFERENCES fields(id) ON DELETE CASCADE,
    rec_date         DATE NOT NULL,
    rec_type         VARCHAR(20) NOT NULL CHECK (rec_type IN ('irrigation','stress','disease','general')),
    action           VARCHAR(50) NOT NULL,
    severity         SMALLINT NOT NULL DEFAULT 0 CHECK (severity BETWEEN 0 AND 3),
    message_uz       TEXT NOT NULL,
    reasoning        JSONB NOT NULL DEFAULT '{}'::jsonb,
    sent_to_telegram BOOLEAN NOT NULL DEFAULT FALSE,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_reco_field_date_type UNIQUE (field_id, rec_date, rec_type)
);
CREATE INDEX idx_reco_field_date ON recommendations(field_id, rec_date DESC);

-- ============ nasa_cache (2-qadamda ishlatiladi) ============
CREATE TABLE nasa_cache (
    cache_key  TEXT PRIMARY KEY,         -- masalan: power:41.31:69.24:20260101:20260107
    payload    JSONB NOT NULL,
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX idx_cache_expires ON nasa_cache(expires_at);

-- Keyingi qadamlarda qo'shiladi:
--   5-qadam: water_stress_scores (SuvRadar)
--   6-qadam: soil_health_scores (Tuproq Pasporti)
