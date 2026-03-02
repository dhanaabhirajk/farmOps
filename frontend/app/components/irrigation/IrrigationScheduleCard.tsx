/**
 * IrrigationScheduleCard component
 * Displays the full 14-day irrigation schedule with summary stats.
 */

import { IrrigationEventItem } from "./IrrigationEventItem";
import type { IrrigationEvent } from "./IrrigationEventItem";
import { SoilMoistureIndicator } from "./SoilMoistureIndicator";
import type { SoilMoisture } from "./SoilMoistureIndicator";

interface IrrigationScheduleSummary {
  total_irrigation_events: number;
  total_skipped_events: number;
  total_water_mm: number;
  total_cost_inr: number;
  cost_per_acre_inr: number;
  next_irrigation_date: string | null;
  current_soil_status: string;
}

interface IrrigationScheduleData {
  schedule_days: number;
  from_date: string;
  to_date: string;
  farm_data: {
    soil_type: string;
    crop_name: string;
    crop_stage: string;
    area_acres: number;
    irrigation_method: string;
  };
  current_soil_moisture: SoilMoisture;
  events: IrrigationEvent[];
  summary: IrrigationScheduleSummary;
}

interface IrrigationScheduleCardProps {
  schedule: IrrigationScheduleData;
}

const METHOD_LABELS: Record<string, string> = {
  drip: "Drip",
  sprinkler: "Sprinkler",
  flood: "Flood",
  furrow: "Furrow",
  default: "Flood",
};

export function IrrigationScheduleCard({ schedule }: IrrigationScheduleCardProps) {
  const { summary, events, current_soil_moisture, farm_data } = schedule;
  const irrigationEvents = events.filter((e) => e.action === "irrigate");
  const skipEvents = events.filter((e) => e.action === "skip");

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
        <div className="flex items-center justify-between flex-wrap gap-2 mb-3">
          <div>
            <h2 className="text-lg font-bold text-gray-900">14-Day Irrigation Schedule</h2>
            <p className="text-sm text-gray-500">
              {schedule.from_date} — {schedule.to_date}
            </p>
          </div>
          <div className="text-sm text-gray-600">
            <span className="font-medium">{farm_data.crop_name}</span>
            {" · "}
            <span className="capitalize">{farm_data.crop_stage} stage</span>
            {" · "}
            <span>{METHOD_LABELS[farm_data.irrigation_method] ?? farm_data.irrigation_method}</span>
          </div>
        </div>

        {/* Summary stats */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="bg-blue-50 rounded-lg p-3 text-center">
            <div className="text-xl font-bold text-blue-700">{summary.total_irrigation_events}</div>
            <div className="text-xs text-blue-600">Irrigations</div>
          </div>
          <div className="bg-cyan-50 rounded-lg p-3 text-center">
            <div className="text-xl font-bold text-cyan-700">{summary.total_water_mm} mm</div>
            <div className="text-xs text-cyan-600">Total water</div>
          </div>
          <div className="bg-green-50 rounded-lg p-3 text-center">
            <div className="text-xl font-bold text-green-700">₹{summary.total_cost_inr.toFixed(0)}</div>
            <div className="text-xs text-green-600">Total cost</div>
          </div>
          <div className="bg-gray-50 rounded-lg p-3 text-center">
            <div className="text-xl font-bold text-gray-700">{summary.total_skipped_events}</div>
            <div className="text-xs text-gray-500">Skipped (rain)</div>
          </div>
        </div>
      </div>

      {/* Soil moisture */}
      <SoilMoistureIndicator moisture={current_soil_moisture} />

      {/* Next irrigation alert */}
      {summary.next_irrigation_date && (
        <div className="bg-blue-600 text-white rounded-xl p-4">
          <div className="flex items-center gap-2">
            <span className="text-2xl">💧</span>
            <div>
              <div className="font-semibold">Next Irrigation</div>
              <div className="text-sm text-blue-100">
                {new Date(summary.next_irrigation_date).toLocaleDateString("en-IN", {
                  weekday: "long",
                  month: "long",
                  day: "numeric",
                })}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Events list */}
      {events.length > 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
          <h3 className="font-semibold text-gray-800 mb-3 text-sm">Schedule Events</h3>
          <div className="space-y-2">
            {events.map((event, i) => (
              <IrrigationEventItem key={`${event.date}-${i}`} event={event} />
            ))}
          </div>
        </div>
      ) : (
        <div className="bg-green-50 border border-green-200 rounded-xl p-6 text-center">
          <div className="text-3xl mb-2">☀️</div>
          <p className="text-green-700 font-medium">No irrigation needed in the next 14 days</p>
          <p className="text-green-600 text-sm mt-1">Soil moisture is adequate or rain is expected</p>
        </div>
      )}
    </div>
  );
}

export type { IrrigationScheduleData };
