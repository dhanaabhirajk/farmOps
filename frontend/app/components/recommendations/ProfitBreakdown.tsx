/**
 * ProfitBreakdown Component
 * 
 * Displays detailed cost and revenue breakdown for a crop recommendation.
 */

import type { FC } from "react";

export interface CostBreakdown {
  seeds: number;
  fertilizer: number;
  pesticides: number;
  labor: number;
  irrigation: number;
  machinery: number;
  miscellaneous: number;
}

export interface ProfitBreakdownProps {
  /** Expected revenue per acre */
  revenue: number;
  /** Total production cost per acre */
  totalCost: number;
  /** Detailed cost breakdown */
  costBreakdown?: CostBreakdown;
  /** Currency symbol */
  currency?: string;
}

export const ProfitBreakdown: FC<ProfitBreakdownProps> = ({
  revenue,
  totalCost,
  costBreakdown,
  currency = "₹",
}) => {
  const profit = revenue - totalCost;
  const profitMarginPercent = revenue > 0 ? (profit / revenue) * 100 : 0;

  const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const costItems = costBreakdown
    ? [
        { label: "Seeds", amount: costBreakdown.seeds, color: "bg-blue-100 text-blue-700" },
        { label: "Fertilizer", amount: costBreakdown.fertilizer, color: "bg-green-100 text-green-700" },
        { label: "Pesticides", amount: costBreakdown.pesticides, color: "bg-orange-100 text-orange-700" },
        { label: "Labor", amount: costBreakdown.labor, color: "bg-purple-100 text-purple-700" },
        { label: "Irrigation", amount: costBreakdown.irrigation, color: "bg-cyan-100 text-cyan-700" },
        { label: "Machinery", amount: costBreakdown.machinery, color: "bg-yellow-100 text-yellow-700" },
        { label: "Miscellaneous", amount: costBreakdown.miscellaneous, color: "bg-gray-100 text-gray-700" },
      ]
    : [];

  // Calculate percentage of total cost for each item
  const costItemsWithPercentage = costItems
    .filter((item) => item.amount > 0)
    .map((item) => ({
      ...item,
      percentage: (item.amount / totalCost) * 100,
    }))
    .sort((a, b) => b.amount - a.amount);

  return (
    <div className="space-y-4">
      {/* Summary Cards */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-xs text-blue-600 font-medium mb-1">Revenue</p>
          <p className="text-lg font-bold text-blue-700">{formatCurrency(revenue)}</p>
        </div>

        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-xs text-red-600 font-medium mb-1">Total Cost</p>
          <p className="text-lg font-bold text-red-700">{formatCurrency(totalCost)}</p>
        </div>

        <div className={`${profit >= 0 ? "bg-green-50 border-green-200" : "bg-red-50 border-red-200"} border rounded-lg p-4`}>
          <p className={`text-xs ${profit >= 0 ? "text-green-600" : "text-red-600"} font-medium mb-1`}>
            Net Profit
          </p>
          <p className={`text-lg font-bold ${profit >= 0 ? "text-green-700" : "text-red-700"}`}>
            {formatCurrency(profit)}
          </p>
          <p className={`text-xs ${profit >= 0 ? "text-green-600" : "text-red-600"}`}>
            {profitMarginPercent.toFixed(1)}% margin
          </p>
        </div>
      </div>

      {/* Cost Breakdown */}
      {costBreakdown && costItemsWithPercentage.length > 0 && (
        <div className="border border-gray-200 rounded-lg p-4">
          <h4 className="font-semibold text-gray-900 mb-3">Cost Breakdown</h4>
          <div className="space-y-2">
            {costItemsWithPercentage.map((item) => (
              <div key={item.label} className="flex items-center gap-3">
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium text-gray-700">{item.label}</span>
                    <span className="text-sm font-semibold text-gray-900">
                      {formatCurrency(item.amount)}
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-300 ${
                        item.color.split(" ")[0].replace("100", "500")
                      }`}
                      style={{ width: `${item.percentage}%` }}
                    />
                  </div>
                </div>
                <span className="text-xs text-gray-500 w-12 text-right">
                  {item.percentage.toFixed(0)}%
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Profit Analysis */}
      <div className="border border-gray-200 rounded-lg p-4 bg-gray-50">
        <h4 className="font-semibold text-gray-900 mb-2">Profit Analysis</h4>
        <div className="space-y-1 text-sm text-gray-700">
          <p>
            • <span className="font-medium">Revenue per acre:</span> {formatCurrency(revenue)}
          </p>
          <p>
            • <span className="font-medium">Cost per acre:</span> {formatCurrency(totalCost)}
          </p>
          <p>
            • <span className="font-medium">Profit per acre:</span>{" "}
            <span className={profit >= 0 ? "text-green-600 font-semibold" : "text-red-600 font-semibold"}>
              {formatCurrency(profit)}
            </span>
          </p>
          <p>
            • <span className="font-medium">Profit margin:</span>{" "}
            <span className={profitMarginPercent >= 20 ? "text-green-600 font-semibold" : "text-yellow-600 font-semibold"}>
              {profitMarginPercent.toFixed(1)}%
            </span>
          </p>
        </div>
      </div>
    </div>
  );
};
