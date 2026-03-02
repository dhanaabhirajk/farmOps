/**
 * SoilMoistureIndicator component
 * Visual gauge showing current soil moisture status and depletion level.
 */

interface SoilMoisture {
  status: "critical" | "low" | "moderate" | "adequate" | "unknown";
  depletion_pct: number;
  current_moisture_mm: number;
  available_water_mm: number;
  irrigation_needed: boolean;
  urgency: "immediate" | "within_24h" | "within_3days" | "none" | "unknown";
  confidence: number;
}

interface SoilMoistureIndicatorProps {
  moisture: SoilMoisture;
}

const STATUS_CONFIG = {
  critical: { label: "Critical — Needs Water Now", color: "bg-red-500", textColor: "text-red-700", bg: "bg-red-50 border-red-200" },
  low: { label: "Low — Irrigate Soon", color: "bg-orange-400", textColor: "text-orange-700", bg: "bg-orange-50 border-orange-200" },
  moderate: { label: "Moderate", color: "bg-yellow-400", textColor: "text-yellow-700", bg: "bg-yellow-50 border-yellow-200" },
  adequate: { label: "Adequate", color: "bg-green-500", textColor: "text-green-700", bg: "bg-green-50 border-green-200" },
  unknown: { label: "Unknown", color: "bg-gray-300", textColor: "text-gray-500", bg: "bg-gray-50 border-gray-200" },
};

const URGENCY_LABELS: Record<string, string> = {
  immediate: "💧 Irrigate immediately",
  within_24h: "⚡ Irrigate within 24 hours",
  within_3days: "📅 Schedule within 3 days",
  none: "✅ No irrigation needed",
  unknown: "—",
};

export function SoilMoistureIndicator({ moisture }: SoilMoistureIndicatorProps) {
  const config = STATUS_CONFIG[moisture.status] ?? STATUS_CONFIG.unknown;
  const waterLevel = Math.max(0, 100 - moisture.depletion_pct);

  return (
    <div className={`rounded-xl border p-4 ${config.bg}`}>
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold text-gray-800 text-sm">Soil Moisture</h3>
        <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${config.textColor} bg-white border`}>
          {config.label}
        </span>
      </div>

      {/* Water level bar */}
      <div className="mb-3">
        <div className="flex justify-between text-xs text-gray-500 mb-1">
          <span>Water level</span>
          <span>{waterLevel.toFixed(0)}% of field capacity</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
          <div
            className={`h-3 rounded-full transition-all duration-500 ${config.color}`}
            style={{ width: `${waterLevel}%` }}
          />
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-2 text-xs mb-3">
        <div className="bg-white rounded-lg p-2 text-center">
          <div className="font-bold text-gray-900">{moisture.current_moisture_mm.toFixed(0)} mm</div>
          <div className="text-gray-500">Available water</div>
        </div>
        <div className="bg-white rounded-lg p-2 text-center">
          <div className="font-bold text-gray-900">{moisture.depletion_pct.toFixed(0)}%</div>
          <div className="text-gray-500">Depleted</div>
        </div>
      </div>

      {/* Urgency & confidence */}
      <div className={`text-xs font-medium ${config.textColor}`}>
        {URGENCY_LABELS[moisture.urgency] ?? URGENCY_LABELS.unknown}
      </div>
      <div className="text-xs text-gray-400 mt-1">Confidence: {moisture.confidence}%</div>
    </div>
  );
}

export type { SoilMoisture };
