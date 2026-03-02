/**
 * MandiPrice Component
 *
 * Displays current mandi (market) prices for a crop.
 */

import type { FC } from "react";

export interface MandiPriceData {
  commodity?: string;
  modal_price_inr_per_quintal?: number;
  min_price_inr_per_quintal?: number;
  max_price_inr_per_quintal?: number;
  price_per_kg_inr?: number;
  market?: string;
  state?: string;
  trend?: string;
  trend_direction?: "up" | "down" | "stable";
  is_live_data?: boolean;
  source?: string;
  confidence?: number;
  last_updated?: string;
}

interface MandiPriceProps {
  market: MandiPriceData;
}

const TrendIcon: FC<{ trend?: string; direction?: string }> = ({ trend, direction }) => {
  const t = (direction || trend || "").toLowerCase();
  if (t.includes("up") || t.includes("rising") || t.includes("increasing"))
    return <span className="text-green-600">📈</span>;
  if (t.includes("down") || t.includes("falling") || t.includes("decreasing"))
    return <span className="text-red-600">📉</span>;
  return <span className="text-gray-500">➡️</span>;
};

const formatINR = (amount: number) =>
  new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(amount);

export const MandiPrice: FC<MandiPriceProps> = ({ market }) => {
  const spread = market.max_price_inr_per_quintal && market.min_price_inr_per_quintal
    ? market.max_price_inr_per_quintal - market.min_price_inr_per_quintal
    : null;

  return (
    <div className="space-y-3">
      <div className="flex items-start justify-between">
        <div>
          <h4 className="font-semibold text-gray-900 text-sm">🏪 Mandi Prices</h4>
          {market.market && (
            <p className="text-xs text-gray-400 mt-0.5">
              {market.market}{market.state ? `, ${market.state}` : ""}
            </p>
          )}
        </div>
        <div className="flex flex-col items-end gap-0.5">
          {market.is_live_data && (
            <span className="px-2 py-0.5 text-xs font-semibold bg-green-100 text-green-700 rounded-full">
              ● Live
            </span>
          )}
          {market.confidence != null && (
            <span className="text-xs text-gray-400">Confidence: {market.confidence}%</span>
          )}
        </div>
      </div>

      {/* Commodity name */}
      {market.commodity && (
        <div className="text-sm font-medium text-gray-700 capitalize">{market.commodity}</div>
      )}

      {/* Modal price (primary display) */}
      {market.modal_price_inr_per_quintal != null && (
        <div className="bg-gradient-to-r from-green-50 to-emerald-50 rounded-lg p-4">
          <div className="flex items-end gap-2">
            <div>
              <div className="text-xs text-gray-500 mb-0.5">Modal Price</div>
              <div className="text-3xl font-bold text-gray-900">
                {formatINR(market.modal_price_inr_per_quintal)}
              </div>
              <div className="text-sm text-gray-500">per quintal</div>
            </div>
            <div className="ml-auto text-right">
              <TrendIcon trend={market.trend} direction={market.trend_direction} />
              <div className="text-xs text-gray-500 capitalize mt-0.5">{market.trend || "stable"}</div>
            </div>
          </div>

          {market.price_per_kg_inr != null && (
            <div className="text-sm text-gray-600 mt-1">
              ≈ {formatINR(market.price_per_kg_inr)} / kg
            </div>
          )}
        </div>
      )}

      {/* Price range */}
      {market.min_price_inr_per_quintal != null && market.max_price_inr_per_quintal != null && (
        <div>
          <div className="flex justify-between text-xs text-gray-500 mb-1">
            <span>Min: {formatINR(market.min_price_inr_per_quintal)}</span>
            {spread != null && <span>Spread: {formatINR(spread)}</span>}
            <span>Max: {formatINR(market.max_price_inr_per_quintal)}</span>
          </div>
          {/* Price range bar */}
          {market.modal_price_inr_per_quintal != null && (
            <div className="relative w-full bg-gray-200 rounded-full h-2">
              <div
                className="absolute bg-green-500 h-2 rounded-full"
                style={{
                  left: `${((market.min_price_inr_per_quintal / market.max_price_inr_per_quintal) * 100).toFixed(1)}%`,
                  width: `${(((market.max_price_inr_per_quintal - market.min_price_inr_per_quintal) / market.max_price_inr_per_quintal) * 100).toFixed(1)}%`,
                }}
              />
              <div
                className="absolute w-3 h-3 bg-white border-2 border-green-600 rounded-full -top-0.5 transform -translate-x-1/2"
                style={{
                  left: `${(((market.modal_price_inr_per_quintal - market.min_price_inr_per_quintal) /
                    (market.max_price_inr_per_quintal - market.min_price_inr_per_quintal || 1)) * 100).toFixed(1)}%`,
                }}
              />
            </div>
          )}
        </div>
      )}

      {/* Source + timestamp */}
      <div className="flex items-center justify-between text-xs text-gray-400 border-t pt-2">
        {market.source && <span>Source: {market.source}</span>}
        {market.last_updated && (
          <span>Updated: {new Date(market.last_updated).toLocaleDateString("en-IN")}</span>
        )}
      </div>
    </div>
  );
};

export default MandiPrice;
