import React from 'react';
import { json, type LoaderFunctionArgs } from '@remix-run/node';
import { useOutletContext, useLoaderData, Link, useSearchParams } from '@remix-run/react';
import { Leaf, Sprout, RefreshCw, ChevronRight, Clock, AlertCircle } from 'lucide-react';
import { cn } from '~/lib/utils'; // Use our Remix util

interface CropItem {
  name: string;
  expected_yield_kg_acre: number;
  production_cost_per_acre: number;
  expected_profit_per_acre: number;
  risk_score: number;
  planting_window: { start: string; end: string } | null;
  harvest_window: { start: string; end: string } | null;
  duration_days: number;
  water_requirement_mm: string;
  reason: string;
  confidence: number;
}

interface PersistedRec {
  id: string;
  confidence: number;
  explanation: string;
  model_version: string;
  created_at: string;
  expires_at: string | null;
  human_review_required: boolean;
  payload: {
    season: string;
    recommended_crops: CropItem[];
    explanation: string;
    confidence: number;
    generated_at: string;
  };
}

export async function loader({ params, request }: LoaderFunctionArgs) {
  const farmId = params.farmId;
  if (!farmId) return json({ farmId: '', persistedRecs: [] as PersistedRec[] });

  const backendUrl = process.env.BACKEND_URL || 'http://farmops-backend-dev:8000';
  try {
    const res = await fetch(
      `${backendUrl}/api/v1/farm/recommendations/${farmId}?status=active&limit=5`,
      { headers: { 'Content-Type': 'application/json' } }
    );
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const body = await res.json();
    const rows: PersistedRec[] = body?.data?.recommendations ?? [];
    return json({ farmId, persistedRecs: rows });
  } catch (err) {
    console.error('[planning] failed to load recommendations:', err);
    return json({ farmId, persistedRecs: [] as PersistedRec[] });
  }
}

export default function PlanningRoute() {
  const { farmData } = useOutletContext<{ farmData: any }>();
  const { farmId, persistedRecs } = useLoaderData<typeof loader>();
  const [searchParams] = useSearchParams();
  const recsPath = `/farm/${farmId}/recommendations?${searchParams.toString()}`;

  // Flatten persisted recs → array of crop items with extra context
  const persistedCrops: Array<CropItem & { recId: string; season: string; recCreatedAt: string; humanReview: boolean; recConfidence: number }> =
    persistedRecs.flatMap((rec) =>
      (rec.payload?.recommended_crops ?? []).map((crop) => ({
        ...crop,
        recId: rec.id,
        season: rec.payload?.season ?? '',
        recCreatedAt: rec.created_at,
        humanReview: rec.human_review_required,
        recConfidence: rec.confidence,
      }))
    );

  // Still support legacy farmData.crops if present
  const activeCrops = farmData?.crops || [];

  return (
    <div className="space-y-8">
      {/* Active Crops Section */}
      <div className="space-y-6">
        <h2 className="font-serif font-bold text-xl flex items-center gap-2">
            <Leaf className="w-5 h-5 text-farm-green" /> Crop Planning
        </h2>

        {activeCrops.length === 0 ? (
          <div className="p-8 bg-white rounded-3xl border border-gray-100 text-center">
            <Sprout className="w-12 h-12 text-gray-300 mx-auto mb-3" />
            <p className="text-gray-500">No active crops planned yet.</p>
          </div>
        ) : (
          <div>{/* Active crops list would go here */}</div>
        )}
      </div>

      {/* Persisted Recommendations from DB */}
      <div className="bg-white p-6 rounded-3xl shadow-sm border border-gray-100">
        <div className="flex items-center justify-between mb-1">
          <h2 className="font-serif font-bold text-xl">Planting Recommendations</h2>
          <Link
            to={recsPath}
            className="text-xs text-farm-green font-medium flex items-center gap-1 hover:underline"
          >
            Get new <ChevronRight className="w-3 h-3" />
          </Link>
        </div>
        <p className="text-gray-500 text-sm mb-6">Saved AI recommendations based on your soil, climate &amp; market.</p>

        {persistedCrops.length === 0 ? (
          <div className="text-center py-8">
            <Sprout className="w-10 h-10 text-gray-300 mx-auto mb-3" />
            <p className="text-gray-500 mb-3">No saved recommendations yet.</p>
            <Link
              to={recsPath}
              className="inline-flex items-center gap-2 px-4 py-2 bg-farm-green text-white rounded-xl text-sm font-medium hover:bg-farm-green/90 transition-colors"
            >
              <RefreshCw className="w-4 h-4" /> Generate Recommendations
            </Link>
          </div>
        ) : (
          <>
            {/* Season badge for latest batch */}
            {persistedCrops[0]?.season && (
              <div className="flex items-center gap-2 mb-4">
                <span className="text-xs bg-farm-green/10 text-farm-green font-semibold px-3 py-1 rounded-full">
                  Season: {persistedCrops[0].season}
                </span>
                <span className="text-xs text-gray-400 flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  Saved {persistedCrops[0].recCreatedAt.slice(0, 10)}
                </span>
                {persistedCrops[0].humanReview && (
                  <span className="text-xs bg-yellow-100 text-yellow-700 font-semibold px-2 py-0.5 rounded-full flex items-center gap-1">
                    <AlertCircle className="w-3 h-3" /> Needs Review
                  </span>
                )}
              </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {persistedCrops.map((crop, i) => (
                <div
                  key={`${crop.recId}-${i}`}
                  className="border border-gray-200 rounded-2xl p-5 hover:shadow-md transition-shadow relative overflow-hidden"
                >
                  {i === 0 && (
                    <div className="absolute top-0 right-0 bg-farm-green text-white text-[10px] font-bold px-3 py-1 rounded-bl-xl">
                      TOP PICK
                    </div>
                  )}

                  <div className="flex justify-between items-start mb-3">
                    <h3 className="font-bold text-lg text-gray-900">{crop.name}</h3>
                    <span className={cn(
                      "text-xs font-bold px-2 py-1 rounded-full",
                      crop.risk_score < 0.3
                        ? "bg-green-100 text-green-700"
                        : crop.risk_score < 0.6
                        ? "bg-yellow-100 text-yellow-700"
                        : "bg-red-100 text-red-700"
                    )}>
                      {crop.risk_score < 0.3 ? "Low Risk" : crop.risk_score < 0.6 ? "Med Risk" : "High Risk"}
                    </span>
                  </div>

                  <p className="text-sm text-gray-600 mb-4 min-h-[40px] line-clamp-3">
                    {crop.reason}
                  </p>

                  <div className="grid grid-cols-2 gap-3 mb-4">
                    <div className="bg-gray-50 p-3 rounded-xl">
                      <p className="text-xs text-gray-500">Est. Profit/acre</p>
                      <p className="font-bold text-farm-green text-sm">
                        ₹{crop.expected_profit_per_acre != null ? Math.round(crop.expected_profit_per_acre).toLocaleString('en') : '—'}
                      </p>
                    </div>
                    <div className="bg-gray-50 p-3 rounded-xl">
                      <p className="text-xs text-gray-500">Yield/acre</p>
                      <p className="font-bold text-gray-900 text-sm">
                        {crop.expected_yield_kg_acre != null ? Math.round(crop.expected_yield_kg_acre).toLocaleString('en') : '—'} kg
                      </p>
                    </div>
                    <div className="bg-gray-50 p-3 rounded-xl">
                      <p className="text-xs text-gray-500">Duration</p>
                      <p className="font-bold text-gray-900 text-sm">
                        {crop.duration_days ? `${crop.duration_days} days` : '—'}
                      </p>
                    </div>
                    <div className="bg-gray-50 p-3 rounded-xl">
                      <p className="text-xs text-gray-500">Water need</p>
                      <p className="font-bold text-gray-900 text-sm">{crop.water_requirement_mm ?? '—'}</p>
                    </div>
                  </div>

                  {crop.planting_window && (
                    <div className="text-xs text-gray-500 mb-4 border-t pt-3">
                      <span className="font-medium text-gray-700">Plant: </span>
                      {crop.planting_window.start} – {crop.planting_window.end}
                      {crop.harvest_window && (
                        <>
                          <span className="mx-2 text-gray-300">|</span>
                          <span className="font-medium text-gray-700">Harvest: </span>
                          {crop.harvest_window.start} – {crop.harvest_window.end}
                        </>
                      )}
                    </div>
                  )}

                  <div className="flex items-center justify-between mb-3">
                    <span className="text-xs text-gray-400">
                      Confidence: <strong>{crop.recConfidence}%</strong>
                    </span>
                  </div>

                  <Link
                    to={recsPath}
                    className="block w-full py-2 text-center border border-farm-green text-farm-green rounded-xl text-sm font-medium hover:bg-farm-green hover:text-white transition-colors"
                  >
                    Full Plan
                  </Link>
                </div>
              ))}
            </div>

            <div className="mt-6 text-center">
              <Link
                to={recsPath}
                className="inline-flex items-center gap-2 text-sm text-farm-green hover:underline"
              >
                <RefreshCw className="w-4 h-4" /> Regenerate for a different season
              </Link>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
