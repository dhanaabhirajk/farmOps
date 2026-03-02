/**
 * SoilSummary Component
 *
 * Displays a soil profile summary card with key metrics.
 */

import type { FC } from "react";

export interface SoilData {
  soil_type?: string;
  ph?: number;
  organic_carbon_pct?: number;
  nitrogen_kg_ha?: number;
  phosphorus_kg_ha?: number;
  potassium_kg_ha?: number;
  drainage?: string;
  texture?: string;
  confidence?: number;
}

interface SoilSummaryProps {
  soil: SoilData;
}

const PHBadge: FC<{ ph: number }> = ({ ph }) => {
  let label = "Neutral";
  let color = "bg-green-100 text-green-700";
  if (ph < 5.5) { label = "Acidic"; color = "bg-red-100 text-red-700"; }
  else if (ph < 6.5) { label = "Slightly Acidic"; color = "bg-yellow-100 text-yellow-700"; }
  else if (ph > 7.5) { label = "Alkaline"; color = "bg-blue-100 text-blue-700"; }
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-semibold ${color}`}>{label}</span>
  );
};

const NutrientBar: FC<{ label: string; value: number; max: number; unit: string; color: string }> = ({
  label, value, max, unit, color,
}) => {
  const pct = Math.min((value / max) * 100, 100);
  const level = pct < 30 ? "Low" : pct < 60 ? "Medium" : "High";
  const levelColor = pct < 30 ? "text-red-600" : pct < 60 ? "text-yellow-600" : "text-green-600";
  return (
    <div>
      <div className="flex justify-between text-xs mb-1">
        <span className="text-gray-600 font-medium">{label}</span>
        <span className="text-gray-800">{value} {unit} · <span className={levelColor}>{level}</span></span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div
          className={`h-2 rounded-full ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
};

export const SoilSummary: FC<SoilSummaryProps> = ({ soil }) => {
  return (
    <div className="space-y-4">
      <div className="flex items-start justify-between">
        <div>
          <h4 className="font-semibold text-gray-900 text-sm">🌱 Soil Profile</h4>
          {soil.soil_type && (
            <p className="text-gray-600 text-xs mt-0.5">{soil.soil_type} · {soil.texture || "—"}</p>
          )}
        </div>
        {soil.confidence != null && (
          <span className="text-xs text-gray-400">
            Confidence: {soil.confidence}%
          </span>
        )}
      </div>

      {/* pH */}
      {soil.ph != null && (
        <div className="flex items-center gap-3">
          <div className="text-2xl font-bold text-gray-900">{soil.ph.toFixed(1)}</div>
          <div>
            <div className="text-xs text-gray-500">pH Value</div>
            <PHBadge ph={soil.ph} />
          </div>
        </div>
      )}

      {/* Organic Carbon */}
      {soil.organic_carbon_pct != null && (
        <div className="p-2 bg-amber-50 rounded-md">
          <div className="flex justify-between text-xs">
            <span className="text-amber-700 font-medium">Organic Carbon</span>
            <span className="text-amber-900 font-bold">{soil.organic_carbon_pct.toFixed(2)}%</span>
          </div>
          <div className="w-full bg-amber-200 rounded-full h-1.5 mt-1">
            <div
              className="bg-amber-500 h-1.5 rounded-full"
              style={{ width: `${Math.min(soil.organic_carbon_pct / 2 * 100, 100)}%` }}
            />
          </div>
          <p className="text-xs text-amber-600 mt-0.5">
            {soil.organic_carbon_pct < 0.5 ? "Low — consider organic amendments" :
             soil.organic_carbon_pct < 1.0 ? "Moderate — good baseline" :
             "High — excellent organic matter"}
          </p>
        </div>
      )}

      {/* NPK */}
      <div className="space-y-2">
        {soil.nitrogen_kg_ha != null && (
          <NutrientBar
            label="Nitrogen (N)"
            value={soil.nitrogen_kg_ha}
            max={500}
            unit="kg/ha"
            color="bg-green-500"
          />
        )}
        {soil.phosphorus_kg_ha != null && (
          <NutrientBar
            label="Phosphorus (P)"
            value={soil.phosphorus_kg_ha}
            max={80}
            unit="kg/ha"
            color="bg-orange-500"
          />
        )}
        {soil.potassium_kg_ha != null && (
          <NutrientBar
            label="Potassium (K)"
            value={soil.potassium_kg_ha}
            max={400}
            unit="kg/ha"
            color="bg-purple-500"
          />
        )}
      </div>

      {/* Drainage */}
      {soil.drainage && (
        <div className="text-xs text-gray-500 border-t pt-2">
          Drainage: <span className="font-medium text-gray-700 capitalize">{soil.drainage}</span>
        </div>
      )}
    </div>
  );
};

export default SoilSummary;
