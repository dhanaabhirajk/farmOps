/**
 * PlantingWindowCalendar Component
 * 
 * Displays a visual calendar highlighting the optimal planting window for a crop.
 */

import type { FC } from "react";

export interface PlantingWindowCalendarProps {
  /** Planting window start (MM-DD format) */
  startDate: string;
  /** Planting window end (MM-DD format) */
  endDate: string;
  /** Crop name */
  cropName: string;
  /** Season name */
  season?: string;
}

export const PlantingWindowCalendar: FC<PlantingWindowCalendarProps> = ({
  startDate,
  endDate,
  cropName,
  season,
}) => {
  // Parse MM-DD format
  const parseDate = (dateStr: string): { month: number; day: number } => {
    const [month, day] = dateStr.split("-").map(Number);
    return { month, day };
  };

  const start = parseDate(startDate);
  const end = parseDate(endDate);

  // Month names
  const monthNames = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
  ];

  // Check if month is in planting window
  const isInWindow = (monthIndex: number): boolean => {
    // Handle year wrapping (e.g., Nov to Jan)
    if (start.month <= end.month) {
      return monthIndex + 1 >= start.month && monthIndex + 1 <= end.month;
    } else {
      return monthIndex + 1 >= start.month || monthIndex + 1 <= end.month;
    }
  };

  // Format date for display
  const formatDate = (dateStr: string): string => {
    const { month, day } = parseDate(dateStr);
    return `${monthNames[month - 1]} ${day}`;
  };

  return (
    <div className="border border-gray-200 rounded-lg p-4 bg-white">
      {/* Header */}
      <div className="mb-4">
        <h3 className="font-semibold text-gray-900 mb-1">Planting Window</h3>
        <p className="text-sm text-gray-600">
          Optimal time to plant {cropName}
          {season && ` in ${season} season`}
        </p>
      </div>

      {/* Calendar Grid */}
      <div className="grid grid-cols-6 gap-2 mb-4">
        {monthNames.map((month, index) => (
          <div
            key={month}
            className={`relative text-center py-3 rounded-lg transition-all ${
              isInWindow(index)
                ? "bg-green-100 border-2 border-green-500 text-green-700 font-semibold"
                : "bg-gray-50 border border-gray-200 text-gray-500"
            }`}
          >
            <span className="text-xs">{month}</span>
            {isInWindow(index) && (
              <div className="absolute top-0 right-0 w-2 h-2 bg-green-500 rounded-full m-1" />
            )}
          </div>
        ))}
      </div>

      {/* Date Range Display */}
      <div className="bg-green-50 border border-green-200 rounded-lg p-3">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs text-green-600 font-medium mb-1">Start Date</p>
            <p className="text-sm font-bold text-green-700">{formatDate(startDate)}</p>
          </div>
          <div className="text-green-400">
            <svg
              className="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M13 7l5 5m0 0l-5 5m5-5H6"
              />
            </svg>
          </div>
          <div className="text-right">
            <p className="text-xs text-green-600 font-medium mb-1">End Date</p>
            <p className="text-sm font-bold text-green-700">{formatDate(endDate)}</p>
          </div>
        </div>
      </div>

      {/* Recommendation Note */}
      <div className="mt-3 pt-3 border-t border-gray-200">
        <p className="text-xs text-gray-600">
          <span className="font-medium">💡 Tip:</span> Planting within this window gives the best
          chance of success. Consider local weather patterns and soil moisture levels.
        </p>
      </div>
    </div>
  );
};
