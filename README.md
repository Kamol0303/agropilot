# AgroPilot 🌾

NASA Yer kuzatuvi ma'lumotlari asosidagi qishloq xo'jaligi platformasi:
**AgroPilot** (kundalik tavsiyalar) · **SuvRadar** (suv stressi xaritasi) · **Tuproq Pasporti** (tuproq sog'ligi).

## 1-qadam: ishga tushirish
```bash
cp .env.example .env
docker compose up -d --build        # PostGIS + FastAPI
curl localhost:8000/api/v1/health/db

cd frontend && cp .env.local.example .env.local
npm install && npm run dev          # http://localhost:3000
```
To'liq README 7-qadamda yoziladi.
