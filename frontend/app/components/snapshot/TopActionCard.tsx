/**
 * TopActionCard Component
 *
 * Displays the AI-generated top priority action for the farmer.
 */

import type { FC } from "react";

export interface TopAction {
  priority?: "high" | "medium" | "low";
  action?: string;
  reason?: string;
  confidence?: number;
  deadline?: string;
  estimated_impact?: string;
}

interface TopActionCardProps {
  action: TopAction;
  overallConfidence?: number;
  dataSources?: string[];
  llmModel?: string;
}

const PriorityBadge: FC<{ priority?: string }> = ({ priority }) => {
  const p = (priority || "medium").toLowerCase();
  const config = {
    high: { label: "🔴 High Priority", classes: "bg-red-100 text-red-700 border-red-200" },
    medium: { label: "🟡 Medium Priority", classes: "bg-yellow-100 text-yellow-700 border-yellow-200" },
    low: { label: "🟢 Low Priority", classes: "bg-green-100 text-green-700 border-green-200" },
  };
  const { label, classes } = config[p as keyof typeof config] || config.medium;
  return (
    <span className={`px-3 py-1 text-xs font-semibold rounded-full border ${classes}`}>
      {label}
    </span>
  );
};

const ConfidenceGauge: FC<{ confidence: number }> = ({ confidence }) => {
  const pct = Math.min(Math.max(confidence, 0), 100);
  const color = pct >= 75 ? "bg-green-500" : pct >= 50 ? "bg-yellow-500" : "bg-red-500";
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 bg-gray-200 rounded-full h-2">
        <div className={`${color} h-2 rounded-full transition-all`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs font-bold text-gray-700 w-8 text-right">{pct}%</span>
    </div>
  );
};

export const TopActionCard: FC<TopActionCardProps> = ({
  action,
  overallConfidence,
  dataSources,
  llmModel,
}) => {
  return (
    <div
      className={`rounded-xl border-2 p-5 ${
        action.priority === "high"
          ? "border-red-300 bg-red-50"
          : action.priority === "low"
          ? "border-green-300 bg-green-50"
          : "border-yellow-300 bg-yellow-50"
      }`}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xl">🎯</span>
            <h4 className="font-bold text-gray-900">Top Priority Action</h4>
          </div>
          <PriorityBadge priority={action.priority} />
        </div>
        {action.deadline && (
          <div className="text-right">
            <div className="text-xs text-gray-500">Deadline</div>
            <div className="text-sm font-semibold text-gray-800">{action.deadline}</div>
          </div>
        )}
      </div>

      {/* Action */}
      {action.action && (
        <div className="mb-3">
          <p className="text-lg font-bold text-gray-900">{action.action}</p>
        </div>
      )}

      {/* Reason */}
      {action.reason && (
        <div className="p-3 bg-white/60 rounded-lg mb-3">
          <p className="text-xs text-gray-500 font-medium mb-1 uppercase tracking-wide">Why</p>
          <p className="text-sm text-gray-700">{action.reason}</p>
        </div>
      )}

      {/* Estimated impact */}
      {action.estimated_impact && (
        <div className="p-3 bg-white/60 rounded-lg mb-3">
          <p className="text-xs text-gray-500 font-medium mb-1 uppercase tracking-wide">Expected Impact</p>
          <p className="text-sm text-gray-700">{action.estimated_impact}</p>
        </div>
      )}

      {/* AI confidence */}
      {(action.confidence != null || overallConfidence != null) && (
        <div className="border-t pt-3 mt-3">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs text-gray-500 font-medium">AI Confidence</span>
            {llmModel && <span className="text-xs text-gray-400">{llmModel}</span>}
          </div>
          <ConfidenceGauge confidence={action.confidence ?? overallConfidence ?? 0} />
        </div>
      )}

      {/* Data sources */}
      {dataSources && dataSources.length > 0 && (
        <div className="mt-3 pt-3 border-t">
          <p className="text-xs text-gray-400 mb-1">Data Sources</p>
          <div className="flex flex-wrap gap-1">
            {dataSources.map((src) => (
              <span
                key={src}
                className="px-2 py-0.5 text-xs bg-white/70 text-gray-600 rounded border border-gray-200"
              >
                {src}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default TopActionCard;
