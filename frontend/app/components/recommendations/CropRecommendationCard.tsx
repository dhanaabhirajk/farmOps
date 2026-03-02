/**
 * CropRecommendationCard Component
 * 
 * Displays a single crop recommendation with yield, profit, risk, planting window,
 * and LLM-generated AI insights.
 */

import type { FC } from "react";
import { Card } from "../ui/Card";
import { RiskScoreIndicator } from "./RiskScoreIndicator";

export interface AiInsight {
  why_this_crop: string;
  key_risks: string;
  planting_tip: string;
  harvest_advice: string;
  one_liner: string;
}

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
  ai_insight?: AiInsight;
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

  const formatCurrency = (amount: number) =>
    new Intl.NumberFormat("en", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0,
    }).format(amount);

  // SSR-safe date formatter: "MM-DD" → "Mar 15"
  const formatDate = (dateStr: string) => {
    try {
      const parts = dateStr.split("-");
      if (parts.length === 2) {
        const months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
        return `${months[parseInt(parts[0]) - 1] ?? parts[0]} ${parts[1]}`;
      }
      return dateStr;
    } catch {
      return dateStr;
    }
  };

  const insight = recommendation.ai_insight;

  return (
    <Card className={`p-6 ${isTopChoice ? "border-green-500 border-2" : ""}`}>
      {/* Header */}
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
          {/* AI one-liner */}
          {insight?.one_liner && (
            <p className="mt-1.5 text-xs font-medium text-indigo-600 italic">
              ✦ {insight.one_liner}
            </p>
          )}
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
            {formatDate(recommendation.planting_window.start)} –{" "}
            {formatDate(recommendation.planting_window.end)}
          </p>
        </div>
      )}

      {/* Risk Breakdown */}
      <div className="grid grid-cols-3 gap-2 text-xs mb-4">
        <div>
          <p className="text-gray-600">Drought Risk</p>
          <p className={`font-semibold ${recommendation.risk_score.drought_risk > 0.5 ? "text-red-600" : "text-green-600"}`}>
            {(recommendation.risk_score.drought_risk * 100).toFixed(0)}%
          </p>
        </div>
        <div>
          <p className="text-gray-600">Pest Risk</p>
          <p className={`font-semibold ${recommendation.risk_score.pest_risk > 0.5 ? "text-red-600" : "text-green-600"}`}>
            {(recommendation.risk_score.pest_risk * 100).toFixed(0)}%
          </p>
        </div>
        <div>
          <p className="text-gray-600">Market Risk</p>
          <p className={`font-semibold ${recommendation.risk_score.market_risk > 0.5 ? "text-red-600" : "text-green-600"}`}>
            {(recommendation.risk_score.market_risk * 100).toFixed(0)}%
          </p>
        </div>
      </div>

      {/* Water Requirement */}
      <div className="pt-3 border-t border-gray-200">
        <p className="text-xs text-gray-600">
          Water Requirement:{" "}
          <span className="font-semibold">{recommendation.water_requirement_mm} mm/season</span>
        </p>
      </div>

      {/* ── AI Insights ─────────────────────────────────────────────────────── */}
      {insight && (
        <div className="mt-5 pt-4 border-t border-indigo-100">
          <div className="flex items-center gap-1.5 mb-3">
            <span className="text-base">🤖</span>
            <p className="text-xs font-bold uppercase tracking-widest text-indigo-600">
              AI Insights
            </p>
          </div>
          <div className="space-y-3">
            {insight.why_this_crop && (
              <div className="p-3 bg-indigo-50 rounded-lg">
                <p className="text-xs font-semibold text-indigo-700 mb-1">Why This Crop</p>
                <p className="text-sm text-gray-700 leading-relaxed">{insight.why_this_crop}</p>
              </div>
            )}
            {insight.key_risks && (
              <div className="p-3 bg-amber-50 rounded-lg">
                <p className="text-xs font-semibold text-amber-700 mb-1">⚠ Key Risks</p>
                <p className="text-sm text-gray-700 leading-relaxed">{insight.key_risks}</p>
              </div>
            )}
            <div className="grid grid-cols-2 gap-3">
              {insight.planting_tip && (
                <div className="p-3 bg-green-50 rounded-lg">
                  <p className="text-xs font-semibold text-green-700 mb-1">🌱 Planting Tip</p>
                  <p className="text-xs text-gray-700 leading-relaxed">{insight.planting_tip}</p>
                </div>
              )}
              {insight.harvest_advice && (
                <div className="p-3 bg-orange-50 rounded-lg">
                  <p className="text-xs font-semibold text-orange-700 mb-1">🌾 Harvest & Sell</p>
                  <p className="text-xs text-gray-700 leading-relaxed">{insight.harvest_advice}</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </Card>
  );
};
