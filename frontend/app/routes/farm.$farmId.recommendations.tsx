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
}

interface RecommendationResponse {
  success: boolean;
  data?: {
    recommended_crops: CropRecommendation[];
    season: string;
    confidence: number;
    explanation: string;
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
  const farmName = url.searchParams.get("farm_name") ?? "Farm";

  // Available seasons for Tamil Nadu
  const seasons = ["Kharif", "Rabi", "Summer", "Kar", "Samba", "Thaladi"];

  return json<LoaderData>({ farmId, farmName, seasons });
}

export async function action({ request, params }: ActionFunctionArgs) {
  if (request.method !== "POST") {
    return json({ error: "Method not allowed" }, { status: 405 });
  }

  const farmId = params.farmId;
  const formData = await request.formData();
  const season = formData.get("season") as string;

  try {
    // Call backend API (using relative path - will be proxied by Remix)
    const backendUrl = process.env.BACKEND_URL || "http://farmops-backend-dev:8000";
    const response = await fetch(`${backendUrl}/api/v1/farm/recommendations`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        farm_id: farmId,
        season: season,
        use_cache: true,
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
  const { farmId, farmName, seasons } = useLoaderData<typeof loader>();
  const [searchParams] = useSearchParams();
  const fetcher = useFetcher<RecommendationResponse>();
  const [selectedSeason, setSelectedSeason] = useState<string>("Samba");
  const [recommendations, setRecommendations] = useState<CropRecommendation[] | null>(null);
  const [confidence, setConfidence] = useState<number>(0);

  // Handle fetcher state changes
  useEffect(() => {
    if (fetcher.data) {
      if (fetcher.data.success && fetcher.data.data) {
        setRecommendations(fetcher.data.data.recommended_crops || []);
        setConfidence(fetcher.data.data.confidence || 0);
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
        <Card className="p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Select Season</h2>
          <fetcher.Form method="POST" className="space-y-4">
            <div className="flex flex-wrap gap-3 mb-4">
              {seasons.map((season) => (
                <button
                  key={season}
                  type="button"
                  onClick={() => setSelectedSeason(season)}
                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                    selectedSeason === season
                      ? "bg-blue-600 text-white"
                      : "bg-gray-200 text-gray-700 hover:bg-gray-300"
                  }`}
                >
                  {season}
                </button>
              ))}
            </div>

            <input type="hidden" name="season" value={selectedSeason} />
            
            <button
              type="submit"
              disabled={isLoading}
              className="w-full md:w-auto px-6 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-400"
            >
              {isLoading ? (
                <>
                  <Spinner size="sm" className="mr-2 inline-block" />
                  Generating Recommendations...
                </>
              ) : (
                "Get Recommendations"
              )}
            </button>
          </fetcher.Form>
        </Card>

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
