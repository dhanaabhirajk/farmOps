/**
 * Farm Snapshot Route — farm.$farmId.snapshot
 *
 * Fetches and displays a comprehensive farm snapshot: soil, weather,
 * NDVI trend, mandi prices, and the AI-generated top priority action.
 *
 * Manual location mode: accepts lat/lon/district/main_crop/area_acres as search params.
 * Pre-seeded farms: uses farmId UUID to identify the farm.
 */

import type { LoaderFunctionArgs, MetaFunction, ShouldRevalidateFunctionArgs } from "@remix-run/node";
import { json } from "@remix-run/node";
import {
  Link,
  useLoaderData,
  useNavigation,
  useRevalidator,
  useRouteLoaderData,
  useSearchParams,
} from "@remix-run/react";
import { useEffect, useState } from "react";
import { FarmSnapshotCard } from "~/components/FarmSnapshotCard";
import type { SnapshotData } from "~/components/FarmSnapshotCard";
import { Spinner } from "~/components/ui/Spinner";
import { Button } from "~/components/ui/Button";

// Don't re-run the snapshot loader when the user just tabs between pages within
// the same farm — reuse the already-loaded data.  Only re-fetch when:
//   • A different farm is selected (farmId changes), or
//   • The user explicitly hits Refresh (use_cache=false).
export function shouldRevalidate({
  currentUrl,
  nextUrl,
  defaultShouldRevalidate,
}: ShouldRevalidateFunctionArgs) {
  const currentFarmId = currentUrl.pathname.match(/\/farm\/([^/]+)/)?.[1];
  const nextFarmId = nextUrl.pathname.match(/\/farm\/([^/]+)/)?.[1];
  const forceRefresh = nextUrl.searchParams.get("use_cache") === "false";

  if (nextFarmId && currentFarmId === nextFarmId && !forceRefresh) {
    return false; // same farm, just switching tabs — keep cached data
  }
  return defaultShouldRevalidate;
}

export const meta: MetaFunction<typeof loader> = ({ data }) => {
  const name = data?.farmName ?? "Farm Snapshot";
  return [
    { title: `${name} — FarmOps` },
    { name: "description", content: "AI-powered farm snapshot with soil, weather, NDVI and market data" },
  ];
};

// ─── Loader ─────────────────────────────────────────────────────────────────

interface LoaderData {
  farmId: string;
  farmName: string;
  district: string;
  mainCrop: string;
  areaAcres: number;
  lat: number;
  lon: number;
  snapshot: SnapshotData | null;
  error: string | null;
  cached: boolean;
  responseTimeMs: number | null;
}

export async function loader({ params, request }: LoaderFunctionArgs) {
  const farmId = params.farmId ?? "00000000-0000-0000-0000-000000000001";
  const url = new URL(request.url);

  // Accept optional overrides via search params (used when coming from FarmSelector manual mode)
  const lat = parseFloat(url.searchParams.get("lat") ?? "10.787");
  const lon = parseFloat(url.searchParams.get("lon") ?? "79.1378");
  const district = url.searchParams.get("district") ?? "Thanjavur";
  const mainCrop = url.searchParams.get("main_crop") ?? "Rice";
  const areaAcres = parseFloat(url.searchParams.get("area_acres") ?? "5.0");
  const farmName = url.searchParams.get("farm_name") ?? `${district} Farm`;
  const useCache = url.searchParams.get("use_cache") !== "false";

  const backendUrl = process.env.BACKEND_URL ?? "http://farmops-backend-dev:8000";

  try {
    const queryParams = new URLSearchParams({
      farm_id: farmId,
      farm_name: farmName,
      lat: lat.toString(),
      lon: lon.toString(),
      district,
      main_crop: mainCrop,
      area_acres: areaAcres.toString(),
      use_cache: useCache.toString(),
    });

    const response = await fetch(
      `${backendUrl}/api/v1/farm/snapshot?${queryParams.toString()}`,
      { signal: AbortSignal.timeout(15_000) }
    );

    if (!response.ok) {
      const errText = await response.text().catch(() => `HTTP ${response.status}`);
      throw new Error(errText);
    }

    const body = await response.json();

    // Normalise the raw API response into SnapshotData shape
    const raw = body?.data ?? {};
    const meta = body?.metadata ?? {};

    const snapshot: SnapshotData = normaliseSnapshot(raw, meta, {
      farmId,
      farmName,
      district,
      mainCrop,
      areaAcres,
    });

    return json<LoaderData>({
      farmId,
      farmName,
      district,
      mainCrop,
      areaAcres,
      lat,
      lon,
      snapshot,
      error: null,
      cached: meta.cached ?? false,
      responseTimeMs: meta.response_time_ms ?? null,
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return json<LoaderData>(
      {
        farmId,
        farmName,
        district,
        mainCrop,
        areaAcres,
        lat,
        lon,
        snapshot: null,
        error: message,
        cached: false,
        responseTimeMs: null,
      },
      { status: 502 }
    );
  }
}

// ─── Normalise helper ────────────────────────────────────────────────────────
// Maps the backend snapshot payload (snapshot_generator.py) to SnapshotData.
//
// Backend payload keys:
//   farm, soil_summary, ndvi_trend, weather, nearest_mandi_price,
//   top_action, ai_insights, data_freshness
//
// weather shape:  { current: {temperature_c, humidity_pct, ...}, forecast_7_days, rainfall_probability_24h, source }
// ndvi_trend:     { current_value, last_14_days, trend, interpretation, confidence, source }
// soil_summary:   { type, pH, organic_carbon_pct, drainage, status, confidence, source }
// nearest_mandi_price: { commodity, market, modal_price_per_quintal, min_price_per_quintal,
//                        max_price_per_quintal, price_per_kg, trend, source, is_live_data,
//                        price_date, confidence, interpretation }

function toPercent(v: number | undefined | null): number | undefined {
  if (v == null) return undefined;
  // backend uses 0-1 scale for confidence; components expect 0-100
  return v <= 1 ? Math.round(v * 100) : v;
}

function normaliseSnapshot(
  raw: Record<string, any>,
  meta: Record<string, any>,
  farmInfo: { farmId: string; farmName: string; district: string; mainCrop: string; areaAcres: number }
): SnapshotData {
  // ── Weather ───────────────────────────────────────────────────────────────
  const rawWeather = raw.weather ?? {};
  const weatherCurrent = rawWeather.current ?? {};
  const weather = {
    current_temp_c: weatherCurrent.temperature_c ?? weatherCurrent.temp_c,
    humidity_pct: weatherCurrent.humidity_pct ?? weatherCurrent.humidity,
    rainfall_7day_mm: weatherCurrent.rainfall_7day_mm,
    rainfall_probability_24h: rawWeather.rainfall_probability_24h,
    wind_speed_kmh: weatherCurrent.wind_speed_kmh ?? weatherCurrent.wind_speed,
    condition: weatherCurrent.condition ?? weatherCurrent.description,
    forecast_7_days: rawWeather.forecast_7_days ?? rawWeather.forecast ?? [],
    source: rawWeather.source,
    confidence: toPercent(rawWeather.confidence),
  };

  // ── NDVI ──────────────────────────────────────────────────────────────────
  const rawNdvi = raw.ndvi_trend ?? {};
  const ndvi = {
    current_ndvi: rawNdvi.current_value ?? rawNdvi.current_ndvi,
    ndvi_values: rawNdvi.last_14_days ?? rawNdvi.ndvi_values ?? [],
    trend: typeof rawNdvi.trend === "string" ? rawNdvi.trend : "stable",
    interpretation: typeof rawNdvi.interpretation === "string" ? rawNdvi.interpretation : undefined,
    confidence: toPercent(rawNdvi.confidence),
  };

  // ── Soil ──────────────────────────────────────────────────────────────────
  const rawSoil = raw.soil_summary ?? {};
  const soil = {
    soil_type: rawSoil.type ?? rawSoil.soil_type,
    ph: rawSoil.pH ?? rawSoil.ph,
    organic_carbon_pct: rawSoil.organic_carbon_pct,
    nitrogen_kg_ha: rawSoil.nitrogen_kg_ha,
    phosphorus_kg_ha: rawSoil.phosphorus_kg_ha,
    potassium_kg_ha: rawSoil.potassium_kg_ha,
    drainage: rawSoil.drainage,
    texture: rawSoil.texture,
    confidence: toPercent(rawSoil.confidence),
  };

  // ── Market ────────────────────────────────────────────────────────────────
  const rawMarket = raw.nearest_mandi_price ?? {};
  const market = {
    commodity: rawMarket.commodity ?? farmInfo.mainCrop,
    modal_price_inr_per_quintal: rawMarket.modal_price_per_quintal ?? rawMarket.modal_price_inr_per_quintal,
    min_price_inr_per_quintal: rawMarket.min_price_per_quintal ?? rawMarket.min_price_inr_per_quintal,
    max_price_inr_per_quintal: rawMarket.max_price_per_quintal ?? rawMarket.max_price_inr_per_quintal,
    price_per_kg_inr: rawMarket.price_per_kg ?? rawMarket.price_per_kg_inr,
    market: rawMarket.market ?? rawMarket.market_name,
    trend: typeof rawMarket.trend === "string" ? rawMarket.trend : "stable",
    is_live_data: rawMarket.is_live_data ?? false,
    source: rawMarket.source,
    confidence: toPercent(rawMarket.confidence),
    last_updated: rawMarket.price_date,
  };

  // ── Top action ────────────────────────────────────────────────────────────
  const rawAction = raw.top_action ?? {};
  const topAction = {
    priority: rawAction.priority ?? "medium",
    action: typeof rawAction.action === "string" ? rawAction.action : undefined,
    reason: typeof rawAction.reason === "string" ? rawAction.reason : undefined,
    confidence: rawAction.confidence,
    estimated_impact: rawAction.estimated_impact,
  };

  // ── AI insights ───────────────────────────────────────────────────────────
  const aiInsights = raw.ai_insights ?? {};

  // ── Farm name from payload if available ───────────────────────────────────
  const farmFromPayload = raw.farm ?? {};
  const resolvedName = farmFromPayload.name || farmInfo.farmName;
  const resolvedDistrict = farmFromPayload.district || farmInfo.district;

  return {
    farm_id: farmInfo.farmId,
    farm_name: resolvedName,
    district: resolvedDistrict,
    main_crop: farmInfo.mainCrop,
    area_acres: farmFromPayload.area_acres ?? farmInfo.areaAcres,
    top_action: topAction,
    weather,
    ndvi,
    soil,
    market,
    overall_confidence: raw.overall_confidence ?? meta.confidence,
    data_sources: meta.sources ?? [],
    weather_insight: typeof aiInsights.weather_insight === "string" ? aiInsights.weather_insight : undefined,
    ndvi_insight: typeof aiInsights.ndvi_insight === "string" ? aiInsights.ndvi_insight : undefined,
    market_insight: typeof aiInsights.market_insight === "string" ? aiInsights.market_insight : undefined,
    generated_at: meta.timestamp ?? raw.generated_at,
    response_time_ms: meta.response_time_ms,
    cached: meta.cached ?? false,
  };
}

// ─── Component ───────────────────────────────────────────────────────────────

export default function FarmSnapshotPage() {
  const data = useLoaderData<typeof loader>();
  const parentData = useRouteLoaderData("routes/farm.$farmId") as
    | { farmName: string | null }
    | undefined;
  const navigation = useNavigation();
  const revalidator = useRevalidator();
  const [searchParams] = useSearchParams();
  const isLoading = navigation.state === "loading" || revalidator.state === "loading";

  // ── Strip use_cache=false from the URL after a successful load ────────────
  // This ensures repeat visits (bookmarks, tabs, sharing the URL) don't
  // re-trigger LLM calls. use_cache=false is only meant as a one-shot
  // "force refresh" signal — once the snapshot is generated and cached,
  // future visits should get the fast path.
  useEffect(() => {
    if (isLoading || !data.snapshot) return;

    const current = new URL(window.location.href);
    if (current.searchParams.get("use_cache") === "false") {
      current.searchParams.delete("use_cache");
      window.history.replaceState(null, "", current.toString());
    }
  }, [isLoading, data.snapshot]);

  // Prefer the parent layout's farm name (comes from URL params on first entry
  // and never loses it on tab switches), falling back to the snapshot loader's value.
  const displayFarmName = parentData?.farmName || data.farmName;

  // Show a countdown while fetching cold data (LLM can take up to 8s)
  const [elapsed, setElapsed] = useState(0);
  useEffect(() => {
    if (!isLoading) { setElapsed(0); return; }
    const t = setInterval(() => setElapsed((s) => s + 1), 1000);
    return () => clearInterval(t);
  }, [isLoading]);

  const handleRefresh = () => {
    const params = new URLSearchParams(searchParams);
    params.set("use_cache", "false");
    // Trigger a re-fetch with cache bypassed
    window.location.search = params.toString();
  };

  // ── Loading state ─────────────────────────────────────────────────────────
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50 flex flex-col items-center justify-center gap-4">
        <Spinner size="lg" />
        <div className="text-center">
          <p className="text-lg font-semibold text-gray-800">Generating Farm Snapshot…</p>
          <p className="text-sm text-gray-500 mt-1">
            {elapsed < 3
              ? "Checking cache and fetching live data…"
              : elapsed < 6
              ? "Running AI analysis with real-time tools…"
              : "Almost there — compiling insights…"}
          </p>
          <p className="text-xs text-gray-400 mt-0.5">{elapsed}s elapsed (cold: up to 8s)</p>
        </div>
        <div className="flex gap-2 text-sm text-gray-400">
          <span>🌤 Weather</span>
          <span>🛰 NDVI</span>
          <span>🏪 Mandi</span>
          <span>🌱 Soil</span>
        </div>
      </div>
    );
  }

  // ── Error state ───────────────────────────────────────────────────────────
  if (data.error || !data.snapshot) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-red-50 to-orange-50 flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-white rounded-xl shadow-lg p-6 text-center">
          <div className="text-4xl mb-3">⚠️</div>
          <h2 className="text-xl font-bold text-gray-900 mb-2">Snapshot Failed</h2>
          <p className="text-gray-600 text-sm mb-4">
            {data.error ?? "Could not generate farm snapshot. The backend may be unavailable."}
          </p>
          <div className="space-y-2">
            <Button onClick={handleRefresh} className="w-full bg-orange-500 hover:bg-orange-600">
              🔄 Try Again
            </Button>
            <Link to="/" className="block">
              <Button className="w-full bg-gray-100 text-gray-700 hover:bg-gray-200">
                ← Back to Home
              </Button>
            </Link>
          </div>
          {process.env.NODE_ENV === "development" && (
            <pre className="mt-4 text-left text-xs text-red-500 bg-red-50 p-3 rounded overflow-x-auto">
              {data.error}
            </pre>
          )}
        </div>
      </div>
    );
  }

  // ── Success state ─────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50">
      {/* Nav bar */}
      <nav className="bg-white shadow-sm sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Link to="/" className="text-green-600 hover:text-green-700 text-sm">
                ← Home
              </Link>
              <span className="text-gray-300">/</span>
              <span className="text-gray-800 font-semibold text-sm">{displayFarmName}</span>
            </div>
            <div className="flex items-center gap-3">
              <Link
                to={`/farm/${data.farmId}/recommendations?${searchParams.toString()}`}
                className="text-sm text-blue-600 hover:text-blue-700"
              >
                🌱 Crop Recs
              </Link>
              <Link
                to={`/farm/${data.farmId}/harvest?${searchParams.toString()}`}
                className="text-sm text-blue-600 hover:text-blue-700"
              >
                🚜 Harvest
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Main content */}
      <main className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <FarmSnapshotCard
          snapshot={data.snapshot}
          onRefresh={handleRefresh}
          isLoading={isLoading}
        />
      </main>

      <footer className="bg-gray-900 text-white py-6 mt-12">
        <div className="max-w-6xl mx-auto px-4 text-center">
          <p className="text-gray-400 text-sm">
            FarmOps v0.1.0 · Location-Based Insights Engine for Tamil Nadu Farmers
          </p>
        </div>
      </footer>
    </div>
  );
}
