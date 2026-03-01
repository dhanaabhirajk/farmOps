/**
 * NDVITrend Component
 *
 * Displays NDVI (vegetation health) trend as a sparkline chart.
 */

import type { FC } from "react";

export interface NDVIData {
  ndvi_values?: number[];
  current_ndvi?: number;
  trend?: string;
  interpretation?: string;
  confidence?: number;
  dates?: string[];
}

interface NDVITrendProps {
  ndvi: NDVIData;
}

const Sparkline: FC<{ values: number[]; width?: number; height?: number }> = ({
  values,
  width = 200,
  height = 50,
}) => {
  if (!values || values.length < 2) return null;

  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 0.01;

  const toX = (i: number) => (i / (values.length - 1)) * width;
  const toY = (v: number) => height - ((v - min) / range) * (height - 4) - 2;

  const pathD = values
    .map((v, i) => `${i === 0 ? "M" : "L"} ${toX(i).toFixed(1)} ${toY(v).toFixed(1)}`)
    .join(" ");

  // Fill area under the line
  const areaD =
    pathD +
    ` L ${toX(values.length - 1).toFixed(1)} ${height} L ${toX(0).toFixed(1)} ${height} Z`;

  // Color based on current NDVI
  const latest = values[values.length - 1];
  const lineColor = latest > 0.6 ? "#16a34a" : latest > 0.4 ? "#ca8a04" : "#dc2626";
  const fillColor = latest > 0.6 ? "#bbf7d0" : latest > 0.4 ? "#fef9c3" : "#fee2e2";

  return (
    <svg width={width} height={height} className="overflow-visible">
      <defs>
        <linearGradient id="ndvi-fill" x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stopColor={fillColor} stopOpacity="0.8" />
          <stop offset="100%" stopColor={fillColor} stopOpacity="0.1" />
        </linearGradient>
      </defs>
      <path d={areaD} fill="url(#ndvi-fill)" />
      <path d={pathD} fill="none" stroke={lineColor} strokeWidth="2" strokeLinejoin="round" />
      {/* Last point dot */}
      <circle
        cx={toX(values.length - 1)}
        cy={toY(latest)}
        r={3}
        fill={lineColor}
      />
    </svg>
  );
};

const getNDVILabel = (ndvi: number): { label: string; color: string; emoji: string } => {
  if (ndvi >= 0.7) return { label: "Excellent", color: "text-green-700", emoji: "🌿" };
  if (ndvi >= 0.5) return { label: "Good", color: "text-green-600", emoji: "🌱" };
  if (ndvi >= 0.3) return { label: "Moderate", color: "text-yellow-600", emoji: "🍂" };
  if (ndvi >= 0.1) return { label: "Sparse", color: "text-orange-600", emoji: "⚠️" };
  return { label: "Bare / Stressed", color: "text-red-600", emoji: "🚨" };
};

export const NDVITrend: FC<NDVITrendProps> = ({ ndvi }) => {
  const currentNDVI = ndvi.current_ndvi ?? (ndvi.ndvi_values?.at(-1) ?? 0);
  const { label, color, emoji } = getNDVILabel(currentNDVI);

  return (
    <div className="space-y-3">
      <div className="flex items-start justify-between">
        <div>
          <h4 className="font-semibold text-gray-900 text-sm">🛰 Vegetation Health (NDVI)</h4>
          <p className="text-xs text-gray-500 mt-0.5">Sentinel-2 satellite · Last 30 days</p>
        </div>
        {ndvi.confidence != null && (
          <span className="text-xs text-gray-400">Confidence: {ndvi.confidence}%</span>
        )}
      </div>

      {/* Current value */}
      <div className="flex items-center gap-3">
        <div className="text-3xl font-bold text-gray-900">{currentNDVI.toFixed(2)}</div>
        <div>
          <div className="text-xs text-gray-500">NDVI Index</div>
          <div className={`text-sm font-semibold ${color}`}>{emoji} {label}</div>
          {ndvi.trend && (
            <div className="text-xs text-gray-400 capitalize">
              Trend: {ndvi.trend === "increasing" ? "📈" : ndvi.trend === "decreasing" ? "📉" : "➡️"} {ndvi.trend}
            </div>
          )}
        </div>
      </div>

      {/* Sparkline */}
      {ndvi.ndvi_values && ndvi.ndvi_values.length >= 2 && (
        <div className="bg-gray-50 rounded-md p-2">
          <div className="flex items-end justify-between mb-1">
            <span className="text-xs text-gray-400">30-day trend</span>
            <span className="text-xs text-gray-400">
              {(Math.min(...ndvi.ndvi_values)).toFixed(2)} – {(Math.max(...ndvi.ndvi_values)).toFixed(2)}
            </span>
          </div>
          <Sparkline values={ndvi.ndvi_values} width={220} height={48} />
        </div>
      )}

      {/* Interpretation */}
      {ndvi.interpretation && (
        <p className="text-xs text-gray-600 bg-gray-50 p-2 rounded">{ndvi.interpretation}</p>
      )}

      {/* Scale reference */}
      <div className="flex gap-1 text-xs">
        {[
          { min: 0.7, label: "Excellent", color: "bg-green-500" },
          { min: 0.5, label: "Good", color: "bg-green-400" },
          { min: 0.3, label: "Moderate", color: "bg-yellow-400" },
          { min: 0.1, label: "Sparse", color: "bg-orange-400" },
          { min: 0.0, label: "Bare", color: "bg-red-400" },
        ].map(({ label: l, color: c }) => (
          <div key={l} className="flex items-center gap-0.5">
            <span className={`w-2 h-2 rounded-full inline-block ${c}`} />
            <span className="text-gray-400">{l}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default NDVITrend;
