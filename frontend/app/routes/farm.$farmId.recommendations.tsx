/**
 * Crop Recommendations Route
 * 
 * Allows farmers to get crop recommendations for their farm based on season.
 */

import type { ActionFunctionArgs, LoaderFunctionArgs, MetaFunction } from "@remix-run/node";
import { json } from "@remix-run/node";
import { Form, Link, useLoaderData, useNavigation, useFetcher, useSearchParams } from "@remix-run/react";
import { useState, useEffect } from "react";
import { CropRecommendationCard } from "~/components/recommendations/CropRecommendationCard";
import type { CropRecommendation } from "~/components/recommendations/CropRecommendationCard";
import { Button } from "~/components/ui/Button";
import { Card } from "~/components/ui/Card";
import { Spinner } from "~/components/ui/Spinner";

export const meta: MetaFunction = () => {
  return [
    { title: "Crop Recommendations - FarmOps" },
    { name: "description", content: "Get AI-powered crop recommendations for your farm" },
  ];
};

interface LoaderData {
  farmId: string;
  farmName: string;
  seasons: string[];
  district: string | null;
  lat: number | null;
  lon: number | null;
  mainCrop: string | null;
  areaAcres: number | null;
}

interface AiSummary {
  summary: string;
  action_items: string[];
}

interface RecommendationResponse {
  success: boolean;
  data?: {
    recommended_crops: CropRecommendation[];
    season: string;
    confidence: number;
    explanation: string;
    ai_summary?: AiSummary;
    tool_calls: Array<any>;
  };
  error?: string;
  metadata?: {
    cached: boolean;
    response_time_ms: number;
    timestamp: string;
  };
}

export async function loader({ params, request }: LoaderFunctionArgs) {
  const farmId = params.farmId || "00000000-0000-0000-0000-000000000000";
  const url = new URL(request.url);
  const farmName  = url.searchParams.get("farm_name") ?? "Farm";
  const district  = url.searchParams.get("district")  ?? null;
  const lat       = parseFloat(url.searchParams.get("lat") ?? "") || null;
  const lon       = parseFloat(url.searchParams.get("lon") ?? "") || null;
  const mainCrop  = url.searchParams.get("main_crop")  ?? null;
  const areaAcres = parseFloat(url.searchParams.get("area_acres") ?? "") || null;

  // Available seasons for Tamil Nadu
  const seasons = ["Kharif", "Rabi", "Summer", "Kar", "Samba", "Thaladi"];

  return json({ farmId, farmName, seasons, district, lat, lon, mainCrop, areaAcres });
}

export async function action({ request, params }: ActionFunctionArgs) {
  if (request.method !== "POST") {
    return json({ error: "Method not allowed" }, { status: 405 });
  }

  const farmId = params.farmId;
  const formData = await request.formData();
  const season    = formData.get("season")     as string;
  const district  = formData.get("district")   as string | null;
  const lat       = parseFloat(formData.get("lat")        as string) || null;
  const lon       = parseFloat(formData.get("lon")        as string) || null;
  const mainCrop  = formData.get("main_crop")  as string | null;
  const areaAcres = parseFloat(formData.get("area_acres") as string) || null;

  try {
    // Call backend API (using relative path - will be proxied by Remix)
    const backendUrl = process.env.BACKEND_URL || "http://farmops-backend-dev:8000";
    const response = await fetch(`${backendUrl}/api/v1/farm/recommendations`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        farm_id:    farmId,
        season,
        use_cache:  true,
        ...(district  && { district }),
        ...(lat       && { lat }),
        ...(lon       && { lon }),
        ...(mainCrop  && { main_crop: mainCrop }),
        ...(areaAcres && { area_acres: areaAcres }),
      }),
    });

    if (!response.ok) {
      throw new Error(`Backend error: ${response.status}`);
    }

    const result = (await response.json()) as RecommendationResponse;
    return json(result);
  } catch (err) {
    return json(
      { 
        success: false, 
        error: err instanceof Error ? err.message : "Failed to get recommendations" 
      } as RecommendationResponse
    );
  }
}

export default function FarmRecommendations() {
  const { farmId, farmName, seasons, district, lat, lon, mainCrop, areaAcres } = useLoaderData<typeof loader>();
  const [searchParams] = useSearchParams();
  const fetcher = useFetcher<RecommendationResponse>();
  const [selectedSeason, setSelectedSeason] = useState<string>("Samba");
  const [recommendations, setRecommendations] = useState<CropRecommendation[] | null>(null);
  const [confidence, setConfidence] = useState<number>(0);
  const [aiSummary, setAiSummary] = useState<AiSummary | null>(null);

  // Handle fetcher state changes
  useEffect(() => {
    if (fetcher.data) {
      if (fetcher.data.success && fetcher.data.data) {
        setRecommendations(fetcher.data.data.recommended_crops || []);
        setConfidence(fetcher.data.data.confidence || 0);
        setAiSummary(fetcher.data.data.ai_summary ?? null);
      }
    }
  }, [fetcher.data]);

  const isLoading = fetcher.state === "submitting";
  const error = fetcher.data?.success === false ? fetcher.data.error : null;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Nav bar */}
      <nav className="bg-white shadow-sm sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Link to="/" className="text-green-600 hover:text-green-700 text-sm">
                ← Home
              </Link>
              <span className="text-gray-300">/</span>
              <Link
                to={`/farm/${farmId}/snapshot?${searchParams.toString()}`}
                className="text-green-600 hover:text-green-700 text-sm"
              >
                ← Snapshot
              </Link>
              <span className="text-gray-300">/</span>
              <span className="text-gray-800 font-semibold text-sm">{farmName} — Crop Recs</span>
            </div>
            <div className="flex items-center gap-3">
              <Link
                to={`/farm/${farmId}/snapshot?${searchParams.toString()}`}
                className="text-sm text-blue-600 hover:text-blue-700"
              >
                📸 Snapshot
              </Link>
              <Link
                to={`/farm/${farmId}/irrigation?${searchParams.toString()}`}
                className="text-sm text-blue-600 hover:text-blue-700"
              >
                💧 Irrigation
              </Link>
            </div>
          </div>
        </div>
      </nav>

      <div className="p-4 md:p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Crop Recommendations
          </h1>
          <p className="text-gray-600">
            Get AI-powered crop recommendations based on your farm's soil, climate, and market conditions
          </p>
        </div>

        {/* Season Selection */}
        <div className="mb-6 rounded-2xl border border-green-200 bg-gradient-to-br from-green-50 to-emerald-50 p-6 shadow-sm">
          <div className="flex items-center gap-2 mb-5">
            <span className="text-xl">🌾</span>
            <h2 className="text-lg font-bold text-green-900">Select Season</h2>
            {district && (
              <span className="ml-auto text-xs text-green-700 bg-green-100 border border-green-200 px-2 py-0.5 rounded-full">
                📍 {district}
              </span>
            )}
          </div>
          <fetcher.Form method="POST" className="space-y-5">
            <div className="grid grid-cols-3 sm:grid-cols-6 gap-2">
              {seasons.map((season) => (
                <button
                  key={season}
                  type="button"
                  onClick={() => setSelectedSeason(season)}
                  className={`relative py-2.5 px-3 rounded-xl text-sm font-semibold transition-all duration-150 border ${
                    selectedSeason === season
                      ? "bg-green-600 text-white border-green-700 shadow-md scale-105"
                      : "bg-white text-green-800 border-green-200 hover:bg-green-100 hover:border-green-400"
                  }`}
                >
                  {season}
                  {selectedSeason === season && (
                    <span className="absolute -top-1 -right-1 w-3 h-3 bg-amber-400 rounded-full border-2 border-white" />
                  )}
                </button>
              ))}
            </div>

            <input type="hidden" name="season"     value={selectedSeason} />
            {district  && <input type="hidden" name="district"   value={district} />}
            {lat       && <input type="hidden" name="lat"        value={lat} />}
            {lon       && <input type="hidden" name="lon"        value={lon} />}
            {mainCrop  && <input type="hidden" name="main_crop"  value={mainCrop} />}
            {areaAcres && <input type="hidden" name="area_acres" value={areaAcres} />}

            <button
              type="submit"
              disabled={isLoading}
              className="flex items-center gap-2 px-6 py-2.5 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white rounded-xl font-semibold shadow-sm transition-colors"
            >
              {isLoading ? (
                <>
                  <Spinner size="sm" className="inline-block" />
                  Generating Recommendations…
                </>
              ) : (
                <>
                  <span>✨</span> Get Recommendations
                </>
              )}
            </button>
          </fetcher.Form>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-700 font-medium">Error: {error}</p>
          </div>
        )}

        {/* Recommendations */}
        {recommendations && recommendations.length > 0 && (
          <>
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-2xl font-semibold text-gray-900">
                Top Recommendations for {selectedSeason} Season
              </h2>
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-600">Confidence:</span>
                <span className="text-lg font-bold text-blue-600">
                  {confidence.toFixed(0)}%
                </span>
              </div>
            </div>

            {/* AI Season Strategy Summary */}
            {aiSummary && (
              <div className="mb-6 p-5 bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-xl shadow-sm">
                <div className="flex items-center gap-2 mb-3">
                  <span className="text-2xl">🌾</span>
                  <h3 className="font-bold text-green-900 text-lg">AI Season Strategy</h3>
                  <span className="ml-auto text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full font-medium">
                    Mistral AI
                  </span>
                </div>
                <p className="text-sm text-gray-700 mb-3 leading-relaxed">{aiSummary.summary}</p>
                {aiSummary.action_items && aiSummary.action_items.length > 0 && (
                  <ul className="space-y-1">
                    {aiSummary.action_items.map((item, i) => (
                      <li key={i} className="text-xs text-gray-600 flex items-start gap-2">
                        <span className="text-green-500 mt-0.5 shrink-0">→</span>
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}

            <div className="grid gap-6 md:grid-cols-1 lg:grid-cols-1">
              {recommendations.map((rec, index) => (
                <CropRecommendationCard
                  key={`${rec.crop_name}-${index}`}
                  recommendation={rec}
                  isTopChoice={index === 0}
                />
              ))}
            </div>

            {/* Additional Info */}
            <Card className="mt-6 p-6 bg-blue-50">
              <h3 className="font-semibold text-blue-900 mb-2">
                ℹ️ How to Use These Recommendations
              </h3>
              <ul className="text-sm text-blue-800 space-y-1">
                <li>• Rankings are based on expected profit adjusted for risk</li>
                <li>• Profit estimates include current market prices and production costs</li>
                <li>• Plant within the recommended window for best results</li>
                <li>• Consider your available resources (water, labor, capital)</li>
                <li>• Diversify crops to reduce overall risk</li>
              </ul>
            </Card>
          </>
        )}

        {/* Empty State */}
        {!isLoading && !recommendations && !error && (
          <Card className="p-12 text-center">
            <div className="text-gray-400 mb-4">
              <svg
                className="w-16 h-16 mx-auto"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              No Recommendations Yet
            </h3>
            <p className="text-gray-600">
              Select a season and click "Get Recommendations" to see AI-powered crop suggestions
            </p>
          </Card>
        )}
      </div>
      </div>
    </div>
  );
}
