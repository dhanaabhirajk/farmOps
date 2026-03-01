/**
 * WeatherForecast Component
 *
 * Displays current weather conditions and 7-day forecast.
 */

import type { FC } from "react";

export interface WeatherDay {
  date?: string;
  day?: string;
  max_temp_c?: number;
  min_temp_c?: number;
  rainfall_mm?: number;
  humidity_pct?: number;
  rain_probability?: number;
  condition?: string;
}

export interface WeatherData {
  current_temp_c?: number;
  humidity_pct?: number;
  rainfall_7day_mm?: number;
  rainfall_probability_24h?: number;
  wind_speed_kmh?: number;
  condition?: string;
  forecast_7_days?: WeatherDay[];
  source?: string;
  confidence?: number;
}

interface WeatherForecastProps {
  weather: WeatherData;
}

const WeatherIcon: FC<{ condition?: string; rainProb?: number }> = ({ condition, rainProb }) => {
  const c = (condition || "").toLowerCase();
  if (rainProb != null && rainProb > 0.7) return <>🌧</>;
  if (rainProb != null && rainProb > 0.4) return <>🌦</>;
  if (c.includes("rain") || c.includes("storm")) return <>🌧</>;
  if (c.includes("cloud") || c.includes("overcast")) return <>⛅</>;
  if (c.includes("mist") || c.includes("fog")) return <>🌫</>;
  return <>☀️</>;
};

const RainBar: FC<{ prob: number }> = ({ prob }) => (
  <div className="w-full bg-blue-100 rounded-full h-1.5 mt-1">
    <div
      className="bg-blue-500 h-1.5 rounded-full"
      style={{ width: `${(prob * 100).toFixed(0)}%` }}
    />
  </div>
);

export const WeatherForecast: FC<WeatherForecastProps> = ({ weather }) => {
  return (
    <div className="space-y-4">
      <div className="flex items-start justify-between">
        <div>
          <h4 className="font-semibold text-gray-900 text-sm">🌤 Weather</h4>
          {weather.source && (
            <p className="text-xs text-gray-400 mt-0.5">Source: {weather.source}</p>
          )}
        </div>
        {weather.confidence != null && (
          <span className="text-xs text-gray-400">Confidence: {weather.confidence}%</span>
        )}
      </div>

      {/* Current conditions */}
      <div className="grid grid-cols-2 gap-3">
        {weather.current_temp_c != null && (
          <div className="p-3 bg-orange-50 rounded-lg text-center">
            <div className="text-2xl">🌡️</div>
            <div className="text-2xl font-bold text-orange-700">{weather.current_temp_c}°C</div>
            <div className="text-xs text-gray-500">Temperature</div>
          </div>
        )}
        {weather.humidity_pct != null && (
          <div className="p-3 bg-blue-50 rounded-lg text-center">
            <div className="text-2xl">💧</div>
            <div className="text-2xl font-bold text-blue-700">{weather.humidity_pct}%</div>
            <div className="text-xs text-gray-500">Humidity</div>
          </div>
        )}
        {weather.rainfall_7day_mm != null && (
          <div className="p-3 bg-indigo-50 rounded-lg text-center">
            <div className="text-2xl">🌧</div>
            <div className="text-2xl font-bold text-indigo-700">{weather.rainfall_7day_mm} mm</div>
            <div className="text-xs text-gray-500">7-day Rainfall</div>
          </div>
        )}
        {weather.rainfall_probability_24h != null && (
          <div className="p-3 bg-cyan-50 rounded-lg text-center">
            <div className="text-2xl">☔</div>
            <div className="text-2xl font-bold text-cyan-700">
              {(weather.rainfall_probability_24h * 100).toFixed(0)}%
            </div>
            <div className="text-xs text-gray-500">Rain Probability Today</div>
          </div>
        )}
        {weather.wind_speed_kmh != null && (
          <div className="p-3 bg-gray-50 rounded-lg text-center">
            <div className="text-2xl">💨</div>
            <div className="text-2xl font-bold text-gray-700">{weather.wind_speed_kmh} km/h</div>
            <div className="text-xs text-gray-500">Wind Speed</div>
          </div>
        )}
      </div>

      {/* 7-day forecast */}
      {weather.forecast_7_days && weather.forecast_7_days.length > 0 && (
        <div>
          <h5 className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
            7-Day Forecast
          </h5>
          <div className="overflow-x-auto">
            <div className="flex gap-2 min-w-max">
              {weather.forecast_7_days.map((day, i) => (
                <div
                  key={i}
                  className="flex flex-col items-center bg-gray-50 rounded-lg px-3 py-2 min-w-[60px]"
                >
                  <span className="text-xs text-gray-500 mb-1">
                    {day.day || (day.date ? new Date(day.date).toLocaleDateString("en-IN", { weekday: "short" }) : `D${i + 1}`)}
                  </span>
                  <span className="text-lg">
                    <WeatherIcon condition={day.condition} rainProb={day.rain_probability} />
                  </span>
                  {day.max_temp_c != null && (
                    <span className="text-xs font-bold text-gray-800">{day.max_temp_c}°</span>
                  )}
                  {day.min_temp_c != null && (
                    <span className="text-xs text-gray-400">{day.min_temp_c}°</span>
                  )}
                  {day.rain_probability != null && (
                    <>
                      <span className="text-xs text-blue-600 mt-1">
                        {(day.rain_probability * 100).toFixed(0)}%
                      </span>
                      <RainBar prob={day.rain_probability} />
                    </>
                  )}
                  {day.rainfall_mm != null && day.rainfall_mm > 0 && (
                    <span className="text-xs text-blue-400">{day.rainfall_mm}mm</span>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Rain alert */}
      {weather.rainfall_probability_24h != null && weather.rainfall_probability_24h > 0.7 && (
        <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg text-sm">
          🌧 <strong>Heavy rain expected today</strong> — consider postponing irrigation and field operations.
        </div>
      )}
    </div>
  );
};

export default WeatherForecast;
