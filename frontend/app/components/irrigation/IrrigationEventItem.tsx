/**
 * IrrigationEventItem component
 * Displays a single irrigation event (irrigate or skip) in the 14-day schedule.
 */

interface IrrigationEvent {
  date: string;
  day_offset: number;
  action: "irrigate" | "skip";
  water_volume_mm?: number;
  water_volume_liters?: number;
  duration_hours?: number;
  cost_inr?: number;
  soil_depletion_pct?: number;
  rain_probability?: number;
  expected_rainfall_mm?: number;
  reason: string;
  weather_note?: string;
}

interface IrrigationEventItemProps {
  event: IrrigationEvent;
}

export function IrrigationEventItem({ event }: IrrigationEventItemProps) {
  const eventDate = new Date(event.date);
  const dayLabel = event.day_offset === 0
    ? "Today"
    : event.day_offset === 1
    ? "Tomorrow"
    : eventDate.toLocaleDateString("en-IN", { weekday: "short", month: "short", day: "numeric" });

  const isIrrigate = event.action === "irrigate";

  return (
    <div
      className={`flex items-start gap-3 p-3 rounded-lg border ${
        isIrrigate
          ? "bg-blue-50 border-blue-200"
          : "bg-gray-50 border-gray-200"
      }`}
    >
      {/* Icon + date */}
      <div className="flex-shrink-0 text-center min-w-[56px]">
        <div className="text-xl">{isIrrigate ? "💧" : "🌧️"}</div>
        <div className="text-[10px] text-gray-500 mt-0.5 font-medium">{dayLabel}</div>
      </div>

      {/* Details */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span
            className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
              isIrrigate
                ? "bg-blue-100 text-blue-700"
                : "bg-gray-200 text-gray-600"
            }`}
          >
            {isIrrigate ? "Irrigate" : "Skip — Rain"}
          </span>
          {isIrrigate && event.water_volume_mm != null && (
            <span className="text-xs text-gray-500">{event.water_volume_mm} mm</span>
          )}
          {event.rain_probability != null && event.rain_probability > 0.3 && (
            <span className="text-xs text-cyan-600 font-medium">
              🌧 {Math.round(event.rain_probability * 100)}% rain
            </span>
          )}
        </div>
        <p className="text-sm text-gray-700 mt-1 leading-snug">{event.reason}</p>
        {isIrrigate && (
          <div className="mt-1 flex flex-wrap gap-x-3 gap-y-0.5 text-xs text-gray-500">
            {event.duration_hours != null && (
              <span>⏱ {event.duration_hours.toFixed(1)}h</span>
            )}
            {event.water_volume_liters != null && (
              <span>🪣 {Math.round(event.water_volume_liters).toLocaleString()} L</span>
            )}
            {event.cost_inr != null && (
              <span className="text-green-700">₹{event.cost_inr.toFixed(0)}</span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export type { IrrigationEvent };
