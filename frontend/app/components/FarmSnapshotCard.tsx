/**
 * FarmSnapshotCard Component
 *
 * Aggregates all snapshot sub-components (soil, NDVI, weather, mandi, top action)
 * into a unified dashboard card.
 */

import type { FC } from "react";
import { Card } from "~/components/ui/Card";
import { SoilSummary } from "~/components/snapshot/SoilSummary";
import { NDVITrend } from "~/components/snapshot/NDVITrend";
import { WeatherForecast } from "~/components/snapshot/WeatherForecast";
import { MandiPrice } from "~/components/snapshot/MandiPrice";
import { TopActionCard } from "~/components/snapshot/TopActionCard";
import type { SoilData } from "~/components/snapshot/SoilSummary";
import type { NDVIData } from "~/components/snapshot/NDVITrend";
import type { WeatherData } from "~/components/snapshot/WeatherForecast";
import type { MandiPriceData } from "~/components/snapshot/MandiPrice";
import type { TopAction } from "~/components/snapshot/TopActionCard";

export interface SnapshotData {
  farm_id?: string;
  farm_name?: string;
  district?: string;
  main_crop?: string;
  area_acres?: number;
  top_action?: TopAction;
  weather?: WeatherData;
  ndvi?: NDVIData;
  soil?: SoilData;
  market?: MandiPriceData;
  overall_confidence?: number;
  data_sources?: string[];
  weather_insight?: string;
  ndvi_insight?: string;
  market_insight?: string;
  generated_at?: string;
  response_time_ms?: number;
  cached?: boolean;
}

interface FarmSnapshotCardProps {
  snapshot: SnapshotData;
  onRefresh?: () => void;
  isLoading?: boolean;
}

const SectionDivider: FC<{ title: string; subtitle?: string }> = ({ title, subtitle }) => (
  <div className="flex items-center gap-3 my-4">
    <div className="flex-1 border-t border-gray-200" />
    <div className="text-center">
      <span className="text-sm font-semibold text-gray-600">{title}</span>
      {subtitle && <p className="text-xs text-gray-400">{subtitle}</p>}
    </div>
    <div className="flex-1 border-t border-gray-200" />
  </div>
);

export const FarmSnapshotCard: FC<FarmSnapshotCardProps> = ({
  snapshot,
  onRefresh,
  isLoading = false,
}) => {
  const formatDate = (iso?: string) => {
    if (!iso) return null;
    try {
      return new Date(iso).toLocaleString("en-IN", {
        day: "numeric",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return iso;
    }
  };

  return (
    <div className={`space-y-4 ${isLoading ? "opacity-60 pointer-events-none" : ""}`}>
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">
            {snapshot.farm_name || `${snapshot.district || "Farm"} Snapshot`}
          </h2>
          <div className="flex items-center gap-3 mt-1">
            {snapshot.district && (
              <span className="text-sm text-gray-500">📍 {snapshot.district}</span>
            )}
            {snapshot.main_crop && (
              <span className="text-sm text-gray-500">🌾 {snapshot.main_crop}</span>
            )}
            {snapshot.area_acres && (
              <span className="text-sm text-gray-500">{snapshot.area_acres} acres</span>
            )}
          </div>
          <div className="flex items-center gap-2 mt-1">
            {snapshot.cached && (
              <span className="px-2 py-0.5 text-xs bg-blue-100 text-blue-700 rounded-full">
                ⚡ Cached
              </span>
            )}
            {snapshot.response_time_ms != null && (
              <span className="text-xs text-gray-400">
                {snapshot.response_time_ms < 1000
                  ? `${snapshot.response_time_ms.toFixed(0)}ms`
                  : `${(snapshot.response_time_ms / 1000).toFixed(1)}s`}
              </span>
            )}
            {snapshot.generated_at && (
              <span className="text-xs text-gray-400">{formatDate(snapshot.generated_at)}</span>
            )}
          </div>
        </div>
        {onRefresh && (
          <button
            onClick={onRefresh}
            disabled={isLoading}
            className="px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-md transition-colors disabled:opacity-50"
          >
            {isLoading ? "⏳ Loading…" : "🔄 Refresh"}
          </button>
        )}
      </div>

      {/* Top Action — most prominent section */}
      {snapshot.top_action && (
        <TopActionCard
          action={snapshot.top_action}
          overallConfidence={snapshot.overall_confidence}
          dataSources={snapshot.data_sources}
        />
      )}

      {/* Quick insights row */}
      {(snapshot.weather_insight || snapshot.ndvi_insight || snapshot.market_insight) && (
        <div className="grid md:grid-cols-3 gap-3">
          {snapshot.weather_insight && (
            <Card className="p-3 bg-sky-50 border border-sky-100">
              <p className="text-xs text-sky-600 font-medium mb-1">☁️ Weather Insight</p>
              <p className="text-sm text-gray-700">{snapshot.weather_insight}</p>
            </Card>
          )}
          {snapshot.ndvi_insight && (
            <Card className="p-3 bg-green-50 border border-green-100">
              <p className="text-xs text-green-600 font-medium mb-1">🛰 NDVI Insight</p>
              <p className="text-sm text-gray-700">{snapshot.ndvi_insight}</p>
            </Card>
          )}
          {snapshot.market_insight && (
            <Card className="p-3 bg-amber-50 border border-amber-100">
              <p className="text-xs text-amber-600 font-medium mb-1">🏪 Market Insight</p>
              <p className="text-sm text-gray-700">{snapshot.market_insight}</p>
            </Card>
          )}
        </div>
      )}

      <SectionDivider title="Detailed Data" />

      {/* 2-column grid for detail components */}
      <div className="grid md:grid-cols-2 gap-4">
        {/* Weather */}
        {snapshot.weather && (
          <Card className="p-4">
            <WeatherForecast weather={snapshot.weather} />
          </Card>
        )}

        {/* NDVI */}
        {snapshot.ndvi && (
          <Card className="p-4">
            <NDVITrend ndvi={snapshot.ndvi} />
          </Card>
        )}

        {/* Soil */}
        {snapshot.soil && (
          <Card className="p-4">
            <SoilSummary soil={snapshot.soil} />
          </Card>
        )}

        {/* Market */}
        {snapshot.market && (
          <Card className="p-4">
            <MandiPrice market={snapshot.market} />
          </Card>
        )}
      </div>

      {/* Navigation to other features */}
      <SectionDivider title="Next Steps" />
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { href: "recommendations", emoji: "🌱", label: "Crop Recs" },
          { href: "irrigation", emoji: "💧", label: "Irrigation" },
          { href: "harvest", emoji: "🚜", label: "Harvest Timing" },
          { href: "subsidies", emoji: "📋", label: "Subsidies" },
        ].map(({ href, emoji, label }) => (
          <a
            key={href}
            href={href}
            className="flex flex-col items-center p-3 bg-gray-50 border border-gray-200 rounded-lg hover:bg-green-50 hover:border-green-300 transition-all text-center"
          >
            <span className="text-2xl mb-1">{emoji}</span>
            <span className="text-xs font-medium text-gray-700">{label}</span>
          </a>
        ))}
      </div>
    </div>
  );
};

export default FarmSnapshotCard;
