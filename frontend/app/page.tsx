'use client';

import React, { useState, useEffect } from 'react';

export default function Home() {
  const [activeTab, setActiveTab] = useState<'agropilot' | 'suvradar' | 'pasport'>('agropilot');
  const [backendStatus, setBackendStatus] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    fetch('http://localhost:8001/api/v1/health')
      .then((res) => {
        if (!res.ok) throw new Error('Serverga ulanib boʻlmadi');
        return res.json();
      })
      .then((data) => {
        setBackendStatus(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Backend xatosi:', err);
        setErrorMsg("Backend server ishlamayapti yoki port yopiq (8001)");
        setLoading(false);
      });
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Top Header */}
      <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex justify-between items-center">
          <div className="flex items-center space-x-3">
            <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-400 flex items-center justify-center text-xl shadow-lg shadow-emerald-900/40">
              🌾
            </div>
            <div>
              <h1 className="font-bold text-lg tracking-wide text-white">Agro<span className="text-emerald-400">Pilot</span></h1>
              <p className="text-[10px] text-slate-400 tracking-wider uppercase font-semibold">AI & NASA Earth Intelligence</p>
            </div>
          </div>

          {/* Backend Status Badge */}
          <div className="flex items-center space-x-3">
            {loading ? (
              <span className="text-xs text-slate-400 animate-pulse bg-slate-800 px-3 py-1.5 rounded-full border border-slate-700">
                Bog'lanmoqda...
              </span>
            ) : errorMsg ? (
              <span className="text-xs text-red-400 bg-red-950/50 border border-red-800 px-3 py-1.5 rounded-full flex items-center space-x-1.5">
                <span className="h-2 w-2 rounded-full bg-red-500 animate-ping"></span>
                <span>Backend o'chiq</span>
              </span>
            ) : (
              <span className="text-xs text-emerald-400 bg-emerald-950/50 border border-emerald-800/60 px-3 py-1.5 rounded-full flex items-center space-x-1.5 shadow-sm">
                <span className="h-2 w-2 rounded-full bg-emerald-500"></span>
                <span>Backend: {backendStatus?.status || 'Aktiv'} (PostGIS)</span>
              </span>
            )}
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="max-w-7xl mx-auto px-6 flex space-x-8 border-t border-slate-800/80">
          <button
            onClick={() => setActiveTab('agropilot')}
            className={`py-3 text-sm font-medium border-b-2 transition-all flex items-center space-x-2 ${
              activeTab === 'agropilot' ? 'border-emerald-500 text-emerald-400' : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <span>🌱</span>
            <span>1. AgroPilot (AI Tavsiyalar)</span>
          </button>
          <button
            onClick={() => setActiveTab('suvradar')}
            className={`py-3 text-sm font-medium border-b-2 transition-all flex items-center space-x-2 ${
              activeTab === 'suvradar' ? 'border-emerald-500 text-emerald-400' : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <span>💧</span>
            <span>2. SuvRadar (Stress xaritasi)</span>
          </button>
          <button
            onClick={() => setActiveTab('pasport')}
            className={`py-3 text-sm font-medium border-b-2 transition-all flex items-center space-x-2 ${
              activeTab === 'pasport' ? 'border-emerald-500 text-emerald-400' : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <span>📊</span>
            <span>3. Tuproq Pasporti & Simulyator</span>
          </button>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="max-w-7xl mx-auto px-6 py-8 flex-1 w-full">
        {errorMsg && (
          <div className="mb-6 p-4 rounded-xl bg-amber-950/30 border border-amber-800/50 text-amber-300 text-sm flex items-center justify-between">
            <span>⚠️ <b>Eslatma:</b> {errorMsg}. Zudlik bilan terminalda uvicorn serverini ishga tushiring.</span>
          </div>
        )}

        {/* TAB 1: AGROPILOT */}
        {activeTab === 'agropilot' && (
          <div className="space-y-6">
            <div className="flex justify-between items-center bg-slate-900/80 border border-slate-800 p-6 rounded-2xl shadow-xl">
              <div>
                <span className="text-xs uppercase tracking-wider text-emerald-400 font-bold">Faol Dala</span>
                <h2 className="text-2xl font-extrabold text-white mt-1">Paxta Maydoni №1 (Toyloq tumani)</h2>
                <p className="text-xs text-slate-400 mt-1">GPS: 39.65° N, 67.20° E · Maydoni: 15.4 gektar</p>
              </div>
              <button className="bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2.5 rounded-xl text-sm font-semibold transition shadow-lg shadow-emerald-900/30">
                + Yangi Dala Qo'shish
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="bg-slate-900/60 border border-slate-800 p-5 rounded-2xl">
                <span className="text-xs text-slate-400 font-medium">Havo Harorati (NASA POWER)</span>
                <div className="text-3xl font-black text-white mt-2">34.2 <span className="text-lg text-emerald-400">°C</span></div>
              </div>
              <div className="bg-slate-900/60 border border-slate-800 p-5 rounded-2xl">
                <span className="text-xs text-slate-400 font-medium">Tuproq Namligi (SMAP)</span>
                <div className="text-3xl font-black text-white mt-2">0.18 <span className="text-lg text-amber-400">m³/m³</span></div>
              </div>
              <div className="bg-slate-900/60 border border-slate-800 p-5 rounded-2xl">
                <span className="text-xs text-slate-400 font-medium">Vegetatsiya Indeksi (NDVI)</span>
                <div className="text-3xl font-black text-white mt-2">0.74 <span className="text-lg text-emerald-400">INDEX</span></div>
              </div>
              <div className="bg-slate-900/60 border border-slate-800 p-5 rounded-2xl">
                <span className="text-xs text-slate-400 font-medium">Yog'ingarchilik Prognozi</span>
                <div className="text-3xl font-black text-white mt-2">0.0 <span className="text-lg text-slate-400">mm</span></div>
              </div>
            </div>

            <div className="bg-gradient-to-br from-emerald-950/40 via-slate-900 to-slate-900 border border-emerald-500/30 p-6 rounded-2xl shadow-2xl">
              <div className="flex items-start space-x-4">
                <div className="h-12 w-12 rounded-2xl bg-emerald-600/20 border border-emerald-500/40 flex items-center justify-center text-2xl shrink-0">
                  🤖
                </div>
                <div>
                  <h3 className="text-lg font-bold text-white">Bugungi AI Sug'orish va Agrotexnika Tavsiyasi</h3>
                  <p className="text-slate-300 mt-2 text-sm leading-relaxed">
                    "Hozirgi tuproq namligi va yaqin kunlarda yog'ingarchilik kutilmayotganligi sababli, ertaga ertalab soat <b>06:00 dan 10:00 gacha 25 mm normada sug'orish tavsiya etiladi</b>."
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: SUVRADAR */}
        {activeTab === 'suvradar' && (
          <div className="space-y-6">
            <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-2xl">
              <h2 className="text-xl font-bold text-white">Hududiy Suv Stresi Xaritasi</h2>
              <p className="text-sm text-slate-400 mt-1">SMAP va ECOSTRESS ma'lumotlari asosida tuman bo'yicha suv taqsimoti.</p>
            </div>
            <div className="bg-slate-900/60 border border-slate-800 p-12 rounded-2xl flex flex-col justify-center items-center h-80 border-dashed border-slate-800 text-center">
              <span className="text-4xl mb-2">🗺️</span>
              <span className="text-slate-300 font-semibold">Interaktiv Suv Stresi Heatmap Vizualizatsiyasi</span>
            </div>
          </div>
        )}

        {/* TAB 3: TUPROQ PASPORTI */}
        {activeTab === 'pasport' && (
          <div className="space-y-6">
            <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-2xl">
              <h2 className="text-xl font-bold text-white">Tuproq Pasporti & Almashlab Ekish Simulyatori</h2>
              <p className="text-sm text-slate-400 mt-1">Tuproq sog'ligi indeksi va kelgusi mavsum hosildorlik prognozi.</p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-slate-900/60 border border-slate-800 p-6 rounded-2xl flex flex-col items-center justify-center text-center">
                <span className="text-xs font-bold text-slate-400 uppercase">Tuproq Sog'ligi Indeksi</span>
                <div className="text-6xl font-black text-emerald-400 my-3">82<span className="text-2xl text-slate-500">/100</span></div>
              </div>
              <div className="bg-slate-900/60 border border-slate-800 p-6 rounded-2xl md:col-span-2">
                <h3 className="font-bold text-white mb-3">Agrotexnik Simulyator</h3>
                <p className="text-sm text-slate-300">Paxta va kuzgi bug'doyni almashlab ekish tuproq sho'rlanishini kamaytiradi.</p>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}