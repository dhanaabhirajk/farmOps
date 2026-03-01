/**
 * RiskScoreIndicator Component
 * 
 * Visual indicator for overall risk score (0-1 scale).
 */

import type { FC } from "react";

interface RiskScoreIndicatorProps {
  riskScore: number; // 0.0 - 1.0
  size?: "sm" | "md" | "lg";
}

export const RiskScoreIndicator: FC<RiskScoreIndicatorProps> = ({
  riskScore,
  size = "md",
}) => {
  const getRiskLevel = (score: number): { label: string; color: string; bgColor: string } => {
    if (score < 0.25) {
      return { label: "Low Risk", color: "text-green-700", bgColor: "bg-green-100" };
    } else if (score < 0.50) {
      return { label: "Medium Risk", color: "text-yellow-700", bgColor: "bg-yellow-100" };
    } else if (score < 0.75) {
      return { label: "High Risk", color: "text-orange-700", bgColor: "bg-orange-100" };
    } else {
      return { label: "Very High Risk", color: "text-red-700", bgColor: "bg-red-100" };
    }
  };

  const risk = getRiskLevel(riskScore);
  
  const sizeClasses = {
    sm: "text-xs px-2 py-1",
    md: "text-sm px-3 py-1",
    lg: "text-base px-4 py-2",
  };

  return (
    <div className={`inline-flex items-center gap-2 rounded-full ${risk.bgColor} ${sizeClasses[size]}`}>
      <div className="relative w-12 h-2 bg-gray-200 rounded-full overflow-hidden">
        <div
          className={`absolute h-full ${riskScore < 0.25 ? 'bg-green-500' : riskScore < 0.50 ? 'bg-yellow-500' : riskScore < 0.75 ? 'bg-orange-500' : 'bg-red-500'}`}
          style={{ width: `${riskScore * 100}%` }}
        />
      </div>
      <span className={`font-semibold ${risk.color}`}>{risk.label}</span>
    </div>
  );
};
