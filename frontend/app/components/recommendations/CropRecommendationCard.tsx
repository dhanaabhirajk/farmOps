/**
 * CropRecommendationCard Component
 * 
 * Displays a single crop recommendation with yield, profit, risk, and planting window.
 */

import type { FC } from "react";
import { Card } from "../ui/Card";
import { RiskScoreIndicator } from "./RiskScoreIndicator";

export interface CropRecommendation {
  rank: number;
  crop_name: string;
  expected_yield_kg_acre: number;
  expected_revenue_per_acre: number;
  expected_cost_per_acre: number;
  expected_profit_per_acre: number;
  planting_window: {
    start: string;
    end: string;
  } | null;
  water_requirement_mm: number;
  risk_score: {
    drought_risk: number;
    pest_risk: number;
    market_risk: number;
    overall: number;
  };
}

interface CropRecommendationCardProps {
  recommendation: CropRecommendation;
  isTopChoice?: boolean;
}

export const CropRecommendationCard: FC<CropRecommendationCardProps> = ({
  recommendation,
  isTopChoice = false,
}) => {
  const profitMargin =
    ((recommendation.expected_profit_per_acre /
      recommendation.expected_revenue_per_acre) *
      100) || 0;

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const formatDate = (dateStr: string) => {
    try {
      const [month, day] = dateStr.split("-");
      const date = new Date(2024, parseInt(month) - 1, parseInt(day));
      return date.toLocaleDateString("en-IN", { month: "short", day: "numeric" });
    } catch {
      return dateStr;
    }
  };

  return (
    <Card className={`p-6 ${isTopChoice ? "border-green-500 border-2" : ""}`}>
      <div className="flex items-start justify-between mb-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-sm font-medium text-gray-500">
              #{recommendation.rank}
            </span>
            <h3 className="text-2xl font-bold text-gray-900">
              {recommendation.crop_name}
            </h3>
            {isTopChoice && (
              <span className="px-2 py-1 text-xs font-semibold text-green-700 bg-green-100 rounded">
                Top Choice
              </span>
            )}
          </div>
          <p className="text-sm text-gray-600">
            Expected Yield: {recommendation.expected_yield_kg_acre.toFixed(0)} kg/acre
          </p>
        </div>
        <RiskScoreIndicator riskScore={recommendation.risk_score.overall} />
      </div>

      {/* Financial Breakdown */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="p-3 bg-blue-50 rounded">
          <p className="text-xs text-gray-600 mb-1">Expected Revenue</p>
          <p className="text-lg font-bold text-blue-700">
            {formatCurrency(recommendation.expected_revenue_per_acre)}
          </p>
          <p className="text-xs text-gray-500">per acre</p>
        </div>
        
        <div className="p-3 bg-red-50 rounded">
          <p className="text-xs text-gray-600 mb-1">Production Cost</p>
          <p className="text-lg font-bold text-red-700">
            {formatCurrency(recommendation.expected_cost_per_acre)}
          </p>
          <p className="text-xs text-gray-500">per acre</p>
        </div>
        
        <div className="p-3 bg-green-50 rounded col-span-2">
          <p className="text-xs text-gray-600 mb-1">Expected Profit</p>
          <p className="text-2xl font-bold text-green-700">
            {formatCurrency(recommendation.expected_profit_per_acre)}
          </p>
          <p className="text-xs text-gray-500">
            Margin: {profitMargin.toFixed(1)}%
          </p>
        </div>
      </div>

      {/* Planting Window */}
      {recommendation.planting_window && (
        <div className="mb-4 p-3 bg-purple-50 rounded">
          <p className="text-xs text-gray-600 mb-1">Planting Window</p>
          <p className="text-sm font-semibold text-purple-700">
            {formatDate(recommendation.planting_window.start)} -{" "}
            {formatDate(recommendation.planting_window.end)}
          </p>
        </div>
      )}

      {/* Risk Breakdown */}
      <div className="grid grid-cols-3 gap-2 text-xs">
        <div>
          <p className="text-gray-600">Drought Risk</p>
          <p className={`font-semibold ${recommendation.risk_score.drought_risk > 0.5 ? 'text-red-600' : 'text-green-600'}`}>
            {(recommendation.risk_score.drought_risk * 100).toFixed(0)}%
          </p>
        </div>
        <div>
          <p className="text-gray-600">Pest Risk</p>
          <p className={`font-semibold ${recommendation.risk_score.pest_risk > 0.5 ? 'text-red-600' : 'text-green-600'}`}>
            {(recommendation.risk_score.pest_risk * 100).toFixed(0)}%
          </p>
        </div>
        <div>
          <p className="text-gray-600">Market Risk</p>
          <p className={`font-semibold ${recommendation.risk_score.market_risk > 0.5 ? 'text-red-600' : 'text-green-600'}`}>
            {(recommendation.risk_score.market_risk * 100).toFixed(0)}%
          </p>
        </div>
      </div>

      {/* Water Requirement */}
      <div className="mt-4 pt-4 border-t border-gray-200">
        <p className="text-xs text-gray-600">
          Water Requirement: <span className="font-semibold">{recommendation.water_requirement_mm} mm/season</span>
        </p>
      </div>
    </Card>
  );
};
