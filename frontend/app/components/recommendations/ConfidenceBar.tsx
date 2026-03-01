/**
 * ConfidenceBar Component
 * 
 * Displays a confidence score as a horizontal progress bar with color coding.
 */

import type { FC } from "react";

export interface ConfidenceBarProps {
  /** Confidence score (0-100) */
  confidence: number;
  /** Optional label */
  label?: string;
  /** Size variant */
  size?: "sm" | "md" | "lg";
  /** Show percentage text */
  showPercentage?: boolean;
}

export const ConfidenceBar: FC<ConfidenceBarProps> = ({
  confidence,
  label = "Confidence",
  size = "md",
  showPercentage = true,
}) => {
  const clampedConfidence = Math.min(100, Math.max(0, confidence));

  // Color based on confidence level
  const getConfidenceColor = (score: number): string => {
    if (score >= 80) return "bg-green-500";
    if (score >= 60) return "bg-blue-500";
    if (score >= 40) return "bg-yellow-500";
    return "bg-red-500";
  };

  const getTextColor = (score: number): string => {
    if (score >= 80) return "text-green-700";
    if (score >= 60) return "text-blue-700";
    if (score >= 40) return "text-yellow-700";
    return "text-red-700";
  };

  // Size variants
  const sizeClasses = {
    sm: "h-2",
    md: "h-3",
    lg: "h-4",
  };

  const textSizeClasses = {
    sm: "text-xs",
    md: "text-sm",
    lg: "text-base",
  };

  return (
    <div className="w-full">
      {/* Header */}
      <div className="flex items-center justify-between mb-1">
        <span className={`font-medium text-gray-700 ${textSizeClasses[size]}`}>
          {label}
        </span>
        {showPercentage && (
          <span className={`font-bold ${getTextColor(clampedConfidence)} ${textSizeClasses[size]}`}>
            {clampedConfidence.toFixed(0)}%
          </span>
        )}
      </div>

      {/* Progress Bar */}
      <div className={`w-full bg-gray-200 rounded-full overflow-hidden ${sizeClasses[size]}`}>
        <div
          className={`${getConfidenceColor(clampedConfidence)} rounded-full transition-all duration-300 ${
            sizeClasses[size]
          }`}
          style={{ width: `${clampedConfidence}%` }}
        />
      </div>

      {/* Optional description */}
      {clampedConfidence < 50 && (
        <p className="text-xs text-gray-500 mt-1">
          Low confidence - recommendation may be less reliable
        </p>
      )}
    </div>
  );
};
