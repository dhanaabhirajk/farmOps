import type { MetaFunction } from "@remix-run/node";
import { useNavigate, useNavigation } from "@remix-run/react";
import { useEffect, useState } from "react";
import { FarmSelector } from "~/components/FarmSelector";
import type { FarmLocation } from "~/components/FarmSelector";

export const meta: MetaFunction = () => {
  return [
    { title: "FarmOps - AI Agricultural Insights for Tamil Nadu Farmers" },
    {
      name: "description",
      content: "Select or draw your farm on the map to get instant AI-powered crop snapshots, recommendations, and irrigation schedules.",
    },
  ];
};

const FEATURES = [
  {
    emoji: "📸",
    title: "Farm Snapshot",
    desc: "Instant soil, weather, NDVI, and mandi price analysis for your exact location",
    href: "snapshot",
    color: "from-green-400 to-emerald-500",
  },
  {
    emoji: "🌱",
    title: "Crop Recommendations",
    desc: "AI-ranked crop suggestions with yield, profit, and risk scores for this season",
    href: "recommendations",
    color: "from-lime-400 to-green-500",
  },
  {
    emoji: "💧",
    title: "Irrigation Scheduling",
    desc: "14-day smart irrigation calendar based on soil moisture and weather forecast",
    href: "irrigation",
    color: "from-blue-400 to-cyan-500",
  },
  {
    emoji: "🚜",
    title: "Harvest Timing",
    desc: "Optimal harvest window and sell-vs-store decision based on price forecasts",
    href: "harvest",
    color: "from-amber-400 to-orange-500",
  },
  {
    emoji: "📋",
    title: "Subsidy Match",
    desc: "Check your farm's eligibility for Tamil Nadu government schemes and programmes",
    href: "subsidies",
    color: "from-purple-400 to-violet-500",
  },
];

export default function Home() {
  const navigate = useNavigate();
  const navigation = useNavigation();
  const isNavigating = navigation.state === "loading";

  // Tick elapsed seconds while navigating so user sees progress
  const [elapsed, setElapsed] = useState(0);
  useEffect(() => {
    if (!isNavigating) { setElapsed(0); return; }
    const t = setInterval(() => setElapsed((s) => s + 1), 1000);
    return () => clearInterval(t);
  }, [isNavigating]);

  const handleFarmSelected = (farm: FarmLocation) => {
    // Build query params so the snapshot page knows the location
    const params = new URLSearchParams({
      lat: farm.lat.toString(),
      lon: farm.lon.toString(),
      district: farm.district,
      main_crop: farm.main_crop,
      area_acres: farm.area_acres.toString(),
      farm_name: farm.farm_name,
    });
    navigate(`/farm/${farm.farm_id}/snapshot?${params.toString()}`);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-white to-blue-50">
      {/* ── Navigation loading overlay ───────────────────────────────── */}
      {isNavigating && (
        <div className="fixed inset-0 z-50 bg-white/80 backdrop-blur-sm flex flex-col items-center justify-center gap-4">
          <div className="flex flex-col items-center gap-4 bg-white rounded-2xl shadow-xl border border-green-100 p-8 max-w-sm w-full mx-4">
            <div className="flex gap-2 text-3xl animate-bounce">
              <span>🌾</span>
            </div>
            <h2 className="text-xl font-bold text-gray-900 text-center">Analysing Your Farm…</h2>
            <p className="text-sm text-gray-500 text-center">
              {elapsed < 3
                ? "Connecting to live data sources…"
                : elapsed < 6
                ? "Fetching weather, soil & NDVI…"
                : elapsed < 9
                ? "Running AI analysis with Mistral…"
                : "Compiling insights for your farm…"}
            </p>
            {/* Progress bar */}
            <div className="w-full bg-gray-100 rounded-full h-2">
              <div
                className="bg-green-500 h-2 rounded-full transition-all duration-1000"
                style={{ width: `${Math.min(elapsed * 8, 90)}%` }}
              />
            </div>
            <p className="text-xs text-gray-400">{elapsed}s elapsed · cold fetch up to 15s</p>
            <div className="flex gap-3 text-sm text-gray-400">
              <span>🌤 Weather</span>
              <span>🛰 NDVI</span>
              <span>🏪 Mandi</span>
              <span>🌱 Soil</span>
            </div>
          </div>
        </div>
      )}
      {/* ── Nav ─────────────────────────────────────────────────────────── */}
      <nav className="bg-white/80 backdrop-blur-sm shadow-sm sticky top-0 z-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-2xl">🌾</span>
            <span className="text-xl font-bold text-green-700">FarmOps</span>
          </div>
          <p className="text-gray-500 text-sm hidden sm:block">
            Location-Based Insights Engine · Tamil Nadu
          </p>
        </div>
      </nav>

      {/* ── Hero + Farm Selector ─────────────────────────────────────────── */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid lg:grid-cols-2 gap-10 items-start">
          {/* Left — headline */}
          <div className="lg:sticky lg:top-24">
            <span className="inline-block px-3 py-1 text-xs font-semibold text-green-700 bg-green-100 rounded-full mb-4">
              🤖 Powered by Mistral AI
            </span>
            <h1 className="text-4xl sm:text-5xl font-extrabold text-gray-900 leading-tight mb-4">
              AI-Powered<br />
              <span className="text-green-600">Agricultural</span> Insights
            </h1>
            <p className="text-lg text-gray-600 mb-6">
              Select your farm on the map — or draw its boundary — to instantly get soil
              analysis, weather, satellite NDVI, live mandi prices, and an AI-generated
              priority action tailored to your land.
            </p>

            {/* Feature pills */}
            <div className="flex flex-wrap gap-2 mb-8">
              {["📸 Farm Snapshot", "🌱 Crop Recs", "💧 Irrigation", "🚜 Harvest", "📋 Subsidies"].map((f) => (
                <span key={f} className="px-3 py-1 bg-white border border-gray-200 rounded-full text-sm text-gray-600 shadow-sm">
                  {f}
                </span>
              ))}
            </div>

            {/* Stats row */}
            <div className="grid grid-cols-3 gap-4 text-center">
              {[
                { value: "<8s", label: "Cold response" },
                { value: "<300ms", label: "Cached" },
                { value: "5 insights", label: "Per snapshot" },
              ].map(({ value, label }) => (
                <div key={label} className="bg-white rounded-xl shadow-sm p-3 border border-gray-100">
                  <div className="text-xl font-bold text-green-600">{value}</div>
                  <div className="text-xs text-gray-500">{label}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Right — Farm Selector card */}
          <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-6">
            <div className="mb-5">
              <h2 className="text-xl font-bold text-gray-900">📍 Select Your Farm</h2>
              <p className="text-sm text-gray-500 mt-0.5">
                Choose a test farm, enter coordinates, or draw your farm boundary on the map.
              </p>
            </div>
            <FarmSelector onFarmSelected={handleFarmSelected} />
          </div>
        </div>
      </section>

      {/* ── Features grid ───────────────────────────────────────────────── */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <h2 className="text-2xl font-bold text-gray-900 mb-6 text-center">
          What You Get After Selecting Your Farm
        </h2>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {FEATURES.map(({ emoji, title, desc, color }) => (
            <div
              key={title}
              className="bg-white rounded-xl border border-gray-100 shadow-sm p-5 hover:shadow-md transition-shadow"
            >
              <div className={`inline-flex items-center justify-center w-10 h-10 rounded-lg bg-gradient-to-br ${color} text-white text-xl mb-3`}>
                {emoji}
              </div>
              <h3 className="font-semibold text-gray-900 mb-1">{title}</h3>
              <p className="text-sm text-gray-500">{desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── How it works ────────────────────────────────────────────────── */}
      <section className="bg-white border-y border-gray-100 py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-8 text-center">How It Works</h2>
          <div className="grid sm:grid-cols-3 gap-6 text-center">
            {[
              { step: "1", emoji: "🗺", title: "Select Your Farm", desc: "Pick a test farm, enter coordinates, or draw your farm boundary on the Tamil Nadu map" },
              { step: "2", emoji: "🤖", title: "AI Analyses Data", desc: "Mistral LLM calls real-time tools: satellite NDVI, weather API, mandi prices, soil profile" },
              { step: "3", emoji: "📊", title: "Get Insights", desc: "Receive a prioritised action card, crop rankings, irrigation schedule, and subsidy matches" },
            ].map(({ step, emoji, title, desc }) => (
              <div key={step} className="relative">
                <div className="w-12 h-12 bg-green-100 text-green-700 rounded-full flex items-center justify-center text-xl font-bold mx-auto mb-3">
                  {step}
                </div>
                <div className="text-3xl mb-2">{emoji}</div>
                <h3 className="font-semibold text-gray-900 mb-1">{title}</h3>
                <p className="text-sm text-gray-500">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Data sources ────────────────────────────────────────────────── */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <div className="bg-gradient-to-r from-green-50 to-blue-50 border border-green-100 rounded-2xl p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-3">🛰 Data Sources Used</h3>
          <div className="flex flex-wrap gap-3">
            {[
              "Sentinel-2 / Google Earth Engine (NDVI)",
              "IMD / OpenWeatherMap (Weather)",
              "AGMARKNET / data.gov.in (Mandi Prices)",
              "ISRO Soil Grids (Soil Profiles)",
              "Mistral AI (LLM Reasoning)",
              "Tamil Nadu Agriculture Dept (Schemes)",
            ].map((src) => (
              <span
                key={src}
                className="px-3 py-1.5 bg-white border border-gray-200 rounded-lg text-xs text-gray-600 shadow-sm"
              >
                {src}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* ── Footer ──────────────────────────────────────────────────────── */}
      <footer className="bg-gray-900 text-white py-8 mt-4">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <p className="text-gray-400 text-sm">
            FarmOps v0.1.0 · Location-Based Insights Engine for Tamil Nadu Farmers
          </p>
          <p className="text-gray-600 text-xs mt-1">
            Built with Remix · FastAPI · Mistral AI · Supabase · Tailwind CSS
          </p>
        </div>
      </footer>
    </div>
  );
}
