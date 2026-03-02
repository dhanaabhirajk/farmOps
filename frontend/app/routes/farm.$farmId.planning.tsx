import React, { useEffect, useState } from 'react';
import { json, type LoaderFunctionArgs } from '@remix-run/node';
import { useOutletContext, useLoaderData, Link } from '@remix-run/react';
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
  const { persistedRecs } = useLoaderData<typeof loader>();

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

      {/* Recommendations Section */}
      <div className="bg-white p-6 rounded-3xl shadow-sm border border-gray-100">
        <h2 className="font-serif font-bold text-xl mb-2">New Planting Recommendations</h2>
        <p className="text-gray-500 text-sm mb-6">Based on your soil and season.</p>
        
        {recommendations.length === 0 ? (
          <p className="text-gray-500 italic">No recommendations available from backend yet.</p>
        ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {recommendations.map((rec: any, i: number) => (
            <div key={rec.id} className="border border-gray-200 rounded-2xl p-5 hover:shadow-md transition-shadow relative overflow-hidden group">
              {i === 0 && (
                <div className="absolute top-0 right-0 bg-farm-green text-white text-[10px] font-bold px-3 py-1 rounded-bl-xl">
                  TOP PICK
                </div>
              )}
              
              <div className="flex justify-between items-start mb-4">
                <h3 className="font-bold text-lg text-gray-900">{rec.crop}</h3>
                <div className="text-right">
                  <span className={cn(
                    "text-xs font-bold px-2 py-1 rounded-full",
                    rec.riskScore < 0.3 ? "bg-green-100 text-green-700" : "bg-yellow-100 text-yellow-700"
                  )}>
                    {rec.riskScore < 0.3 ? "Low Risk" : "Medium Risk"}
                  </span>
                </div>
              </div>
              
              <p className="text-sm text-gray-600 mb-4 min-h-[40px]">{rec.reason}</p>
              
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div className="bg-gray-50 p-3 rounded-xl">
                  <p className="text-xs text-gray-500">Est. Profit</p>
                  <p className="font-bold text-farm-green">{rec.metrics.profit}</p>
                </div>
                <div className="bg-gray-50 p-3 rounded-xl">
                  <p className="text-xs text-gray-500">Duration</p>
                  <p className="font-bold text-gray-900">{rec.metrics.duration}</p>
                </div>
              </div>
              
              <button 
                className="w-full py-2 border border-farm-green text-farm-green rounded-xl font-medium hover:bg-farm-green hover:text-white transition-colors"
                onClick={() => alert("Implementation coming soon: Select plan via API")}
              >
                Select Plan
              </button>
            </div>
          ))}
        </div>
        )}
      </div>
    </div>
  );
}
